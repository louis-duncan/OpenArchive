import os
import re
import sqlite3
import time
import sql
import datetime
import easygui
import pickle
import temp
import textdistance

__title__ = "OpenArchive"

# noinspection SpellCheckingInspection
valid_chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz1234567890!&()':-.,/?*# \n\t"

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
    physical_ref = ""
    other_ref = ""
    linked_files = []
    thumb_files = []
    created_by = ""
    created_time = datetime.datetime
    last_changed_by = ""
    last_changed_time = datetime.datetime

    # noinspection PyDefaultArgument
    def __init__(self, record_id=0, title="", description="", record_type="", local_auth="",
                 start_date=None, end_date=None, physical_ref="", other_ref="", tags=[], linked_files=[],
                 thumb_files=[], created_by="", created_time=None, last_changed_by=None, last_changed_time=None):
        self.record_id = record_id
        self.title = title
        self.description = description
        self.record_type = record_type
        self.local_auth = local_auth
        self.start_date = start_date
        self.end_date = end_date
        self.physical_ref = physical_ref
        self.other_ref = other_ref
        self.tags = tags
        self.linked_files = linked_files
        self.thumb_files = thumb_files
        self.created_by = created_by
        self.created_time = created_time
        self.last_changed_by = last_changed_by
        self.last_changed_time = last_changed_time

    def __len__(self):
        return 0

    def __str__(self, *args):
        title_len = 20
        desc_len = 40

        if len(args) == 2:
            title_len = args[0]
            desc_len = args[1]

        id_string = str(self.record_id).zfill(4)

        if len(self.title) > title_len:
            title_string = self.title[:title_len - 3] + "..."
        else:
            title_string = self.title

        if len(self.description) > desc_len:
            desc_string = self.description[:desc_len - 3] + "..."
        else:
            desc_string = self.description

        return "{} - {} - {}".format(id_string, title_string.ljust(title_len), desc_string.ljust(desc_len))

    def launch_file(self, file_index=0):
        if self.linked_files is None:
            pass
        else:
            try:
                if os.path.exists(self.linked_files[file_index]):
                    fail = os.startfile(self.linked_files[file_index])
                    if fail:
                        return "Unknown Error"
                    else:
                        return True
                else:
                    return "Path Error"
            except IndexError:
                return "Index Error"

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

    def created_time_string(self):
        if self.created_time is None:
            return None
        else:
            return "{:%d/%m/%Y %H:%Mhrs}".format(self.created_time)

    def last_changed_time_string(self):
        if self.last_changed_time is None:
            return None
        else:
            return "{:%d/%m/%Y %H:%Mhrs}".format(self.last_changed_time)

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
    except EOFError:
        return False
    return data


def save_bin_file(filename, data):
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
            return True
        else:
            return bad_chars


def get_record_by_id(record_id=0):
    if ";" in str(record_id):
        return None
    else:
        item = bliss.one("SELECT * FROM resources WHERE id=?", (record_id,))
        if item is None:
            return None
        else:
            return format_sql_to_record_obj(item)


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
    records = bliss.all(q, ())
    formatted_records = []
    for r in records:
        formatted_records.append(format_sql_to_record_obj(r))
    return formatted_records


def format_sql_to_record_obj(db_record_object):
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
    if db_record_object.last_changed_time is None:
        last_changed_time = None
    else:
        last_changed_time = datetime.datetime.fromtimestamp(int(db_record_object.last_changed_time / 1000))

    # Create tag and item lists
    if db_record_object.tags is not None:
        tags = db_record_object.tags.split("|")
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
    record_obj = ArchiveRecord(record_id=db_record_object.id,
                               title=db_record_object.title,
                               description=db_record_object.description,
                               record_type=type_text,
                               local_auth=auth_text,
                               start_date=start_date,
                               end_date=end_date,
                               physical_ref=db_record_object.physical_ref,
                               other_ref=db_record_object.other_ref,
                               tags=tags,
                               linked_files=linked_files,
                               thumb_files=thumb_files,
                               created_by=db_record_object.created_by,
                               created_time=created_time,
                               last_changed_by=db_record_object.last_changed_by,
                               last_changed_time=last_changed_time,
                               )
    return record_obj


def format_record_obj_to_sql(record_obj: ArchiveRecord):
    if record_obj is None:
        return None
    else:
        pass
        record_type_id = int(bliss.one("SELECT id FROM types WHERE type_text=?", (record_obj.record_type,)))
        local_auth_id = int(bliss.one("SELECT id FROM local_authorities WHERE local_auth=?", (record_obj.local_auth,)))
        if record_obj.start_date is None:
            start_date_stamp = None
        else:
            start_date_stamp = int(record_obj.start_date.timestamp() * 1000)
        if record_obj.start_date is None:
            end_date_stamp = None
        else:
            end_date_stamp = int(record_obj.end_date.timestamp() * 1000)
        if record_obj.created_time is None:
            created_time_stamp = None
        else:
            created_time_stamp = int(record_obj.created_time.timestamp() * 1000)
        if record_obj.last_changed_time is None:
            last_changed_time_stamp = None
        else:
            last_changed_time_stamp = int(record_obj.last_changed_time.timestamp() * 1000)

        tags_string = ""
        for t in record_obj.tags:
            tags_string += str(t) + "|"
        tags_string = tags_string.strip("|")

        params_list = [record_obj.title,
                       record_obj.description,
                       record_type_id,
                       local_auth_id,
                       start_date_stamp,
                       end_date_stamp,
                       record_obj.physical_ref,
                       record_obj.other_ref,
                       tags_string,
                       record_obj.created_by,
                       created_time_stamp,
                       record_obj.last_changed_by,
                       last_changed_time_stamp,
                       ]
        return record_obj.record_id, params_list


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


def float_none_drop_other(t):
    if t == "None":
        return "AAAAAAAAAA"
    elif t.endswith("Other"):
        parts = t.split(" ")
        new = ""
        parts.pop(len(parts) - 1)
        for p in parts:
            new += p + " "
        new += "zzzzzzzzzz"
        return new
    else:
        return t


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


def format_search_string(search_string):
    special_chars = [".", "^", "$", "+", "{"]
    formatted_string = search_string.upper()
    for c in special_chars:
        formatted_string = formatted_string.replace(c, "\\" + c)
    formatted_string = formatted_string.replace("?", ".")
    formatted_string = formatted_string.replace("*", ".*?")
    return formatted_string


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
                    if data is False:
                        os.remove(full_f)
                    elif data.unsaved_changes:
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
        record_obj = ArchiveRecord(record_id=0)
    else:
        record_obj = get_record_by_id(record_id)

    if record_obj is None:
        return None
    else:
        fd, record_object_path = temp.mkstemp(".dat", "OATEMP", TEMP_DATA_LOCATION)
        os.close(fd)
        save_bin_file(record_object_path, record_obj)
        return record_object_path


def commit_record(cached_record_path=None, record_obj: ArchiveRecord = None):
    # Commits changes or new record to db
    try:
        if record_obj is None:
            record_obj = access_bin_file(cached_record_path)
        else:
            pass

        if record_obj.created_time is None:
            record_obj.created_time = datetime.datetime.fromtimestamp(time.time())
            record_obj.created_by = os.environ['USERNAME']

        record_obj.last_changed_time = datetime.datetime.fromtimestamp(time.time())
        record_obj.last_changed_by = os.environ['USERNAME']

        record_id, params = format_record_obj_to_sql(record_obj)
        print(record_id)
        print(params)

        if (record_id == 0) or (record_id == "New Record") or (record_id is None):
            bliss.run("INSERT INTO resources (title, description, record_type, local_auth, start_date, end_date,"
                      "physical_ref, other_ref, tags, created_by, created_time, last_changed_by, last_changed_time)"
                      "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                      params)
            record_obj = format_sql_to_record_obj(bliss.one("FROM resources SELECT 1 WHERE last_changed=?",
                                                            (record_obj.last_changed_time.timestamp() * 1000,)))
        else:
            params.append(record_id)
            bliss.run("UPDATE resources set title=?, description=?, record_type=?, local_auth=?, start_date=?, end_date=?,"
                      "physical_ref=?, other_ref=?, tags=?, created_by=?, created_time=? WHERE id=?", params)
        conn.commit()
        return record_obj


def search_archive(text="", resource_type=None, local_auth=None, start_date=None, end_date=None):
    # Only retrieve results in the resource and auth brackets.
    if (resource_type is None) and (local_auth is None):
        base_list = bliss.all("SELECT * FROM resources", [])
    elif (resource_type is not None) and (local_auth is None):
        base_list = bliss.all("SELECT * FROM resources WHERE record_type=?", [resource_type, ])
    elif (resource_type is None) and (local_auth is not None):
        base_list = bliss.all("SELECT * FROM resources WHERE local_auth=?", [local_auth, ])
    else:
        base_list = bliss.all("SELECT * FROM resources WHERE local_auth=? AND record_type=?",
                              (local_auth, resource_type))
    if (len(str(text)) != 0) and (text is not None):
        scored_results = score_results(base_list, text)
        return scored_results
    else:
        return base_list


def score_results(results, text):
    scores = []
    r: ArchiveRecord
    for r in results:
        print()
        # Gen score
        title_similarity = textdistance.levenshtein.normalized_similarity(text.upper(), r.title.upper())
        key_words = text.upper().split(" ")
        # print(text, key_words)
        if text.upper() not in key_words:
            key_words.append(text.upper())
        key_word_hits = 1
        physical_ref_hit = 1
        other_ref_hit = 1
        for k in key_words:
            formatted = format_search_string(k)
            if re.search(formatted, r.title.upper()) is not None:
                key_word_hits += 1
            else:
                pass
            if re.search(formatted, r.description.upper()) is not None:
                key_word_hits += 1
            else:
                pass
            if r.tags is not None:
                for t in r.tags:
                    if re.search(formatted, t.upper()) is not None:
                        key_word_hits += 1
                    else:
                        pass
            else:
                pass
            if r.physical_ref is not None:
                if re.search(formatted, r.physical_ref) is not None:
                    physical_ref_hit = 2
                else:
                    pass
            else:
                pass
            if r.other_ref is not None:
                if re.search(formatted, r.other_ref) is not None:
                    other_ref_hit = 2
                else:
                    pass
            else:
                pass
        print(key_words)
        print(title_similarity, key_word_hits, int(physical_ref_hit), int(other_ref_hit))
        score = float(title_similarity * key_word_hits * int(physical_ref_hit) * int(other_ref_hit))
        print(r.id, score)
        if score == 0.0:
            pass
        else:
            scores.append((r, score))
    scores.sort(key=lambda s: s[1])
    final_results = []
    for sr in scores:
        final_results.append(sr[0])
    return final_results


def check_record(record_obj: ArchiveRecord):
    if "" in (record_obj.title.strip(), record_obj.title.strip()):
        return "Missing Field"
    else:
        title_valid = check_text_is_valid(record_obj.title)
        description_valid = check_text_is_valid(record_obj.description)
        if (title_valid is True) and (description_valid is True):
            return True
        else:
            return "Bad Chars"
