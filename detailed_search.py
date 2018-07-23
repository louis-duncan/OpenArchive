import wx
import wx.adv
from wx.lib import sized_controls
import os
import subprocess
import string
import collections
import datetime

import database_io
import textdistance

__title__ = "OpenArchive"


class NumberValidator(wx.Validator):
    def __init__(self, flag=None, pyVar=None):
        wx.Validator.__init__(self)
        self.flag = flag
        self.Bind(wx.EVT_CHAR, self.on_char)

    def Clone(self):
        return NumberValidator(self.flag)

    def Validate(self, win):
        tc = self.GetWindow()
        val = tc.GetValue()

        for x in val:
            if x not in string.digits:
                return False

        return True

    def on_char(self, event):
        key = event.GetKeyCode()

        if key < wx.WXK_SPACE or key == wx.WXK_DELETE or key > 255:
            event.Skip()
            return

        if chr(key) in string.digits:
            event.Skip()
            return

        if not wx.Validator.IsSilent():
            wx.Bell()

        # Returning without calling even.Skip eats the event before it
        # gets to the text control
        return


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


class DetailedSearch(wx.Frame):
    def __init__(self, parent, title):
        frame_width = 600
        frame_height = 800

        wx.Frame.__init__(self, parent, title=title + " - Detailed Search", size=(frame_width, frame_height),
                          style=wx.DEFAULT_FRAME_STYLE ^ wx.RESIZE_BORDER ^ wx.MAXIMIZE_BOX)

        # Add bg panel
        bg_panel = wx.Panel(self, size=(frame_width, frame_height))

        self.previous_id = ""

        row_one = wx.BoxSizer(wx.HORIZONTAL)
        # Record ID
        record_id_lbl = wx.StaticText(bg_panel, label="Record ID:")
        row_one.Add(record_id_lbl, flag=wx.ALIGN_CENTRE_VERTICAL | wx.TOP, border=2)
        self.record_id_box = wx.TextCtrl(bg_panel, size=(50, -1), validator=NumberValidator(),
                                         style=wx.TE_PROCESS_ENTER)
        record_id_tip_msg = """Number only.
If an ID is entered here, no other search options will be available."""
        record_id_tip = wx.ToolTip(record_id_tip_msg)
        self.record_id_box.SetToolTip(record_id_tip)
        row_one.AddSpacer(10)
        row_one.Add(self.record_id_box, flag=wx.ALIGN_CENTRE_VERTICAL)

        row_two = wx.BoxSizer(wx.HORIZONTAL)
        # Free Text
        self.free_text_lbl = wx.StaticText(bg_panel, label="Free Text:")
        row_two.Add(self.free_text_lbl, flag=wx.ALIGN_CENTRE_VERTICAL | wx.TOP, border=2)
        self.free_text_box = wx.TextCtrl(bg_panel, size=(300, -1),
                                         style=wx.TE_PROCESS_ENTER)
        row_two.AddSpacer(10)
        row_two.Add(self.free_text_box, flag=wx.ALIGN_CENTRE_VERTICAL)

        # Search filters
        # self.filters_lbl = wx.StaticText(bg_panel, label="Filters:")

        self.filters_panel = wx.StaticBox(bg_panel, size=(400, 200), label="Filters:")

        filters_sizer = wx.BoxSizer(wx.VERTICAL)

        # Types Filter
        type_sizer = wx.GridBagSizer(0, 0)
        type_lbl = wx.StaticText(self.filters_panel, label="Resource Types:")
        self.record_types = database_io.return_types()
        self.record_types.sort(key=database_io.float_none_drop_other)
        self.types_multi_choice = wx.CheckListBox(self.filters_panel, size=(300, 80), choices=self.record_types)
        type_sizer.Add(self.types_multi_choice, (0, 0), span=(3, 1))
        self.check_all_types_button = wx.Button(self.filters_panel, label="Select All")
        type_sizer.Add(self.check_all_types_button, (0, 2))
        self.clear_all_types_button = wx.Button(self.filters_panel, label="Clear All")
        type_sizer.Add(self.clear_all_types_button, (2, 2))

        filters_sizer.Add(type_lbl)
        filters_sizer.Add(type_sizer)

        # Auths Filter
        auth_sizer = wx.GridBagSizer(0, 0)
        auth_lbl = wx.StaticText(self.filters_panel, label="Sources/Local Authorities:")
        self.record_auths = database_io.return_local_authorities()
        self.record_auths.sort(key=database_io.float_none_drop_other)
        self.auths_multi_choice = wx.CheckListBox(self.filters_panel, size=(300, 80), choices=self.record_auths)
        auth_sizer.Add(self.auths_multi_choice, (0, 0), span=(3, 1))
        self.check_all_auths_button = wx.Button(self.filters_panel, label="Select All")
        auth_sizer.Add(self.check_all_auths_button, (0, 2))
        self.clear_all_auths_button = wx.Button(self.filters_panel, label="Clear All")
        auth_sizer.Add(self.clear_all_auths_button, (2, 2))

        filters_sizer.AddSpacer(5)
        filters_sizer.Add(auth_lbl)
        filters_sizer.Add(auth_sizer)

        # Date Range
        dates_lbl = wx.StaticText(self.filters_panel, label="Date Range:")
        self.start_date = wx.adv.DatePickerCtrl(self.filters_panel, size=(120, -1),
                                                style=wx.adv.DP_DROPDOWN | wx.adv.DP_SHOWCENTURY | wx.adv.DP_ALLOWNONE)
        self.end_date = wx.adv.DatePickerCtrl(self.filters_panel, size=(120, -1),
                                              style=wx.adv.DP_DROPDOWN | wx.adv.DP_SHOWCENTURY | wx.adv.DP_ALLOWNONE)
        arrows = wx.StaticText(self.filters_panel, label="<->", style=wx.ALIGN_BOTTOM)
        dates_sizer = wx.BoxSizer(wx.HORIZONTAL)
        dates_sizer.Add(self.start_date)
        dates_sizer.AddSpacer(5)
        dates_sizer.Add(arrows, flag=wx.ALIGN_CENTRE_VERTICAL)
        dates_sizer.AddSpacer(5)
        dates_sizer.Add(self.end_date)

        filters_sizer.AddSpacer(5)
        filters_sizer.Add(dates_lbl)
        filters_sizer.Add(dates_sizer)

        # Coordinate
        coord_lbl = wx.StaticText(self.filters_panel, label="Position/Coordinate:")
        coord_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.longitude_box = wx.SearchCtrl(self.filters_panel, size=(120, -1))
        self.longitude_box.ShowSearchButton(False)
        self.longitude_box.SetDescriptiveText('Longitude: E/W')
        self.latitude_box = wx.SearchCtrl(self.filters_panel, size=(120, -1))
        comma = wx.StaticText(self.filters_panel, label="/")
        self.latitude_box.ShowSearchButton(False)
        self.latitude_box.SetDescriptiveText('Latitude: N/S')

        radius_lbl = wx.StaticText(self.filters_panel, label="Radius (km):")
        self.radius_spinner = wx.SpinCtrlDouble(self.filters_panel,
                                                value='0.00',
                                                pos=(75, 50),
                                                size=(70, -1),
                                                min=0.0,
                                                max=999.99,
                                                inc=0.50)
        self.radius_spinner.SetDigits(2)

        coord_sizer.Add(self.longitude_box)
        coord_sizer.AddSpacer(5)
        coord_sizer.Add(comma, flag=wx.ALIGN_CENTRE_VERTICAL)
        coord_sizer.AddSpacer(5)
        coord_sizer.Add(self.latitude_box)
        coord_sizer.AddSpacer(10)
        coord_sizer.Add(radius_lbl, flag=wx.ALIGN_CENTRE_VERTICAL)
        coord_sizer.AddSpacer(5)
        coord_sizer.Add(self.radius_spinner)

        filters_sizer.AddSpacer(5)
        filters_sizer.Add(coord_lbl)
        filters_sizer.Add(coord_sizer)

        filters_pad = wx.BoxSizer()
        filters_pad.Add(filters_sizer, 1, wx.EXPAND | wx.ALL, 20)
        self.filters_panel.SetSizerAndFit(filters_pad)

        # Buttons
        buttons_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.search_button = wx.Button(bg_panel, size=(120, 30), label="Search")
        self.cancel_button = wx.Button(bg_panel, size=(120, 30), label="Cancel")
        buttons_sizer.Add(self.search_button)
        buttons_sizer.AddSpacer(10)
        buttons_sizer.Add(self.cancel_button)

        # Add rows to column
        row_sizer = wx.BoxSizer(wx.VERTICAL)
        # row_sizer.AddSpacer(10)
        # row_sizer.Add(header)
        row_sizer.AddSpacer(15)
        row_sizer.Add(wx.Panel(self, size=(430, 1), style=wx.BORDER_SIMPLE, name="line"))
        row_sizer.AddSpacer(15)
        row_sizer.Add(row_one)
        row_sizer.AddSpacer(15)
        row_sizer.Add(wx.Panel(self, size=(430, 1), style=wx.BORDER_SIMPLE, name="line"))
        row_sizer.AddSpacer(20)
        row_sizer.Add(row_two)
        row_sizer.AddSpacer(15)
        row_sizer.Add(self.filters_panel)
        row_sizer.AddSpacer(15)
        row_sizer.Add(buttons_sizer, wx.EXPAND, wx.ALIGN_CENTRE)
        row_sizer.AddSpacer(15)

        col_sizer = wx.BoxSizer(wx.HORIZONTAL)
        col_sizer.AddSpacer(10)
        col_sizer.Add(row_sizer)
        col_sizer.AddSpacer(10)

        self.SetSizerAndFit(col_sizer)
        self.create_binds()

        self.Show(True)

    def create_binds(self):
        # Bind Data Entry
        self.Bind(wx.EVT_TEXT, self.record_id_changed, self.record_id_box)

        # Bind Enter Key
        self.Bind(wx.EVT_TEXT_ENTER, self.search, self.record_id_box)
        self.Bind(wx.EVT_TEXT_ENTER, self.search, self.free_text_box)

        # Bind Button Presses
        self.Bind(wx.EVT_BUTTON, self.select_all_types, self.check_all_types_button)
        self.Bind(wx.EVT_BUTTON, self.clear_all_types, self.clear_all_types_button)
        self.Bind(wx.EVT_BUTTON, self.select_all_auths, self.check_all_auths_button)
        self.Bind(wx.EVT_BUTTON, self.clear_all_auths, self.clear_all_auths_button)

        self.Bind(wx.EVT_BUTTON, self.search, self.search_button)
        self.Bind(wx.EVT_BUTTON, self.close_button_press, self.cancel_button)

        # Close Frame
        self.Bind(wx.EVT_CLOSE, self.close_button_press)

    def select_all_types(self, event):
        for i in range(len(self.record_types)):
            self.types_multi_choice.Check(i)

    def clear_all_types(self, event):
        for i in range(len(self.record_types)):
            self.types_multi_choice.Check(i, False)

    def select_all_auths(self, event):
        for i in range(len(self.record_auths)):
            self.auths_multi_choice.Check(i)

    def clear_all_auths(self, event):
        for i in range(len(self.record_auths)):
            self.auths_multi_choice.Check(i, False)

    def record_id_changed(self, event):
        # Todo: Add validator
        changed_text = self.record_id_box.GetValue()
        if changed_text != "":
            entry_valid = validate_numbers(changed_text)
            if not entry_valid:
                self.record_id_box.SetValue(self.previous_id)
            else:
                pass
        else:
            pass

        if self.record_id_box.GetValue() != "":
            self.disable_filters()
        else:
            self.enable_filters()

        self.previous_id = self.record_id_box.GetValue()

    def disable_filters(self):
        self.free_text_lbl.Disable()
        self.free_text_box.Disable()
        self.filters_panel.Disable()

    def enable_filters(self):
        self.free_text_lbl.Enable()
        self.free_text_box.Enable()
        self.filters_panel.Enable()

    def search(self, event=None):
        print("Search")
        search_data = self.gather_data()
        print(search_data)

    def gather_data(self):
        Search = collections.namedtuple("Search",
                                        "record_id free_text types auths start_date end_date latitude longitude radius")
        if self.record_id_box.GetValue() != "":
            print("Quick Search")
            return Search(self.record_id_box.GetValue(),
                          "",
                          "",
                          "",
                          "",
                          "",
                          "",
                          "",
                          ""
                          )
        else:
            print("Not Quick Search")
            wx_start_date = self.start_date.GetValue()
            wx_end_date = self.end_date.GetValue()
            start_date = datetime.datetime(wx_start_date.GetYear(),
                                           wx_start_date.GetMonth() + 1,
                                           wx_start_date.GetDay(),
                                           )
            end_date = datetime.datetime(wx_end_date.GetYear(),
                                         wx_end_date.GetMonth() + 1,
                                         wx_end_date.GetDay(),
                                         )
            return Search(None,
                          self.free_text_box.GetValue(),
                          self.types_multi_choice.GetCheckedStrings(),
                          self.auths_multi_choice.GetCheckedStrings(),
                          start_date,
                          end_date,
                          self.latitude_box.GetValue(),
                          self.longitude_box.GetValue(),
                          self.radius_spinner.GetValue(),
                          )

    def close_button_press(self, event):
        self.Destroy()


def validate_numbers(text):
    assert type(text) == str
    valid = True
    try:
        int(text)
    except ValueError:
        if text == "":
            valid = None
        else:
            valid = False
    return valid


def main(title=__title__):
    app = wx.App(False)
    frame = DetailedSearch(None, title)
    app.MainLoop()


if __name__ == "__main__":
    database_io.init()
    main()
