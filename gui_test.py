import wx
import os


class MainWindow(wx.Frame):
    def __init__(self, parent, title):
        wx.Frame.__init__(self, parent, title=title, size=(500, 300))
        self.text_control = wx.TextCtrl(self, style=wx.TE_MULTILINE)

        # Bottom Status Bar
        self.CreateStatusBar()

        # Setting up the menu.
        file_menu = wx.Menu()
        menu_open = file_menu.Append(wx.ID_OPEN, "&Open", " Open file.")
        menu_save = file_menu.Append(wx.ID_SAVE, "&Save", " Save file.")
        menu_about = file_menu.Append(wx.ID_ABOUT, "&About", " Information about this program")
        file_menu.AppendSeparator()
        menu_exit = file_menu.Append(wx.ID_EXIT, "E&xit", " Terminate the program")

        # Creating the menu bar
        menu_bar = wx.MenuBar()
        menu_bar.Append(file_menu, "&File")  # Adding the file_menu to the menu_bar
        self.SetMenuBar(menu_bar)  # Adding the men_bar to the Frame content.

        self.Bind(wx.EVT_MENU, self.on_open, menu_open)
        self.Bind(wx.EVT_MENU, self.on_save, menu_save)
        self.Bind(wx.EVT_MENU, self.on_about, menu_about)
        self.Bind(wx.EVT_MENU, self.on_exit, menu_exit)

        self.Show(True)

    def on_about(self, event):
        # A message dialog box with an OK button. wx.OK is a standard ID in wxWidgets.
        dlg = wx.MessageDialog(self, "A small text editor", "About Sample Editor", wx.OK)
        dlg.ShowModal() # Show it
        dlg.Destroy() # Destroy it when finished.

    def on_exit(self, event):
        self.Close(True) # Close the frame.

    def on_open(self, event):
        """Open a file."""
        self.dir_name = ""
        dlg = wx.FileDialog(self, "Choose a file", self.dir_name, "", "*.*", wx.FD_OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            self.file_name = dlg.GetFilename()
            self.dir_name = dlg.GetDirectory()
            f = open(os.path.join(self.dir_name, self.file_name), "r")
            self.text_control.SetValue(f.read())
            f.close()
        dlg.Destroy()

    def on_save(self, event):
        """Save file."""
        dlg = wx.FileDialog(self, "Choose Save Location", "", "", "*.txt", wx.FD_SAVE)
        if dlg.ShowModal() == wx.ID_OK:
            data = self.text_control.GetValue()
            file_name = dlg.GetFilename()
            dir_name = dlg.GetDirectory()
            with open(os.path.join(dir_name, file_name), "w") as f:
                f.write(data)
        dlg.Destroy()


app = wx.App(False)
frame = MainWindow(None, "My Text Editor")
app.MainLoop()
