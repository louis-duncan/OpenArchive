import datetime
import os
import coord
try:
    import database_io
except ModuleNotFoundError:
    print("Could not load database_io!")


class Point:
    def __init__(self, name="", description="", linked_files=[], longitude=0, latitude=0):
        self.name = name
        self.description = description
        self.linked_files = list(linked_files)
        self.longitude = longitude
        self.latitude = latitude
        
    def add_link(self, path):
        self.linked_files.append(path)


def load_kml_data(path):
    with open(path, "r") as fh:
        data = fh.readlines()
    return data


def decode_description(text):
    description = ""
    found_files = []
    
    # Check for tag which Google Earth uses to denote a point with a complex description.
    if text.startswith("<![CDATA["):
        pass
    else:
        return text, []
    trimmed = text.replace("<![CDATA[", "").replace("]]>", "")
    
    in_tag = False
    tags = []
    current_tag_text = ""
    for c in trimmed:
        if not in_tag:
            if c == "<":
                in_tag = True
                current_tag_text = ""
            else:
                description += c
        else:
            if c == ">":
                in_tag = False
                tags.append(current_tag_text)
            else:
                current_tag_text += c
    description = description.strip()
    
    for t in tags:
        new_path = t.split("src=")[1].strip('"').replace("file://", "").strip("/")
        found_files.append(new_path)
        
    return description, found_files
    
    
def process_points(data_lines):
    points = []
    current_point = Point()
    in_point = False
    in_name = False
    in_description = False
    in_lat_lon = False
    for line in data_lines:
        raw_line = line.strip()
        
        # Start new points and save finished points.
        if raw_line == "<Placemark>":
            current_point = Point()
            in_point = True
            in_name = False
            in_description = False
            in_lat_lon = False
        elif raw_line == "</Placemark>":
            points.append(current_point)
            in_point = False
        else:
            pass
            
        # Track which part of the point we are reading.
        if in_point:
            if raw_line.startswith("<name>"):
                in_name = True
                raw_line = raw_line.replace("<name>", "")
                    
            if raw_line.startswith("<description>"):
                in_description = True
                raw_line = raw_line.replace("<description>", "")
            
            if raw_line.startswith("<coordinates>"):
                in_lat_lon = True
                raw_line = raw_line.replace("<coordinates>", "")
            
            # Put the line's data in the right place depending on current area being read.
            if in_name:
                if raw_line.endswith("</name>"):
                    in_name = False
                    raw_line = raw_line.replace("</name>", "")
                current_point.name += "\n" + raw_line
                current_point.name = current_point.name.strip()
            
            if in_description:
                if raw_line.endswith("</description>"):
                    in_description = False
                    raw_line = raw_line.replace("</description>", "")
                current_point.description += "\n" + raw_line
                current_point.description = current_point.description.strip()
            
            if in_lat_lon:
                if raw_line.endswith("</coordinates>"):
                    in_lat_lon = False
                    raw_line = raw_line.replace("</coordinates>", "")
                current_point.longitude, current_point.latitude = coord.normalise(raw_line)
        else:
            pass
    
    print("Found {} points.".format(len(points)))
    print("Checking data integrity...")

    error_count = 0
    for p in range(len(points)):
        new_desc, point_files = decode_description(points[p].description)
        points[p].description = new_desc
        if len(point_files) == 0:
            print("{}: Has no attached files!".format(points[p].name))
            error_count += 1
        else:
            for f in point_files:
                points[p].add_link(f)
                # Check file.
                if os.path.exists(f):
                    pass
                else:
                    print("{}: File {} not found!".format(points[p].name, f))
                    error_count += 1
    if error_count == 0:
        print("No Errors Found!")
    else:
        print(error_count, "Errors Found!")
    
    return points


def convert_points_to_records(points,
                              title_prefix="",
                              title_suffix="",
                              description_prefix="",
                              description_suffix="",
                              record_type=0,
                              local_auth=0,
                              tags=list(),
                              ):
    new_records = []

    p: Point
    for p in points:
        if len(p.linked_files) == 0:
            print("{} skipped due to having no files linked.".format(p.name))
        else:
            skip = False
            for f in p.linked_files:
                if os.path.exists(f):
                    pass
                else:
                    skip = True
            if skip:
                print("{} skipped due to having an invalid file.".format(p.name))
            else:
                new_records.append(database_io.ArchiveRecord(record_id=None,
                                                             title="{}{}{}".format(title_prefix,
                                                                                   p.name,
                                                                                   title_suffix),
                                                             description="{}{}{}".format(description_prefix,
                                                                                         p.description,
                                                                                         description_suffix),
                                                             record_type=record_type,
                                                             local_auth=local_auth,
                                                             start_date=None,
                                                             end_date=None,
                                                             new_tags=tags,
                                                             linked_files=p.linked_files,
                                                             longitude=p.longitude,
                                                             latitude=p.latitude
                                                             ))
    return new_records


if __name__ == "__main__":
    pass                 
