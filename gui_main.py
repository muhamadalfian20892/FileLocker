import wx
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional
import threading

# Local imports
from translate import _
from gui_utils import (
    create_bold_label,
    show_error_dialog,
    show_success_dialog,
    format_file_size,
    FileDropTarget,
    ThemeManager
)
from gui_dialogs import PasswordGeneratorDialog, ProgressDialog, SettingsDialog
from core_history import PasswordHistory
from core_encryption import Encryption
from core_paths import is_path_restricted

class MainWindow(wx.Frame):
    def __init__(self, settings):
        super().__init__(
            parent=None,
            title=_("File Locker"),
            size=(800, 600),
            style=wx.DEFAULT_FRAME_STYLE | wx.RESIZE_BORDER
        )
        
        self.settings = settings
        self.encryption = Encryption()
        self.password_history = PasswordHistory(self.settings.get('max_history_entries'))
        self.current_file = None
        self.program_directory = self.get_program_directory()
        self.history_data = {}
        
        self.panel = wx.Panel(self)
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        self.init_ui()
        self.init_menubar()
        self.setup_drag_drop()
        
        self.panel.SetSizer(self.main_sizer)
        ThemeManager.apply_theme(self, self.settings.get('theme'))
        
        self.CreateStatusBar()
        self.SetStatusText(_("Ready"))
        
        self.Center()
        
        if len(sys.argv) > 1 and sys.argv[1] != '--register':
            wx.CallAfter(self.handle_dropped_file, sys.argv[1])
        
        self.Bind(wx.EVT_CLOSE, self.on_close)
        
        self.update_ui_state()
        self.update_history_list()

    def get_program_directory(self) -> Path:
        if getattr(sys, 'frozen', False):
            return Path(sys.executable).parent
        else:
            return Path(__file__).parent

    def init_ui(self):
        file_box = wx.StaticBox(self.panel, label=_("File Selection"))
        file_sizer = wx.StaticBoxSizer(file_box, wx.VERTICAL)
        
        file_ctrl_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.file_path = wx.TextCtrl(self.panel, style=wx.TE_READONLY)
        browse_btn = wx.Button(self.panel, label=_("Browse..."))
        browse_btn.Bind(wx.EVT_BUTTON, self.on_browse)
        
        file_ctrl_sizer.Add(self.file_path, 1, wx.EXPAND | wx.RIGHT, 5)
        file_ctrl_sizer.Add(browse_btn, 0)
        
        self.file_info = wx.TextCtrl(
            self.panel,
            style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH2,
            size=(-1, 100)
        )
        
        file_sizer.Add(file_ctrl_sizer, 0, wx.EXPAND | wx.ALL, 5)
        file_sizer.Add(self.file_info, 1, wx.EXPAND | wx.ALL, 5)
        
        action_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.lock_btn = wx.Button(self.panel, label=_("Lock File"))
        self.unlock_btn = wx.Button(self.panel, label=_("Unlock File"))
        
        self.lock_btn.Bind(wx.EVT_BUTTON, self.on_lock)
        self.unlock_btn.Bind(wx.EVT_BUTTON, self.on_unlock)
        
        action_sizer.Add(self.lock_btn, 1, wx.EXPAND | wx.RIGHT, 5)
        action_sizer.Add(self.unlock_btn, 1, wx.EXPAND)
        
        history_box = wx.StaticBox(self.panel, label=_("Recent Files"))
        history_sizer = wx.StaticBoxSizer(history_box, wx.VERTICAL)
        
        self.history_list = wx.ListCtrl(
            self.panel,
            style=wx.LC_REPORT | wx.BORDER_SUNKEN | wx.LC_SINGLE_SEL
        )
        self.history_list.InsertColumn(0, _("File"), width=200)
        self.history_list.InsertColumn(1, _("Password"), width=150)
        self.history_list.InsertColumn(2, _("Date"), width=150)
        
        self.history_list.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.on_history_item_activated)
        
        history_sizer.Add(self.history_list, 1, wx.EXPAND | wx.ALL, 5)
        
        self.main_sizer.Add(file_sizer, 0, wx.EXPAND | wx.ALL, 10)
        self.main_sizer.Add(action_sizer, 0, wx.EXPAND | wx.ALL, 10)
        self.main_sizer.Add(history_sizer, 1, wx.EXPAND | wx.ALL, 10)

    def init_menubar(self):
        menubar = wx.MenuBar()
        
        file_menu = wx.Menu()
        open_item = file_menu.Append(wx.ID_OPEN, _("&Open\tCtrl+O"))
        file_menu.AppendSeparator()
        exit_item = file_menu.Append(wx.ID_EXIT, _("E&xit\tAlt+F4"))
        
        tools_menu = wx.Menu()
        settings_item = tools_menu.Append(wx.ID_PREFERENCES, _("&Settings\tCtrl+,"))
        tools_menu.AppendSeparator()
        clear_history_item = tools_menu.Append(wx.ID_ANY, _("Clear Password &History"))
        
        help_menu = wx.Menu()
        about_item = help_menu.Append(wx.ID_ABOUT, _("&About File Locker"))
        
        menubar.Append(file_menu, _("&File"))
        menubar.Append(tools_menu, _("&Tools"))
        menubar.Append(help_menu, _("&Help"))
        
        self.SetMenuBar(menubar)
        
        self.Bind(wx.EVT_MENU, self.on_browse, open_item)
        self.Bind(wx.EVT_MENU, self.on_exit, exit_item)
        self.Bind(wx.EVT_MENU, self.on_settings, settings_item)
        self.Bind(wx.EVT_MENU, self.on_clear_history, clear_history_item)
        self.Bind(wx.EVT_MENU, self.on_about, about_item)

    def setup_drag_drop(self):
        drop_target = FileDropTarget(self)
        self.SetDropTarget(drop_target)

    def is_file_in_program_directory(self, filepath: str) -> bool:
        try:
            file_path = Path(filepath).resolve()
            return self.program_directory in file_path.parents or file_path == self.program_directory
        except Exception:
            return False

    def can_lock_file(self, filepath: str) -> tuple[bool, str]:
        if self.is_file_in_program_directory(filepath):
            return False, (
                _("Cannot lock files in the program directory:\n{}\n\nThis is a safety measure to keep the program files secure.").format(self.program_directory)
            )
        
        is_restricted, reason = is_path_restricted(filepath)
        if is_restricted:
            return False, reason
        
        return True, ""

    def update_ui_state(self):
        has_file = bool(self.current_file)
        is_locked = self.is_file_locked() if has_file else False
        
        self.lock_btn.Enable(has_file and not is_locked)
        self.unlock_btn.Enable(has_file and is_locked)
        
        if has_file:
            self.update_file_info()
            self.SetStatusText(_("Selected: {}").format(self.current_file))
        else:
            self.SetStatusText(_("Ready"))

    def update_file_info(self):
        if not self.current_file or not os.path.exists(self.current_file):
            self.file_info.SetValue("")
            return
        
        try:
            stats = os.stat(self.current_file)
            file_path = Path(self.current_file)
            
            status_text = _('Locked') if self.is_file_locked() else _('Unlocked')
            
            info = [
                f"{_('Filename')}: {file_path.name}",
                f"{_('Location')}: {file_path.parent}",
                f"{_('Size')}: {format_file_size(stats.st_size)}",
                f"{_('Last Modified')}: {datetime.fromtimestamp(stats.st_mtime).strftime('%Y-%m-%d %H:%M:%S')}",
                f"{_('Status')}: {status_text}",
                f"{_('Type')}: {file_path.suffix[1:].upper() if file_path.suffix else _('No extension')}"
            ]
            
            self.file_info.SetValue("\n".join(info))
            
            start = self.file_info.GetValue().find(f"{_('Status')}: ")
            if start != -1:
                self.file_info.SetStyle(
                    start, 
                    start + len(f"{_('Status')}: {status_text}"), 
                    wx.TextAttr(
                        wx.RED if self.is_file_locked() else wx.GREEN,
                        wx.NullColour,
                        wx.Font(
                            self.file_info.GetFont().GetPointSize(),
                            wx.FONTFAMILY_DEFAULT,
                            wx.FONTSTYLE_NORMAL,
                            wx.FONTWEIGHT_BOLD
                        )
                    )
                )
            
        except Exception as e:
            self.file_info.SetValue(_("Error reading file info: {}").format(str(e)))

    def update_history_list(self):
        self.history_list.DeleteAllItems()
        self.history_data.clear()
        
        recent_passwords = self.password_history.get_recent_passwords(
            limit=self.settings.get('max_history_entries')
        )
        
        for entry in recent_passwords:
            index = self.history_list.GetItemCount()
            self.history_list.InsertItem(index, os.path.basename(entry['filepath']))
            
            masked_password = '*' * len(entry['password'])
            self.history_list.SetItem(index, 1, masked_password)
            
            date = datetime.fromisoformat(entry['timestamp']).strftime('%Y-%m-%d %H:%M')
            self.history_list.SetItem(index, 2, date)
            
            self.history_data[index] = {
                'filepath': entry['filepath'],
                'password': entry['password']
            }
            self.history_list.SetItemData(index, index)
        
        for i in range(3):
            self.history_list.SetColumnWidth(i, wx.LIST_AUTOSIZE_USEHEADER)

    def is_file_locked(self) -> bool:
        if not self.current_file or not os.path.exists(self.current_file):
            return False
        try:
            with open(self.current_file, 'rb') as f:
                return f.read(4) == b'FLCK'
        except:
            return False

    def handle_dropped_file(self, filepath: str):
        if not os.path.isfile(filepath):
            show_error_dialog(self, _("Please drop a valid file."))
            return
        
        can_lock, reason = self.can_lock_file(filepath)
        if not can_lock:
            show_error_dialog(self, reason)
            return
        
        self.current_file = filepath
        self.file_path.SetValue(filepath)
        self.update_ui_state()
        
        if self.is_file_locked():
            self.on_unlock(None)
        else:
            self.on_lock(None)

    def on_browse(self, event):
        with wx.FileDialog(
            self,
            _("Choose a file"),
            defaultDir=self.settings.get('last_directory'),
            wildcard=_("All files (*.*)|*.*"),
            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST
        ) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return
            
            filepath = fileDialog.GetPath()
            can_lock, reason = self.can_lock_file(filepath)
            if not can_lock:
                show_error_dialog(self, reason)
                return
            
            self.current_file = filepath
            self.file_path.SetValue(filepath)
            
            if self.settings.get('remember_last_directory'):
                self.settings.set('last_directory', os.path.dirname(filepath))
            
            self.update_ui_state()

    def on_lock(self, event):
        if not self.current_file:
            show_error_dialog(self, _("Please select a file first!"))
            return
        
        can_lock, reason = self.can_lock_file(self.current_file)
        if not can_lock:
            show_error_dialog(self, reason)
            return
        
        if self.settings.get('confirm_file_operations'):
            msg = _("Are you sure you want to lock '{}'?").format(os.path.basename(self.current_file))
            if wx.MessageBox(msg, _("Confirm Lock"), wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION) != wx.YES:
                return
        
        recent_passwords = self.password_history.get_history_for_file(self.current_file)
        if recent_passwords:
            password = recent_passwords[0]['password']
            if wx.MessageBox(_("Use last password for this file?"), _("Use Last Password"), wx.YES_NO | wx.ICON_QUESTION) == wx.YES:
                self.start_encryption(password)
                return

        if self.settings.get('default_password_mode') == 'generate':
            self.show_password_generator()
        else:
            self.show_manual_password_entry()

    def show_password_generator(self):
        dlg = PasswordGeneratorDialog(self, self.settings)
        if dlg.ShowModal() == wx.ID_OK:
            self.start_encryption(dlg.password)
        dlg.Destroy()

    def show_manual_password_entry(self):
        dlg = wx.TextEntryDialog(
            self,
            _("Enter password for encryption:"),
            _("Enter Password"),
            style=wx.TE_PASSWORD | wx.OK | wx.CANCEL
        )
        
        if dlg.ShowModal() == wx.ID_OK:
            password = dlg.GetValue()
            if not password:
                show_error_dialog(self, _("Password cannot be empty!"))
                dlg.Destroy()
                return
            self.start_encryption(password)
        dlg.Destroy()

    def start_encryption(self, password: str):
        progress_dlg = ProgressDialog(
            self,
            _("Locking File"),
            _("Locking {}...").format(os.path.basename(self.current_file))
        )
        progress_dlg.Show()
        
        def encrypt_thread():
            try:
                success = self.encryption.encrypt_file(self.current_file, password, progress_dlg.update)
                wx.CallAfter(progress_dlg.Destroy)
                if success:
                    self.password_history.add_entry(self.current_file, password)
                    wx.CallAfter(self.on_encryption_success, password)
                else:
                    wx.CallAfter(self.on_encryption_error)
            except Exception as e:
                wx.CallAfter(progress_dlg.Destroy)
                wx.CallAfter(show_error_dialog, self, _("Encryption error: {}").format(str(e)))
        
        threading.Thread(target=encrypt_thread).start()

    def on_encryption_success(self, password: str):
        msg = _("File has been locked successfully!\n\nFile: {}\nPassword: {}\n\nPlease keep this password safe!").format(self.current_file, password)
        show_success_dialog(self, msg)
        self.update_history_list()
        self.update_ui_state()

    def on_encryption_error(self):
        show_error_dialog(self, _("Failed to lock file!"))

    def on_unlock(self, event):
        if not self.current_file:
            show_error_dialog(self, _("Please select a file first!"))
            return
        
        if not self.is_file_locked():
            show_error_dialog(self, _("This file is not locked!"))
            return
        
        if self.settings.get('confirm_file_operations'):
            msg = _("Are you sure you want to unlock '{}'?").format(os.path.basename(self.current_file))
            if wx.MessageBox(msg, _("Confirm Unlock"), wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION) != wx.YES:
                return
        self.show_unlock_password_entry()

    def show_unlock_password_entry(self):
        dlg = wx.TextEntryDialog(
            self,
            _("Enter password to unlock the file:"),
            _("Enter Password"),
            style=wx.TE_PASSWORD | wx.OK | wx.CANCEL
        )
        
        if dlg.ShowModal() == wx.ID_OK:
            password = dlg.GetValue()
            if not password:
                show_error_dialog(self, _("Password cannot be empty!"))
                dlg.Destroy()
                return
            self.start_decryption(password)
        dlg.Destroy()

    def start_decryption(self, password: str):
        progress_dlg = ProgressDialog(
            self,
            _("Unlocking File"),
            _("Unlocking {}...").format(os.path.basename(self.current_file))
        )
        progress_dlg.Show()
        
        def decrypt_thread():
            try:
                success = self.encryption.decrypt_file(self.current_file, password, progress_dlg.update)
                wx.CallAfter(progress_dlg.Destroy)
                if success:
                    wx.CallAfter(self.on_decryption_success)
                else:
                    wx.CallAfter(self.on_decryption_error)
            except Exception as e:
                wx.CallAfter(progress_dlg.Destroy)
                wx.CallAfter(show_error_dialog, self, _("Decryption error: {}").format(str(e)))
        
        threading.Thread(target=decrypt_thread).start()

    def on_decryption_success(self):
        show_success_dialog(self, _("File has been unlocked successfully!"))
        self.update_ui_state()
        if self.settings.get('auto_launch_after_unlock'):
            self.launch_file()

    def on_decryption_error(self):
        show_error_dialog(self, _("Failed to unlock file!\nPlease check if the password is correct."))

    def launch_file(self):
        try:
            if sys.platform == 'win32':
                os.startfile(self.current_file)
            elif sys.platform == 'darwin':
                os.system(f'open "{self.current_file}"')
            else:
                os.system(f'xdg-open "{self.current_file}"')
        except Exception as e:
            show_error_dialog(self, _("Could not open file: {}").format(str(e)))

    def on_history_item_activated(self, event):
        index = event.GetIndex()
        item_data = self.history_data.get(index)
        if not item_data: return
        filepath = item_data['filepath']
        password = item_data['password']
        
        if not os.path.exists(filepath):
            show_error_dialog(self, _("File no longer exists!"))
            self.update_history_list()
            return
            
        can_lock, reason = self.can_lock_file(filepath)
        if not can_lock:
            show_error_dialog(self, reason)
            return
        
        self.current_file = filepath
        self.file_path.SetValue(filepath)
        self.update_ui_state()
        
        if self.is_file_locked():
            self.start_decryption(password)

    def on_settings(self, event):
        dlg = SettingsDialog(self, self.settings)
        if dlg.ShowModal() == wx.ID_OK:
            ThemeManager.apply_theme(self, self.settings.get('theme'))
            self.update_history_list()
        dlg.Destroy()

    def on_clear_history(self, event):
        if wx.MessageBox(_("Are you sure you want to clear all password history?\nThis action cannot be undone."), _("Confirm Clear History"), wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION) == wx.YES:
            self.password_history.clear_history()
            self.update_history_list()
            show_success_dialog(self, _("Password history has been cleared."))

    def on_about(self, event):
        info = wx.adv.AboutDialogInfo()
        info.SetName(_("File Locker"))
        info.SetVersion("1.2.1")
        description = _("With this program, you can lock/unlock your secret file using a set of passwords.\n\nFeatures:\n- AES-256 encryption,\n- Password generation,\n- Password history,\n- File drag and drop support,\n- Theme support,\n- Auto-launch file after unlock.")
        info.SetDescription(description)
        wx.adv.AboutBox(info)

    def on_exit(self, event):
        self.Close()

    def on_close(self, event):
        self.settings.save_settings()
        event.Skip()