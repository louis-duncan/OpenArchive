import os
import datetime
import easygui
import datebase_io
import im2pdf_fix.im2pdf as im2pdf

__title__ = "OpenArchive"
__author__ = "Louis Thurman"


def main_menu():
    run = True
    choices = ("Add ")
    while run:
        choice = easygui.buttonbox()


def join_files():
    files = easygui.fileopenbox("Select Files To Combine",
                                __title__ + " - Combine to PDF",
                                os.path.join(os.environ["HOMEPATH"],"*.jpg"),
                                [".jpg", ".pdf"],
                                True)
    if files is None:
        pass
    else:
        output_path = easygui.filesavebox("Choose Save Location",
                                          __title__ + " - Combine to PDF",
                                          os.path.join(os.environ["HOMEPATH"],"*.pdf"),
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


join_files()