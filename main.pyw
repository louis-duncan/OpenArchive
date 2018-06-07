import os
import time

import easygui
import record_list_viewer
import database_io
import record_editor
import wx
import signal

__title__ = "OpenArchive"
__author__ = "Louis Thurman"


class LaunchPad(wx.Frame):
    def __init__(self, parent, title):

        window_size = (500, 280)
        wx.Frame.__init__(self, parent, title=title, size=window_size,
                          style=wx.DEFAULT_FRAME_STYLE ^ wx.RESIZE_BORDER ^ wx.MAXIMIZE_BOX)

        # Add bg panel
        bg_panel = wx.Panel(self, size=window_size)

        self.choices = ["Quick Search", "Detailed Search", "Create New Record", "View My List"]
        msg = """- Welcome to OpenArchive -

Database File:
{}

Archive Location:
{}""".format(database_io.DATABASE_LOCATION, database_io.ARCHIVE_LOCATION_ROOT)

        msg_lbl = wx.StaticText(bg_panel, label=msg, style=wx.ALIGN_CENTER)

        button_sizer = wx.GridBagSizer(10, 10)
        button_size = (130, 40)

        self.buttons = []
        for c in self.choices:
            self.buttons.append(wx.Button(bg_panel, size=button_size, label=c))

        for i, b in enumerate(self.buttons):
            row = i // 2
            col = i % 2
            button_sizer.Add(self.buttons[i], pos=(row, col))

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.AddSpacer(10)
        sizer.Add(msg_lbl, 1, wx.ALIGN_CENTER)
        sizer.AddSpacer(20)
        sizer.Add(button_sizer, 1, wx.ALIGN_CENTER)
        sizer.AddSpacer(10)

        self.Bind(wx.EVT_BUTTON, self.button_pressed)
        self.Bind(wx.EVT_CLOSE, self.on_close)

        self.SetSizer(sizer)

        self.Show()

    def button_pressed(self, e):
        lbl_pressed = e.GetEventObject().Label
        if lbl_pressed == self.choices[0]:
            quick_search()
        elif lbl_pressed == self.choices[1]:
            detailed_search()
        elif lbl_pressed == self.choices[2]:
            launch_record_viewer()
        elif lbl_pressed == self.choices[3]:
            access_users_list()
        else:
            pass

    def on_close(self, e):
        dlg = wx.MessageDialog(self, "Continue with Close?\n"
                                     "\n"
                                     "All OpenArchive windows will be closed,\n"
                                     "and any unsaved changes will be lost.",
                               style=wx.YES_NO | wx.NO_DEFAULT
                                     | wx.ICON_INFORMATION, caption="Unsaved Changes")
        resp = dlg.ShowModal()
        dlg.Destroy()
        if resp == wx.ID_YES:
            pass
        elif resp == wx.ID_NO:
            return None
        else:
            return None
        print("Closing")
        database_io.clear_cache()
        database_io.conn.close()
        os.kill(os.getpid(), signal.CTRL_C_EVENT)


def quick_search():
    # todo: Write quick search
    # Get user input
    msg = "Enter Search Terms:"
    user_input = easygui.enterbox(msg, __title__ + " - Quick Search")
    if user_input is None:
        pass
    else:
        pass
        # Perform search
        # Display results


def detailed_search():
    pass
    # Get user input.
    # Perform search.
    # Display results.
    # todo: Write detailed search


def launch_record_viewer(r = None):
    # Created Blank Record and loads editor.

    r = database_io.ArchiveRecord()
    r.record_id = "New Record"
    #print(r)
    # r = database_io.get_record_by_id(50)
    record_editor.main(r)


def access_users_list():
    # Access to users list
    user_name = os.environ["USERNAME"]
    bookmarks = database_io.get_user_bookmarks(user_name)
    # Check bookmarks for dead links
    dead_bookmarks = []
    for b in bookmarks:
        test = database_io.get_record_by_id(b)
        if test is None:
            database_io.remove_bookmark(user_name, b)
            dead_bookmarks.append(b)
    for d in dead_bookmarks:
        bookmarks.remove(d)

    #print("Launching")
    record_list_viewer.main("{} - User Bookmarks - {}".format(__title__, user_name.title()), bookmarks)


def main(title):
    app = wx.App(False)
    frame = LaunchPad(None, title)
    app.MainLoop()
    database_io.clear_cache()


if __name__ == "__main__":
    print("PID:",os.getpid())
    print("PPID:",os.getppid())
    main(__title__)
    os.system("TaskKill /PID {}".format(os.getpid()))
else:
    pass
