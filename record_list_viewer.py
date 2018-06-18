from typing import Optional

import wx
import wx.dataview as dv
import easygui
import csv
import database_io
import os
import record_editor

from database_io import ArchiveRecord

__title__ = "OpenArchive"

test_data = None


class RecordListViewer(wx.Frame):
    def __init__(self, parent, title, records):
        # Define the headings for later

        closing = False

        headings = (("ID:", 35),
                    ("Title:", 250),
                    ("Description:", 500),
                    ("Type:", 150),
                    ("Source/Local Auth.:", 150),
                    ("Date Period:", 150),
                    ("Tags:", 200)
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

        self.data = []
        for r in records:
            #print(r)
            if type(r) in (str, int):
                record: ArchiveRecord = database_io.get_record_by_id(int(r))
            else:
                record = database_io.format_sql_to_record_obj(r)

            # Todo: Add catch for none records. Including removing dead bookmarks.
            assert record is not None

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
                     record.string_tags()
                     ]
            if entry[6] == record.tags_prompt:
                entry[6] = ""
            self.data.append(entry)

        for r in self.data:
            self.dvc.AppendItem(r)


        # Add columns
        for i, (h, w) in enumerate(headings):
            self.dvc.AppendTextColumn(h, i, width=w)

        self.export_button = wx.Button(self, -1, "Export to '.csv'")

        self.Bind(dv.EVT_DATAVIEW_ITEM_ACTIVATED, self.record_activated, self.dvc)
        self.Bind(wx.EVT_BUTTON, self.export_csv, self.export_button)
        self.Bind(wx.EVT_CLOSE, self.on_close)

        sizer = wx.BoxSizer(wx.VERTICAL)

        sizer.Add(self.dvc, 1, wx.EXPAND)

        sizer.Add(self.export_button, 0)

        self.SetSizer(sizer)

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
                pass
        else:
            pass
        with open(dlg.GetPath(), "w", newline='') as file:
            writer: csv.writer = csv.writer(file, csv.excel)
            for row in self.data:
                writer.writerow(row)
        os.startfile(dlg.GetPath())
        dlg.Destroy()

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
