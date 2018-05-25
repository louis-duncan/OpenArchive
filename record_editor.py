import wx
import wx.adv
import os
import database_io


class RecordEditor(wx.Frame):
    def __init__(self, parent, title, record_to_edit: database_io.ArchiveRecord):

        wx.Frame.__init__(self, parent, title=title, size=(1000, 500))

        self.record = record_to_edit

        sizer = wx.BoxSizer(wx.VERTICAL)
        grid = wx.GridBagSizer(vgap=10, hgap=10)

        # Add bg panel
        bg_panel = wx.Panel(self, size=(1000, 500))

        # Add Record ID
        id_lbl = wx.StaticText(bg_panel, label="Record ID:")
        grid.Add(id_lbl, pos=(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        record_id = wx.StaticText(bg_panel, label=str(self.record.record_id))
        grid.Add(record_id, pos=(1, 2))

        # Add Adjustable Title
        title_lbl = wx.StaticText(bg_panel, label="Title*:")
        grid.Add(title_lbl, (2, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        self.title_box = wx.TextCtrl(bg_panel, value=str(self.record.title), size=(350, -1))
        grid.Add(self.title_box, pos=(2, 2), span=(1, 4))

        # Add Adjustable Description
        desc_lbl = wx.StaticText(bg_panel, label="Description*:")
        grid.Add(desc_lbl, (3, 1), flag=wx.ALIGN_TOP | wx.ALIGN_RIGHT)
        self.desc_box = wx.TextCtrl(bg_panel, value=str(self.record.description), size=(350, 140),
                                    style=wx.TE_MULTILINE)
        grid.Add(self.desc_box, pos=(3, 2), span=(2, 4))

        # Add Type Selection
        type_lbl = wx.StaticText(bg_panel, label="Resource Type*:")
        grid.Add(type_lbl, (5, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        types = database_io.return_types()
        types.sort(key=database_io.float_none_drop_other)
        types.append("Add New...")
        self.type_comb = wx.ComboBox(bg_panel, size=(350, -1), choices=types, value=self.record.record_type,
                                     style=wx.CB_DROPDOWN | wx.CB_READONLY)
        grid.Add(self.type_comb, pos=(5, 2), span=(1, 4))

        # Add Local Authority Selection
        local_authorities_lbl = wx.StaticText(bg_panel, label="Local Authority*:")
        grid.Add(local_authorities_lbl, (6, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        local_authorities = database_io.return_local_authorities()
        local_authorities.sort(key=database_io.float_none_drop_other)
        local_authorities.append("Add New...")
        self.local_authorities_comb = wx.ComboBox(bg_panel, size=(350, -1), choices=local_authorities,
                                                  value=self.record.local_auth, style=wx.CB_DROPDOWN | wx.CB_READONLY,
                                                  name="Click to choose Local Authority")
        grid.Add(self.local_authorities_comb, pos=(6, 2), span=(1, 4))

        # Add date selectors
        start_date_lbl = wx.StaticText(bg_panel, label="Start Date:")
        grid.Add(start_date_lbl, (7, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        self.start_date_picker = wx.adv.DatePickerCtrl(bg_panel, size=(120, -1), style=wx.adv.DP_DROPDOWN
                                                                                       | wx.adv.DP_SHOWCENTURY
                                                                                       | wx.adv.DP_ALLOWNONE)
        if self.record.start_date is not None:
            start_dt = wx.DateTime(self.record.start_date.day,
                                   self.record.start_date.month - 1,  # Because for some reason the months start at 0.
                                   self.record.start_date.year)
            self.start_date_picker.SetValue(start_dt)
        grid.Add(self.start_date_picker, pos=(7, 2))

        grid.Add((5, 10), pos=(7, 3))  # Gap

        end_date_lbl = wx.StaticText(bg_panel, label="End Date:")
        grid.Add(end_date_lbl, (7, 4), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        self.end_date_picker = wx.adv.DatePickerCtrl(bg_panel, size=(120, -1), style=wx.adv.DP_DROPDOWN
                                                                                     | wx.adv.DP_SHOWCENTURY
                                                                                     | wx.adv.DP_ALLOWNONE)
        if self.record.end_date is not None:
            end_dt = wx.DateTime(self.record.end_date.day,
                                 self.record.end_date.month - 1,  # Because for some reason the months start at 0.
                                 self.record.end_date.year)
            self.end_date_picker.SetValue(end_dt)
        grid.Add(self.end_date_picker, pos=(7, 5))

        # Add Physical and Other Refs
        physical_ref_lbl = wx.StaticText(bg_panel, label="Physical Ref:")
        grid.Add(physical_ref_lbl, (8, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        self.physical_ref_box = wx.TextCtrl(bg_panel, size=(120, -1))
        if self.record.physical_ref is not None:
            self.physical_ref_box.SetValue(self.record.physical_ref)
        grid.Add(self.physical_ref_box, (8, 2))

        other_ref_lbl = wx.StaticText(bg_panel, label="Other Ref:")
        grid.Add(other_ref_lbl, (8, 4), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        self.other_ref_box = wx.TextCtrl(bg_panel, size=(120, -1))
        if self.record.other_ref is not None:
            self.other_ref_box.SetValue(self.record.other_ref)
        grid.Add(self.other_ref_box, (8, 5))

        # New Column!
        file_list_lbl = wx.StaticText(bg_panel, label="Linked Files:")
        grid.Add(file_list_lbl, (1, 7))
        file_list = self.record.linked_files
        if file_list is None:
            file_list = []
        self.file_list_box = wx.ListBox(bg_panel, size=(320, 150), choices=file_list)
        grid.Add(self.file_list_box, (2, 7), span=(2, 1))

        # File Buttons
        file_buttons_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.upload_single_button = wx.Button(bg_panel, size=(100, -1), label="Upload\nSingle File")
        file_buttons_sizer.Add(self.upload_single_button)
        self.upload_multiple_button = wx.Button(bg_panel, size=(100, -1), label="Merge to PDF\nand Upload")
        file_buttons_sizer.Add(self.upload_multiple_button)
        file_buttons_sizer.Add((10, -1), wx.EXPAND)
        self.remove_file_button = wx.Button(bg_panel, size=(70, -1), label="Unlink\nFile")
        file_buttons_sizer.Add(self.remove_file_button)

        grid.Add(file_buttons_sizer, (4, 7), flag=wx.EXPAND)

        # Add Save and Close Buttons
        main_buttons_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.save_button = wx.Button(bg_panel, size=(100, -1), label="Save Changes", name="Save Changes to Record")
        self.save_button.Disable()
        main_buttons_sizer.Add((0, 0), wx.EXPAND)
        main_buttons_sizer.Add(self.save_button)
        main_buttons_sizer.Add((0, 0), wx.EXPAND)
        self.close_button = wx.Button(bg_panel, size=(100, -1), label="Close")
        main_buttons_sizer.Add(self.close_button)
        main_buttons_sizer.Add((0, 0), wx.EXPAND)

        grid.Add(main_buttons_sizer, (6, 7), flag=wx.EXPAND)

        # Add created and changed info
        created_text = wx.StaticText(bg_panel, label="Created by:\n{} - {}"
                                     .format(str(self.record.created_by), str(self.record.created_time_string())))
        grid.Add(created_text, (7, 7))

        changed_text = wx.StaticText(bg_panel, label="Last Changed:\n{} - {}"
                                     .format(str(self.record.last_changed_by),
                                             str(self.record.last_changed_time_string())))
        grid.Add(changed_text, (8, 7))

        # Add a spacer to the sizer
        grid.Add((20, 10), pos=(9, 8))

        sizer.Add(grid, 0, wx.ALL, 0)

        self.SetSizerAndFit(sizer)

        self.create_binds()

        self.Show(True)

        self.unsaved_changes = False

    def create_binds(self):
        # All Entry Fields > Update Change Status
        self.Bind(wx.EVT_TEXT, self.set_changed, self.title_box)
        self.Bind(wx.EVT_TEXT, self.set_changed, self.desc_box)
        self.Bind(wx.EVT_COMBOBOX, self.set_changed, self.type_comb)
        self.Bind(wx.EVT_COMBOBOX, self.set_changed, self.local_authorities_comb)
        self.Bind(wx.adv.EVT_DATE_CHANGED, self.set_changed, self.start_date_picker)
        self.Bind(wx.adv.EVT_DATE_CHANGED, self.set_changed, self.end_date_picker)
        self.Bind(wx.EVT_TEXT, self.set_changed, self.physical_ref_box)
        self.Bind(wx.EVT_TEXT, self.set_changed, self.other_ref_box)

        # File Link Double-click
        self.Bind(wx.EVT_LISTBOX_DCLICK, self.file_link_clicked, self.file_list_box)

        # Close Button > Close Frame
        self.Bind(wx.EVT_BUTTON, self.close_button_press, self.close_button)

    def close_button_press(self, event):
        self.Close()

    def set_changed(self, event):
        self.unsaved_changes = True
        self.save_button.Enable()

    def file_link_clicked(self, event):
        suc = self.record.launch_file(self.record.linked_files.index(event.GetString()))
        if suc is True:
            return None
        elif suc == "Index Error":
            msg = "File {} does not appear to be linked to this record!".format(event.GetString())
        elif suc == "Path Error":
            msg = "File {} does not appear to exist!".format(event.GetString())
        else:
            msg = "File {} could not be opened for an unknown reason, which is worrying...".format(event.GetString())
        dlg = wx.MessageDialog(self, msg, "File Error", wx.OK)
        dlg.ShowModal()
        dlg.Destroy()


def main(record_obj):
    app = wx.App(False)
    frame = RecordEditor(None, "OpenArchive - View/Edit Record", record_obj)
    app.MainLoop()


if __name__ == "__main__":
    main(database_io.get_record_by_id(6))
