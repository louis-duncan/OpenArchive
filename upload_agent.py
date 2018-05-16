import easygui
import os
import im2pdf_fix.im2pdf
import database_io

__title__ = "OpenArchive - Upload Agent"
__author__ = "Louis Thurman"


def upload_single_file():
    # todo Write single upload
    # Select file
    # Offer deletion on completion
    # Get info
    # Add to archive
    # Add to DB
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
