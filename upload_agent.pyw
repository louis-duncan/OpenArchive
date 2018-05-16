import easygui
import os
import im2pdf_fix.im2pdf
import database_io
import temp
from PIL import Image
import message_window

__title__ = "OpenArchive - Upload Agent"
__author__ = "Louis Thurman"


def fill_new_record(file_path):

    choices = ["Add/Edit\nInformation", "Set Record\nType", "Set Local\nAuthority", "\nUpload!\n", "Cancel"]

    edit_msg = "* = required"
    fields = ["Title:",
              "Description:",
              "Start Date:",
              "End Date:",
              "Physical Ref:",
              "Other Ref:",
              "Tags:"
              ]
    info = ["*",
            "",
            "DD/MM/YY",
            "DD/MM/YY",
            "",
            "",
            "tag1, tag2, etc"
            ]
    while True:
        # Generate Thumbnail from selected image
        file_type = file_path.split(".")[-1].upper()
        if file_type in ("JPG",
                         "JPEG",
                         "BMP",
                         "PNG",
                         ):
            fd, thumb_file = temp.mkstemp(suffix=".jpg", dir=os.environ["TEMP"])
            os.close(fd)
            im = Image.open(file_path)
            im.thumbnail((800, 200), Image.ANTIALIAS)
            im.save(thumb_file, "JPEG")
            im.close()
        else:
            thumb_file = ".\\bin\\no_thumb.jpg"

        view_msg = ""

        choice = easygui.buttonbox(view_msg, __title__ + " - New Record", choices, thumb_file)
        if choice is None or choice == "Cancel":
            break
        elif choice == [0]:
            info = easygui.multenterbox(edit_msg,
                                        __title__ + " - Edit Record",
                                        fields,
                                        info
                                        )
        # Todo: finish adding choices.
        elif choice not in choices:
            os.startfile(file_path)
        else:
            pass


def upload_single_file(part=False):
    # todo Write single upload
    # Select file
    file_path = easygui.fileopenbox("",
                                    __title__ + " - File Upload",
                                    default=os.path.join(os.environ["userprofile"], "*"))

    # Get Info
    record_info = fill_new_record(file_path)
    # Add to archive
    # add thumbnail to archive
    # Add to DB
    # add thumbnail to db
    # Offer deletion on completion
    pass


def upload_batch():
    # todo: Write batch upload
    # Get file list
    # Offer deletion on completion
    # then perform single upload for each file.
    pass


def merge_and_upload():
    # Get files
    # Offer deletion on completion
    # get info
    # merge
    # add to archive
    # ass to db
    pass


def main_menu():
    choices = ["Single\nFile", "Multiple\nFiles", "Multiple Files to\nSingles Document"]
    if __name__ == "__main__":
        pass
    else:
        choices.append("Cancel")
    msg = """Upload Agent:
¯¯¯¯¯¯¯¯¯¯¯¯¯
Single File:
- Upload a single file to the archive.

Multiple Files:
- Upload multiple single files to the archive.
  Enter information about each file individually.

Multiple Files as Single Document:
- Upload multiple image or PDF files as a single PDF document.
  This will auto-combine the files and then allow information to be added."""

    while True:
        choice = easygui.buttonbox(msg, __title__, choices)
        if choice is None or choice == "Cancel":
            break
        elif choice == choices[0]:
            upload_single_file()
        elif choice == choices[1]:
            upload_batch()
        elif choice == choices[2]:
            merge_and_upload()
        else:
            pass


if __name__ == '__main__':
    main_menu()
