# encoding: utf-8
"""
#earthquake
"""

import logging
from skypehub.handlers import on_message, on_time
from time import time
from lxml import html
import re
from datetime import datetime
from models import *
from utils import scrape
from django.utils import simplejson as json
from django.conf import settings

from django.utils.encoding import force_unicode

TENKI_JP_URL = getattr(settings, 'SKYPE_EARTHQUAKE_TENKI_JP_URL', "http://tenki.jp/earthquake/")

logger = logging.getLogger("django.skypehub.earthquake")

MIN_MAGNITUDE=getattr(settings, 'SKYPE_EARTHQUAKE_MIN_MAGNITUDE', 3)
POLL_INTERVAL=getattr(settings, 'SKYPE_EARTHQUAKE_POLL_INTERVAL', 15)
PLACES=map(lambda x: map(lambda y: re.compile(y), x), getattr(settings, 'SKYPE_EARTHQUAKE_PLACES', (('.*', '.*', '.*'),)))

def format_intensity(d):
    retval = []
    intensity, places = d
    retval.append(u"""%s:""" % intensity)
    for place in places:
        retval.append(u"""%s, %s, %s""" % (
            place['prefecture'],
            " ".join(place['area']),
            " ".join(place['district']),
        ))
    retval.append("")
    return "\n".join(retval)

def format_latitude(value):
    if value is not None:
        return u'%s%.2f度' % ((u'北緯', u'南緯')[value < 0], value)
    else:
        return u'不明'

def format_longitude(value):
    if value is not None:
        return u'%s%.2f度' % ((u'東経', u'西経')[value < 0], value)
    else:
        return u'不明'


def format_event(d):
    return u"""%(year)d年%(month)d月%(day)d日%(hour)d時%(minute)d分ごろ地震がありました。%(message)s
震源: %(place)s %(magnitude)s %(depth)s [%(latitude)s %(longitude)s]
%(map_image_url)s
%(intensity_table)s
各地の震度は http://tenki.jp/earthquake/detail-%(event_id)s.html を参照してください。
(%(updated_at_year)d年%(updated_at_month)d月%(updated_at_day)d日%(updated_at_hour)d時%(updated_at_minute)d分 更新)
""" % dict(
        event_id=d['id'],
        year=d['time'].year,
        month=d['time'].month,
        day=d['time'].day,
        hour=d['time'].hour,
        minute=d['time'].minute,
        message=d['message'],
        place=d['place']['area'],
        magnitude=d['magnitude'],
        depth=d['depth'],
        latitude=format_latitude(d['place']['latitude']),
        longitude=format_longitude(d['place']['longitude']),
        map_image_url=d['map_image_url'] or u"",
        intensity_table=len(d['intensity_table']) > 0 and format_intensity(d['intensity_table'][0]) or "",
        updated_at_year=d['updated_at'].year,
        updated_at_month=d['updated_at'].month,
        updated_at_day=d['updated_at'].day,
        updated_at_hour=d['updated_at'].hour,
        updated_at_minute=d['updated_at'].minute)

def receiver(handler, message, status):
    g = re.match(ur"#earthquake(?:\s+(\S+))?", message.Body)
    if g:
        command = g.group(1)
        if not command:
            last_event = Event.last()
            if last_event is None:
                message.Chat.SendMessage(u"データがありません")
            else:
                message.Chat.SendMessage(format_event(last_event.todict()))
        elif command == u"on":
            # Register
            room, created = BroadcastRoom.objects.get_or_create(
                chat_name = message.Chat.Name,
                defaults={'sender': message.Sender.Handle},
            )
            if created:
                message.Chat.SendMessage(u"この部屋を登録しました。")
            else:
                message.Chat.SendMessage(u"この部屋はすでに登録しています。")
        elif command == u"off":
            # Unregister
            BroadcastRoom.objects.filter(chat_name = message.Chat.Name).delete()
            message.Chat.SendMessage(u"この部屋の登録を外しました。")

def poller(handler, time):
    try:
        logger.info("Fetching %s" % TENKI_JP_URL)
        data = scrape(html.parse(TENKI_JP_URL))
        try:
            last_event = Event.objects.get(event_id=data['id'])
        except Event.DoesNotExist:
            last_event = None

        updated=False
        if last_event is None:
            logger.info("New event with id %s" % data['id'])
            last_event = Event.fromdict(data)
            last_event.save()
            updated=True
        elif last_event.updated_at < data['updated_at']:
            event_dict = last_event.todict()
            if (event_dict['time'] != data['time'] or
                    event_dict['magnitude'] != data['magnitude'] or
                    event_dict['place']['area'] != data['place']['area'] or
                    event_dict['place']['latitude'] != data['place']['latitude'] or
                    event_dict['place']['longitude'] != data['place']['longitude'] or
                    len(event_dict['intensity_table']) != len(data['intensity_table'])):
                logger.info("Event %s updated" % data['id'])
                last_event.populatewithdict(data)
                last_event.save()
                updated=True

        place_intensity_hit = False
        if data['place']['area'] != u'不明' and data['intensity_table']:
            logger.debug("Checking PLACES...")
            for intensity, intensity_table in data['intensity_table']:
                if intensity >= (u"震度%s" % MIN_MAGNITUDE):
                    for intensity_data in intensity_table:
                        logger.debug(u"Checking intensity: %s %s %s" % (
                            intensity_data['prefecture'],
                            intensity_data['area'],
                            intensity_data['district'],
                        ))
                        for prefecture, area, district in PLACES:
                            logger.debug(u"Checking area: %s %s %s" % (
                                force_unicode(prefecture),
                                force_unicode(area),
                                force_unicode(district)
                            ))
                            if (prefecture.match(intensity_data['prefecture']) and
                               not not filter(lambda a: area.match(a), intensity_data['area']) and
                               not not filter(lambda d: district.match(d), intensity_data['district'])):
                                logging.info(u"Intensity hit: %s==%s %s==%s %s==%s (%s >= %s)" % (
                                    intensity_data['prefecture'], prefecture,
                                    intensity_data['area'], area,
                                    intensity_data['district'], district,
                                    intensity, (u"震度%s" % MIN_MAGNITUDE)))
                                place_intensity_hit = True


        if (updated and place_intensity_hit):
            for room in BroadcastRoom.objects.all():
                handler.skype.Chat(room.chat_name).SendMessage(format_event(data))
    except Exception, e:
        logger.exception(str(e))
    handler.connect(poller, time + POLL_INTERVAL)

on_message.connect(receiver)
on_time.connect(poller, time() + 5)
