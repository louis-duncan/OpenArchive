import os

# Config Path
LOCAL_CONFIG = ".\\bin\\local_config.cfg"
GLOBAL_CONFIG = ".\\bin\\global_config.cfg"

# Root path of the repo.
ARCHIVE_LOCATION_ROOT = os.path.abspath(".\\New")  # os.path.abspath(os.path.join(os.environ["ONEDRIVE"], "Test DB Location"))
# Path of the sql database file.
DATABASE_LOCATION = os.path.abspath(os.path.join(ARCHIVE_LOCATION_ROOT, "open_archvie.db"))  # os.path.abspath(".\\bin\\archive.db")
# The sub directory in which OpenArchive will place new uploaded content.
ARCHIVE_LOCATION_SUB = os.path.join(ARCHIVE_LOCATION_ROOT, "OpenArchive")
# Directories in which files are left in place and not copied to the archive when linked.
ARCHIVE_INCLUDED_DIRS = [os.path.abspath(".\\Also Included"),]
# Directory used for holding local files. Cleared on program exit.
TEMP_DATA_LOCATION = os.path.abspath(os.path.join(os.environ["TEMP"], "OpenArchive"))


def load_config():
    global LOCAL_CONFIG, GLOBAL_CONFIG, ARCHIVE_LOCATION_ROOT, DATABASE_LOCATION, ARCHIVE_LOCATION_SUB, ARCHIVE_INCLUDED_DIRS, TEMP_DATA_LOCATION
    local_config = {"GLOBAL_CONFIG" : GLOBAL_CONFIG,
                    "TEMP_DATA_LOCATION" : TEMP_DATA_LOCATION,
                    }
    formatted_incs = ""
    for i in ARCHIVE_INCLUDED_DIRS:
        formatted_incs += i + "|"
    formatted_incs = formatted_incs.strip("|")
        
    global_config = {"DATABASE_LOCATION" : DATABASE_LOCATION,
                     "ARCHIVE_LOCATION_ROOT" : ARCHIVE_LOCATION_ROOT,
                     "ARCHIVE_LOCATION_SUB" : ARCHIVE_LOCATION_SUB,
                     "ARCHIVE_INCLUDED_DIRS" : formatted_incs,
                     }
    # Load local config
    print("Loading local config...")
    try:
        with open(LOCAL_CONFIG, "r") as file:
            local_config_lines = file.readlines()
    except FileNotFoundError:
            local_config_lines = []

    for l in local_config_lines:
        v_name, v_value = l.split("=", 1)
        v_name = v_name.strip()
        v_value = v_value.strip()
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
        listed_incs.append(os.path.abspath(p.strip()))        

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
