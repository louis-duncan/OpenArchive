import os
import database_io
import temp
import coord

head_text = """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2" xmlns:gx="http://www.google.com/kml/ext/2.2" xmlns:kml="http://www.opengis.net/kml/2.2" xmlns:atom="http://www.w3.org/2005/Atom">
<Folder>
\t<name>OpenArchive Pins</name>"""

tail_text = """</Folder>
</kml>"""

point_base = """\t<Placemark>
\t\t<name>name-here</name>
\t\t<description>description-here</description>
\t\t<LookAt>
\t\t\t<longitude>lon-here</longitude>
\t\t\t<latitude>lat-here</latitude>
\t\t\t<altitude>0</altitude>
\t\t\t<heading>0</heading>
\t\t\t<tilt>0</tilt>
\t\t\t<range>2000</range>
\t\t\t<gx:altitudeMode>relativeToSeaFloor</gx:altitudeMode>
\t\t</LookAt>
\t\t<Point>
\t\t\t<coordinates>lon-here, lat-here</coordinates>
\t\t</Point>
\t</Placemark>"""


def create_kml_point(title, description, lon, lat):
    assert type(title) == type(description) == str
    assert type(lon) == type(lat) == float
    new_point = point_base
    new_point = new_point.replace("name-here", title)
    new_point = new_point.replace("description-here", description)
    new_point = new_point.replace("lon-here", str(lon))
    new_point = new_point.replace("lat-here", str(lat))
    return new_point


def launch(kml_text, cache_path=database_io.TEMP_DATA_LOCATION):
    fd, file_name = temp.mkstemp(suffix=".kml", prefix="OATEMP_", dir=cache_path)
    os.close(fd)
    with open(file_name, "w") as file:
        file.write(kml_text)
    os.startfile(file_name)


def load_batch(points):
    kml_text = ""
    kml_text += head_text
    for p in points:
        kml_text += create_kml_point(p[0], p[1], p[2], p[3]) + "\n"
    kml_text += tail_text
    launch(kml_text)