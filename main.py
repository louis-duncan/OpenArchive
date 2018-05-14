import os
import datetime
import easygui
import datebase_io
import im2pdf_fix.im2pdf as im2pdf

__title__ = "OpenArchive"
__author__ = "Louis Thurman"


def main_menu():
    run = True
    choices = ()
    while run:
        choice = easygui.buttonbox()

