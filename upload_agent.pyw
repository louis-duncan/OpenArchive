import easygui
import os
import im2pdf_fix.im2pdf
import database_io
import temp
from PIL import Image
import textwrap
import message_window

__title__ = "OpenArchive - Upload Agent"
__author__ = "Louis Thurman"

temp_thumb_file = ".\\bin\\no_thumb.jpg"


def choose_record_type():
    types = database_io.return_types()
    return easygui.choicebox("Choose type for this record:", __title__ + " - Choose Type", types)


def choose_local_auth():
    local_authorities = database_io.return_local_authorities()
    return easygui.choicebox("Choose local authority for this record:",
                             __title__ + " - Choose Local Authority",
                             local_authorities)


def format_description(record_desc, left_margin=0):
    pads = ["Description:", "¯¯¯¯¯¯¯¯¯¯¯¯", "            "]

    new_lines = []
    paragraphs = record_desc.split("\n")
    for p in paragraphs:
        paragraph_lines = textwrap.wrap(p, 50, expand_tabs=True)
        for pl in paragraph_lines:
            new_lines.append(pl)

    if len(new_lines) < 2:
        for i in range(2 - len(new_lines)):
            new_lines.append("")

    formatted_desc = ""
    for i, l in enumerate(new_lines):
        line = left_margin * " "
        try:
            line += pads[i]
        except IndexError:
            line += pads[-1]
        line += " " + l
        formatted_desc += line + "\n"
    formatted_desc.strip("\n")
    return formatted_desc


def format_record_for_display(record):
    display_text = """          * = required fields.
          
      Title*: {title}
      ¯¯¯¯¯¯¯
{desc}
       Type*: {record_type}
       ¯¯¯¯¯¯
  Local Auth: {auth}
  ¯¯¯¯¯¯¯¯¯¯¯

  Start Date: {start_date}      End Date: {end_date}
  ¯¯¯¯¯¯¯¯¯¯¯ {gap1}      ¯¯¯¯¯¯¯¯¯

Physical Ref: {phys_ref}      Other Ref: {oth_ref}
¯¯¯¯¯¯¯¯¯¯¯¯¯ {gap2}      ¯¯¯¯¯¯¯¯¯¯
        Tags: {tags}
        ¯¯¯¯¯
Linked File(s) (click thumbnail to open):""".format(title=record.title,
                                                    desc=format_description(record.description, 1),
                                                    record_type=record.record_type,
                                                    auth=record.local_auth,
                                                    start_date=record.start_date_string(),
                                                    end_date=record.end_date_string(),
                                                    gap1=len(record.start_date_string()) * " ",
                                                    phys_ref=record.physical_index,
                                                    oth_ref=record.other_ref,
                                                    gap2=len(record.physical_index) * " ",
                                                    tags=record.string_tags()
                                                    )
    return display_text


def manage_attachments(record):
    add_new_prompt = "Link new file..."
    files = []
    for f in record.linked_files:
        files.append(f)
    files.append("")
    files.append(add_new_prompt)
    easygui.choicebox("Choose file for more options:",
                      __title__ + " - Manage Attachments",
                      files)



def fill_new_record(f):
    new_record = database_io.ArchiveRecord(linked_files=[f])
    choices = ["Add\nInformation",
               "Edit\nDescription",
               "Select\nRecord Type",
               "Select Local\nAuthority",
               "Manage\nAttachment(s)",
               "Upload to\nArchive",
               " Cancel "
               ]
    while True:  # Stay in loop until form has been either filled or cancelled.
        # Generate Thumbnail for files
        thumb_files = []
        for f in new_record.linked_files:
            if database_io.get_thumbnail(f) is not None:
                pass
            else:
                file_type = f.split(".")[-1].upper()
                if file_type in ("JPG",
                                 "JPEG",
                                 "BMP",
                                 "PNG",  # If file is image, create thumbnail.
                                 ):
                    fd, thumb_file = temp.mkstemp(suffix=".jpg", dir=os.environ["TEMP"])
                    os.close(fd)
                    im = Image.open(f)
                    im.thumbnail((300, 150), Image.ANTIALIAS)
                    im.save(thumb_file, "JPEG")
                    im.close()
                    thumb_files.append(thumb_file)
                else:  # Else, use place holder.
                    thumb_files.append(temp_thumb_file)

        choice = easygui.buttonbox(format_record_for_display(new_record),
                                   __title__ + " - New Record",
                                   choices,
                                   images=thumb_files
                                   )
        if choice is None or "Cancel" in choice:
            break
        elif choice == choices[0]:
            edit_msg = "* = required"
            fields = ["\n\nTitle*:\n\n",
                      "Start Date:",
                      "End Date:",
                      "\n\nTags:\n\n",
                      "Physical Index:",
                      "Other Reference:"]
            values = [new_record.title,
                      new_record.start_date_string(),
                      new_record.end_date_string(),
                      new_record.string_tags(),
                      new_record.physical_index,
                      new_record.other_ref]
            new_info = easygui.multenterbox(edit_msg,
                                            __title__ + " - Edit Record",
                                            fields,
                                            values
                                            )
            if new_info is None:
                pass
            else:
                new_record.title = new_info[0]
                new_record.start_date_string(new_info[1])
                new_record.end_date_string(new_info[2])
                new_record.string_tags(new_info[3])
                new_record.physical_index = new_info[4]
                new_record.other_ref = new_info[5]
        elif choice == choices[1]:
            # noinspection PyNoneFunctionAssignment
            new_desc = easygui.textbox("Enter description for new item below:",
                                       __title__ + " - Edit Record: Description",
                                       new_record.description)
            if new_desc is None:
                pass
            else:
                check = database_io.check_text_is_valid(new_desc)
                if check == True:
                    new_record.description = new_desc
                else:
                    # easygui.msgbox(new_desc + str(database_io.check_text_is_valid(new_desc)))
                    error_msg = "Invalid character(s) used:\n" + (26 * "¯") + "\n"
                    bad_chars = ""
                    for c in check:
                        bad_chars += c + ", "
                    error_msg += bad_chars.strip(", ")
                    easygui.msgbox(error_msg, __title__ + " - Error")
        elif choice == choices[2]:
            new_type = choose_record_type()
            if new_type is None:
                pass
            else:
                new_record.record_type = new_type
        elif choice == choices[3]:
            new_local_auth = choose_local_auth()
            if new_local_auth is None:
                pass
            else:
                new_record.local_auth = new_local_auth
        elif choice == choices[4]:
            manage_attachments(new_record)
        elif choice == choices[5]:
            return new_record
        elif choice not in choices:
            new_record.launch_file(thumb_files.index(choice))
        else:
            pass
    return None


def upload_single_file(part=False):
    # todo Write single upload
    # Select file
    file_path = easygui.fileopenbox("",
                                    __title__ + " - File Upload",
                                    default=os.path.join(os.environ["userprofile"], "*"))
    if file_path is None:
        pass
    else:
        # Get Info
        record_info = fill_new_record(file_path)
        if record_info is None:
            pass
        else:
            pass
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
    choices = ["  Single  \nFile", "Multiple\nFiles", "Multiple Files to\nSingle Document"]
    if __name__ == "__main__":
        pass
    else:
        choices.append("Cancel")
    explanation_msg = """Upload Agent:
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
        choice = easygui.buttonbox(explanation_msg, __title__, choices)
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
