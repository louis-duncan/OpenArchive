import wx
import wx.adv
from wx.lib import sized_controls
import os
import subprocess

import database_io
import textdistance

__title__ = "OpenArchive"


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
        frame_height = 500

        wx.Frame.__init__(self, parent, title=title + " - Detailed Search", size=(frame_width, frame_height),
                          style=wx.DEFAULT_FRAME_STYLE ^ wx.RESIZE_BORDER ^ wx.MAXIMIZE_BOX)

        # Add bg panel
        bg_panel = wx.Panel(self, size=(frame_width, frame_height))

        header = wx.StaticText(bg_panel, label="   Fill boxes as required to refine your search:")

        row_one = wx.BoxSizer(wx.HORIZONTAL)

        # Record ID
        row_one.AddSpacer(10)
        record_id_lbl = wx.StaticText(bg_panel, label="Record ID:")
        row_one.Add(record_id_lbl, flag=wx.ALIGN_CENTRE_VERTICAL | wx.TOP, border=2)
        self.record_id_box = wx.TextCtrl(bg_panel, size=(50, -1))
        record_id_tip_msg = """Number only.
        If an ID is entered here """
        record_id_tip = wx.ToolTip(record_id_tip_msg)
        self.record_id_box.SetToolTip(record_id_tip)
        row_one.AddSpacer(10)
        row_one.Add(self.record_id_box, flag=wx.ALIGN_CENTRE_VERTICAL)

        # Free Text
        row_one.AddSpacer(20)
        free_text_lbl = wx.StaticText(bg_panel, label="Free Text:")
        row_one.Add(free_text_lbl, flag=wx.ALIGN_CENTRE_VERTICAL | wx.TOP, border=2)
        self.free_text_box = wx.TextCtrl(bg_panel, size=(300, -1))
        row_one.AddSpacer(10)
        row_one.Add(self.free_text_box, flag=wx.ALIGN_CENTRE_VERTICAL)

        row_sizer = wx.BoxSizer(wx.VERTICAL)
        row_sizer.AddSpacer(10)
        row_sizer.Add(header)
        row_sizer.AddSpacer(10)
        row_sizer.Add(row_one)
        row_sizer.AddSpacer(10)

        self.SetSizer(row_sizer)
        self.create_binds()

        self.Show(True)

    def create_binds(self):
        # Bind Data Entry

        # Close Frame
        self.Bind(wx.EVT_CLOSE, self.close_button_press)

    def close_button_press(self, e):
        self.Destroy()


def main(title=__title__):
    app = wx.App(False)
    frame = DetailedSearch(None, title)
    app.MainLoop()


if __name__ == "__main__":
    main()
