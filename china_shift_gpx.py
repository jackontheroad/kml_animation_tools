#! python3
import gpxpy
from eviltransform import gcj2wgs_exact, wgs2gcj

file = r"c:\Users\jack\Desktop\test\河源_新丰江-万绿湖港口码头_骑行探路_with_time.gpx"
gpx_file = open(file, "r", encoding="UTF-8")
gpx = gpxpy.parse(gpx_file)
points = gpx.tracks[0].segments[0].points
for point in points:
    (point.latitude, point.longitude) = wgs2gcj(point.latitude, point.longitude)

output_file = file[:-4] + "_gcj02.gpx"
with open(output_file, "w", encoding="UTF-8") as f:
    f.write(gpx.to_xml())
