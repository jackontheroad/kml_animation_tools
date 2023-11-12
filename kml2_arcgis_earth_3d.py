from pykml import parser
from lxml import etree, objectify
import json
from copy import deepcopy
from dotmap import DotMap
import sys

kml_file = r"c:\Users\jack\Desktop\test\梅里雪山Tracks_modified_relive1_json_test.kml"
movies_json_tpl_file = r"c:\Users\jack\Desktop\test\movies_tpl.json"

def populate_camera(start, end, id, camera_tpl):
    camera = deepcopy(camera_tpl)
    camera["id"] = id
    camera["start"] = start.time
    camera["end"] = end.time
    camera["viewpointStart"]["targetGeometry"]["x"] = start.lon
    camera["viewpointStart"]["targetGeometry"]["y"] = start.lat
    camera["viewpointStart"]["targetGeometry"]["z"] = start.ele
    camera["viewpointStart"]["camera"]["position"]["x"] = start.lon
    camera["viewpointStart"]["camera"]["position"]["y"] = start.lat
    camera["viewpointStart"]["camera"]["position"]["z"] = start.ele
    camera["viewpointStart"]["camera"]["heading"] = start.heading
    camera["viewpointStart"]["camera"]["tilt"] = start.tilt

    camera["viewpointEnd"]["targetGeometry"]["x"] = end.lon
    camera["viewpointEnd"]["targetGeometry"]["y"] = end.lat
    camera["viewpointEnd"]["targetGeometry"]["z"] = end.ele
    camera["viewpointEnd"]["camera"]["position"]["x"] = end.lon
    camera["viewpointEnd"]["camera"]["position"]["y"] = end.lat
    camera["viewpointEnd"]["camera"]["position"]["z"] = end.ele
    camera["viewpointEnd"]["camera"]["heading"] = end.heading
    camera["viewpointEnd"]["camera"]["tilt"] = end.tilt
    return camera


def kml_camera2json_camera(kml_camera, time, duration):
    camera = DotMap()
    camera.lat = kml_camera.latitude.text
    camera.lon = kml_camera.longitude.text
    camera.ele = kml_camera.altitude.text
    camera.heading = kml_camera.heading.text
    camera.tilt = kml_camera.tilt.text
    camera.time = time
    camera.duration = duration
    return camera



with open(movies_json_tpl_file, "rt", encoding="utf-8") as f:
    movies_tpl = json.load(f)
    # json.dump(movies_tpl, indent=4)
    movie = movies_tpl["movies"][0]
    print(movie["duration"])
    camera_tpl = deepcopy(movie["actions"]["camera"][0])
    movie["actions"]["camera"].clear()
    # print(camera_tpl)

with open(kml_file, "rb") as f:
    root = parser.parse(f).getroot()
    movie["name"] = root.Document.Folder.Placemark.name.text
    i = 0
    time = 0
    last_camera = None
    for flyto in root.Document.Folder[
        "{http://www.google.com/kml/ext/2.2}Tour"
    ].Playlist.FlyTo:
        camera = flyto["{http://www.opengis.net/kml/2.2}Camera"]
        # camera.tilt = 0
        # camera.heading = 0
        # camera.altitude = 5000
        if i == 0:
            last_camera = kml_camera2json_camera(camera, 0, flyto.duration)
        start = last_camera
        end = kml_camera2json_camera(camera, start.time + flyto.duration, flyto.duration)
        movie["actions"]["camera"].append(
            populate_camera(start, end, "camera-id-" + str(i), camera_tpl)
        )
        last_camera = end
        i += 1
    movie["duration"] = last_camera.time

out_movies_json_file = movies_json_tpl_file[:-15] + movie["name"] + "_movies_3d.json"
with open(out_movies_json_file, "w", encoding="UTF-8") as f:
    f.write(json.dumps(movies_tpl, indent=4, ensure_ascii=False))
