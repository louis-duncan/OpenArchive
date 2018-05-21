import os
import sqlite3
import sql
import datetime
import easygui
import pickle
import temp

__title__ = "OpenArchive"

valid_chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz1234567890!&()':-.,/?# \n\t"

# Define database location and test it's existence.
DATABASE_LOCATION = "bin\\archive.db"
ARCHIVE_LOCATION = os.path.join(os.environ["ONEDRIVE"], "Test DB Location")
TEMP_DATA_LOCATION = os.path.join(os.environ["TEMP"], "OpenArchive")

if os.path.exists(DATABASE_LOCATION):
    conn = sqlite3.connect(DATABASE_LOCATION)
    bliss = sql.SQL(conn)
    # A test to see if tables 'resources', 'resource_types', and 'local_authorities' should go here.
    # But I haven't worked out the best way to check yet.
else:
    easygui.msgbox("The database could not be located.\n{}\n\nThe program will now exit."
                   .format(DATABASE_LOCATION))
    exit()
if os.path.exists(ARCHIVE_LOCATION):
    pass
else:
    easygui.msgbox("The data repository could not be located.\n{}\n\nThe program will now exit."
                   .format(ARCHIVE_LOCATION))
if os.path.exists(TEMP_DATA_LOCATION):
    pass
else:
    os.mkdir(TEMP_DATA_LOCATION)


class ArchiveRecord:
    record_id = None
    title = ""
    description = ""
    record_type = ""
    local_auth = ""
    start_date = datetime.datetime
    end_date = datetime.datetime
    tags = []
    physical_index = ""
    other_ref = ""
    linked_files = []
    thumb_files = []
    created_by = ""
    created_time = datetime.datetime

    def __init__(self, record_id=0, title="", description="", record_type="", local_auth="",
                 start_date=None, end_date=None, physical_index="", other_ref="", tags=[], linked_files=[],
                 thumb_files=[], created_by="", created_time=None):
        self.record_id = record_id
        self.title = title
        self.description = description
        self.record_type = record_type
        self.local_auth = local_auth
        self.start_date = start_date
        self.end_date = end_date
        self.physical_index = physical_index
        self.other_ref = other_ref
        self.tags = tags
        self.linked_files = linked_files
        self.thumb_files = thumb_files
        self.created_by = created_by
        self.created_time = created_time

    def launch_file(self, file_index=0):
        if self.linked_files is None:
            pass
        else:
            try:
                if os.path.exists(self.linked_files[file_index]):
                    fail = os.startfile(self.linked_files[file_index])
                    if fail:
                        easygui.msgbox("File {} could not be opened. Unknown error.".
                                       format(self.linked_files[file_index]))
                    else:
                        pass
                else:
                    easygui.msgbox("File {} could not be opened. Path does not exist."
                                   .format(self.linked_files[file_index]))
            except IndexError:
                easygui.msgbox("No file in record {} ({}) with index {}.".format(self.record_id, self.title, file_index))

    def start_date_string(self, date_to_add=None):
        if (date_to_add is None) or (date_to_add == ""):
            if self.start_date is None:
                return "DD/MM/YYYY"
            else:
                return "{:%d/%m/%Y}".format(self.start_date)
        elif date_to_add == "DD/MM/YYYY":
            pass
        else:
            try:
                parts = date_to_add.split("/")
                self.start_date = datetime.datetime(int(parts[2]), int(parts[1]), int(parts[0]))
            except ValueError or TypeError:
                error_msg = """Error:
¯¯¯¯¯¯

Date is invalid. The format DD/MM/YYYY must be followed."""
                easygui.msgbox(error_msg, __title__ + " - Date Error")

    def end_date_string(self, date_to_add=None):
        if (date_to_add is None) or (date_to_add == ""):
            if self.end_date is None:
                return "DD/MM/YYYY"
            else:
                return "{:%d/%m/%Y}".format(self.end_date)
        elif date_to_add == "DD/MM/YYYY":
            pass
        else:
            try:
                parts = date_to_add.split("/")
                self.end_date = datetime.datetime(int(parts[2]), int(parts[1]), int(parts[0]))
            except ValueError or TypeError:
                error_msg = """Error:
¯¯¯¯¯¯

Date is invalid. The format DD/MM/YYYY must be followed."""
                easygui.msgbox(error_msg, __title__ + " - Date Error")

    def string_tags(self, tags_to_add=None):
        prompt = 'Enter tags comma separated. (eg. tag1, tag2,...)'
        if tags_to_add is None:
            if len(self.tags) == 0:
                return prompt
            else:
                output = ""
                for t in self.tags:
                    output += t + ", "
                output = output.strip(", ")
                return output
        elif tags_to_add == prompt:
            pass
        else:
            parts = tags_to_add.split(",")
            for i, p in enumerate(parts):
                parts[i] = p.strip(" ")

            easygui.msgbox(str(parts))
            for p in parts:
                if p in self.tags:
                    pass
                else:
                    self.tags.append(p)


def access_bin_file(filename):
    """Accesses a '.dat' binary file."""
    try:  # Tries to access the file normally
        # If unsuccessful due to non-existent file resort to 'except' statement
        file = open(filename, "br")
        data = pickle.load(file)
        file.close()
    except FileNotFoundError:
        # Creates empty file and returns 'None'
        data = None
        file = open(filename, "bw")
        pickle.dump(data, file)
        file.close()
    return data


def save_bin_file(filename,data):
    """Saves to a '.dat' binary file"""
    file = open(filename, "bw")  # If file doesn't exists it is created with the file-name given
    pickle.dump(data, file)
    file.close()


def check_text_is_valid(text):
    if text is None:
        return True
    else:
        valid = True
        bad_chars = []
        for c in text:
            if c in valid_chars:
                pass
            else:
                valid = False
                bad_chars.append(c)
        if valid:
            return valid
        else:
            return bad_chars


def get_record_by_id(record_id=0):
    if ";" in str(record_id):
        return None
    else:
        item = bliss.one("SELECT * FROM resources WHERE id=?", (record_id,))
        return format_returned_item(item)


def get_filtered_records(types=(), local_authorities=()):
    # break in case of incorrect types
    assert type(types) == type(local_authorities) == tuple

    types_param_string = ""
    for t in types:
        types_param_string += str(t) + ","
    types_param_string = types_param_string.strip(",")

    local_authorities_string = ""
    #
    for l in local_authorities:
        local_authorities_string += str(l) + ","
    local_authorities_string = local_authorities_string.strip(",")

    q = "SELECT * FROM resources WHERE record_type IN ({}) OR local_auth IN ({})".format(types_param_string,
                                                                                         local_authorities_string)
    records =  bliss.all(q, ())
    formatted_records = []
    for r in records:
        formatted_records.append(format_returned_item(r))
    return formatted_records


def format_returned_item(db_record_object):
    # Convert Type and Auth ids to text.
    type_text = bliss.one("SELECT * FROM types WHERE id=?", (db_record_object.record_type,)).type_text
    auth_text = bliss.one("SELECT * FROM local_authorities WHERE id=?", (db_record_object.local_auth,)).local_auth

    # Convert dates to datetimes
    if db_record_object.start_date is None:
        start_date = None
    else:
        start_date = datetime.datetime.fromtimestamp(int(db_record_object.start_date / 1000))
    if db_record_object.end_date is None:
        end_date = None
    else:
        end_date = datetime.datetime.fromtimestamp(int(db_record_object.end_date / 1000))
    if db_record_object.created_time is None:
        created_time = None
    else:
        created_time = datetime.datetime.fromtimestamp(int(db_record_object.created_time / 1000))

    # Create tag and item lists
    if db_record_object.tags is not None:
        tags = db_record_object.tags.split(",")
        while tags.count("") > 0:
            tags.remove("")
    else:
        tags = None

    linked_files = []
    thumb_files = []
    for f in bliss.all("SELECT * FROM file_links WHERE record_id=?", (db_record_object.id,)):
        linked_files.append(f.file_path)
        thumb_files.append(f.thumbnail_path)

    # Create Record obj
    record_obj = ArchiveRecord(id=db_record_object.id,
                               title=db_record_object.title,
                               description=db_record_object.description,
                               record_type=type_text,
                               local_auth=auth_text,
                               start_date=start_date,
                               end_date=end_date,
                               physical_index=db_record_object.physical_ref,
                               other_ref=db_record_object.other_ref,
                               tags=tags,
                               linked_files=linked_files,
                               thumb_files=thumb_files,
                               created_by=db_record_object.created_by,
                               created_time=created_time,
                               )
    return record_obj


def return_types():
    type_records = bliss.all("SELECT * FROM types", ())
    types = []
    for r in type_records:
        types.append(r.type_text)
    return types


def return_local_authorities():
    local_authority_records = bliss.all("SELECT * FROM local_authorities", ())
    local_authorities = []
    for r in local_authority_records:
        local_authorities.append(r.local_auth)
    return local_authorities


def get_thumbnail(file_link_id=None, file_path=None):
    if file_link_id is not None:
        thumbnail_record = bliss.one("SELECT * FROM file_links WHERE id=?", (file_link_id,))
    elif file_path is not None:
        thumbnail_record = bliss.one("SELECT * FROM file_links WHERE file_path=?", (file_path,))
    else:
        return None
    if thumbnail_record is None:
        return None
    else:
        return thumbnail_record.thumbnailpath


def clear_cache():
    temp_files = os.listdir(TEMP_DATA_LOCATION)
    print("Clearing {} files from:\n{}".format(len(temp_files), TEMP_DATA_LOCATION))
    fails = []
    for f in temp_files:
        full_f = os.path.join(TEMP_DATA_LOCATION, f)

        try:
            if full_f.endswith('.dat'):
                try:
                    data = access_bin_file(full_f)
                    if data.unsaved_changes:
                        pass
                    else:
                        os.remove(full_f)
                except AttributeError or EOFError:
                    os.remove(full_f)
            else:
                os.remove(full_f)
        except PermissionError:
            fails.append(full_f)
        except FileNotFoundError:
            pass
    return fails
          

def create_cached_record(record_id=None):
    if record_id is None:
        # New empty obj
        # Add to new file
        pass
    else:
        record_obj = get_record_by_id(record_id)
        if record_obj is None:
            return None
        else:
            record_object_path = temp.mkstemp(".dat", "OATEMP", TEMP_DATA_LOCATION)
    return record_object_path


def commit_record():
    # Commits changes or new record to db
    pass
