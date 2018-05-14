import os
import sqlite3
import sql
import datetime
import easygui_custom as easygui


class ArchiveRecord:
    id = 0
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

    def __init__(self, record_id, title, description, record_type, local_auth, start_date,
                 end_date, physical_index, other_ref, tags, linked_files):
        self.id = record_id
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

    def launch_file(self, file_index=0):
        if self.linked_files is None:
            pass
        else:
            try:
                if os.path.exists(self.linked_files[file_index]):
                    fail = os.system('"{}"'.format(self.linked_files[file_index]))
                    if fail:
                        easygui.msgbox("File {} could not be opened. Unknown error.".format(self.linked_files[file_index]))
                    else:
                        pass
                else:
                    easygui.msgbox("File {} could not be opened. Path does not exist."
                                   .format(self.linked_files[file_index]))
            except IndexError:
                easygui.msgbox("No file in record {} ({}) with index {}.".format(self.id, self.title, file_index))


# Define database location and test it's existence.
DATABASE_LOCATION = "bin\\archive.db"
if os.path.exists(DATABASE_LOCATION):
    conn = sqlite3.connect(DATABASE_LOCATION)
    bliss = sql.SQL(conn)
    # A test to see if tables 'resources', 'resource_types', and 'local_authorities' should go here.
    # But I haven't worked out the best way to check yet.
else:
    easygui.msgbox("The database could not be located.\nThe program will now exit.")
    exit()


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
    for l in local_authorities:
        local_authorities_string += str(l) + ","
    local_authorities_string = local_authorities_string.strip(",")

    q = "SELECT * FROM resources WHERE record_type IN ({}) OR local_auth IN ({})".format(types_param_string,
                                                                                         local_authorities_string)

    return bliss.all(q, ())


def format_returned_item(item):
    # Convert Type and Auth ids to text.
    type_text = bliss.one("SELECT * FROM types WHERE id=?", (item.record_type,)).type_text
    auth_text = bliss.one("SELECT * FROM local_authorities WHERE id=?", (item.local_auth,)).local_auth

    # Convert dates to datetimes
    if item.start_date is None:
        start_date = None
    else:
        start_date = datetime.datetime.fromtimestamp(int(item.start_date / 1000))
    if item.end_date is None:
        end_date = None
    else:
        end_date = datetime.datetime.fromtimestamp(int(item.end_date / 1000))

    # Create tag and item lists
    if item.tags is not None:
        tags = item.tags.split("|")
        null_count = tags.count("")
        for n in range(null_count):
            tags.remove("")
        for i in range(len(tags)):
            tags[i] = tags[i].strip("'")
    else:
        tags = None

    if item.linked_files is not None:
        linked_files = item.linked_files.split("|")
        null_count = linked_files.count("")
        for n in range(null_count):
            linked_files.remove("")
        for i in range(len(linked_files)):
            linked_files[i] = linked_files[i].strip("'")
    else:
        linked_files = None

    # Create Record obj
    record_obj = ArchiveRecord(item.id,
                               item.title,
                               item.description,
                               type_text,
                               auth_text,
                               start_date,
                               end_date,
                               item.physical_ref,
                               item.other_ref,
                               tags,
                               linked_files,
                               )
    return record_obj
