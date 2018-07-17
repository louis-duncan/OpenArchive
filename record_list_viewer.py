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
    def __init__(self, parent, title, records):
        # Define the headings for later
        self.records = records

        closing = False

        headings = (("ID:", 35),
                    ("Title:", 250),
                    ("Description:", 500),
                    ("Type:", 150),
                    ("Source/Local Auth.:", 150),
                    ("Date Period:", 150),
                    ("Tags:", 200),
                    ("NESW:", 50)
                    )

        total_width = 0
        for h in headings:
            total_width += h[1]

        wx.Frame.__init__(self, parent, title=title,
                          size=(total_width + 20, 500), style=wx.DEFAULT_FRAME_STYLE)

        if len(records) == 0:
            dlg = wx.MessageDialog(self, "No Records\n"
                                         "\n"
                                         "No records to show.",
                                   title)
            dlg.ShowModal()
            dlg.Destroy()
            self.Destroy()
            closing = True
        else:
            pass

        # Create List Control
        self.dvc = dv.DataViewListCtrl(self,
                                       style=wx.BORDER_THEME
                                             | dv.DV_ROW_LINES
                                             | dv.DV_VERT_RULES
                                             | dv.DV_VARIABLE_LINE_HEIGHT
                                       )

        # Format records.
        assert (type(records[0]) == database_io.ArchiveRecord) or (str(type(records[0])) == "<class 'sql.Record'>")
        assert None not in records
        if type(self.records[0]) == database_io.ArchiveRecord:
            pass
        elif type(self.records) == database_io.ArchiveRecord:
            self.records = [self.records]
        else:
            print("Records are sql objects, formatting...")
            self.records = database_io.format_sql_to_record_obj(self.records)
        assert type(self.records) in (list, tuple)
        self.data = []
        for record in self.records:
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
            self.data.append(entry)

        for r in self.data:
            self.dvc.AppendItem(r)


        # Add columns
        for i, (h, w) in enumerate(headings):
            if h == "NESW:":
                self.dvc.AppendToggleColumn(h, i, width=w)
            else:
                self.dvc.AppendTextColumn(h, i, width=w)

        sizer = wx.BoxSizer(wx.VERTICAL)

        sizer.Add(self.dvc, 1, wx.EXPAND)

        button_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.export_button = wx.Button(self, wx.NewId(), "Export to Excel", size=(200, 30))
        button_sizer.AddSpacer(5)
        button_sizer.Add(self.export_button)

        self.kml_button = wx.Button(self, wx.NewId(), "View Points in Google Earth", size=(200, 30))
        button_sizer.AddSpacer(5)
        button_sizer.Add(self.kml_button)

        sizer.AddSpacer(5)
        sizer.Add(button_sizer, 0)
        sizer.AddSpacer(5)

        self.SetSizer(sizer)

        self.Bind(dv.EVT_DATAVIEW_ITEM_ACTIVATED, self.record_activated, self.dvc)
        self.Bind(wx.EVT_BUTTON, self.export_csv, self.export_button)
        self.Bind(wx.EVT_BUTTON, self.export_kml, self.kml_button)
        self.Bind(wx.EVT_CLOSE, self.on_close)

        if not closing:
            self.Show()

    def record_activated(self, event):
        selection = self.dvc.GetSelection()
        id_of_record_to_show = self.data[int(selection.ID) - 1][0]
        record_editor.main(database_io.get_record_by_id(id_of_record_to_show))
        record_editor.RecordEditor(self, __title__ + " - Record Viewer",
                                   database_io.get_record_by_id(id_of_record_to_show))

    def export_csv(self, e, dest=None):
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
            for row in self.data:
                writer.writerow(row)
        os.startfile(dest)

    def export_kml(self, e):
        points = []
        assert type(self.records[0]) == database_io.ArchiveRecord
        for record in self.records:
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
