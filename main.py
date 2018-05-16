import os
import datetime
import easygui
import datebase_io
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
    pass
    # todo: Write quick search


def detailed_search():
    pass
    # todo: Write detailed search


def upload_agent():
    pass
    # Launch upload agent


def access_user_list():
    pass
    # Write access to users list


def main_menu():
    run = True
    choices = ("Quick\nSearch", "Detailed\nSearch", "Upload\nFiles", "My List")
    msg = """- Welcome to OpenArchive -
Database File: {}
Archive Location: {}""".format(datebase_io.DATABASE_LOCATION, datebase_io.DATA_LOCATION)
    while run:
        choice = easygui.buttonbox()
        if choice is None:
            break
        elif choice == choices[0]:
            quick_search()
        elif choice == choices[1]:
            detailed_search()
        elif choice == choices[2]:
            upload_agent()
        elif choice == choices[3]:
            access_user_list()


if __name__ == "__main__":
    main_menu()
else:
    pass
