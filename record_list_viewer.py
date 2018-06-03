from typing import Optional

import wx
import wx.dataview as dv
import easygui
import csv
import database_io
import os

from database_io import ArchiveRecord

__title__ = "OpenArchive"


class DataModel(dv.DataViewIndexListModel):
    def __init__(self, data):
        dv.DataViewIndexListModel.__init__(self, len(data))
        self.data = data

    # All of our columns are strings.  If the model or the renderers
    # in the view are other types then that should be reflected here.
    def GetColumnType(self, col):
        return "string"

    # This method is called to provide the data object for a
    # particular row,col
    def GetValueByRow(self, row, col):
        return self.data[row][col]

    # This method is called when the user edits a data item in the view.
    def SetValueByRow(self, value, row, col):
        self.data[row][col] = value
        return True

    # Report how many columns this model provides data for.
    def GetColumnCount(self):
        return len(self.data[0])

    # Report the number of rows in the model
    def GetCount(self):
        return len(self.data)

    # Called to check if non-standard attributes should be used in the
    # cell at (row, col)
    def GetAttrByRow(self, row, col, attr):
        #if col == 3:
        #    attr.SetColour('blue')
        #    attr.SetBold(True)
        #    return True
        return False


class RecordListViewer(wx.Frame):
    def __init__(self, parent, title, record_ids):
        # Define the headings for later
        headings = (("ID:", 35),
                    ("Title:", 250),
                    ("Description:", 400),
                    ("Type:", 250),
                    ("Local Auth:", 120),
                    ("Date Period:", 150),
                    )

        total_width = 0
        for h in headings:
            total_width += h[1]

        wx.Frame.__init__(self, parent, title=title,
                          size=(total_width + 20, 500), style=wx.DEFAULT_FRAME_STYLE)

        if len(record_ids) == 0:
            dlg = wx.MessageDialog(self, "No Records\n"
                                         "\n"
                                         "No records to show.",
                                   title)
            dlg.ShowModal()
            dlg.Destroy()
            self.Destroy()
        else:
            pass

        # Create List Control
        self.dvc = dv.DataViewCtrl(self,
                                   style=wx.BORDER_THEME
                                   | dv.DV_ROW_LINES
                                   | dv.DV_VERT_RULES
                                   | dv.DV_VARIABLE_LINE_HEIGHT
                                   )

        self.data = []
        for r in record_ids:
            print(r)
            record: ArchiveRecord = database_io.get_record_by_id(r)

            # Todo: Add catch for none records. Including removing dead bookmarks.
            assert record is not None

            dates = ()
            # Todo: Finish data formatting.
            date_range_string = ""
            entry = (record.record_id,
                     record.title,
                     record.description.replace("\n", " "),
                     record.record_type,
                     record.local_auth,
                     date_range_string,
                     record.string_tags()
                     )
            self.data.append(entry)

        # Add columns
        for i, (h, w) in enumerate(headings):
            self.dvc.AppendTextColumn(h, i, width=w)

        self.dvc.AssociateModel(DataModel(self.data))

        self.export_button = wx.Button(self, -1, "Export to '.csv'")
        self.Bind(wx.EVT_BUTTON, self.export_csv, self.export_button)

        sizer = wx.BoxSizer(wx.VERTICAL)

        sizer.Add(self.dvc, 1, wx.EXPAND)

        sizer.Add(self.export_button, 0)

        self.SetSizer(sizer)

        self.Show()


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


def main(title, record_ids):
    app = wx.App(False)
    frame = RecordListViewer(None, title, record_ids=record_ids)
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