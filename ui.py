# ui.py
import wx
import os

# Import our custom modules
from translate import _
from variables import APP_VERSION
from paths import CONFIG_FILE
import core
from gui_dialogs import SettingsDialog 

class FileLockerFrame(wx.Frame):
    def __init__(self, settings):
        super().__init__(None, title=_("FileLocker") + f" v{APP_VERSION}", size=(500, 250))
        self.settings = settings # gotta have this now
        self.SetMinSize((450, 240))
        
        self.setup_ui()
        self.Center()
        self.Show()

    def setup_ui(self):
        self.create_menu()
        self.create_statusbar()
        
        panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        file_box = wx.StaticBox(panel, label=_("Select File"))
        file_sizer = wx.StaticBoxSizer(file_box, wx.HORIZONTAL)
        
        self.file_path_ctrl = wx.TextCtrl(panel, style=wx.TE_READONLY)
        browse_button = wx.Button(panel, label=_("Browse..."))
        
        file_sizer.Add(self.file_path_ctrl, 1, wx.EXPAND | wx.ALL, 5)
        file_sizer.Add(browse_button, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT | wx.TOP | wx.BOTTOM, 5)

        pass_box = wx.StaticBox(panel, label=_("Enter Password"))
        pass_sizer = wx.StaticBoxSizer(pass_box, wx.VERTICAL)
        
        self.password_ctrl = wx.TextCtrl(panel, style=wx.TE_PASSWORD)
        pass_sizer.Add(self.password_ctrl, 1, wx.EXPAND | wx.ALL, 5)

        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        encrypt_button = wx.Button(panel, label=_("Encrypt"))
        decrypt_button = wx.Button(panel, label=_("Decrypt"))
        
        button_sizer.Add(encrypt_button, 1, wx.EXPAND | wx.RIGHT, 5)
        button_sizer.Add(decrypt_button, 1, wx.EXPAND | wx.LEFT, 5)

        main_sizer.Add(file_sizer, 0, wx.EXPAND | wx.ALL, 10)
        main_sizer.Add(pass_sizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)
        main_sizer.Add(button_sizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)

        panel.SetSizer(main_sizer)

        self.Bind(wx.EVT_BUTTON, self.on_browse, browse_button)
        self.Bind(wx.EVT_BUTTON, self.on_encrypt, encrypt_button)
        self.Bind(wx.EVT_BUTTON, self.on_decrypt, decrypt_button)
    
    def create_menu(self):
        menubar = wx.MenuBar()

        settings_menu = wx.Menu()
        
        # new, cleaner settings menu item
        settings_item = settings_menu.Append(wx.ID_PREFERENCES, _("Settings..."), _("Open application settings"))
        self.Bind(wx.EVT_MENU, self.on_settings, settings_item)
        
        settings_menu.AppendSeparator()
        exit_item = settings_menu.Append(wx.ID_EXIT, _("Exit"))

        help_menu = wx.Menu()
        about_item = help_menu.Append(wx.ID_ABOUT, _("About..."))

        menubar.Append(settings_menu, _("Settings"))
        menubar.Append(help_menu, _("Help"))
        self.SetMenuBar(menubar)
        
        self.Bind(wx.EVT_MENU, lambda e: self.Close(), exit_item)
        self.Bind(wx.EVT_MENU, self.on_about, about_item)

    def create_statusbar(self):
        self.statusbar = self.CreateStatusBar(1)
        self.statusbar.SetStatusText(_("Ready"))
    
    def on_settings(self, event):
        # opens the settings dialog
        dlg = SettingsDialog(self, self.settings)
        dlg.ShowModal()
        dlg.Destroy()

    def on_about(self, event):
        about_msg = f"FileLocker v{APP_VERSION}\n\n{_('A simple tool to encrypt and decrypt files.')}"
        wx.MessageBox(about_msg, _("About FileLocker"), wx.OK | wx.ICON_INFORMATION)

    def on_browse(self, event):
        with wx.FileDialog(self, _("Select a file"), wildcard=_("All files (*.*)|*.*"),
                           style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as file_dialog:
            if file_dialog.ShowModal() == wx.ID_CANCEL:
                return
            
            pathname = file_dialog.GetPath()
            self.file_path_ctrl.SetValue(pathname)
            self.statusbar.SetStatusText(_("File selected: {}").format(os.path.basename(pathname)))

    def _execute_action(self, action_func):
        file_path = self.file_path_ctrl.GetValue()
        password = self.password_ctrl.GetValue()

        if not file_path or not password:
            wx.MessageBox(_("File path and password are required."), _("Error"), wx.OK | wx.ICON_ERROR)
            return

        try:
            action_func(file_path, password)
            self.statusbar.SetStatusText(_("Operation successful!"))
            wx.MessageBox(_("Operation completed successfully."), _("Success"), wx.OK | wx.ICON_INFORMATION)
            self.file_path_ctrl.SetValue("")
            self.password_ctrl.SetValue("")
        except Exception as e:
            self.statusbar.SetStatusText(_("Operation failed!"))
            wx.MessageBox(str(e), _("Error"), wx.OK | wx.ICON_ERROR)

    def on_encrypt(self, event):
        self._execute_action(core.encrypt_file)

    def on_decrypt(self, event):
        self._execute_action(core.decrypt_file)