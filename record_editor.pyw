import datetime
import sqlite3
import time
import wx
import wx.adv
from wx.lib import sized_controls
from wx.lib.pdfviewer import pdfViewer
import os
import database_io
import textdistance

import PIL
import PIL.Image
from PyPDF2 import PdfFileWriter, PdfFileReader
import temp

no_preview_file = ".\\bin\\no_thumb.jpg"
no_locate_file = ".\\bin\\no_locate.jpg"
__title__ = "OpenArchive - Record Viewer"


class RecordEditor(wx.Frame):
    def __init__(self, parent, title, record_to_edit: database_io.ArchiveRecord):

        wx.Frame.__init__(self, parent, title=title, size=(900, 500),
                          style=wx.DEFAULT_FRAME_STYLE ^ wx.RESIZE_BORDER ^ wx.MAXIMIZE_BOX)

        self.record = record_to_edit

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        column_one = wx.GridBagSizer(vgap=10, hgap=10)

        # Add bg panel
        bg_panel = wx.Panel(self, size=(1500, 500))

        # Add Record ID
        id_lbl = wx.StaticText(bg_panel, label="Record ID:")
        column_one.Add(id_lbl, pos=(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        self.record_id_text = wx.StaticText(bg_panel, label=str(self.record.record_id), size=(100, -1))
        column_one.Add(self.record_id_text, pos=(1, 2))

        # Add Adjustable Title
        title_lbl = wx.StaticText(bg_panel, label="Title*:")
        column_one.Add(title_lbl, (2, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        self.title_box = wx.TextCtrl(bg_panel, value=str(self.record.title), size=(350, -1))
        column_one.Add(self.title_box, pos=(2, 2), span=(1, 4))

        # Add Adjustable Description
        desc_lbl = wx.StaticText(bg_panel, label="Description*:")
        column_one.Add(desc_lbl, (3, 1), flag=wx.ALIGN_TOP | wx.ALIGN_RIGHT)
        self.desc_box = wx.TextCtrl(bg_panel, value=str(self.record.description), size=(350, 117),
                                    style=wx.TE_MULTILINE)
        column_one.Add(self.desc_box, pos=(3, 2), span=(1, 4))

        # Add Type Selection
        type_lbl = wx.StaticText(bg_panel, label="Resource Type*:")
        column_one.Add(type_lbl, (4, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        types = database_io.return_types()
        types.sort(key=database_io.float_none_drop_other)
        types.append("Add New...")
        self.type_comb = wx.ComboBox(bg_panel, size=(350, -1), choices=types, value=str(self.record.record_type),
                                     style=wx.CB_DROPDOWN | wx.CB_READONLY)
        column_one.Add(self.type_comb, pos=(4, 2), span=(1, 4))

        # Add Local Authority Selection
        local_authorities_lbl = wx.StaticText(bg_panel, label="Local Authority*:")
        column_one.Add(local_authorities_lbl, (5, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        local_authorities = database_io.return_local_authorities()
        local_authorities.sort(key=database_io.float_none_drop_other)
        local_authorities.append("Add New...")
        self.local_authorities_comb = wx.ComboBox(bg_panel, size=(350, -1), choices=local_authorities,
                                                  value=str(self.record.local_auth),
                                                  style=wx.CB_DROPDOWN | wx.CB_READONLY,
                                                  name="Click to choose Local Authority")
        column_one.Add(self.local_authorities_comb, pos=(5, 2), span=(1, 4))

        # Add date selectors
        start_date_lbl = wx.StaticText(bg_panel, label="Start Date:")
        column_one.Add(start_date_lbl, (6, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        self.start_date_picker = wx.adv.DatePickerCtrl(bg_panel, size=(120, -1), style=wx.adv.DP_DROPDOWN
                                                                                       | wx.adv.DP_SHOWCENTURY
                                                                                       | wx.adv.DP_ALLOWNONE)
        if self.record.start_date is not None:
            start_dt = wx.DateTime(self.record.start_date.day,
                                   self.record.start_date.month - 1,  # Because for some reason the months start at 0.
                                   self.record.start_date.year)
            self.start_date_picker.SetValue(start_dt)
        column_one.Add(self.start_date_picker, pos=(6, 2))

        column_one.Add((27, -1), pos=(6, 3))  # Gap

        end_date_lbl = wx.StaticText(bg_panel, label="End Date:")
        column_one.Add(end_date_lbl, (6, 4), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        self.end_date_picker = wx.adv.DatePickerCtrl(bg_panel, size=(120, -1), style=wx.adv.DP_DROPDOWN
                                                                                     | wx.adv.DP_SHOWCENTURY
                                                                                     | wx.adv.DP_ALLOWNONE)
        if self.record.end_date is not None:
            end_dt = wx.DateTime(self.record.end_date.day,
                                 self.record.end_date.month - 1,  # Because for some reason the months start at 0.
                                 self.record.end_date.year)
            self.end_date_picker.SetValue(end_dt)
        column_one.Add(self.end_date_picker, pos=(6, 5))

        # Add Physical and Other Refs
        physical_ref_lbl = wx.StaticText(bg_panel, label="Physical Ref:")
        column_one.Add(physical_ref_lbl, (7, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        self.physical_ref_box = wx.TextCtrl(bg_panel, size=(120, -1))
        if self.record.physical_ref is not None:
            self.physical_ref_box.SetValue(self.record.physical_ref)
        column_one.Add(self.physical_ref_box, (7, 2))

        other_ref_lbl = wx.StaticText(bg_panel, label="Other Ref:")
        column_one.Add(other_ref_lbl, (7, 4), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        self.other_ref_box = wx.TextCtrl(bg_panel, size=(120, -1))
        if self.record.other_ref is not None:
            self.other_ref_box.SetValue(self.record.other_ref)
        column_one.Add(self.other_ref_box, (7, 5))

        # Add Tags Box
        tags_lbl = wx.StaticText(bg_panel, label="Tags:")
        column_one.Add(tags_lbl, (8, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        self.tags_box = wx.TextCtrl(bg_panel, value=str(self.record.string_tags()), size=(350, -1))
        column_one.Add(self.tags_box, pos=(8, 2), span=(1, 4))

        # New Column!
        column_two = wx.GridBagSizer(vgap=10, hgap=10)
        file_list_lbl = wx.StaticText(bg_panel, label="Linked Files (Single click to Preview, Double click to open):")
        column_two.Add(file_list_lbl, (1, 1))
        self.temp_files = []
        self.display_file_list = []
        if not self.record.linked_files:
            pass
        else:
            for f in self.record.linked_files:
                self.temp_files.append(f)
                self.display_file_list.append(format_path_to_title(os.path.basename(f)))
        self.file_list_box = wx.ListBox(bg_panel, size=(320, 120), choices=self.display_file_list,
                                        style=wx.LB_HSCROLL)
        column_two.Add(self.file_list_box, (2, 1))

        # File Buttons
        file_buttons_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.upload_single_button = wx.Button(bg_panel, size=(100, -1), label="Upload\nSingle File")
        file_buttons_sizer.Add(self.upload_single_button)
        file_buttons_sizer.Add((0, 0), wx.EXPAND)
        self.upload_multiple_button = wx.Button(bg_panel, size=(100, -1), label="Merge to PDF\nand Upload")
        file_buttons_sizer.Add(self.upload_multiple_button)
        file_buttons_sizer.Add((0, 0), wx.EXPAND)
        self.remove_file_button = wx.Button(bg_panel, size=(100, -1), label="Unlink\nFile")
        file_buttons_sizer.Add(self.remove_file_button)

        column_two.Add(file_buttons_sizer, (3, 1), flag=wx.EXPAND)

        column_two.Add((0, 0), (4, 1), flag=wx.EXPAND)

        # Add Save and Close Buttons
        main_buttons_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.save_button = wx.Button(bg_panel, size=(100, 35), label="Save Changes", name="Save Changes to Record")
        self.save_button.Disable()
        main_buttons_sizer.Add(self.save_button)

        main_buttons_sizer.Add((0, 0), wx.EXPAND)

        self.add_to_list_button = wx.Button(bg_panel, size=(100, 35), label="Add To My List")
        main_buttons_sizer.Add(self.add_to_list_button)

        main_buttons_sizer.Add((0, 0), wx.EXPAND)

        self.close_button = wx.Button(bg_panel, size=(100, 35), label="Close")
        main_buttons_sizer.Add(self.close_button)

        column_two.Add(main_buttons_sizer, (5, 1), flag=wx.EXPAND)

        # Add created and changed info
        self.created_text = wx.StaticText(bg_panel, label="Created by:\n{} - {}"
                                          .format(str(self.record.created_by), str(self.record.created_time_string())))

        column_two.Add((0, 0), (6, 1), flag=wx.EXPAND)

        column_two.Add(self.created_text, (7, 1))

        self.changed_text = wx.StaticText(bg_panel, label="Last Changed:\n{} - {}"
                                          .format(str(self.record.last_changed_by),
                                                  str(self.record.last_changed_time_string())))
        column_two.Add(self.changed_text, (8, 1))

        # New Column!
        column_three = wx.GridBagSizer(vgap=10, hgap=10)

        # Previewer
        previewer_lbl = wx.StaticText(bg_panel, label="Preview:")
        column_three.Add(previewer_lbl, (1, 1))
        self.previewer = pdfViewer(bg_panel, wx.NewId(), wx.DefaultPosition, (315, 315),
                                   style=wx.HSCROLL | wx.VSCROLL | wx.SUNKEN_BORDER)
        column_three.Add(self.previewer, (2, 1))

        # Previewed file name.
        self.previewer_file_name_lbl = wx.StaticText(bg_panel, label="#############################################",
                                                     style=wx.ALIGN_RIGHT | wx.ST_ELLIPSIZE_MIDDLE)
        self.previewer_file_name_lbl.SetLabel("")
        column_three.Add(self.previewer_file_name_lbl, (3, 1))

        # Add a spacer to the sizer
        column_three.Add((15, 20), pos=(3, 2))

        sizer.Add(column_one, 0, wx.EXPAND, 0)
        sizer.Add(column_two, 0, wx.EXPAND, 0)
        sizer.Add(column_three, 0, wx.EXPAND, 0)

        self.SetSizerAndFit(sizer)

        self.create_binds()

        self.Show(True)

        self.unsaved_changes = False

    def create_binds(self):
        # Bind Data Entry
        self.Bind(wx.EVT_TEXT, self.update_title, self.title_box)
        self.Bind(wx.EVT_TEXT, self.update_description, self.desc_box)
        self.Bind(wx.EVT_COMBOBOX, self.update_type, self.type_comb)
        self.Bind(wx.EVT_COMBOBOX, self.update_local_auth, self.local_authorities_comb)
        self.Bind(wx.adv.EVT_DATE_CHANGED, self.update_start_date, self.start_date_picker)
        self.Bind(wx.adv.EVT_DATE_CHANGED, self.update_end_date, self.end_date_picker)
        self.Bind(wx.EVT_TEXT, self.update_physical_ref, self.physical_ref_box)
        self.Bind(wx.EVT_TEXT, self.update_other_ref, self.other_ref_box)
        self.Bind(wx.EVT_TEXT, self.update_tags, self.tags_box)

        # File Link Box
        self.Bind(wx.EVT_LISTBOX, self.file_link_selected, self.file_list_box)
        self.Bind(wx.EVT_LISTBOX_DCLICK, self.file_link_double_clicked, self.file_list_box)

        # File Management Buttons
        self.Bind(wx.EVT_BUTTON, self.link_new_file, self.upload_single_button)
        self.Bind(wx.EVT_BUTTON, self.merge_and_link_multiple_files, self.upload_multiple_button)

        # Save Button > Save Record
        self.Bind(wx.EVT_BUTTON, self.save_record, self.save_button)

        # Close Button > Close Frame
        self.Bind(wx.EVT_BUTTON, self.close_button_press, self.close_button)

    def update_title(self, event):
        self.set_changed()

    def update_description(self, event):
        self.set_changed()

    def update_type(self, event):
        selection = self.type_comb.GetStringSelection()
        if selection == "Add New...":
            valid = False
            new_type = ""
            while valid is not True:
                # Get new type.
                msg = "Enter new resource type:\n" \
                      "'Type: Sub-Type'"
                input_dlg = wx.TextEntryDialog(self, msg, __title__ + " - New Type")
                input_dlg.SetValue(new_type)
                if input_dlg.ShowModal() == wx.ID_OK:
                    new_type = input_dlg.GetValue()
                else:
                    # I no new type given, quit here.
                    self.type_comb.SetSelection(0)
                    input_dlg.Destroy()
                    return None
                input_dlg.Destroy()
                valid = database_io.check_text_is_valid(new_type)
                if valid is True:
                    pass
                else:
                    pass
                    error_dlg = wx.MessageDialog(self, "Entry contains invalid characters!\nDisallowed Characters:\n{}"
                                                 .format(database_io.invalid_chars),
                                                 "Error", style=wx.ICON_ERROR)
                    error_dlg.ShowModal()
                    error_dlg.Destroy()
            # Add to database.
            try:
                database_io.add_new_type(new_type)
            except sqlite3.IntegrityError:
                error_dlg = wx.MessageDialog(self, "A type of this name already exists!",
                                             "Error", style=wx.ICON_ERROR)
                error_dlg.ShowModal()
                error_dlg.Destroy()
                self.type_comb.SetSelection(0)
                return None
            # Add to list.
            self.type_comb.Append(new_type)
            # Set as current selected value.
            self.type_comb.SetSelection(self.type_comb.FindString(new_type))
        else:
            pass
        self.set_changed()

    def update_local_auth(self, event):
        selection = self.local_authorities_comb.GetStringSelection()
        if selection == "Add New...":
            valid = False
            new_local_auth = ""
            while valid is not True:
                # Get new type.
                msg = "Enter new local authority:"
                input_dlg = wx.TextEntryDialog(self, msg, __title__ + " - New Local Authority")
                input_dlg.SetValue(new_local_auth)
                if input_dlg.ShowModal() == wx.ID_OK:
                    new_local_auth = input_dlg.GetValue()
                else:
                    # I no new auth given, quit here.
                    self.local_authorities_comb.SetSelection(0)
                    input_dlg.Destroy()
                    return None
                input_dlg.Destroy()
                valid = database_io.check_text_is_valid(new_local_auth)
                if valid is True:
                    pass
                else:
                    error_dlg = wx.MessageDialog(self, "Entry contains invalid characters!\nDisallowed Characters:\n{}"
                                                 .format(database_io.invalid_chars),
                                                 "Error", style=wx.ICON_ERROR)
                    error_dlg.ShowModal()
                    error_dlg.Destroy()
            # Add to database.
            try:
                database_io.add_new_local_authority(new_local_auth)
            except sqlite3.IntegrityError:
                error_dlg = wx.MessageDialog(self, "A local authority of this name already exists!",
                                             "Error", style=wx.ICON_ERROR)
                error_dlg.ShowModal()
                error_dlg.Destroy()
                self.local_authorities_comb.SetSelection(0)
                return None
            # Add to list.
            self.local_authorities_comb.Append(new_local_auth)
            # Set as current selected value.
            self.local_authorities_comb.SetSelection(self.local_authorities_comb.FindString(new_local_auth))
        else:
            pass
        self.set_changed()

    def update_start_date(self, event):
        self.set_changed()

    def update_end_date(self, event):
        self.set_changed()

    def update_physical_ref(self, event):
        self.set_changed()

    def update_other_ref(self, event):
        self.set_changed()

    def update_tags(self, event):
        if textdistance.levenshtein(self.tags_box.GetValue(), self.record.tags_prompt) == 1:
            if len(self.tags_box.GetValue()) < len(self.record.tags_prompt):
                self.tags_box.ChangeValue("")
            else:
                if self.tags_box.GetValue().startswith(self.record.tags_prompt):
                    self.tags_box.ChangeValue(self.tags_box.GetValue()[len(self.record.tags_prompt):])
                else:
                    pass
        else:
            pass
        self.set_changed()

    # Todo: Add File Removing

    # Todo: Add adding My List.

    def close_button_press(self, event):
        if self.unsaved_changes:
            dlg = wx.MessageDialog(self, "Do you want to save changes to record: {}\n"
                                         "\n"
                                         "If not saved, any changes including newly linked "
                                         "files will not be stored in the archive."
                                   .format(self.record.record_id, self.record.title),
                                   style=wx.YES_NO | wx.CANCEL | wx.CANCEL_DEFAULT
                                         | wx.ICON_INFORMATION, caption="Unsaved Changes")
            resp = dlg.ShowModal()
            dlg.Destroy()
            if resp == wx.ID_YES:
                # process for saving record
                save_completed = self.save_record()
                if save_completed:
                    pass
                else:
                    return None
            elif resp == wx.ID_NO:
                pass
            else:
                return None
        else:
            pass
        self.Close()

    def set_changed(self, event=None):
        self.unsaved_changes = False
        if self.title_box.GetValue().strip() != self.record.title:
            self.unsaved_changes = True
            print("Title Changed")
        if self.desc_box.GetValue().strip() != self.record.description:
            self.unsaved_changes = True
            print("Description Changed")
        if self.type_comb.GetValue() != str(self.record.record_type):
            self.unsaved_changes = True
            print("Type Changed")
        if self.local_authorities_comb.GetValue() != str(self.record.local_auth):
            self.unsaved_changes = True
            print("Auth Changed")

        # Check Dates
        if self.record.start_date is None:
            test_start_date = None
        else:
            test_start_date = wx.DateTime(self.record.start_date.day,
                                          self.record.start_date.month - 1,
                                          self.record.start_date.year)
        if str(self.start_date_picker.GetValue()) == "INVALID DateTime":
            field_start_date = None
        else:
            field_start_date = self.start_date_picker.GetValue()
        if field_start_date != test_start_date:
            self.unsaved_changes = True
            print("Start Date Changed")

        if self.record.end_date is None:
            test_end_date = None
        else:
            test_end_date = wx.DateTime(self.record.end_date.day,
                                        self.record.end_date.month - 1,
                                        self.record.end_date.year)
        if str(self.end_date_picker.GetValue()) == "INVALID DateTime":
            field_end_date = None
        else:
            field_end_date = self.end_date_picker.GetValue()
        if field_end_date != test_end_date:
            self.unsaved_changes = True
            print("End Date Changed")

        # Ref boxes
        if self.physical_ref_box.GetValue().strip() != self.record.physical_ref:
            self.unsaved_changes = True
            print("Physical Ref Changed")
        if self.other_ref_box.GetValue().strip() != self.record.other_ref:
            self.unsaved_changes = True
            print("Other Ref Changed")

        # Tags
        check_tags = self.record.format_string_to_tags(self.tags_box.GetValue().strip())
        if len(check_tags) != len(self.record.tags):
            self.unsaved_changes = True
            print("Tags Changed - Len\n", check_tags, self.record.tags, "\n", len(check_tags), len(self.record.tags))
        else:
            for t in check_tags:
                if t.upper().strip() not in self.record.tags:
                    self.unsaved_changes = True
                    print("Tags Changed -", t.upper().strip(), str(self.record.tags))
                    break

        # Files
        if len(self.temp_files) != len(self.record.linked_files):
            self.unsaved_changes = True
            print("Files Changed - Len")
        else:
            for f in self.temp_files:
                if f not in self.record.linked_files:
                    self.unsaved_changes = True
                    print("Files changed - Different File")
                    break

        if self.unsaved_changes:
            self.save_button.Enable()
        else:
            self.save_button.Disable()

    def file_link_selected(self, event=None):
        path = self.temp_files[self.file_list_box.GetSelection()]
        self.previewer_file_name_lbl.SetLabel(path)
        if os.path.exists(path):
            file_extension = path.split(".")[-1].upper()
            if file_extension in ("PDF", "JPG", "JPEG", "BMP", "PNG"):
                try:
                    self.previewer.LoadFile(path)
                except RuntimeError:
                    print("Tried to load a bad file type!")
                    self.previewer.LoadFile(no_preview_file)
            else:
                self.previewer.LoadFile(no_preview_file)
        else:
            self.previewer.LoadFile(no_locate_file)

    def file_link_double_clicked(self, event):
        dlg = LoadingDialog(self)
        dlg.Show(True)
        suc = self.record.launch_file(file_path=self.temp_files[self.file_list_box.GetSelection()])
        if suc is True:
            dlg.Destroy()
            return None
        elif suc == "Index Error":
            msg = "File '{}' does not appear to be linked to this record!" \
                .format(self.record.linked_files[self.file_list_box.GetSelection()])
        elif suc == "Path Error":
            msg = "File '{}' does not appear to exist!" \
                .format(self.record.linked_files[self.file_list_box.GetSelection()])
        else:
            msg = "File '{}' could not be opened for an unknown reason, which is worrying..." \
                .format(self.record.linked_files[self.file_list_box.GetSelection()])
        dlg.Destroy()
        dlg = wx.MessageDialog(self, msg, "File Error", wx.OK)
        dlg.ShowModal()
        dlg.Destroy()

    def save_record(self, event=None):
        if (self.record.record_id == "New Record") or (self.record.record_id == 0):
            pass
        else:
            dlg = wx.MessageDialog(self, "Are you sure you want to save changes?\n\nSaving will permanently update "
                                         "the record with the newly entered data.", "Confirm Save",
                                   style=wx.YES_NO | wx.ICON_EXCLAMATION | wx.NO_DEFAULT)
            resp = dlg.ShowModal()
            dlg.Destroy()
            if resp == wx.ID_YES:
                pass
            else:
                return False

        if str(self.start_date_picker.GetValue()) == "INVALID DateTime":
            new_start_date = None
        else:
            new_start_date = datetime.datetime(self.start_date_picker.GetValue().year,
                                               self.start_date_picker.GetValue().month + 1,
                                               self.start_date_picker.GetValue().day)
        if str(self.end_date_picker.GetValue()) == "INVALID DateTime":
            new_end_date = None
        else:
            new_end_date = datetime.datetime(self.end_date_picker.GetValue().year,
                                             self.end_date_picker.GetValue().month + 1,
                                             self.end_date_picker.GetValue().day)

        new_record_obj = database_io.ArchiveRecord(record_id=self.record.record_id,
                                                   title=self.title_box.GetValue().strip(),
                                                   description=self.desc_box.GetValue().strip(),
                                                   record_type=self.type_comb.GetValue(),
                                                   local_auth=self.local_authorities_comb.GetValue(),
                                                   start_date=new_start_date,
                                                   end_date=new_end_date,
                                                   physical_ref=self.physical_ref_box.GetValue().strip(),
                                                   other_ref=self.other_ref_box.GetValue().strip(),
                                                   linked_files=self.temp_files,
                                                   created_by=self.record.created_by,
                                                   created_time=self.record.created_time
                                                   )
        new_record_obj.string_tags(self.tags_box.GetValue())

        valid = database_io.check_record(new_record_obj)
        if valid is True:
            suc = database_io.commit_record(record_obj=new_record_obj)
            if type(suc) == database_io.ArchiveRecord:
                self.record = suc
                self.refresh_all()
                return None
            else:
                error_msg = "Record not added due to:\n\n{}!\nConcerning...".format(suc)
            dlg = wx.MessageDialog(self, error_msg, style=wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
        elif valid == "Bad Chars":
            dlg = wx.MessageDialog(self, "Record contains invalid characters!\n\nDisallowed Characters:\n{}"
                                   .format(database_io.invalid_chars),
                                   "Error", style=wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
        else:
            dlg = wx.MessageDialog(self, "Record is missing required fields!\n\nFields marked with an * must be filled",
                                   "Error", style=wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
        return True

    def refresh_all(self):
        if self.record.title is None:
            self.record.title = ""
        if self.record.description is None:
            self.record.description = ""
        self.record_id_text.Label = str(self.record.record_id)
        self.title_box.ChangeValue(str(self.record.title))
        self.desc_box.ChangeValue(str(self.record.description))
        self.physical_ref_box.ChangeValue(str(self.record.physical_ref))
        self.other_ref_box.ChangeValue(str(self.record.other_ref))
        self.tags_box.ChangeValue(self.record.string_tags())
        self.temp_files = []
        display_files = []
        for f in self.record.linked_files:
            self.temp_files.append(f)
            display_files.append(format_path_to_title(os.path.basename(f)))
        self.file_list_box.Set(display_files)
        self.created_text.Label = "Created by:\n{} - {}".format(str(self.record.created_by),
                                                                str(self.record.created_time_string()))
        self.changed_text.Label = "Last Changed:\n{} - {}".format(str(self.record.last_changed_by),
                                                                  str(self.record.last_changed_time_string()))
        self.set_changed()

        print("Linked Files:", self.record.linked_files)
        print("Temp File:", self.temp_files)

    def link_new_file(self, event=None, new_file_path=None):
        """Links single file to the record."""
        # Select the file
        if new_file_path is None:
            file_open_dlg = wx.FileDialog(self, __title__ + " - Select File To Link",
                                          style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)
            resp = file_open_dlg.ShowModal()
            if resp == wx.ID_CANCEL:
                return None
            else:
                new_file_path = file_open_dlg.GetPath()
        else:
            pass
        # Copy it to the cache
        if new_file_path.startswith(database_io.TEMP_DATA_LOCATION):
            pass
        else:
            new_file_path = database_io.move_file_to_cache(new_file_path)
        # Add the cached dir to the temp dir list
        self.temp_files.append(new_file_path)
        self.file_list_box.Append(format_path_to_title(os.path.basename(new_file_path)))
        self.file_list_box.SetSelection(len(self.temp_files) - 1)
        self.file_link_selected()
        self.set_changed()

    def merge_and_link_multiple_files(self, event):
        # Select the files
        file_open_dlg = wx.FileDialog(self, __title__ + " - Select File To Link",
                                      wildcard="Image files (*.jpg;*.jpeg,*.bmp)|*.jpg;*.jpeg;*.bmp|"
                                               "PDF files (*.pdf)|*.pdf|"
                                               "All files (*.*)|*.*",
                                      style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST | wx.FD_MULTIPLE)
        resp = file_open_dlg.ShowModal()
        if resp == wx.ID_CANCEL:
            return None
        else:
            file_paths = file_open_dlg.GetPaths()

        # If only one file was selected, skip, and link it as a single file.
        if len(file_paths) == 1:
            self.link_new_file(new_file_path=file_paths[0])
            return None
        else:
            pass

        # Get a name for the new file.
        t = datetime.datetime.fromtimestamp(time.time())
        new_file_name = "PDF Merge {}{}{}{}{}{}.pdf".format(str(t.year)[2:4],
                                                            str(t.month).zfill(2),
                                                            str(t.day).zfill(2),
                                                            str(t.hour).zfill(2),
                                                            str(t.minute).zfill(2),
                                                            str(t.second).zfill(2)
                                                            )
        new_file_path = os.path.join(database_io.TEMP_DATA_LOCATION, new_file_name)

        loading_dlg = wx.ProgressDialog("Merge Files", "Merging files...", len(file_paths))
        loading_dlg.ShowModal()

        try:
            output = PdfFileWriter()
            part_files_handles = []  # [fh, created=True/False]

            for progress, input_file in enumerate(file_paths):
                if input_file.endswith('.pdf'):
                    fh = open(input_file, 'rb')
                    part_files_handles.append([fh, False])
                    input = PdfFileReader(fh)
                    num_pages = input.getNumPages()

                    for i in range(0, num_pages):
                        output.addPage(input.getPage(i))

                else:  # input_file isn't pdf ex. jpeg, png
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
                loading_dlg.Update(progress + 1)

            with open(new_file_path, 'wb') as outputStream:
                output.write(outputStream)

            for f in part_files_handles:
                part_path = f[0].name
                f[0].close()  # Close each file.
                if f[1]:
                    os.remove(part_path)  # If 'created' flag is True, remove file a it was created in this process.
                suc = True
        except:
            suc = False

        loading_dlg.Destroy()

        if suc is False:
            dlg = wx.MessageDialog(self, "Could not merge the files!", "Error")
            dlg.ShowModal()
            dlg.Destroy()
        else:
            self.link_new_file(new_file_path=new_file_path)


class LoadingDialog(wx.lib.sized_controls.SizedDialog):

    def __init__(self, *args, **kwargs):
        super(LoadingDialog, self).__init__(title="Loading...", style=wx.STAY_ON_TOP | wx.CAPTION, *args, **kwargs)
        pane = self.GetContentsPane()

        self.loading_bar = wx.Gauge(pane, -1, 75, (110, 95), (250, -1))

        self.Fit()

        self.loading_bar.Pulse()


def format_path_to_title(path):
    n, e = path.rsplit(".", 1)
    return "({}) {}".format(e.upper(), n)


def main(record_obj):
    app = wx.App(False)
    frame = RecordEditor(None, __title__, record_obj)
    app.MainLoop()
    database_io.clear_cache()


if __name__ == "__main__":
    r = database_io.ArchiveRecord()
    r.record_id = "New Record"
    main(r)
