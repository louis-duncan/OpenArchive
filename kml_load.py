import os
import database_io
import temp
import coord

base_text = """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2" xmlns:gx="http://www.google.com/kml/ext/2.2" xmlns:kml="http://www.opengis.net/kml/2.2" xmlns:atom="http://www.w3.org/2005/Atom">

<Placemark>
\t<name>name-here</name>
\t<description>description-here</description>
\t<LookAt>
\t\t<longitude>lon-here</longitude>
\t\t<latitude>lat-here</latitude>
\t\t<altitude>0</altitude>
\t\t<heading>0</heading>
\t\t<tilt>0</tilt>
\t\t<range>2000</range>
\t\t<gx:altitudeMode>relativeToSeaFloor</gx:altitudeMode>
\t</LookAt>
\t<Point>
\t\t<coordinates>lon-here, lat-here</coordinates>
\t</Point>
</Placemark>

</kml>
"""


def create_kml_point(title, description, lon, lat, cache_path=database_io.TEMP_DATA_LOCATION):
    assert type(title) == type(description) == str
    assert type(lon) == type(lat) == float
    new_point = base_text
    new_point =new_point.replace("name-here", title)
    new_point =new_point.replace("description-here", description)
    new_point = new_point.replace("lon-here", str(lon))
    new_point = new_point.replace("lat-here", str(lat))
    fd, file_name = temp.mkstemp(suffix=".kml", prefix="OATEMP_", dir=cache_path)
    os.close(fd)
    with open(file_name, "w") as file:
        file.write(new_point)
    os.startfile(file_name)
