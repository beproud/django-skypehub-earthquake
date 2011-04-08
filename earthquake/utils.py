# encoding: utf-8
import re
from lxml import html
import datetime

__all__ = (
    'scrape',
    )

class UnexpectedStructureError(Exception):
    pass

def find(n, path):
    retval = n.xpath(path)
    if len(retval) == 0:
        raise UnexpectedStructureError(path, n)
    return retval[0]

def match(regex, text):
    retval = re.match(regex, text)
    if retval is None:
        raise UnexpectedStructureError(regex, text)
    return retval 

def scrape(t):
    first_contents_box_node = find(t, u"//div[@class='contentsBox'][1]")
    g = match(ur"(\d+)年(\d+)月(\d+)日 (\d+)時(\d+)分",
        find(first_contents_box_node, u".//div[@class='dateRight']").text_content().strip())
    try:
        updated_at = datetime.datetime(year=int(g.group(1)),
                                       month=int(g.group(2)),
                                       day=int(g.group(3)),
                                       hour=int(g.group(4)),
                                       minute=int(g.group(5)))
    except ValueError, e:
        raise UnexpectedStructureError(e)

    intro_input_node = find(t, u".//div[@class='introductionTagBox']//input[@name='tag']")
    event_id = int(match(".*\?id=([0-9]+)", intro_input_node.value.strip()).group(1))

    map_image_url_node = first_contents_box_node.find(u".//p[@class='mainImage']/img")
    if map_image_url_node is not None:
        map_image_url = map_image_url_node.get("src")
    else:
        map_image_url = None

    message = find(t, u".//div[@class='contentsBox'][2]//div[contains(string(@class), 'relationMessege')]").text_content().strip()

    table_node = find(t, u".//div[@class='contentsBox'][3]//table[@class='earthquakeDetailTable']")

    g = match(ur"(\d+)月(\d+)日 (\d+)時(\d+)分",
        find(table_node,
            u".//th[@abbr='発生時刻']/following-sibling::td").text_content().strip())
    try:
        event_month = int(g.group(1))
        if event_month > updated_at.month:
            event_year = updated_at.year - 1
        else:
            event_year = updated_at.year
        event_time = datetime.datetime(year=event_year,
                                       month=event_month,
                                       day=int(g.group(2)),
                                       hour=int(g.group(3)),
                                       minute=int(g.group(4)))
    except ValueError, e:
        raise UnexpectedStructureError(e)

    event_place = find(table_node, u".//th[@abbr='震源地']/following-sibling::td").text_content().strip()

    try:
        g = match(ur"(北緯|南緯)(\d+(?:\.\d+)?)度",
            find(table_node, u".//th[@abbr='位置']/following-sibling::th[@abbr='緯度']/following-sibling::td").text_content().strip())
        event_place_latitude = float(g.group(2))
        if g.group(1) == u"南緯":
            event_place_latitude = -event_place_latitude
    except:
        event_place_latitude = None

    try:
        g = match(ur"(東経|西経)(\d+(?:\.\d+)?)度",
            find(table_node, u".//tr[child::th[@abbr='位置']]/following-sibling::tr/th[@abbr='経度']/following::td").text_content().strip())
        event_place_longitude = float(g.group(2))
        if g.group(1) == u"西経":
            event_place_longitude = -event_place_longitude
    except:
        event_place_longitude = None

    magnitude = find(table_node, u".//th[@abbr='震源']/following-sibling::th[@abbr='マグニチュード']/following-sibling::td").text_content().strip()
    depth = find(table_node, u".//tr[child::th[@abbr='震源']]/following-sibling::tr/th[@abbr='深さ']/following::td").text_content().strip()

    intensity_table_node = find(t, u".//div[@class='contentsBox'][4]//table[@id='seismicIntensity']")
    intensity_table = []
    rowspan = 0
    intensity_table_inner = None

    try:
        for n in intensity_table_node.xpath(u".//tr[position() > 1]"):
            row = n.xpath(".//td")
            if rowspan == 0:
                intensity_node=row[0]
                rowspan = int(intensity_node.get("rowspan", 1))
                intensity = intensity_node.text_content().strip()
                intensity_table_inner = []
                intensity_table.append((intensity, intensity_table_inner))
                row.pop(0)
            intensity_table_inner.append(
                dict(
                    prefecture=row[0].text_content().strip(),
                    area=row[1].text_content().strip().split(),
                    district=row[2].text_content().strip().split()))
            rowspan -= 1
    except ValueError, e:
        raise UnexpectedStructureError(e)

    return dict(
        id=event_id,
        updated_at=updated_at,
        map_image_url=map_image_url,
        message=message,
        place=dict(
            area=event_place,
            latitude=event_place_latitude,
            longitude=event_place_longitude),
        time=event_time,
        magnitude=magnitude,
        depth=depth,
        intensity_table=intensity_table)
