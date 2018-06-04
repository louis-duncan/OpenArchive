import os
import datetime
import easygui
import _thread
import record_list_viewer
import database_io
import upload_agent
import record_editor

__title__ = "OpenArchive"
__author__ = "Louis Thurman"


def quick_search():
    # todo: Write quick search
    # Get user input
    msg = "Enter Search Terms:"
    user_input = easygui.enterbox(msg, __title__ + " - Quick Search")
    if user_input is None:
        pass
    else:
        pass
        # Perform search
        # Display results


def detailed_search():
    pass
    # Get user input.
    # Perform search.
    # Display results.
    # todo: Write detailed search


def launch_upload_agent():
    # Created Blank Record and loads editor.
    r = database_io.ArchiveRecord()
    r.record_id = "New Record"
    # r = database_io.get_record_by_id(50)
    record_editor.main(r)


def access_users_list():
    # Access to users list
    user_name = os.environ["USERNAME"]
    bookmarks = database_io.get_user_bookmarks(user_name)
    # Check bookmarks for dead links
    dead_bookmarks = []
    for b in bookmarks:
        test = database_io.get_record_by_id(b)
        if test is None:
            database_io.remove_bookmark(user_name, b)
            dead_bookmarks.append(b)
    for d in dead_bookmarks:
        bookmarks.remove(d)

    record_list_viewer.main("{} - User Bookmarks - {}".format(__title__, user_name.title()), bookmarks)


def main_menu():
    choices = ["Quick\n   Search   ", "Detailed\n   Search   ", "   New   \nRecord", "My\n     List     "]
    msg = """- Welcome to OpenArchive -
    
Database File: {}
Archive Location: {}""".format(database_io.DATABASE_LOCATION, database_io.ARCHIVE_LOCATION_ROOT)
    while True:
        choice = easygui.buttonbox(msg, __title__, choices, )
        if choice is None:
            break
        elif choice == choices[0]:
            quick_search()
        elif choice == choices[1]:
            detailed_search()
        elif choice == choices[2]:
            launch_upload_agent()
        elif choice == choices[3]:
            access_users_list()
        else:
            pass


if __name__ == "__main__":
    main_menu()
    database_io.clear_cache()
    database_io.conn.close()
else:
    pass
