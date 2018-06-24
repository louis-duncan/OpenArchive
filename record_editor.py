import datetime
import sqlite3
import time
import webbrowser

import wx
import wx.adv
from wx.lib import sized_controls
from wx.lib.pdfviewer import pdfViewer
import os
import subprocess

import coord
import database_io
import textdistance
import PIL
import PIL.Image
import PIL.ImageFile
from PyPDF2 import PdfFileWriter, PdfFileReader
import temp

import kml_load

MAP_MODE="GOOGLE EARTH"

PIL.ImageFile.LOAD_TRUNCATED_IMAGES = True

no_preview_thumb = os.path.abspath(".\\bin\\img\\no_preview.jpg")
no_locate_thumb = os.path.abspath(".\\bin\\img\\no_locate.jpg")
no_file_thumb = os.path.abspath(".\\bin\\img\\no_file.jpg")
__title__ = "OpenArchive - Record Viewer"


class FileLinkPopupMenu(wx.Menu):
    def __init__(self, parent, file_path=""):
        self.parent = parent
        wx.Menu.__init__(self)

        self.file_path = file_path

        item = wx.MenuItem(self, wx.NewId(), "Show in archived location...")
        self.Append(item)
        self.Bind(wx.EVT_MENU, self.on_archive_open, item)

        item = wx.MenuItem(self, wx.NewId(), "Create merge request")
        self.Append(item)
        self.Bind(wx.EVT_MENU, self.on_create_merge, item)

    def on_archive_open(self, event):
        try:
            if os.path.exists(self.file_path):
                pass
            else:
                raise FileNotFoundError
            subprocess.Popen(r'explorer /select,"{}"'.format(os.path.abspath(self.file_path)))
        except FileNotFoundError:
            dlg = wx.MessageDialog(self.parent, "Could Not Load File!\n"
                                                "\n"
                                                "The files could not be found at location:\n"
                                                "{}".format(self.file_path),
                                   "OpenArchive - File Error")
            dlg.ShowModal()
            dlg.Destroy()

    def on_create_merge(self, event):
        pass
        # Todo: Add merge request creation.
        dlg = wx.MessageDialog(self.parent, "Inactive Feature!\n"
                                            "\n"
                                            "Merge requests are not currently in operation.\n"
                                            "Please contact your database admin.",
                               __title__)
        dlg.ShowModal()
        dlg.Destroy()


class LoadingDialog(wx.lib.sized_controls.SizedDialog):
    def __init__(self, parent, text="", *args, **kwargs):
        super(LoadingDialog, self).__init__(parent=parent,
                                            title=text,
                                            style=wx.STAY_ON_TOP | wx.CAPTION, *args, **kwargs)
        pane = self.GetContentsPane()

        self.loading_bar = wx.Gauge(pane, -1, 75, (110, 95), (250, -1))

        self.Fit()

        self.loading_bar.Pulse()


class RecordEditor(wx.Frame):
    def __init__(self, parent, title, record_to_edit: database_io.ArchiveRecord):
        # print(record_to_edit)
        wx.Frame.__init__(self, parent, title=title, size=(900, 500),
                          style=wx.DEFAULT_FRAME_STYLE ^ wx.RESIZE_BORDER ^ wx.MAXIMIZE_BOX)

        self.record = record_to_edit
        self.cache_dir = temp.mkdtemp(dir=database_io.TEMP_DATA_LOCATION)

        # Add bg panel
        bg_panel = wx.Panel(self, size=(2000, 2000))

        column_one = wx.GridBagSizer(vgap=10, hgap=10)

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
        type_lbl = wx.StaticText(bg_panel, label="Resource Type:")
        column_one.Add(type_lbl, (4, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        types = database_io.return_types()
        types.sort(key=database_io.float_none_drop_other)
        types.append("Add New...")
        self.type_comb = wx.ComboBox(bg_panel, size=(350, -1), choices=types, value=str(self.record.record_type),
                                     style=wx.CB_DROPDOWN | wx.CB_READONLY)
        column_one.Add(self.type_comb, pos=(4, 2), span=(1, 4))

        # Add Local Authority Selection
        local_authorities_lbl = wx.StaticText(bg_panel, label="Source/Local Authority:")
        column_one.Add(local_authorities_lbl, (5, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        local_authorities = database_io.return_local_authorities()
        local_authorities.sort(key=database_io.float_none_drop_other)
        local_authorities.append("Add New...")
        self.local_authorities_comb = wx.ComboBox(bg_panel, size=(350, -1), choices=local_authorities,
                                                  value=str(self.record.local_auth),
                                                  style=wx.CB_DROPDOWN | wx.CB_READONLY)
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
        self.start_date_picker.SetToolTip(wx.ToolTip("Earliest relevant date."))
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
        self.end_date_picker.SetToolTip(wx.ToolTip("Latest relevant date."))
        column_one.Add(self.end_date_picker, pos=(6, 5))

        # Add Physical and Other Refs
        physical_ref_lbl = wx.StaticText(bg_panel, label="Physical Ref:")
        column_one.Add(physical_ref_lbl, (7, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        self.physical_ref_box = wx.TextCtrl(bg_panel, size=(120, -1))
        if self.record.physical_ref is not None:
            self.physical_ref_box.SetValue(self.record.physical_ref)
        self.physical_ref_box.SetToolTip(wx.ToolTip("Reference or Serial Number for physical copy."))
        column_one.Add(self.physical_ref_box, (7, 2))

        other_ref_lbl = wx.StaticText(bg_panel, label="Other Ref:")
        column_one.Add(other_ref_lbl, (7, 4), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        self.other_ref_box = wx.TextCtrl(bg_panel, size=(120, -1))
        if self.record.other_ref is not None:
            self.other_ref_box.SetValue(self.record.other_ref)
        self.other_ref_box.SetToolTip(wx.ToolTip("Any other reference or serial number."))
        column_one.Add(self.other_ref_box, (7, 5))

        # Add Tags Box
        tags_lbl = wx.StaticText(bg_panel, label="Tags:")
        column_one.Add(tags_lbl, (8, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        self.tags_box = wx.SearchCtrl(bg_panel, size=(350, -1))
        self.tags_box.ShowSearchButton(False)
        self.tags_box.SetDescriptiveText('Enter tags comma separated. (eg. tag1, tag2,...)')
        column_one.Add(self.tags_box, pos=(8, 2), span=(1, 4))

        # Lon/Lat Boxes
        lon_lat_lbl = wx.StaticText(bg_panel, label="Longitude/Latitude:")
        column_one.Add(lon_lat_lbl, (9, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        self.lon_lat_box = wx.SearchCtrl(bg_panel, size=(220, -1))
        self.lon_lat_box.ShowSearchButton(False)
        self.lon_lat_box.SetDescriptiveText('Enter longitude/latitude...')
        coord_msg = """Lon/Lat can be formatted as either:
Lon, Lat (eg. -3.14159, 26.53589), or
Degrees, Minutes, Seconds (eg. 03°08'29.72"W 26°32'09.20"N)"""
        lon_lat_tool_tip = wx.ToolTip(coord_msg)
        lon_lat_tool_tip.SetDelay(1000)
        lon_lat_tool_tip.SetAutoPop(20000)
        self.lon_lat_box.SetToolTip(lon_lat_tool_tip)
        column_one.Add(self.lon_lat_box, pos=(9, 2), span=(1, 3))

        # Pin view button
        self.lon_lat_view_button = wx.Button(bg_panel, size=(120, 23), label="View in Google Earth")
        column_one.Add(self.lon_lat_view_button, pos=(9, 5))

        # New Column!
        column_two = wx.GridBagSizer(vgap=10, hgap=10)
        file_list_lbl = wx.StaticText(bg_panel, label="Linked Files (Single click to Preview, Double click to open):")
        column_two.Add(file_list_lbl, (1, 1))
        self.temp_file_links = []
        self.display_file_list = []
        if not self.record.linked_files:
            pass
        else:
            for f in self.record.linked_files:
                self.temp_file_links.append(f)
                self.display_file_list.append(format_path_to_title(os.path.basename(f)))
        self.file_list_box = wx.ListBox(bg_panel, size=(320, 120), choices=self.display_file_list,
                                        style=wx.LB_HSCROLL)
        column_two.Add(self.file_list_box, (2, 1))

        # File Buttons
        file_buttons_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.upload_single_button = wx.Button(bg_panel, size=(100, -1), label="Upload\nSingle File(s)")
        self.upload_single_button.SetToolTip(wx.ToolTip("Links one or many files to the record as individual entries."))
        file_buttons_sizer.Add(self.upload_single_button)
        file_buttons_sizer.Add((0, 0), wx.EXPAND)
        self.upload_multiple_button = wx.Button(bg_panel, size=(100, -1), label="Upload Many\nAs One PDF")
        self.upload_multiple_button.SetToolTip(wx.ToolTip("Merges multiple image files into a single PDF file\n"
                                                          "then links it to the record as a single entry."))
        file_buttons_sizer.Add(self.upload_multiple_button)
        file_buttons_sizer.Add((0, 0), wx.EXPAND)
        self.remove_file_button = wx.Button(bg_panel, size=(100, -1), label="Unlink\nFile")
        self.remove_file_button.Disable()
        file_buttons_sizer.Add(self.remove_file_button)

        column_two.Add(file_buttons_sizer, (3, 1), flag=wx.EXPAND)

        column_two.Add((0, 0), (4, 1), flag=wx.EXPAND)

        # Add Save and Close Buttons
        main_buttons_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.save_button = wx.Button(bg_panel, size=(100, 35), label="Save Changes", name="Save Changes to Record")
        self.save_button.Disable()
        main_buttons_sizer.Add(self.save_button)

        main_buttons_sizer.Add((0, 0), wx.EXPAND)

        self.bookmark_button = wx.Button(bg_panel, size=(100, 35), label="Add To My List")
        main_buttons_sizer.Add(self.bookmark_button)

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
        self.previewer = pdfViewer(bg_panel, wx.NewId(), wx.DefaultPosition, (348, 348),
                                   style=wx.HSCROLL | wx.VSCROLL | wx.BORDER_SIMPLE)  # | wx.SUNKEN_BORDER)
        self.previewer.ShowLoadProgress = True
        column_three.Add(self.previewer, (2, 1), flag=wx.EXPAND)

        # Previewed file name.
        self.previewer_file_name_lbl = wx.StaticText(bg_panel,
                                                     label="#################################################",
                                                     style=wx.ALIGN_RIGHT | wx.ST_ELLIPSIZE_MIDDLE)
        self.previewer_file_name_lbl.SetLabel("")
        column_three.Add(self.previewer_file_name_lbl, (3, 1))

        # Add a spacer to the sizer
        column_three.Add((15, 20), pos=(3, 2))

        # Normal View
        normal_sizer = wx.BoxSizer(wx.HORIZONTAL)
        normal_sizer.Add(column_one, 0, wx.EXPAND, 0)
        normal_sizer.Add(column_two, 0, wx.EXPAND, 0)
        normal_sizer.Add(column_three, 0, wx.EXPAND, 0)

        # Expanded Preview
        # expanded_preview_sizer = wx.GridBagSizer(10, 10)
        # expanded_preview_sizer.Add(column_one, (0, 0))
        # expanded_preview_sizer.Add(column_two, (1, 0))
        # expanded_preview_sizer.Add(column_three, (0, 1), span=(2, 1))

        self.SetSizerAndFit(normal_sizer)

        self.create_binds()

        self.Show(True)

        self.unsaved_changes = False
        self.refresh_all()

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
        self.Bind(wx.EVT_TEXT, self.update_location, self.lon_lat_box)

        # Location View Button Bind
        self.Bind(wx.EVT_BUTTON, self.open_location_pinpoint, self.lon_lat_view_button)

        # File Link Box
        self.Bind(wx.EVT_LISTBOX, self.file_link_selected, self.file_list_box)
        self.Bind(wx.EVT_LISTBOX_DCLICK, self.file_link_double_clicked, self.file_list_box)

        # File Management Buttons
        self.Bind(wx.EVT_BUTTON, self.link_new_file, self.upload_single_button)
        self.Bind(wx.EVT_BUTTON, self.merge_and_link_multiple_files, self.upload_multiple_button)
        self.Bind(wx.EVT_BUTTON, self.unlink_file, self.remove_file_button)

        # Save Button > Save Record
        self.Bind(wx.EVT_BUTTON, self.save_record, self.save_button)

        # My List button.
        self.Bind(wx.EVT_BUTTON, self.bookmark_button_press, self.bookmark_button)

        # Left Clicks
        self.file_list_box.Bind(wx.EVT_LEFT_DOWN, self.on_left_click)

        # Right Clicks
        self.file_list_box.Bind(wx.EVT_RIGHT_DOWN, self.on_right_click)

        # Close Button > Close Frame
        self.Bind(wx.EVT_BUTTON, self.close_button_press, self.close_button)
        self.Bind(wx.EVT_CLOSE, self.close_button_press)

    def on_left_click(self, event):
        pos = event.GetPosition()
        left_clicked_item = self.file_list_box.HitTest(pos)
        if left_clicked_item == -1:
            pass
        else:
            self.file_list_box.SetSelection(left_clicked_item)
            self.file_link_selected()

    def on_right_click(self, event):
        pos = event.GetPosition()
        right_clicked_item = self.file_list_box.HitTest(pos)
        if right_clicked_item == -1:
            return None
        else:
            # Show context menu.
            pass
        self.file_list_box.SetSelection(right_clicked_item)
        self.file_link_selected()
        print("Hit", right_clicked_item)
        menu = FileLinkPopupMenu(self, self.temp_file_links[right_clicked_item])
        self.file_list_box.PopupMenu(menu, pos)
        menu.Destroy()

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
                if (input_dlg.ShowModal() == wx.ID_OK) and (input_dlg.GetValue().strip() != ""):
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
                msg = "Enter new Source/Local Authority:"
                input_dlg = wx.TextEntryDialog(self, msg, __title__ + " - New Source")
                input_dlg.SetValue(new_local_auth)
                if (input_dlg.ShowModal() == wx.ID_OK) and (input_dlg.GetValue().strip() != ""):
                    new_local_auth = input_dlg.GetValue().strip()
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
                error_dlg = wx.MessageDialog(self, "A Source or Local Authority of this name already exists!",
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

    def update_location(self, event):
        self.set_changed()

    def open_location_pinpoint(self, event):
        if self.lon_lat_box.GetValue().strip() == "":
            return None
        assert coord.validate(self.lon_lat_box.GetValue().strip()) is True
        if MAP_MODE.upper() == "GOOGLE EARTH":
            lon, lat = coord.normalise(self.lon_lat_box.GetValue().strip())
            kml_load.create_kml_point(self.title_box.GetValue().strip(),
                                      self.desc_box.GetValue().strip(),
                                      lon,
                                      lat,
                                      self.cache_dir)
        else:
            lon, lat = coord.normalise(self.lon_lat_box.GetValue().strip())
            url = "https://www.google.com/maps/?q={},{}".format(lat, lon)
            webbrowser.open_new_tab(url)

    def unlink_file(self, event):
        explanation_msg = "Files linked to records in OpenArchive can be stored in two kinds of locations. " \
                          "Dependant on the linked file's location, it will be treated differently when unlinked:\n" \
                          "\n" \
                          "1. The directory managed by OpenArchive:\n" \
                          "In this case, the file will be relocated to the desktop to prevent data loss before being " \
                          "purged from the archive.\n" \
                          "\n" \
                          "2. Other predefined, non-managed, locations:\n" \
                          "OpenArchive allows for the configuration of directories from which it will not copy files " \
                          "when they are linked. This is to prevent duplication of pre-existing archives. When " \
                          "unlinking a file stored in one of these locations it will not be moved or delwted when " \
                          "unlinked.\n" \
                          "\n" \
                          "If you are unsure as to the location of a file which you are unlinking, and you wish to" \
                          " know; select No from this dialog, right-click the file in question, and select " \
                          "\'Show in archived location....\'"

        # Drop out if no file is selected.
        selection = self.file_list_box.GetSelection()

        if selection == -1:
            return None
        else:
            pass
        file_to_remove = self.temp_file_links[self.file_list_box.GetSelection()]
        print(str(self.file_list_box.GetSelection()))
        print(str(file_to_remove))
        # Get all links to the file.
        links = database_io.get_files_links(file_to_remove)
        if (len(links) == 1) and links[0].record_id != self.record.record_id:
            # This allows the process to continue is there is only one link, but that link is from a different record.
            # This shouldn't happen, but might occur if multiple people happen to be accessing the same record.
            pass
        elif (len(links) <= 1) and database_io.is_file_in_root(file_to_remove, database_io.ARCHIVE_LOCATION_SUB):
            #  Raise message, and if continued, create copy, unlink, and remove from repo
            dlg = wx.RichMessageDialog(self, "Are you sure you want to unlink this file?\n"
                                             "\n"
                                             "This is the only record which links to this file in the archive.\n"
                                             "If you choose to to unlink the file, it will be copied to your desktop\n"
                                             "to prevent it being lost.",
                                       style=wx.YES_NO | wx.ICON_EXCLAMATION | wx.NO_DEFAULT)
            dlg.ShowDetailedText(explanation_msg)
            resp = dlg.ShowModal()
            if resp == wx.ID_NO:
                print("Pressed No")
                return None
            else:
                pass
        elif ((len(links) <= 1) and database_io.check_if_in_archive(file_to_remove)) \
                and not database_io.is_file_in_root(database_io.ARCHIVE_LOCATION_SUB, file_to_remove):
            #  Raise message, and if continued, create copy, unlink, and remove from repo
            dlg = wx.RichMessageDialog(self, "Are you sure you want to unlink this file?\n"
                                             "\n"
                                             "This is the only record which links to this file in the archive.\n"
                                             "This file is located in a directory not managed by OpenArchive.\n"
                                             "Please ensure you are satisfied that you know the location of the file\n"
                                             "for future reference. See below for details.",
                                       style=wx.YES_NO | wx.ICON_EXCLAMATION | wx.NO_DEFAULT)
            dlg.ShowDetailedText(explanation_msg)
            resp = dlg.ShowModal()
            if resp == wx.ID_NO:
                print("Pressed No")
                return None
            else:
                pass
        elif os.path.basename(file_to_remove).startswith("OA_PDF_Merge_"):
            # Raise msg about removing staged file
            dlg = wx.MessageDialog(self, "Are you sure you want to unlink this file?\n"
                                         "\n"
                                         "This is a merged file. If you choose to unlink it you will need to\n"
                                         "repeat the merging process if you decide to re-link.",
                                   style=wx.YES_NO | wx.ICON_INFORMATION | wx.NO_DEFAULT)
            resp = dlg.ShowModal()
            if resp == wx.ID_NO:
                print("Pressed No")
                return None
            else:
                pass
        else:
            pass

        # remove link.
        print("Removing {}!".format(file_to_remove))
        self.previewer.LoadFile(no_file_thumb)
        self.previewer_file_name_lbl.SetLabel("")
        if database_io.is_file_in_root(file_to_remove, self.cache_dir):
            print("Deleting {} for Temp Location.".format(file_to_remove))
            try:
                os.remove(file_to_remove)
            except FileNotFoundError:
                print("Already Gone!")
        self.temp_file_links.remove(file_to_remove)
        self.file_list_box.Delete(self.file_list_box.GetSelection())
        self.set_changed()

    def bookmark_button_press(self, event: wx.EVT_BUTTON):
        assert str(self.record.record_id) not in ("New Record", "0")
        if event.GetEventObject().Label == "Add To My List":
            database_io.add_bookmark(os.environ["USERNAME"], self.record.record_id)
        else:
            database_io.remove_bookmark(os.environ["USERNAME"], self.record.record_id)
        self.refresh_all()

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
        self.Destroy()

        self.previewer.LoadFile(no_file_thumb)
        # Purge any files held in the cache for this record.
        for f in os.listdir(self.cache_dir):
            os.remove(os.path.join(self.cache_dir, f))
        os.rmdir(self.cache_dir)

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

        # Lon/Lat Box
        input_lon_lat_valid = coord.validate(self.lon_lat_box.GetValue())
        input_lon_lat_empty = self.lon_lat_box.GetValue().strip() == ""
        if input_lon_lat_valid:
            input_lon, input_lat = coord.normalise(self.lon_lat_box.GetValue())
            if (input_lon != self.record.longitude) or (input_lat != self.record.latitude):
                self.unsaved_changes = True
                print("Lon/Lat Changed")
            else:
                pass
        elif input_lon_lat_empty and (None not in (self.record.longitude, self.record.latitude)):
            self.unsaved_changes = True
            print("Lon/Lat Changed")
        else:
            pass

        # Files
        if len(self.temp_file_links) != len(self.record.linked_files):
            self.unsaved_changes = True
            print("Files Changed - Len")
        else:
            for f in self.temp_file_links:
                if f not in self.record.linked_files:
                    self.unsaved_changes = True
                    print("Files changed - Different File")
                    break

        if self.unsaved_changes:
            self.save_button.Enable()
        else:
            self.save_button.Disable()

        # Update buttons
        # Unlink button
        self.remove_file_button.Disable()
        if len(self.temp_file_links) > 0:
            self.remove_file_button.Enable()
        else:
            pass

        # Lon/Lat View button
        if coord.validate(self.lon_lat_box.GetValue().strip()) is True:
            self.lon_lat_view_button.Enable()
            if MAP_MODE.upper() == "GOOGLE EARTH":
                self.lon_lat_view_button.SetLabel("View in Google Earth")
            else:
                self.lon_lat_view_button.SetLabel("View in Google Maps")
        else:
            self.lon_lat_view_button.Disable()
            self.lon_lat_view_button.SetLabel("Invalid Location")

    def file_link_selected(self, event=None):
        path = self.temp_file_links[self.file_list_box.GetSelection()]
        self.previewer_file_name_lbl.SetLabel(path)
        if os.path.exists(path):
            file_extension = path.split(".")[-1].upper()
            if file_extension in ("PDF", "JPG", "JPEG", "BMP", "PNG"):
                try:
                    self.previewer.LoadFile(path)
                except RuntimeError:
                    print("Tried to load a bad file type!")
                    self.previewer.LoadFile(no_preview_thumb)
            else:
                self.previewer.LoadFile(no_preview_thumb)
        else:
            self.previewer.LoadFile(no_locate_thumb)
        self.remove_file_button.Enable()

    def file_link_double_clicked(self, event):
        dlg = LoadingDialog(self, "Loading...")
        dlg.Show(True)
        suc = self.record.launch_file(file_path=self.temp_file_links[self.file_list_box.GetSelection()],
                                      cache_dir=self.cache_dir)
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
        # Blank the previewer, otherwise file become locked out due to it keeping the open.

        self.previewer.LoadFile(no_file_thumb)

        if (self.record.record_id == "New Record") or (self.record.record_id == 0):
            pass
        else:
            dlg = wx.MessageDialog(self, "Are you sure you want to save changes?\n"
                                         "\n"
                                         "Saving will permanently update the record with the newly entered data.\n"
                                         "Linked files will be uploaded, and unlinked files will be purged.",
                                   "Confirm Save",
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

        if self.lon_lat_box.GetValue().strip() == "":
            lon = lat = None
        elif coord.validate(self.lon_lat_box.GetValue()):
            lon, lat = coord.normalise(self.lon_lat_box.GetValue())
        else:
            dlg = wx.MessageDialog(self, "Invalid location will not be saved.\n"
                                         "\n"
                                         "The location which has been entered is invalid, and so will not be saved."
                                         "Do you wish to continue?",
                                   "Confirm Invalid Location",
                                   style=wx.YES_NO | wx.ICON_EXCLAMATION | wx.NO_DEFAULT)
            resp = dlg.ShowModal()
            dlg.Destroy()
            if resp == wx.ID_YES:
                pass
            else:
                return False
            lon, lat = self.record.longitude, self.record.latitude

        new_record_obj = database_io.ArchiveRecord(record_id=self.record.record_id,
                                                   title=self.title_box.GetValue().strip(),
                                                   description=self.desc_box.GetValue().strip(),
                                                   record_type=self.type_comb.GetValue(),
                                                   local_auth=self.local_authorities_comb.GetValue(),
                                                   start_date=new_start_date,
                                                   end_date=new_end_date,
                                                   physical_ref=self.physical_ref_box.GetValue().strip(),
                                                   other_ref=self.other_ref_box.GetValue().strip(),
                                                   longitude=lon,
                                                   latitude=lat,
                                                   linked_files=self.temp_file_links,
                                                   created_by=self.record.created_by,
                                                   created_time=self.record.created_time
                                                   )
        new_record_obj.string_tags(self.tags_box.GetValue())

        valid = database_io.check_record(new_record_obj)
        if valid is True:
            saving_dlg = LoadingDialog(self, "Saving...")
            saving_dlg.Show(True)
            suc = database_io.commit_record(record_obj=new_record_obj)
            self.previewer.LoadFile(no_file_thumb)
            if type(suc) == database_io.ArchiveRecord:
                self.record = suc
                self.refresh_all()
                saving_dlg.Show(False)
                saving_dlg.Destroy()
                return None
            else:
                error_msg = "Record not added due to:\n\n{}!\nConcerning...".format(suc)
            dlg = wx.MessageDialog(self, error_msg, style=wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
            saving_dlg.Show(False)
            saving_dlg.Destroy()
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
        previous_selected_file = self.file_list_box.GetSelection()
        self.temp_file_links = []
        display_files = []
        for f in self.record.linked_files:
            self.temp_file_links.append(f)
            display_files.append(format_path_to_title(os.path.basename(f)))
        self.file_list_box.Set(display_files)
        if len(display_files) > 0:
            if previous_selected_file == wx.NOT_FOUND:
                print("No file selected")
                self.file_list_box.SetSelection(0)
            else:
                self.file_list_box.SetSelection(previous_selected_file)
            self.file_link_selected()
        else:
            pass
        self.created_text.Label = "Created by:\n{} - {}".format(str(self.record.created_by),
                                                                str(self.record.created_time_string()))
        self.changed_text.Label = "Last Changed:\n{} - {}".format(str(self.record.last_changed_by),
                                                                  str(self.record.last_changed_time_string()))

        self.bookmark_button.Label = "Add To My List"
        self.bookmark_button.Enable()
        if self.record.record_id in ("New Record", "0", 0):
            self.bookmark_button.Disable()

        else:
            if self.record.record_id in database_io.get_user_bookmarks():
                self.bookmark_button.Label = "Remove From\nMy List"
            else:
                pass

        # Lon/Lat Box
        if coord.validate(self.lon_lat_box.GetValue()):
            self.record.longitude, self.record.latitude = coord.normalise(self.lon_lat_box.GetValue())
            self.lon_lat_box.ChangeValue("{}, {}".format(self.record.longitude,
                                                         self.record.latitude))
        else:
            if coord.validate("{},{}".format(self.record.longitude, self.record.latitude)):
                self.lon_lat_box.ChangeValue("{}, {}".format(self.record.longitude, self.record.latitude))
            else:
                self.lon_lat_box.ChangeValue("")

        self.set_changed()

    def link_new_file(self, event=None, new_file_path=None):
        """Links single file to the record."""

        assert type(new_file_path) in (str, tuple, list, type(None))

        # Select the file
        if new_file_path is None:
            file_open_dlg = wx.FileDialog(self, __title__ + " - Select File To Link",
                                          style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST | wx.FD_MULTIPLE)
            resp = file_open_dlg.ShowModal()
            if resp == wx.ID_CANCEL:
                return None
            else:
                new_file_path = file_open_dlg.GetPaths()
        else:
            pass

        if type(new_file_path) == str:
            print("String Path")
            # Copy it to the cache
            if database_io.is_file_in_archive(new_file_path):
                pass
            else:
                new_file_path = database_io.move_file_to_cache(new_file_path, self.cache_dir)
            # Add the cached dir to the temp dir list
            self.temp_file_links.append(new_file_path)
            self.file_list_box.Append(format_path_to_title(os.path.basename(new_file_path)))
            self.file_list_box.SetSelection(len(self.temp_file_links) - 1)
            self.file_link_selected()
            self.set_changed()
        elif type(new_file_path) in (tuple, list):
            print("List/Tuple Path")
            for f in new_file_path:
                self.link_new_file(new_file_path=f)
        else:
            return None

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
        new_file_name = "OA_PDF_Merge_{}{}{}{}{}{}.pdf".format(str(t.year)[2:4],
                                                               str(t.month).zfill(2),
                                                               str(t.day).zfill(2),
                                                               str(t.hour).zfill(2),
                                                               str(t.minute).zfill(2),
                                                               str(t.second).zfill(2)
                                                               )
        new_file_path = os.path.join(self.cache_dir, new_file_name)
        loading_dlg = wx.ProgressDialog("Merge Files", "Merging files...", len(file_paths))
        loading_dlg.ShowModal()
        suc = True
        message = ""
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
                    # Copy the file locally, this makes sure that the file is formatted correctly for the PDF save.
                    im = PIL.Image.open(input_file)
                    fd, local_image_file = temp.mkstemp(prefix="OATMP", suffix=".jpg", dir=self.cache_dir)
                    os.close(fd)
                    im.save(local_image_file, 'JPEG', resolution=100.0)
                    im.close()

                    # Now save it to PDF and delete the temp image.
                    im = PIL.Image.open(local_image_file)
                    fd, input_file_pdf = temp.mkstemp(prefix="OATMP", suffix=".pdf", dir=self.cache_dir)
                    os.close(fd)
                    im.save(input_file_pdf, 'PDF', resolution=100.0)
                    os.remove(local_image_file)

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
            outputStream.close()

        except Exception as ex:
            suc = False
            template = "An exception of type {0} occurred. Arguments:\n{1!r}"
            message = template.format(type(ex).__name__, ex.args)
            print(message)

        loading_dlg.Destroy()

        if suc is False:
            dlg = wx.MessageDialog(self, "Could not merge the files!\n\n{}".format(message), "Error")
            dlg.ShowModal()
            dlg.Destroy()
        else:
            self.link_new_file(new_file_path=new_file_path)


def format_path_to_title(path):
    n, e = path.rsplit(".", 1)
    return "({}) {}".format(e.upper(), n)


def main(record_obj, title=__title__):
    app = wx.App(False)
    frame = RecordEditor(None, title, record_obj)
    app.MainLoop()


if __name__ == "__main__":
    r = database_io.ArchiveRecord()
    r.record_id = "New Record"
    # r = database_io.get_record_by_id(82)
    main(r)
    database_io.clear_cache()
