#:coding=utf-8:

from django.db import models
try:
    import json
except ImportError:
    from django.utils import simplejson as json
from datetime import datetime

__all__ = (
    'BroadcastRoom',
    'Event',
)

class BroadcastRoom(models.Model):
    sender = models.CharField(u'送信者', max_length=200)
    chat_name = models.CharField(u'チャット名', max_length=100, db_index=True)
    ctime = models.DateTimeField(u'作成日時', auto_now_add=True)

class Event(models.Model):
    event_id = models.IntegerField(db_index=True)
    time = models.DateTimeField()
    area = models.CharField(max_length=255)
    latitude = models.FloatField(null=True)
    longitude = models.FloatField(null=True)
    map_image_url = models.URLField(max_length=255, null=True)
    magnitude = models.CharField(max_length=255)
    depth = models.CharField(max_length=255)
    message = models.TextField()
    intensity_table = models.TextField()
    updated_at = models.DateTimeField()
    timestamp = models.DateTimeField()
    is_notified = models.BooleanField(default=False)

    def todict(self):
        return dict(
            id=self.event_id,
            updated_at=self.updated_at,
            map_image_url=self.map_image_url,
            message=self.message,
            place=dict(
                area=self.area,
                latitude=self.latitude,
                longitude=self.longitude),
            time=self.time,
            magnitude=self.magnitude,
            depth=self.depth,
            intensity_table=json.loads(self.intensity_table))

    def populatewithdict(self, d):
        self.event_id=d['id']
        self.updated_at=d['updated_at']
        self.map_image_url=d['map_image_url']
        self.message=d['message']
        self.area=d['place']['area']
        self.latitude=d['place']['latitude']
        self.longitude=d['place']['longitude']
        self.time=d['time']
        self.magnitude=d['magnitude']
        self.depth=d['depth']
        self.intensity_table=json.dumps(d['intensity_table'])

    @classmethod
    def fromdict(klass, d):
        retval = klass()
        retval.populatewithdict(d)
        return retval

    def save(self):
        self.timestamp = datetime.now()
        super(self.__class__, self).save()

    @classmethod
    def last(klass):
        items = Event.objects.order_by('timestamp').reverse()
        if len(items) == 0:
            return None
        else:
            return items[0]
