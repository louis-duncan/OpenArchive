from typing import Optional

import wx
import wx.dataview as dv
import easygui
import csv
import database_io
import os

import kml_load
import record_editor

from database_io import ArchiveRecord

__title__ = "OpenArchive"

test_data = None


class RecordListViewer(wx.Frame):
    def __init__(self, parent, title, records, current_page=0):
        # Define the headings for later
        self.all_records = records
        self.current_page = current_page
        self.title = "{} - {} records".format(title, len(self.all_records))

        self.headings = (("ID:", 35),
                         ("Title:", 250),
                         ("Description:", 500),
                         ("Type:", 150),
                         ("Source/Local Auth.:", 150),
                         ("Date Period:", 150),
                         ("Tags:", 200),
                         ("NESW:", 50)
                         )

        total_width = 0
        for h in self.headings:
            total_width += h[1]

        wx.Frame.__init__(self, parent, title=self.title,
                          size=(total_width + 20, 500), style=wx.DEFAULT_FRAME_STYLE)

        if len(records) == 0:
            dlg = wx.MessageDialog(self, "No Records\n"
                                         "\n"
                                         "No records to show.",
                                   title)
            dlg.ShowModal()
            dlg.Destroy()
            self.Destroy()
            raise Exception("No Records")
        else:
            pass

        assert type(records[0]) == database_io.ArchiveRecord

        page_len = 16
        self.pages = []
        new_page = []
        for i, r in enumerate(records):
            new_page.append(r)
            if (i + 1) % page_len == 0:
                self.pages.append(new_page)
                new_page = []
            else:
                pass
        if len(new_page) > 0:
            self.pages.append(new_page)

        # Create List Control
        self.dvc = dv.DataViewListCtrl(self,
                                       style=wx.BORDER_THEME
                                             | dv.DV_ROW_LINES
                                             | dv.DV_VERT_RULES
                                             | dv.DV_VARIABLE_LINE_HEIGHT
                                       )
        # Add columns
        for i, (h, w) in enumerate(self.headings):
            if h == "NESW:":
                self.dvc.AppendToggleColumn(h, i, width=w)
            else:
                self.dvc.AppendTextColumn(h, i, width=w)

        self.format_data_control()

        self.sizer = wx.BoxSizer(wx.VERTICAL)

        self.sizer.Add(self.dvc, 1, wx.EXPAND)

        self.button_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.export_button = wx.Button(self, wx.NewId(), "Export to Excel", size=(150, 40))
        self.button_sizer.AddSpacer(5)
        self.button_sizer.Add(self.export_button)

        self.kml_page_button = wx.Button(self, wx.NewId(), "View Current Page\nin Google Earth", size=(150, 40))
        self.button_sizer.AddSpacer(5)
        self.button_sizer.Add(self.kml_page_button)

        self.kml_all_button = wx.Button(self, wx.NewId(), "View All Results\nin Google Earth", size=(150, 40))
        self.button_sizer.AddSpacer(5)
        self.button_sizer.Add(self.kml_all_button)

        self.previous_page_button = wx.Button(self, wx.NewId(), "<<<", size=(150, 40))
        if current_page == 0:
            self.previous_page_button.Disable()
        self.button_sizer.AddSpacer(50)
        self.button_sizer.Add(self.previous_page_button)

        self.page_no_text = wx.StaticText(self, label="Page:\n{} of {}".format(self.current_page + 1, len(self.pages)),
                                          style=wx.ALIGN_CENTER)
        self.button_sizer.AddSpacer(20)
        self.button_sizer.Add(self.page_no_text, flag=wx.ALIGN_CENTER)

        self.next_page_button = wx.Button(self, wx.NewId(), ">>>", size=(150, 40))
        if current_page + 1 == len(self.pages):
            self.next_page_button.Disable()
        self.button_sizer.AddSpacer(20)
        self.button_sizer.Add(self.next_page_button)

        self.sizer.AddSpacer(5)
        self.sizer.Add(self.button_sizer, 0)
        self.sizer.AddSpacer(5)

        self.SetSizer(self.sizer)

        self.Bind(dv.EVT_DATAVIEW_ITEM_ACTIVATED, self.record_activated, self.dvc)
        self.Bind(wx.EVT_BUTTON, self.export_csv, self.export_button)
        self.Bind(wx.EVT_BUTTON, self.export_all_kml, self.kml_all_button)
        self.Bind(wx.EVT_BUTTON, self.export_page_kml, self.kml_page_button)
        self.Bind(wx.EVT_BUTTON, self.go_to_previous_page, self.previous_page_button)
        self.Bind(wx.EVT_BUTTON, self.go_to_next_page, self.next_page_button)
        self.Bind(wx.EVT_CLOSE, self.on_close)

        self.Bind(wx.EVT_KEY_DOWN, self.key_press)

        self.Show()

    def format_data_control(self):
        # Format records.
        data = []
        for record in self.pages[self.current_page]:
            dates = []
            date_range_string = ""
            if record.start_date is not None:
                dates.append(record.start_date_string())
            if record.end_date is not None:
                dates.append(record.end_date_string())

            if len(dates) == 2:
                date_range_string = "{} - {}".format(dates[0],
                                                     dates[1])
            elif len(dates) == 1:
                date_range_string = str(dates[0])
            else:
                pass
            entry = [record.record_id,
                     record.title,
                     record.description.replace("\n", " "),
                     record.record_type,
                     record.local_auth,
                     date_range_string,
                     record.string_tags(),
                     None not in (record.latitude, record.longitude),
                     ]
            if entry[6] == record.tags_prompt:
                entry[6] = ""
            data.append(entry)

        for r in data:
            self.dvc.AppendItem(r)

    def go_to_previous_page(self, e):
        self.current_page -= 1
        self.refresh()

    def go_to_next_page(self, e):
        self.current_page += 1
        self.refresh()

    def refresh(self):
        self.page_no_text.SetLabel("Page:\n{} of {}".format(self.current_page + 1, len(self.pages)))
        self.sizer.Layout()
        self.dvc.DeleteAllItems()
        self.format_data_control()
        self.previous_page_button.Enable()
        self.next_page_button.Enable()
        if self.current_page == 0:
            self.previous_page_button.Disable()
        if self.current_page == len(self.pages) - 1:
            self.next_page_button.Disable()

    def key_press(self, e):
        key_code = e.GetKeyCode()
        if key_code == wx.WXK_LEFT:
            print("Pressed Left")
        elif key_code == wx.WXK_RIGHT:
            print("Pressed Right")
        else:
            print("Other Key Press")
        e.Skip()

    def record_activated(self, event):
        selection = self.dvc.GetSelection()
        id_to_show = self.pages[self.current_page][int(selection.ID) - 1].record_id
        record_editor.main(database_io.get_record_by_id(id_to_show))
        record_editor.RecordEditor(self, __title__ + " - Record Viewer",
                                   database_io.get_record_by_id(id_to_show))

    def export_csv(self, e, dest=None):
        data = []
        for record in self.all_records:
            dates = []
            date_range_string = ""
            if record.start_date is not None:
                dates.append(record.start_date_string())
            if record.end_date is not None:
                dates.append(record.end_date_string())

            if len(dates) == 2:
                date_range_string = "{} - {}".format(dates[0],
                                                     dates[1])
            elif len(dates) == 1:
                date_range_string = str(dates[0])
            else:
                pass
            entry = [record.record_id,
                     record.title,
                     record.description.replace("\n", " "),
                     record.record_type,
                     record.local_auth,
                     date_range_string,
                     record.string_tags(),
                     None not in (record.latitude, record.longitude),
                     ]
            if entry[6] == record.tags_prompt:
                entry[6] = ""
            data.append(entry)

        if dest is None:
            dlg = wx.FileDialog(self, "Select Destination:", os.environ["USERPROFILE"], "Export.csv",
                                wildcard="CSV file (*.csv)|*.csv",
                                style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
            resp = dlg.ShowModal()
            if resp == wx.ID_CANCEL:
                print("Users Cancelled")
                return None
            else:
                dest = dlg.GetPath()
            dlg.Destroy()
        else:
            pass

        with open(dest, "w", newline='') as file:
            writer: csv.writer = csv.writer(file, csv.excel)
            for row in data:
                writer.writerow(row)
        os.startfile(dest)

    def export_all_kml(self, e):
        dlg = wx.MessageDialog(self, "Warning\n\nThis will attempt to load {} points in Google Earth.\n"
                                     "\n"
                                     "Do you wish to continue?".format(len(self.all_records)),
                               style=wx.ICON_WARNING | wx.YES_NO)
        resp = dlg.ShowModal()
        if resp == wx.ID_NO:
            return None
        else:
            pass
        assert type(self.all_records[0]) == database_io.ArchiveRecord
        points = []
        for record in self.all_records:
            # Todo: Add catch for none records. Including removing dead bookmarks.
            assert record is not None
            if None not in (record.latitude, record.longitude):
                points.append((record.title, record.description, record.longitude, record.latitude))
            else:
                pass
        kml_load.load_batch(points)

    def export_page_kml(self, e):
        points = []
        for record in self.pages[self.current_page]:
            # Todo: Add catch for none records. Including removing dead bookmarks.
            assert record is not None
            if None not in (record.latitude, record.longitude):
                points.append((record.title, record.description, record.longitude, record.latitude))
            else:
                pass
        kml_load.load_batch(points)

    def on_close(self, event):
        print("Closed")
        self.Destroy()


def main(title, record_ids):
    app = wx.App(False)
    frame = RecordListViewer(None, title, records=record_ids)
    app.MainLoop()
    database_io.clear_cache()


if __name__ == '__main__':
    while True:
        user_name = easygui.enterbox("Enter username to view associated bookmarks:",
                                     __title__ + " - User Bookmarks")
        if user_name is None:
            break
        else:
            bookmarks = database_io.get_user_bookmarks(user_name)
            if len(bookmarks) == 0:
                easygui.msgbox("No bookmarks for user '{}'".format(user_name),
                               __title__ + " - User Bookmarks")
            else:
                main(__title__ + " - Bookmark Viewer - " + user_name, bookmarks)
