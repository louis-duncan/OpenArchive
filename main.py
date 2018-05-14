import os
import datetime
import easygui_custom as easygui
import datebase_io

__title__ = "OpenArchive"
__author__ = "Louis Thurman"


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

