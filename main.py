import os
import datetime
import easygui
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
    # Launch upload agent
    upload_agent.main_menu()


def access_users_list():
    pass
    # Write access to users list


def main_menu():
    choices = ["Quick\n   Search   ", "Detailed\n   Search   ", "   Upload   \nFiles", "My\n     List     ", "test"]
    msg = """- Welcome to OpenArchive -
    
Database File: {}
Archive Location: {}""".format(database_io.DATABASE_LOCATION, database_io.ARCHIVE_LOCATION)
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
        elif choice == choices[4]:
            #r = database_io.get_record_by_id(66)
            r = database_io.ArchiveRecord()
            r.record_id = "New Record"
            record_editor.main(r)
        else:
            pass


if __name__ == "__main__":
    main_menu()
    database_io.clear_cache()
else:
    pass
