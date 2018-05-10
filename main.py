__title__ = "Zetica DB"
__author__ = "Louis Thurman"

import os
import sqlite3
import datetime
import easygui_custom as easygui

# Define database location and test it's existence.
DATABASE_LOCATION = "bin\\zetica.db"
if os.path.exists(DATABASE_LOCATION):
    conn = sqlite3.connect(DATABASE_LOCATION)
    cursor = conn.cursor()
    # A test to see if tables 'resources', 'resource_types', and 'local_authorities' should go here.
    # But I haven't worked out the best way to check yet.
else:
    easygui.msgbox("The database could not be located.\nThe program will now exit.")
    exit()


class Record(object):
    record_id = 0
    record_reference = ""
    other_reference = ""
    title = ""
    description = ""
    record_type = 0
    local_authority = 0
    start_date = datetime.date(1970, 1, 1)
    end_date = datetime.date(1970, 1, 1)
    linked_files = []


class RecordTypes(object):
    type_id = 0
    type_text = ""


class LocalAuthority(object):
    auth_id = 0
    auth_text = ""


def retrieve_record(table, record_id):
    global cursor
    params = (table, record_id)
    record = cursor.execute("SELECT * FROM ? WHERE id=?", params)
    return record

