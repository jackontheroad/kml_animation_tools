#! python3
import gpxpy
from eviltransform import gcj2wgs_exact, wgs2gcj, gcj2wgs

file = r"c:\Users\jack\Desktop\test\mapstogpx20231027_080132.gpx"
gpx_file = open(file, "r", encoding="UTF-8")
gpx = gpxpy.parse(gpx_file)
points = gpx.tracks[0].segments[0].points
for point in points:
    (point.latitude, point.longitude) = gcj2wgs(point.latitude, point.longitude)

output_file = file[:-4] + "_wgs84.gpx"
with open(output_file, "w", encoding="UTF-8") as f:
    f.write(gpx.to_xml())
