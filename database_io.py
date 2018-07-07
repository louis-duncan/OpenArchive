import inspect
import os
import random
import re
import sqlite3
import time
import sql
import datetime
import easygui
import pickle
import temp
import textdistance
import shutil
from sql import SQL

# Initialise the random module
random.seed(str(os.environ["USERNAME"] + str(datetime.datetime.now())))

__title__ = "OpenArchive"

# noinspection SpellCheckingInspection
invalid_chars = ""

# Config Path
LOCAL_CONFIG = os.path.join(os.environ["LOCALAPPDATA"], "OpenArchive\\local_config.cfg")
TEMPLATE_LOCAL_CONFIG = ".\\cfg\\template_local_config.cfg"
GLOBAL_CONFIG = ".\\cfg\\global_config.cfg"

# Root path of the repo.
ARCHIVE_LOCATION_ROOT = os.path.abspath(".\\New")
# Path of the sql database file.
DATABASE_LOCATION = os.path.abspath(os.path.join(ARCHIVE_LOCATION_ROOT, "open_archive.db"))
# The sub directory in which OpenArchive will place new uploaded content.
ARCHIVE_LOCATION_SUB = os.path.join(ARCHIVE_LOCATION_ROOT, "OpenArchive")
# Directories in which files are left in place and not copied to the archive when linked.
ARCHIVE_INCLUDED_DIRS = []
# Directory used for holding local files. Cleared on program exit.
TEMP_DATA_LOCATION = os.path.abspath(os.path.join(os.environ["TEMP"], "OpenArchive"))
# Start DateTime from which all database dates are calculated as a difference.
EPOCH = datetime.datetime(1970, 1, 1)


class DatabaseError(Exception):
    pass


class ArchiveRecord:
    tags_prompt = 'Enter tags comma separated. (eg. tag1, tag2,...)'

    # noinspection PyDefaultArgument
    def __init__(self, record_id=0, title="", description="", record_type=None, local_auth=None,
                 start_date=None, end_date=None, physical_ref="", other_ref="", new_tags=[], linked_files=[],
                 longitude=None, latitude=None, thumb_files=[], created_by=None, created_time=None, last_changed_by=None,
                 last_changed_time=None):
        self.record_id = record_id
        self.title = title
        self.description = description
        self.record_type = record_type
        self.local_auth = local_auth
        self.start_date = start_date
        self.end_date = end_date
        self.physical_ref = physical_ref
        self.other_ref = other_ref
        self.tags = new_tags
        self.linked_files = linked_files
        self.longitude = longitude
        self.latitude = latitude
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

        return "ID: {}\nTitle: {}\nDecription:\n{}\nType: {}\nAuth: {}\nDates: {} - {}\nPhysical Ref: {}\nOther Ref: {}\nTags: {}".format(
            self.record_id,
            self.title,
            self.description,
            self.record_type,
            self.local_auth,
            self.start_date_string(),
            self.end_date_string(),
            self.physical_ref,
            self.other_ref,
            self.string_tags(),
            )

    def launch_file(self, file_index=0, file_path=None, cache_dir=TEMP_DATA_LOCATION):
        if (self.linked_files is None) and (file_path is None):
            pass
        else:
            try:
                print("Launching", file_path)
                if file_path is not None:
                    path = file_path
                else:
                    path = self.linked_files[file_index]
                print(path)
                if os.path.exists(path):
                    # Cache file
                    # See if the file is in the Archive, if not, open it directly.
                    in_archive = check_if_in_archive(path)
                    if in_archive:
                        file_extension = path.split(".")[-1]
                        fd, cached_path = temp.mkstemp("." + file_extension, "OATEMP_", cache_dir)
                        os.close(fd)
                        shutil.copy2(path, cached_path)
                        path = cached_path
                    else:
                        pass
                    fail = os.startfile(path)
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
        prompt = self.tags_prompt
        if tags_to_add is None:
            output = ""
            for t in self.tags:
                output += t + ", "
            output = output.strip(", ")
            return output
        elif tags_to_add == prompt:
            pass
        else:
            parts = self.format_string_to_tags(tags_to_add)
            new_tags = []
            for p in parts:
                if p in new_tags:
                    pass
                else:
                    new_tags.append(p)
            self.tags = new_tags

    def format_string_to_tags(self, text):
        if text == self.tags_prompt:
            return []
        else:
            parts = text.split(",")
            tags = []
            for p in parts:
                p = p.strip()
                if p == "":
                    pass
                else:
                    tags.append(p.upper())
            return tags


def load_config():
    global LOCAL_CONFIG, TEMPLATE_LOCAL_CONFIG, GLOBAL_CONFIG, ARCHIVE_LOCATION_ROOT, DATABASE_LOCATION, ARCHIVE_LOCATION_SUB, ARCHIVE_INCLUDED_DIRS, TEMP_DATA_LOCATION

    local_config = {"GLOBAL_CONFIG": GLOBAL_CONFIG,
                    "TEMP_DATA_LOCATION": TEMP_DATA_LOCATION,
                    }

    formatted_incs = ""
    for i in ARCHIVE_INCLUDED_DIRS:
        formatted_incs += i + "|"
    formatted_incs = formatted_incs.strip("|")
    global_config = {"DATABASE_LOCATION": DATABASE_LOCATION,
                     "ARCHIVE_LOCATION_ROOT": ARCHIVE_LOCATION_ROOT,
                     "ARCHIVE_LOCATION_SUB": ARCHIVE_LOCATION_SUB,
                     "ARCHIVE_INCLUDED_DIRS": formatted_incs,
                     }

    # Load local config
    print("Loading local config at", LOCAL_CONFIG, "...")
    try:
        with open(LOCAL_CONFIG, "r") as file:
            local_config_lines = file.readlines()
    except FileNotFoundError:
        with open(TEMPLATE_LOCAL_CONFIG, "r") as file:
            local_config_lines = file.readlines()

    for l in local_config_lines:
        v_name, v_value = l.split("=", 1)
        v_name = v_name.strip()
        v_value = v_value.strip()
        if v_value == "":
            pass
        else:
            try:
                t = local_config[v_name]
                local_config[v_name] = v_value
            except KeyError:
                print("Ignoring unexpected parameter: {} = {}".format(v_name, v_value))

    # Format the read data
    local_config["GLOBAL_CONFIG"] = os.path.abspath(local_config["GLOBAL_CONFIG"])
    local_config["TEMP_DATA_LOCATION"] = os.path.abspath(local_config["TEMP_DATA_LOCATION"])

    # Set values
    GLOBAL_CONFIG = local_config["GLOBAL_CONFIG"]
    TEMP_DATA_LOCATION = local_config["TEMP_DATA_LOCATION"]

    # Re-write the config file
    try:
        os.mkdir(os.path.dirname(LOCAL_CONFIG))
    except FileExistsError:
        pass
    with open(LOCAL_CONFIG, "w") as file:
        lines = []
        for v in local_config:
            lines.append("{} = {}\n".format(v, local_config[v]))
        file.writelines(lines)

    print("Loading global config...")
    # Load global config
    try:
        with open(GLOBAL_CONFIG, "r") as file:
            global_config_lines = file.readlines()
    except FileNotFoundError:
        global_config_lines = []

    for l in global_config_lines:
        v_name, v_value = l.split("=", 1)
        v_name = v_name.strip()
        v_value = v_value.strip()
        try:
            t = global_config[v_name]
            global_config[v_name] = v_value
        except KeyError:
            print("Ignoring unexpected parameter: {} = {}".format(v_name, v_value))

    # Format the read data
    global_config["DATABASE_LOCATION"] = os.path.abspath(global_config["DATABASE_LOCATION"])
    global_config["ARCHIVE_LOCATION_ROOT"] = os.path.abspath(global_config["ARCHIVE_LOCATION_ROOT"])
    global_config["ARCHIVE_LOCATION_SUB"] = os.path.abspath(global_config["ARCHIVE_LOCATION_SUB"])
    listed_incs = []
    for p in global_config["ARCHIVE_INCLUDED_DIRS"].split("|"):
        sp = p.strip()
        if sp != "":
            listed_incs.append(os.path.abspath(sp))
    print("loaded inc dirs:", listed_incs)
    # Set values
    DATABASE_LOCATION = global_config["DATABASE_LOCATION"]
    ARCHIVE_LOCATION_ROOT = global_config["ARCHIVE_LOCATION_ROOT"]
    ARCHIVE_LOCATION_SUB = global_config["ARCHIVE_LOCATION_SUB"]
    ARCHIVE_INCLUDED_DIRS = listed_incs

    # Re-write the config file
    try:
        os.mkdir(os.path.dirname(GLOBAL_CONFIG))
    except FileExistsError:
        pass
    with open(GLOBAL_CONFIG, "w") as file:
        lines = []
        for v in global_config:
            lines.append("{} = {}\n".format(v, global_config[v]))
        file.writelines(lines)

    print("Local Config: {}\n"
          "Global Config: {}\n"
          "Local Temp Files: {}\n"
          "Database File Location: {}\n"
          "Repos. Locations: {}\n"
          "Repos. Sub. Loc.: {}\n"
          "Other Repo. Dirs.: {}".format(LOCAL_CONFIG,
                                         GLOBAL_CONFIG,
                                         TEMP_DATA_LOCATION,
                                         DATABASE_LOCATION,
                                         ARCHIVE_LOCATION_ROOT,
                                         ARCHIVE_LOCATION_SUB,
                                         ARCHIVE_INCLUDED_DIRS))


def create_new_database():
    try:
        os.mkdir(os.path.abspath(os.path.dirname(DATABASE_LOCATION)))
    except FileExistsError:
        print("Directory already there.")
    new_conn = sqlite3.connect(DATABASE_LOCATION)
    new_bliss = sql.SQL(new_conn)
    queries = ["""CREATE TABLE resources
(
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    title VARCHAR NOT NULL,
    description VARCHAR NOT NULL,
    record_type INTEGER NOT NULL,
    local_auth INTEGER NOT NULL,
    start_date DATE,
    end_date DATE,
    tags VARCHAR,
    other_ref VARCHAR,
    physical_ref VARCHAR,
    longitude FLOAT,
    latitude FLOAT,
    created_by VARCHAR,
    created_time DATETIME,
    last_changed_by VARCHAR,
    last_changed_time DATETIME
)""",
               "CREATE UNIQUE INDEX resources_id_uindex ON resources(id)",
               """CREATE TABLE types
(
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    type_text VARCHAR NOT NULL
)""",
               "CREATE UNIQUE INDEX types_id_uindex ON types(id)",
               "CREATE UNIQUE INDEX types_type_text_uindex ON types (type_text)",
               """CREATE TABLE local_authorities
(
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    local_auth VARCHAR NOT NULL
)""",
               "CREATE UNIQUE INDEX local_authorities_id_uindex ON local_authorities (id)",
               "CREATE UNIQUE INDEX local_authorities_local_auth_uindex ON local_authorities (local_auth)",
               """CREATE TABLE file_links
(
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    record_id INTEGER NOT NULL,
    file_path VARCHAR NOT NULL,
    thumbnail_path VARCHAR
)""",
               "CREATE UNIQUE INDEX file_links_id_uindex ON file_links (id)",
               """CREATE TABLE bookmarks
(
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    user_name VARCHAR NOT NULL,
    record_id INTEGER NOT NULL
)""",
               "CREATE UNIQUE INDEX bookmarks_id_uindex ON bookmarks (id)",
               "INSERT INTO types(id, type_text) VALUES(0, 'None')",
               "INSERT INTO local_authorities(id, local_auth) VALUES(0, 'None')",
               ]
    for q in queries:
        new_bliss.run(q, ())
    new_conn.commit()
    new_conn.close()


def db_run(query, params):
    bliss = db_prep_for_access()
    if bliss is False:
        db_unlock()
        return False
    else:
        bliss.run(query, params)
        bliss.connection.commit()
        bliss.connection.close()
        db_unlock()
        return True


def db_all(query, params):
    bliss = db_prep_for_access()
    if bliss is False:
        db_unlock()
        return False
    else:
        result = bliss.all(query, params)
        bliss.connection.close()
        db_unlock()
        return result


def db_one(query, params):
    bliss = db_prep_for_access()
    if bliss is False:
        db_unlock()
        return False
    else:
        result = bliss.one(query, params)
        bliss.connection.close()
        db_unlock()
        return result


def db_lock(ttl=10):
    stat_file_path = os.path.join(os.path.dirname(DATABASE_LOCATION), "stat.dat")
    lock_time = datetime.datetime.now() + datetime.timedelta(seconds=ttl)
    save_bin_file(stat_file_path, lock_time)
    try:
        caller_name = "{} > {} > {}".format(inspect.stack()[5][3],
                                            inspect.stack()[4][3],
                                            inspect.stack()[3][3])
    except IndexError:
        try:
            caller_name = "{} > {}".format(inspect.stack()[4][3],
                                           inspect.stack()[3][3])
        except IndexError:
            try:
                caller_name = "{}".format(inspect.stack()[2][3])
            except IndexError:
                caller_name = "unknown"
    print("\nDatabase locked at {} until {} by function:\n{}".format(datetime.datetime.now(), lock_time, caller_name))


def db_unlock():
    stat_file_path = os.path.join(os.path.dirname(DATABASE_LOCATION), "stat.dat")
    save_bin_file(stat_file_path, None)
    print("Database unlocked at {}.".format(datetime.datetime.now()))


def db_check_lock_status():
    stat_file_path = os.path.join(os.path.dirname(DATABASE_LOCATION), "stat.dat")
    current_lock: datetime.datetime = access_bin_file(stat_file_path)
    if current_lock is None:
        return 0
    else:
        ttl = (current_lock - datetime.datetime.now()).total_seconds()
        if ttl < 0:
            return 0
        else:
            return ttl


def db_prep_for_access(timeout=10):
    wait_time = 0
    tries = 0
    while True:
        locked = db_check_lock_status()
        if locked > 0:
            salt = random.uniform(0, 3)
            tries += 1
            print("Try number {} failed. Waiting {} seconds...".format(tries, salt))
            time.sleep(salt)
            wait_time += salt
        else:
            break
        if wait_time > timeout:
            print("Timed out after {} tries over {} seconds.".format(tries, wait_time))
            raise DatabaseError("Connection Timed Out")
        else:
            pass
    db_lock()
    bliss = open_database_connection()
    return bliss


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
            if c in invalid_chars:
                valid = False
                bad_chars.append(c)
            else:
                pass
        if valid:
            return True
        else:
            return bad_chars


def get_record_by_id(record_id=0):
    if ";" in str(record_id):
        return None
    else:
        item = db_one("SELECT * FROM resources WHERE id=?", (record_id,))
        # Todo add catch for 'item is false' caused by failed connection.
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
    records = db_all(q, ())
    # Todo: Add catch for 'records if False' caused by failed connection
    formatted_records = []
    for r in records:
        formatted_records.append(format_sql_to_record_obj(r))
    return formatted_records


def format_sql_to_record_obj(db_record_object):
    # Convert Type and Auth ids to text.
    type_text = db_one("SELECT * FROM types WHERE id=?", (db_record_object.record_type,)).type_text
    auth_text = db_one("SELECT * FROM local_authorities WHERE id=?", (db_record_object.local_auth,)).local_auth
    # Todo: Add catch for "False in (type_text, auth_text) caused by failed connection.

    # Convert dates to datetimes
    if db_record_object.start_date is None:
        start_date = None
    else:
        start_date = EPOCH + datetime.timedelta(milliseconds=db_record_object.start_date)
    if db_record_object.end_date is None:
        end_date = None
    else:
        end_date = EPOCH + datetime.timedelta(milliseconds=db_record_object.end_date)
    if db_record_object.created_time is None:
        created_time = None
    else:
        created_time = EPOCH + datetime.timedelta(milliseconds=db_record_object.created_time)
    if db_record_object.last_changed_time is None:
        last_changed_time = None
    else:
        last_changed_time = EPOCH + datetime.timedelta(milliseconds=db_record_object.last_changed_time)

    # Create tag and item lists
    if db_record_object.tags is not None:
        tags = db_record_object.tags.split("|")
        while tags.count("") > 0:
            tags.remove("")
    else:
        tags = None

    linked_files = []
    thumb_files = []
    record_file_links = db_all("SELECT * FROM file_links WHERE record_id=?", (db_record_object.id,))
    # Todo: Add catch for "record_file_links is False" caused by failed connection.
    for f in record_file_links:
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
                               new_tags=tags,
                               linked_files=linked_files,
                               longitude=db_record_object.longitude,
                               latitude=db_record_object.latitude,
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
        record_type_id = db_one("SELECT id FROM types WHERE type_text=?",
                                       (str(record_obj.record_type),))
        local_auth_id = db_one("SELECT id FROM local_authorities WHERE local_auth=?",
                                      (str(record_obj.local_auth),))
        # Todo: Add catch for "False in (record_type_id, local_auth_id)" cause by failed connection.

        record_type_id = int(record_type_id)
        local_auth_id = int(local_auth_id)

        if record_obj.start_date is None:
            start_date_stamp = None
        else:
            start_date_stamp = int((record_obj.start_date - EPOCH).total_seconds() * 1000)
        if record_obj.end_date is None:
            end_date_stamp = None
        else:
            end_date_stamp = int((record_obj.end_date - EPOCH).total_seconds() * 1000)
        if record_obj.created_time is None:
            created_time_stamp = None
        else:
            created_time_stamp = int((record_obj.created_time - EPOCH).total_seconds() * 1000)
        if record_obj.last_changed_time is None:
            last_changed_time_stamp = None
        else:
            last_changed_time_stamp = int((record_obj.last_changed_time - EPOCH).total_seconds() * 1000)

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
                       record_obj.longitude,
                       record_obj.latitude,
                       record_obj.created_by,
                       created_time_stamp,
                       record_obj.last_changed_by,
                       last_changed_time_stamp,
                       ]
        return record_obj.record_id, params_list


def return_types():
    try:
        type_records = db_all("SELECT * FROM types", ())
    except DatabaseError:
        raise
    types = []
    for r in type_records:
        types.append(r.type_text)
    return types


def return_local_authorities():
    try:
        local_authority_records = db_all("SELECT * FROM local_authorities", ())
    except DatabaseError:
        raise
    local_authorities = []
    for r in local_authority_records:
        local_authorities.append(r.local_auth)
    return local_authorities


def float_none_drop_other(t):
    if t == "None":
        return "AAAAAAAAAA"
    elif t.upper().endswith("OTHER"):
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
        thumbnail_record = db_one("SELECT * FROM file_links WHERE id=?", (file_link_id,))
    elif file_path is not None:
        thumbnail_record = db_one("SELECT * FROM file_links WHERE file_path=?", (file_path,))
    else:
        return None
    # Todo: Add catch for "thumbnail_record is False" caused by failed connection.
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
    print("{} files in:\n{}".format(len(temp_files), TEMP_DATA_LOCATION))
    fails = []
    for f in temp_files:
        full_f = os.path.join(TEMP_DATA_LOCATION, f)
        remove = False

        if os.path.basename(f).startswith("OA"):
            remove = True
        else:
            pass

        if remove:
            print("Purging {}... ".format(f), end="")
            try:
                os.remove(full_f)
                print("success")
            except PermissionError:
                fails.append(full_f)
                print("fail")
            except FileNotFoundError:
                print("not found")
        else:
            print("Skipping {}... ".format(f))

    return fails


def create_cached_record(record_id=None):
    if record_id is None:
        record_obj = ArchiveRecord(record_id=0)
    else:
        record_obj = get_record_by_id(record_id)

    if record_obj is None:
        return None
    else:
        fd, record_object_path = temp.mkstemp(".dat", "OATMP", TEMP_DATA_LOCATION)
        os.close(fd)
        save_bin_file(record_object_path, record_obj)
        return record_object_path


def check_if_in_archive(path):
    roots_to_check = [os.path.abspath(ARCHIVE_LOCATION_ROOT),
                      os.path.abspath(ARCHIVE_LOCATION_SUB)]
    for d in ARCHIVE_INCLUDED_DIRS:
        roots_to_check.append(os.path.abspath(d))

    in_archive = False
    for r in roots_to_check:
        print(r)
        if is_file_in_root(path, r):
            in_archive = True
            break
        else:
            pass
    return in_archive


def commit_record(cached_record_path=None, record_obj: ArchiveRecord = None):
    # Commits changes or new record to db
    try:
        if record_obj is None:
            record_obj = access_bin_file(cached_record_path)
        else:
            pass

        # Make Title and Desc None if they are empty so that it will be caught later.
        if record_obj.title == "":
            record_obj.title = None
        if record_obj.description == "":
            record_obj.description = None

        if record_obj.created_time is None:
            record_obj.created_time = datetime.datetime.fromtimestamp(time.time())
            record_obj.created_by = os.environ['USERNAME']

        record_obj.last_changed_time = datetime.datetime.fromtimestamp(time.time())
        record_obj.last_changed_by = os.environ['USERNAME']

        record_id, params = format_record_obj_to_sql(record_obj)
        files_to_link = record_obj.linked_files
        print(record_id)
        print(params)
        print("Files to be linked:", files_to_link)
        if (record_id == 0) or (record_id == "New Record") or (record_id is None):
            suc = db_run('INSERT INTO resources (title, description, record_type, local_auth, start_date, end_date, '
                      'physical_ref, other_ref, tags, longitude, latitude, created_by, created_time, last_changed_by, '
                      'last_changed_time) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                      params)
        else:
            params.append(record_id)
            suc = db_run("UPDATE resources set title=?, description=?, record_type=?, local_auth=?, start_date=?,"
                      "end_date=?, physical_ref=?, other_ref=?, tags=?, longitude=?, latitude=?, created_by=?, "
                      "created_time=?, last_changed_by=?, last_changed_time=? WHERE id=?", params)
        # Todo: Add check to see if "suc is False" caused by failed connection.
        changed_time_stamp = int((record_obj.last_changed_time - EPOCH).total_seconds() * 1000)
        record_obj = format_sql_to_record_obj(db_one("SELECT * FROM resources WHERE last_changed_time=?",
                                                     (changed_time_stamp,)))
        # Todo: Add catch for "record_obj is False" cause by failed connection.
        old_file_links = db_all("SELECT * FROM file_links WHERE record_id=?", (record_obj.record_id,))
        # Todo: Add catch for "old_file_links is False" cause by failed connection.
        # Compare list of old links to the newly submitted links
        # If the old link is not in the new list, mark as dead.
        # If is is, remove that file name from the list.
        dead_links = []
        for link in old_file_links:
            if link.file_path in files_to_link:
                print(link.file_path, "already linked.")
                dead_links.append(False)
                files_to_link.remove(link.file_path)
            else:
                dead_links.append(True)

        # The remaining files in the submitted list are new links, so deal with them.
        for f in files_to_link:
            link_f = os.path.abspath(f)
            if check_if_in_archive(link_f):  # If file in archive, no need to copy it in.
                pass
            else:  # Move the file from it's current location to the archive.
                link_f = move_file_to_archive(f)
            suc = db_run("INSERT INTO file_links (record_id, file_path, thumbnail_path) VALUES (?, ?, ?)",
                         (record_obj.record_id, link_f, ""))
            # Todo: Add catch for "suc is False" caused by failed connection.

        # Now clear away dead links.
        for i, link in enumerate(old_file_links):
            if dead_links[i] is True:
                # Check is truly dead
                hope = db_all("SELECT * FROM file_links WHERE file_path=?", (link.file_path,))
                # Todo: Add catch for "hope is False" caused by failed connection
                if len(hope) <= 1:
                    if (len(hope) == 1) and (int(hope[0].record_id) != int(record_obj.record_id)):
                        print("")
                        # Hope is re-kindled...
                        # This record is linked to another file!
                        # So leave it in place.
                        print("Hope re-kindled for link between "
                              "{} and {}.".format(record_obj.record_id, link.file_path))
                        pass
                    else:
                        # No hope for this link!
                        print("Purging {}!".format(link.file_path))

                        # Check if the file we're un-linking is in the dir managed by OpenArchive.
                        # If so, copy it to the desktop.
                        in_sub = is_file_in_root(ARCHIVE_LOCATION_SUB, link.file_path)

                        suc = True
                        if in_sub:
                            desktop = os.path.join(os.environ["USERPROFILE"], "Desktop")
                            shutil.copy2(link.file_path, desktop)
                            try:
                                os.remove(link.file_path)
                                os.rmdir(os.path.dirname(link.file_path))
                            except PermissionError:
                                suc = False
                                print("PermissionError: Could not delete {}!".format(link.file_path))
                            except OSError:
                                suc = False
                                print("OSError: Could not delete {}!".format(os.path.dirname(link.file_path)))
                        else:
                            # Leave it where it is.
                            print("Leaving {} in place, as it is not in the directory managed by OA."
                                  .format(link.file_path))

                        # Finally, remove the actual link as long as the file was successfuly deleted.
                        if suc:
                            del_suc = db_run("DELETE FROM file_links WHERE id=?", (link.id,))
                            # Todo: Add catch for "del_suc is False" caused by failed connection.
                else:
                    print("Just enough hope to save the link between"
                          "{} and {}.".format(record_obj.record_id, link.file_path))
                    pass
            else:
                pass
        sql_record_obj = db_one("SELECT * FROM resources WHERE last_changed_time=?", (changed_time_stamp,))
        # Todo: Add catch for "sql_record_obj is False" caused by failed connection.
        record_obj = format_sql_to_record_obj(sql_record_obj)
        return record_obj
    except sqlite3.IntegrityError:
        return "IntegrityError"
    except sqlite3.OperationalError:
        return "OperationalError"


def search_archive(text="", resource_type=None, local_auth=None, start_date=None, end_date=None):
    # Only retrieve results in the resource and auth brackets.
    if (resource_type is None) and (local_auth is None):
        base_list = db_all("SELECT * FROM resources", [])
    elif (resource_type is not None) and (local_auth is None):
        base_list = db_all("SELECT * FROM resources WHERE record_type=?", [resource_type, ])
    elif (resource_type is None) and (local_auth is not None):
        base_list = db_all("SELECT * FROM resources WHERE local_auth=?", [local_auth, ])
    else:
        base_list = db_all("SELECT * FROM resources WHERE local_auth=? AND record_type=?",
                              (local_auth, resource_type))
    # Todo: Add catch for "base_list is False" caused by failed connection.
    if (len(str(text)) != 0) and (text is not None):
        scored_results = score_results(base_list, text)
        return scored_results
    else:
        return base_list


def move_file_to_archive(cached_path=""):
    new_root = temp.mkdtemp(prefix="", dir=ARCHIVE_LOCATION_SUB)
    new_full_path = os.path.abspath(os.path.join(new_root, os.path.basename(cached_path)))
    suc = shutil.copy2(cached_path, new_full_path)
    os.remove(cached_path)
    return suc


def score_results(results, text):
    scores = []
    for r in results:
        # Gen score
        title_similarity = 4 * textdistance.levenshtein.normalized_similarity(text.upper(), r.title.upper())
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
        score = float(title_similarity * key_word_hits * int(physical_ref_hit) * int(other_ref_hit))
        score = round(score, 1)
        print(r.id, score)
        if score == 0.0:
            pass
        else:
            scores.append((r, score))
    scores.sort(key=lambda s: s[1])
    scores.reverse()
    final_results = []
    for sr in scores:
        final_results.append(sr[0])
    return final_results


def check_record(record_obj: ArchiveRecord):
    if "" in (record_obj.title.strip(), record_obj.description.strip()):
        return "Missing Field"
    else:
        title_valid = check_text_is_valid(record_obj.title)
        description_valid = check_text_is_valid(record_obj.description)
        if (title_valid is True) and (description_valid is True):
            return True
        else:
            return "Bad Chars"


def add_new_type(type_string):
    suc = db_run("INSERT INTO types (type_text) VALUES (?)", (type_string,))
    # Todo: Add check for "suc is False" caused by failed connection.


def add_new_local_authority(local_auth_string):
    suc = db_run("INSERT INTO local_authorities (local_auth) VALUES (?)", (local_auth_string,))
    # Todo: Add check for "suc is False" caused by failed connection.


def move_file_to_cache(new_file_path, cache_dir=TEMP_DATA_LOCATION):
    assert cache_dir.startswith(TEMP_DATA_LOCATION)

    if is_file_in_root(new_file_path, cache_dir):
        return os.path.abspath(new_file_path)
    else:
        return shutil.copy2(new_file_path, cache_dir)


def add_bookmark(user_name="", record_id=0):
    check = db_one("SELECT title FROM resources WHERE id=?", (record_id,))
    # Todo: Add catch for "check is False" caused by failed connection.
    assert check is not None
    if user_name is None or user_name == "":
        user_name = os.environ["USERNAME"]
    print("Bookmarking {} for {}".format(check, user_name))
    suc = db_run("INSERT INTO bookmarks (user_name, record_id) VALUES (?, ?)", (user_name, record_id))
    # Todo: Add catch for "suc is False" caused by failed connection.


def remove_bookmark(user_name, record_id):
    suc = db_run("DELETE FROM bookmarks WHERE user_name=? AND record_id=?", (user_name, record_id))
    # Todo: Add catch for "suc is False" caused by failed connection.


def get_user_bookmarks(user_name=None):
    if user_name is None:
        user_name = os.environ["USERNAME"]
    else:
        pass
    results = db_all("SELECT record_id FROM bookmarks WHERE user_name=?", (user_name,))
    # Todo: Add catch for "results is False" caused by failed connection
    return results


def get_files_links(file_path):
    results = db_all("SELECT * FROM file_links WHERE file_path=?", (file_path,))
    # Todo: Add catch for "results is False" caused by failed connection.
    return results


def is_file_in_root(file_path, root):
    in_dir = False
    print("Is {} in {}? ".format(file_path, root), end="")
    try:
        in_dir = os.path.abspath(root) == os.path.commonpath((root, file_path))
        print(str(in_dir))
    except ValueError:
        print("Error")

    return in_dir


def is_file_in_archive(file_path):
    in_archive = False
    full_path = os.path.abspath(file_path)
    if full_path.startswith(os.path.abspath(ARCHIVE_LOCATION_ROOT) + "\\"):
        in_archive = True
    else:
        for i_path in ARCHIVE_INCLUDED_DIRS:
            if full_path.startswith(os.path.abspath(i_path) + "\\"):
                in_archive = True
                break
            else:
                pass
    return in_archive


def open_database_connection() -> SQL:
    conn = sqlite3.connect(DATABASE_LOCATION)
    bliss: SQL = sql.SQL(conn)
    return bliss


def init():
    # Main Script
    try:
        load_config()
    except FileNotFoundError:
        easygui.msgbox("Could not load config at {},\nthe program will close.".format(GLOBAL_CONFIG), "OpenArchive")
        exit()

    if os.path.exists(ARCHIVE_LOCATION_ROOT):
        pass
    else:
        try:
            os.mkdir(ARCHIVE_LOCATION_ROOT)
        except:
            easygui.msgbox("OpenArchiveManager could not access or create a data repository at:\n"
                           "{}\n"
                           "\n"
                           "The program will now exit.".format(ARCHIVE_LOCATION_ROOT))

    if os.path.exists(ARCHIVE_LOCATION_SUB):
        pass
    else:
        try:
            os.mkdir(ARCHIVE_LOCATION_SUB)
        except:
            easygui.msgbox("OpenArchiveManager could not access or create a data repository at:\n"
                           "{}\n"
                           "\n"
                           "The program will now exit.".format(ARCHIVE_LOCATION_SUB))

    if os.path.exists(TEMP_DATA_LOCATION):
        pass
    else:
        try:
            os.mkdir(TEMP_DATA_LOCATION)
        except:
            easygui.msgbox("OpenArchiveManager could not access or create the temporary data location at:\n"
                           "{}\n"
                           "\n"
                           "The program will now exit.".format(TEMP_DATA_LOCATION), __title__)

    try:
        if os.path.exists(DATABASE_LOCATION):
            pass
        else:
            easygui.msgbox("Could not load the database at '{}'\n"
                           "\n"
                           "OpenArchive will attempt to start a new database.".format(DATABASE_LOCATION))
            create_new_database()
        test_connection = open_database_connection()
        test_connection.connection.close()
    except sqlite3.OperationalError:
        easygui.msgbox("Could not load the database at '{}'\n"
                       "\n"
                       "The path may not be valid.".format(DATABASE_LOCATION))
        exit()
