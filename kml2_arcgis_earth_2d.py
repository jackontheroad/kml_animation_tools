from pykml import parser
from lxml import etree, objectify
import json
from copy import deepcopy
from dotmap import DotMap
import sys

kml_file = r"c:\Users\jack\Desktop\test\新丰江-新港Tracks.kml"

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


def lookat2camera(lookat, time, duration):
    camera = DotMap()
    camera.lat = lookat.latitude.text
    camera.lon = lookat.longitude.text
    camera.ele = lookat.altitude.text
    camera.heading = lookat.heading.text
    camera.tilt = lookat.tilt.text
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
        lookat = flyto["{http://www.opengis.net/kml/2.2}LookAt"]
        lookat.tilt = 0
        lookat.heading = 0
        lookat.altitude = 8500
        flyto.duration = float(flyto.duration)/3
        if i == 0:
            last_camera = lookat2camera(lookat, 0, flyto.duration)
        start = last_camera
        end = lookat2camera(lookat, start.time + flyto.duration, flyto.duration)
        movie["actions"]["camera"].append(
            populate_camera(start, end, "camera-id-" + str(i), camera_tpl)
        )
        last_camera = end
        i += 1
    movie["duration"] = last_camera.time

out_movies_json_file = kml_file[:-4] + "_movies.json"
with open(out_movies_json_file, "w", encoding="UTF-8") as f:
    f.write(json.dumps(movies_tpl, indent=4, ensure_ascii=False))
