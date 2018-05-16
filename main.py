import os
import datetime
import easygui
import database_io
import upload_agent
import im2pdf_fix.im2pdf as im2pdf

__title__ = "OpenArchive"
__author__ = "Louis Thurman"


def join_files():
    files = easygui.fileopenbox("Select Files To Combine",
                                __title__ + " - Combine to PDF",
                                os.path.join(os.environ["HOMEPATH"], "*.jpg"),
                                [".jpg", ".pdf"],
                                True)
    if files is None:
        pass
    else:
        output_path = easygui.filesavebox("Choose Save Location",
                                          __title__ + " - Combine to PDF",
                                          os.path.join(os.environ["HOMEPATH"], "*.pdf"),
                                          [".pdf"])
        if output_path is None:
            pass
        else:
            if output_path.endswith(".pdf"):
                pass
            else:
                output_path += ".pdf"
            err = im2pdf.union(files, output_path)
            if err:
                easygui.msgbox('The PDF could not be created!',
                               __title__ + " - Error")
            else:
                pass


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


def access_user_list():
    pass
    # Write access to users list


def main_menu():
    choices = ["Quick\n   Search   ", "Detailed\n   Search   ", "   Upload   \nFiles", "My\n     List     "]
    msg = """- Welcome to OpenArchive -
    
Database File: {}
Archive Location: {}""".format(database_io.DATABASE_LOCATION, database_io.DATA_LOCATION)
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
            access_user_list()
        else:
            pass


if __name__ == "__main__":
    main_menu()
else:
    pass
