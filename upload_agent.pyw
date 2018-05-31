import easygui
import os
import im2pdf_fix.im2pdf as im2pdf
import database_io
import temp
from PIL import Image
import textwrap
import pickle

__title__ = "OpenArchive - Upload Agent"
__author__ = "Louis Thurman"

no_thumb_file = ".\\bin\\no_thumb.jpg"


def join_files(file_paths=None, output_path=None):
    if file_paths is None:
        return None
    else:
        if output_path is None:
            fd, output_path = temp.mkstemp(suffix=".pdf", prefix="OATEMP", dir=database_io.TEMP_DATA_LOCATION)
            os.close(fd)
        else:
            pass
        err = im2pdf.union(file_paths, output_path)
        if err:
            easygui.msgbox('The PDF could not be created!',
                           __title__ + " - Error")
            return None
        else:
            return output_path


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
 Local Auth*: {auth}
 ¯¯¯¯¯¯¯¯¯¯¯¯

  Start Date: {start_date}      End Date: {end_date}
  ¯¯¯¯¯¯¯¯¯¯¯ {gap1}      ¯¯¯¯¯¯¯¯¯

Physical Ref: {phys_ref}         Other Ref: {oth_ref}
¯¯¯¯¯¯¯¯¯¯¯¯¯ {gap2}         ¯¯¯¯¯¯¯¯¯¯
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


def manage_attachments(file_list):
    add_new_prompt = "Link new file..."
    save_prompt = "Save Changes"
    files = []
    for f in file_list:
        files.append(f)
    thumb_files = []
    while True:
        display_list = []
        for t in thumb_files:
            name = os.path.split(t)[1]
            if name.startswith("OATEMP"):
                os.remove(t)
            else:
                pass
        thumb_files = []
        for f in files:
            display_list.append(f)
            # Thumbs
            thumb_file = database_io.get_thumbnail(file_path=f)
            if thumb_file is None:
                file_type = f.split(".")[-1].upper()
                if file_type in ("JPG",
                                 "JPEG",
                                 "BMP",
                                 "PNG",  # If file is image, create thumbnail.
                                 ):
                    fd, thumb_file = temp.mkstemp(suffix=".jpg", prefix="OATEMP", dir=database_io.TEMP_DATA_LOCATION)
                    os.close(fd)
                    im = Image.open(f)
                    im.thumbnail((500, 200), Image.ANTIALIAS)
                    im.save(thumb_file, "JPEG")
                    im.close()
                    thumb_files.append(thumb_file)
                else:  # Else, use place holder.
                    thumb_files.append(no_thumb_file)
            else:
                thumb_files.append(no_thumb_file)

        display_list.append("")
        display_list.append(add_new_prompt)
        display_list.append(save_prompt)
        choice = easygui.choicebox("Choose file for more options, press 'Cancel' to :",
                                   __title__ + " - Manage Attachments",
                                   display_list)

        if choice is None:
            return None
        elif choice == add_new_prompt:
            new_file = easygui.fileopenbox("",
                                           __title__ + " - File Upload",
                                           default=os.path.join(os.environ["userprofile"], "*"))
            if new_file is None:
                pass
            else:
                files.append(new_file)
        elif choice == save_prompt:
            return files, thumb_files
        elif choice in files:
            file_view_msg = ""
            view_choices = ["Unlink File",
                            "Keep File",
                            ]
            keep_viewing = True
            while keep_viewing:
                view_choice = easygui.buttonbox(file_view_msg,
                                                __title__ + " - View File",
                                                view_choices,
                                                thumb_files[files.index(choice)])
                if view_choice is None:
                    keep_viewing = False
                elif view_choice == view_choices[0]:
                    keep_viewing = False
                    # Todo: Add check in case file is not linked to elsewhere.
                    files.remove(choice)
                elif view_choice == view_choices[1]:
                    keep_viewing = False
                else:
                    os.startfile(choice)
        else:
            pass
    # Todo: Pick up from here


def edit_record(record_id=None, local_cached_record_path=None):
    if (record_id is None) and (local_cached_record_path is None):
        r_path = database_io.create_cached_record()
    elif record_id is not None:
        r_path = database_io.create_cached_record(record_id)
    else:
        r_path = local_cached_record_path
    record = database_io.load_cached_record(r_path)
    if record is None:
        return None
    else:
        pass
    choices = ["Add\nInformation",
               "Edit\nDescription",
               "Select\nRecord Type",
               "Select Local\nAuthority",
               "Manage\nAttachment(s)",
               "Upload to\nArchive",
               " Cancel "
               ]
    while True:  # Stay in loop until form has been either filled or cancelled.
        # noinspection PyTypeChecker
        choice = easygui.buttonbox(format_record_for_display(record),
                                   __title__ + " - " + str(record.title),
                                   choices,
                                   images=record.thumb_files
                                   )
        if choice is None or "Cancel" in choice:
            break
        elif choice == choices[0]:  # Add Information
            edit_msg = "* = required"
            fields = ["\n\nTitle*:\n\n",
                      "Start Date:",
                      "End Date:",
                      "\n\nTags:\n\n",
                      "Physical Index:",
                      "Other Reference:"]
            values = [record.title,
                      record.start_date_string(),
                      record.end_date_string(),
                      record.string_tags(),
                      record.physical_index,
                      record.other_ref]
            new_info = easygui.multenterbox(edit_msg,
                                            __title__ + " - Edit Record",
                                            fields,
                                            values
                                            )
            if new_info is None:
                pass
            else:
                record.title = new_info[0]
                record.start_date_string(new_info[1])
                record.end_date_string(new_info[2])
                record.string_tags(new_info[3])
                record.physical_index = new_info[4]
                record.other_ref = new_info[5]
        elif choice == choices[1]:  # Edit Info
            # noinspection PyNoneFunctionAssignment
            new_desc = easygui.textbox("Enter description for new item below:",
                                       __title__ + " - Edit Record: Description",
                                       record.description)
            if new_desc is None:
                pass
            else:
                check = database_io.check_text_is_valid(new_desc)
                if check == True:
                    record.description = new_desc
                else:
                    # easygui.msgbox(new_desc + str(database_io.check_text_is_valid(new_desc)))
                    error_msg = "Invalid character(s) used:\n" + (26 * "¯") + "\n"
                    bad_chars = ""
                    for c in check:
                        bad_chars += c + ", "
                    error_msg += bad_chars.strip(", ")
                    easygui.msgbox(error_msg, __title__ + " - Error")
        elif choice == choices[2]:  # Set Type
            new_type = choose_record_type()
            if new_type is None:
                pass
            else:
                record.record_type = new_type
        elif choice == choices[3]:  # Set Auth
            new_local_auth = choose_local_auth()
            if new_local_auth is None:
                pass
            else:
                record.local_auth = new_local_auth
        elif choice == choices[4]:
            new_links = manage_attachments(record.linked_files)
            if new_links is None:
                pass
            else:
                record.linked_files, record.thumb_files = new_links
        elif choice == choices[5]:
            return record
        elif choice not in choices:
            record.launch_file(record.thumb_files.index(choice))
        else:
            pass
    return None


def upload_single_file(file_path=None):
    # todo Write single upload
    # Select file
    if file_path is None:
        file_path = easygui.fileopenbox("",
                                        __title__ + " - File Select",
                                        default=os.path.join(os.environ["userprofile"], "*"))
    else:
        pass

    if file_path is None:
        pass
    else:
        # Create thumbnail file
        thumb_files = []
        file_type = file_path.split(".")[-1].upper()
        if file_type in ("JPG",
                         "JPEG",
                         "BMP",
                         "PNG",  # If file is image, create thumbnail.
                         ):
            fd, thumb_file = temp.mkstemp(suffix=".jpg", dir=database_io.TEMP_DATA_LOCATION)
            os.close(fd)
            im = Image.open(file_path)
            im.thumbnail((500, 200), Image.ANTIALIAS)
            im.save(thumb_file, "JPEG")
            im.close()
            thumb_files.append(thumb_file)
        else:  # Else, use place holder.
            thumb_files.append(no_thumb_file)
        # Get Info
        new_record = edit_record(database_io.ArchiveRecord(record_id="New Record",
                                                           linked_files=[file_path],
                                                           thumb_files=thumb_files))
        if new_record is None:
            return None
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
    files_to_merge = easygui.fileopenbox("Select Files To Combine",
                                         __title__ + " - Combine to PDF",
                                         os.path.join(os.environ["HOMEPATH"], "*.jpg"),
                                         [".jpg", ".pdf"],
                                         True)
    if files_to_merge is None:
        pass
    else:
        # Merge the files.
        merged_file = join_files()

    # Offer deletion on completion
    # get info
    # merge
    # add to archive
    # ass to db


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
