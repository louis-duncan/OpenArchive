#!/usr/bin/env python
# coding: UTF-8

__description__ = 'Tool to convert images to pdf and unite them.'
__author__ = '@tkmru'
__version__ = '0.1'
__date__ = '2014/12/29'
__minimum_python_version__ = (2, 7, 6)
__maximum_python_version__ = (3, 4, 2)
__copyright__ = 'Copyright (c) @tkmru'
__license__ = 'MIT License'

import PIL
import PIL.Image
from PyPDF2 import PdfFileWriter, PdfFileReader
import os
import argparse
#from progressist import ProgressBar
import easygui
import temp

verbose = False


def convert(input_file, output_file):
    im = PIL.Image.open(input_file)
    im.save(output_file, 'PDF', resoultion = 100.0)
    if verbose:
        print('completed.')
        print(input_file + ' --> ' + output_file)


def union(input_files, output_file, progress_bar=False):

    try:
        output = PdfFileWriter()
        part_files_handles = [] # [fh, created=True/False]

        for input_file in input_files:
            if input_file.endswith('.pdf'):
                fh = open(input_file, 'rb')
                part_files_handles.append([fh, False])
                input = PdfFileReader(fh)
                num_pages = input.getNumPages()

                for i in range(0, num_pages):
                    output.addPage(input.getPage(i))

            else: # input_file isn't pdf ex. jpeg, png
                im = PIL.Image.open(input_file)
                fd, input_file_pdf = temp.mkstemp(dir=os.environ["TEMP"])
                os.close(fd)
                im.save(input_file_pdf, 'PDF', resoultion=100.0)

                fh = open(input_file_pdf, 'rb')
                part_files_handles.append([fh, True])
                input = PdfFileReader(fh)
                num_pages = input.getNumPages()

                for i in range(0, num_pages):
                    output.addPage(input.getPage(i))

        with open(output_file, 'wb') as outputStream:
            output.write(outputStream)

        for f in part_files_handles:
            part_path = f[0].name
            f[0].close() # Close each file.
            if f[1]:
                os.remove(part_path) # If 'created' flag is True, remove file a it was created in this process.

        if verbose:
            print('completed.')
            print('Union of some file is ' + output_file)
        else:
            return 0
    except:
        easygui.exceptionbox()
        return 1


if __name__ == '__main__':
    verbose = True