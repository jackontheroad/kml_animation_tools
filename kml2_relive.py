from pykml import parser
from lxml import etree, objectify
import pandas as pd
import math
from copy import deepcopy


def main():
    csv_file = r"c:\Users\jack\Desktop\test\2023万绿湖划船_relive_sqs_lambda_camera.csv"
    kml_file = r"c:\Users\jack\Desktop\test\2023万绿湖Tracks.kml"

    with open(kml_file, "rb") as f:
        root = parser.parse(f).getroot()
        # print(type(root))
        # print(len(root.Document.Folder.Placemark["{http://www.google.com/kml/ext/2.2}Track"].coord))
        # print()
        moving_keyframes_count = (
            len(
                root.Document.Folder[
                    "{http://www.google.com/kml/ext/2.2}Tour"
                ].Playlist.FlyTo
            )
            - 1
        )
        keyframes_data = process_relive_csv_keyframes(csv_file, moving_keyframes_count)
        before_moving_data = keyframes_data["before_moving"]
        moving_data = keyframes_data["moving"]
        after_moving_data = keyframes_data["after_moving"]

        last_flyto_begin = None
        last_flyto_end = None

        playlist = root.Document.Folder[
            "{http://www.google.com/kml/ext/2.2}Tour"
        ].Playlist
        flyto_tpl = deepcopy(playlist.FlyTo[1])

        i = -1
        for flyto in root.Document.Folder[
            "{http://www.google.com/kml/ext/2.2}Tour"
        ].Playlist.FlyTo:
            i += 1
            if i == 0:
                continue
            lookat = flyto["{http://www.opengis.net/kml/2.2}LookAt"]
            csv_data_row = moving_data[i - 1]
            camera_kml = generate_camera_kml(
                lookat.TimeSpan.begin, lookat.TimeSpan.end, csv_data_row
            )
            flyto.remove(lookat)
            flyto.append(camera_kml)
            if i == moving_keyframes_count:
                last_flyto_begin = lookat.TimeSpan.begin
                last_flyto_end = lookat.TimeSpan.end

        # before_moving
        lookat = flyto_tpl["{http://www.opengis.net/kml/2.2}LookAt"]
        flyto_tpl.remove(lookat)
        flyto_tpl.duration = 0.3
        # playlist.remove(flyto)
        for index, csv_row in enumerate(before_moving_data):
            flyto = deepcopy(flyto_tpl)
            if index == 0:
                flyto.duration = 3
            camera_kml = generate_camera_kml(
                last_flyto_begin, last_flyto_begin, csv_row
            )
            flyto.append(camera_kml)
            playlist.insert(index + 1, flyto)
        # after_moving
        for csv_row in after_moving_data:
            flyto = deepcopy(flyto_tpl)
            flyto.duration = 10
            camera_kml = generate_camera_kml(last_flyto_begin, last_flyto_end, csv_row)
            flyto.append(camera_kml)
            playlist.append(flyto)

    objectify.deannotate(root, cleanup_namespaces=True, xsi_nil=True)
    kml_str = etree.tostring(
        etree.ElementTree(root), pretty_print=True, encoding="utf8"
    )
    output_file = kml_file[:-4] + "_modified_relive1.kml"
    with open(output_file, "wb") as f:
        f.write(kml_str)


def generate_camera_kml(begin, end, csv_data_row):
    camera_kml_tpl = """<Camera>
          <TimeSpan>
            <begin>{begin}</begin>
            <end>{end}</end>
          </TimeSpan>
          <longitude>{longitude}</longitude>
          <latitude>{latitude}</latitude>
          <altitude>{altitude}</altitude>
          <heading>{heading}</heading>
          <tilt>{tilt}</tilt>
          <altitudeMode>absolute</altitudeMode>
        </Camera>"""
    values = {
        "begin": begin,
        "end": end,
        "longitude": csv_data_row["camera.lon"],
        "latitude": csv_data_row["camera.lat"],
        "altitude": csv_data_row["camera.ele"],
        "heading": math.degrees(csv_data_row["camera.heading"]),
        "tilt": math.degrees(csv_data_row["camera.pitch"]) + 90,
    }
    camera_kml_str = camera_kml_tpl.format(**values)
    camera_kml = objectify.fromstring(camera_kml_str)
    return camera_kml


def process_relive_csv_keyframes(csv_file, moving_keyframes_count):
    df = pd.read_csv(csv_file)

    index_start_moving = 0
    index_end_moving = 0
    starting_keyframes_count = 10
    ending_keyframes_count = 1
    keyframes_count = moving_keyframes_count

    distance = df.iloc[0].distance

    for index, row in df.iterrows():
        if distance != row.distance:
            index_start_moving = index
            break
    distance = df.iloc[-1].distance

    for index, row in df[::-1].iterrows():
        if distance != row.distance:
            index_end_moving = index
            break

    # 0 - (index_start_moving-1)
    starting_keyframes_list = extract_keyframedata(
        0, index_start_moving - 1, starting_keyframes_count, df
    )
    # index_start_moving - index_end_moving
    moving_keyframes_list = extract_keyframedata(
        index_start_moving, index_end_moving, moving_keyframes_count, df
    )
    # (index_end_moving+1) - end
    ending_keyframes_list = extract_keyframedata(
        index_end_moving + 1, df.index[-1], ending_keyframes_count, df
    )
    return {
        "before_moving": starting_keyframes_list,
        "moving": moving_keyframes_list,
        "after_moving": ending_keyframes_list,
    }


def extract_keyframedata(start, end, count, df):
    index_start_moving = start
    index_end_moving = end
    keyframes_count = count
    keyframes_indexs = []
    if keyframes_count > 2:
        intervel = int((index_end_moving - index_start_moving) / (keyframes_count - 1))
        keyframes_indexs = [*range(index_start_moving, index_end_moving + 1, intervel)]
    elif keyframes_count == 2:
        keyframes_indexs = [start, end]
    else:
        keyframes_indexs = [end]

    keyframes_list = []

    for val_index in keyframes_indexs:
        keyframe = df.iloc[val_index]
        row_dict = {
            "camera.ele": keyframe["camera.ele"],
            "camera.lon": keyframe["camera.lon"],
            "camera.lat": keyframe["camera.lat"],
            "camera.heading": keyframe["camera.heading"],
            "camera.pitch": keyframe["camera.pitch"],
        }
        keyframes_list.append(row_dict)
    return keyframes_list


if __name__ == "__main__":
    main()
