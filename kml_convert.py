import os

class point:
	def __init__(self, name="", description="", files=[], longitude=0, latitude=0):
		self.name = name
		self.description = description
		selcf.files = files
		self.longitude = longitude
		self.latitude = latitude

		
def get_kml_data(path):
	try:
		with open(path, "r") as fh:
			data = fh.readlines()
	return data


def decode_description(text):
	description = ""
	files = []
	
	# Check for tag which Google Earth uses to denote a point with a complex description.
	if text.startswith("<![CDATA["):
		pass
	else:
		return text, []
	trimmed = text.remove("<![CDATA[").remove("]]>")
	
	in_tag = False
	tags = []
	current_tag_text = ""
	for c in trimmed:
		if not in_tag:
			if c == "<"
				in_tag = True
				current_tag_text = ""
			else:
				description += c
		else:
			if c == ">"
				in_tag = False
				tags.append(current_tag_text)
			else:
				current_tag_text += c
	description = description.strip()
	
	for t in tags:
		new_path = t.split("src=")[1].strip('"')
		files.append(new_path
	
	return description, files
	
	
def process_points(data_lines):
	points = []
	current_point = point()
	in_name = False
	in_description = False
	in_lat_lon = False
	for line in data_lines:
		raw_line = line.strip()
		
		# Start new points and save finished points.
		if raw_line == "<Placemark>":
			current_point = point()
		elif raw_line == "</Placemark>":
			points.append(current_point)
		else:
			pass
			
		# Track which part of the point we are reading.
		if raw_line.startswith("<name>"):
			in_name = True
			raw_line = raw_line.remove("<name>")
				
		if raw_line.startswith("<description>"):
			in_description = True
			raw_line = raw_line.remove("<description>")
		
		if raw_line.startswith("<coordinates>"):
			in_lat_lon = True
			raw_line.remove("<coordinates>")
		
		# Put the line's data in the right place depending on current area being read.
		if in_name:
			if raw_line.endswith("</name>"):
				in_name = False
				raw_line = raw_line.remove("</name>")
			current_point.name += "\n" + raw_line
			current_point.name = current_point.name.strip()
		
		if in_description:
			if raw_line.endswith("</description>"):
				in_description = False
				raw_line = raw_line.remove("</description>")
			current_point.description += "\n" + raw_line
			current_point.description = current_point.description.strip()
		
		if in_lat_lon:
			if raw_line.endswith("</coordinates>"):
				in_lat_lon = False
				raw_line = raw_line.remove("</coordinates>")
			current_point.lat, current.lon = normalise(raw_line)
	
	print("Found {} points.".format(len(points)))
	
	for p in points:
		new_desc, files = decode_description(p.description)
		p.description = new_desc
		for f in files:
			p.files.append(f)
			# Check file.
			if os.path.exists(path):
				pass
			else:
				print("{}: File {} not found!".format(p.name, f))
	
	return points
		
	