import wx
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, List
import threading
import subprocess

# Local imports
from translate import _
from nvda import speak
from variables import APP_VERSION
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
from core_paths import is_path_restricted, requires_admin, is_admin

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
        self.current_item = None
        self.item_queue = [] # For batch processing
        self.is_processing = False
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
        
        self.Center()
        
        if len(sys.argv) > 1 and sys.argv[1] != '--register':
            wx.CallAfter(self.handle_dropped_items, sys.argv[1:])
        
        self.Bind(wx.EVT_CLOSE, self.on_close)
        
        self.update_ui_state()
        self.update_history_list()
        
        speak(_("File Locker window ready"))

    def get_program_directory(self) -> Path:
        if getattr(sys, 'frozen', False):
            return Path(sys.executable).parent
        else:
            return Path(__file__).parent

    def init_ui(self):
        # File/Folder selection
        file_box = wx.StaticBox(self.panel, label=_("File/Folder Selection"))
        file_sizer = wx.StaticBoxSizer(file_box, wx.VERTICAL)
        
        file_ctrl_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.path_ctrl = wx.TextCtrl(self.panel, style=wx.TE_READONLY)
        browse_file_btn = wx.Button(self.panel, label=_("Select File..."))
        browse_folder_btn = wx.Button(self.panel, label=_("Select Folder..."))
        browse_file_btn.Bind(wx.EVT_BUTTON, self.on_browse_file)
        browse_folder_btn.Bind(wx.EVT_BUTTON, self.on_browse_folder)
        
        file_ctrl_sizer.Add(self.path_ctrl, 1, wx.EXPAND | wx.RIGHT, 5)
        file_ctrl_sizer.Add(browse_file_btn, 0, wx.RIGHT, 5)
        file_ctrl_sizer.Add(browse_folder_btn, 0)
        
        self.item_info = wx.TextCtrl(
            self.panel,
            style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH2,
            size=(-1, 100)
        )
        
        file_sizer.Add(file_ctrl_sizer, 0, wx.EXPAND | wx.ALL, 5)
        file_sizer.Add(self.item_info, 1, wx.EXPAND | wx.ALL, 5)
        
        # Action buttons
        action_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.process_btn = wx.Button(self.panel, label=_("Lock/Unlock"))
        self.process_btn.Bind(wx.EVT_BUTTON, self.on_process_action)
        action_sizer.Add(self.process_btn, 1, wx.EXPAND)
        
        # History list
        history_box = wx.StaticBox(self.panel, label=_("Recent Items"))
        history_sizer = wx.StaticBoxSizer(history_box, wx.VERTICAL)
        
        self.history_list = wx.ListCtrl(
            self.panel,
            style=wx.LC_REPORT | wx.BORDER_SUNKEN | wx.LC_SINGLE_SEL
        )
        self.history_list.InsertColumn(0, _("Item"), width=200)
        self.history_list.InsertColumn(1, _("Password"), width=150)
        self.history_list.InsertColumn(2, _("Date"), width=150)
        self.history_list.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.on_history_item_activated)
        history_sizer.Add(self.history_list, 1, wx.EXPAND | wx.ALL, 5)
        
        self.main_sizer.Add(file_sizer, 0, wx.EXPAND | wx.ALL, 10)
        self.main_sizer.Add(action_sizer, 0, wx.EXPAND | wx.ALL, 10)
        self.main_sizer.Add(history_sizer, 1, wx.EXPAND | wx.ALL, 10)

    def init_menubar(self):
        menubar = wx.MenuBar()
        file_menu, tools_menu, help_menu = wx.Menu(), wx.Menu(), wx.Menu()
        
        open_file_item = file_menu.Append(wx.ID_OPEN, _("Open &File...\tCtrl+O"))
        open_folder_item = file_menu.Append(wx.ID_ANY, _("Open F&older...\tCtrl+Shift+O"))
        file_menu.AppendSeparator()
        exit_item = file_menu.Append(wx.ID_EXIT, _("E&xit\tAlt+F4"))
        
        settings_item = tools_menu.Append(wx.ID_PREFERENCES, _("&Settings\tCtrl+,"))
        tools_menu.AppendSeparator()
        clear_history_item = tools_menu.Append(wx.ID_ANY, _("Clear Password &History"))
        
        about_item = help_menu.Append(wx.ID_ABOUT, _("&About File Locker"))
        
        menubar.Append(file_menu, _("&File"))
        menubar.Append(tools_menu, _("&Tools"))
        menubar.Append(help_menu, _("&Help"))
        self.SetMenuBar(menubar)
        
        self.Bind(wx.EVT_MENU, self.on_browse_file, open_file_item)
        self.Bind(wx.EVT_MENU, self.on_browse_folder, open_folder_item)
        self.Bind(wx.EVT_MENU, self.on_exit, exit_item)
        self.Bind(wx.EVT_MENU, self.on_settings, settings_item)
        self.Bind(wx.EVT_MENU, self.on_clear_history, clear_history_item)
        self.Bind(wx.EVT_MENU, self.on_about, about_item)

    def SetStatusText(self, text: str):
        super().SetStatusText(text)
        speak(text)

    def setup_drag_drop(self):
        self.SetDropTarget(FileDropTarget(self))

    def can_process_item(self, path: str) -> tuple[bool, str]:
        p = Path(path).resolve()
        if self.program_directory in p.parents or p == self.program_directory:
            return False, _("Cannot lock items in the program directory for safety.")
        
        is_restricted, reason = is_path_restricted(path)
        return not is_restricted, reason

    def update_ui_state(self):
        has_item = bool(self.current_item) and os.path.exists(self.current_item)
        self.process_btn.Enable(has_item and not self.is_processing)
        
        if has_item:
            self.update_item_info()
            op_type = self.encryption.get_operation_type(self.current_item)
            if op_type in ["decrypt_file", "decrypt_folder"]:
                status_text = _("Locked")
            else:
                status_text = _("Unlocked")
            self.SetStatusText(_("Selected: {}. Status: {}.").format(os.path.basename(self.current_item), status_text))
        else:
            self.current_item = None
            self.path_ctrl.SetValue("")
            self.item_info.SetValue("")
            self.SetStatusText(_("Ready"))

    def update_item_info(self):
        if not self.current_item or not os.path.exists(self.current_item):
            self.item_info.SetValue("")
            return
        
        try:
            p = Path(self.current_item)
            stats = os.stat(self.current_item)
            op_type = self.encryption.get_operation_type(self.current_item)
            is_locked = "decrypt" in op_type
            status_text = _('Locked') if is_locked else _('Unlocked')
            
            info = [f"{_('Name')}: {p.name}", f"{_('Location')}: {p.parent}"]
            
            if p.is_dir():
                size = sum(f.stat().st_size for f in p.glob('**/*') if f.is_file())
                info.append(f"{_('Type')}: Folder")
            else:
                size = stats.st_size
                info.append(f"{_('Type')}: {p.suffix[1:].upper() if p.suffix else _('File')}")

            info.extend([
                f"{_('Size')}: {format_file_size(size)}",
                f"{_('Last Modified')}: {datetime.fromtimestamp(stats.st_mtime).strftime('%Y-%m-%d %H:%M:%S')}",
                f"{_('Status')}: {status_text}"
            ])
            
            self.item_info.SetValue("\n".join(info))
            
        except Exception as e:
            self.item_info.SetValue(_("Error reading item info: {}").format(str(e)))

    def update_history_list(self):
        self.history_list.DeleteAllItems()
        self.history_data.clear()
        
        recent_items = self.password_history.get_recent_passwords(
            limit=self.settings.get('max_history_entries')
        )
        
        for index, entry in enumerate(recent_items):
            self.history_list.InsertItem(index, os.path.basename(entry['filepath']))
            self.history_list.SetItem(index, 1, '*' * len(entry['password']))
            date = datetime.fromisoformat(entry['timestamp']).strftime('%Y-%m-%d %H:%M')
            self.history_list.SetItem(index, 2, date)
            self.history_data[index] = entry
            
        for i in range(3): self.history_list.SetColumnWidth(i, wx.LIST_AUTOSIZE_USEHEADER)

    def handle_dropped_items(self, paths: List[str]):
        for path in paths:
            if os.path.exists(path):
                can_process, reason = self.can_process_item(path)
                if can_process:
                    self.item_queue.append(path)
                else:
                    show_error_dialog(self, reason)
            else:
                show_error_dialog(self, _("Item not found: {}").format(path))

        if not self.is_processing and self.item_queue:
            self.process_next_item()

    def process_next_item(self):
        if not self.item_queue:
            self.is_processing = False
            self.update_ui_state()
            show_success_dialog(self, _("All operations completed!"))
            return

        self.is_processing = True
        self.current_item = self.item_queue.pop(0)
        self.path_ctrl.SetValue(self.current_item)
        self.update_ui_state()
        
        # Automatically trigger the action for the new item
        wx.CallAfter(self.on_process_action, None)
        
    def on_browse_file(self, event):
        with wx.FileDialog(
            self, _("Choose a file"),
            defaultDir=self.settings.get('last_directory'),
            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST
        ) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                self.set_current_item(dlg.GetPath())

    def on_browse_folder(self, event):
        with wx.DirDialog(
            self, _("Choose a folder"),
            defaultPath=self.settings.get('last_directory'),
            style=wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST
        ) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                self.set_current_item(dlg.GetPath())
    
    def set_current_item(self, path: str):
        can_process, reason = self.can_process_item(path)
        if not can_process:
            show_error_dialog(self, reason)
            return
        
        self.current_item = path
        self.path_ctrl.SetValue(path)
        if self.settings.get('remember_last_directory'):
            self.settings.set('last_directory', os.path.dirname(path))
        self.update_ui_state()

    def on_process_action(self, event):
        if not self.current_item: return

        op_type = self.encryption.get_operation_type(self.current_item)
        is_encrypt = "encrypt" in op_type
        
        action_word = _("lock") if is_encrypt else _("unlock")
        
        if self.settings.get('confirm_file_operations'):
            msg = _("Are you sure you want to {} '{}'?").format(action_word, os.path.basename(self.current_item))
            if wx.MessageBox(msg, _("Confirm Action"), wx.YES_NO | wx.ICON_QUESTION) != wx.YES:
                if self.is_processing: self.process_next_item() # Continue queue if batch processing
                return
        
        # For decryption, always ask for password
        if not is_encrypt:
            self.show_password_entry_for_unlock()
            return

        # For encryption, check history or show generator/manual entry
        history = self.password_history.get_history_for_file(self.current_item)
        if history:
            password = history[0]['password']
            if wx.MessageBox(_("Use last password for this item?"), _("Use Last Password"), wx.YES_NO | wx.ICON_QUESTION) == wx.YES:
                self.start_operation(password)
                return

        if self.settings.get('default_password_mode') == 'generate':
            self.show_password_generator()
        else:
            self.show_manual_password_entry()
            
    def show_password_generator(self):
        with PasswordGeneratorDialog(self, self.settings) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                self.start_operation(dlg.password)
            elif self.is_processing: self.process_next_item()

    def show_manual_password_entry(self):
        with wx.TextEntryDialog(self, _("Enter password:"), _("Password"), style=wx.TE_PASSWORD) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                password = dlg.GetValue()
                if not password:
                    show_error_dialog(self, _("Password cannot be empty!"))
                    if self.is_processing: self.process_next_item()
                    return
                self.start_operation(password)
            elif self.is_processing: self.process_next_item()
            
    def show_password_entry_for_unlock(self):
        with wx.TextEntryDialog(self, _("Enter password to unlock:"), _("Unlock"), style=wx.TE_PASSWORD) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                self.start_operation(dlg.GetValue())
            elif self.is_processing: self.process_next_item()
                
    def start_operation(self, password: str):
        if not self.current_item or not password:
            if self.is_processing: self.process_next_item()
            return

        # *** NEW: Proactive administrator check ***
        if requires_admin(self.current_item) and not is_admin():
            msg = _("This operation requires administrator privileges. Please restart File Locker as an administrator to proceed.")
            show_error_dialog(self, msg, title=_("Administrator Privileges Required"))
            self.on_operation_complete() # Abort and handle UI state
            return
            
        op_type = self.encryption.get_operation_type(self.current_item)
        op_map = {
            "encrypt_file": (self.encryption.encrypt_file, _("Locking File")),
            "decrypt_file": (self.encryption.decrypt_file, _("Unlocking File")),
            "encrypt_folder": (self.encryption.encrypt_folder, _("Locking Folder")),
            "decrypt_folder": (self.encryption.decrypt_folder, _("Unlocking Folder")),
        }
        
        if op_type not in op_map:
            show_error_dialog(self, _("Unknown operation for the selected item."))
            if self.is_processing: self.process_next_item()
            return
            
        op_func, title = op_map[op_type]
        progress_dlg = ProgressDialog(self, title, f"{title}...")
        progress_dlg.Show()
        
        def operation_thread():
            try:
                original_path = self.current_item
                success, msg = op_func(self.current_item, password, progress_dlg.update)
                wx.CallAfter(progress_dlg.Destroy)
                
                if success:
                    new_path = self.get_new_path(original_path, op_type)
                    wx.CallAfter(self.on_operation_success, original_path, new_path, password, op_type)
                else:
                    wx.CallAfter(self.on_operation_error, op_type, msg)
            except Exception as e:
                wx.CallAfter(progress_dlg.Destroy)
                wx.CallAfter(show_error_dialog, self, _("Operation error: {}").format(e))
                wx.CallAfter(self.on_operation_complete)

        threading.Thread(target=operation_thread).start()
    
    def get_new_path(self, old_path, op_type):
        if op_type == 'encrypt_file': return old_path + '.locked'
        if op_type == 'encrypt_folder': return old_path + '.flka'
        if op_type == 'decrypt_file': return old_path[:-7]
        if op_type == 'decrypt_folder': return old_path[:-5]
        return old_path

    def on_operation_success(self, old_path, new_path, password, op_type):
        is_encrypt = "encrypt" in op_type
        if is_encrypt:
            self.password_history.add_entry(new_path, password)
        
        self.current_item = new_path if os.path.exists(new_path) else None
        
        show_success_dialog(self, _("Operation successful!"))
        
        self.update_history_list()
        self.update_ui_state()
        
        if not is_encrypt and self.settings.get('auto_launch_after_unlock'):
            self.launch_item(new_path)
            
        self.on_operation_complete()

    def on_operation_error(self, op_type: str, error_message: Optional[str] = None):
        is_encrypt = "encrypt" in op_type
        action = _("lock") if is_encrypt else _("unlock")
        base_message = _("Failed to {} item!").format(action)
        
        details = ""
        if error_message:
            if "[WinError 5] Access is denied" in error_message:
                details = _("The file or a file within the folder might be in use by another program, or the application lacks permission to modify it.")
            elif "Incorrect password" in error_message or "corrupted file" in error_message:
                details = _("Please check the password or the file may be corrupted.")
            else:
                details = error_message
        
        if details:
            full_message = f"{base_message}\n\n{_('Reason')}: {details}"
        else:
            full_message = base_message

        show_error_dialog(self, full_message)
        self.on_operation_complete()

    def on_operation_complete(self):
        if self.is_processing:
            wx.CallAfter(self.process_next_item)
        else:
            self.update_ui_state()

    def launch_item(self, path):
        try:
            if sys.platform == 'win32':
                os.startfile(path)
            else:
                opener = 'open' if sys.platform == 'darwin' else 'xdg-open'
                subprocess.call([opener, path])
        except Exception as e:
            show_error_dialog(self, _("Could not open item: {}").format(e))

    def on_history_item_activated(self, event):
        index = event.GetIndex()
        data = self.history_data.get(index)
        if not data: return
        
        path, password = data['filepath'], data['password']
        if not os.path.exists(path):
            show_error_dialog(self, _("Item no longer exists!"))
            self.password_history.remove_file_history(path)
            self.update_history_list()
            return
        
        self.set_current_item(path)
        op_type = self.encryption.get_operation_type(path)
        if "decrypt" in op_type:
            speak(_("Attempting to unlock {} from history.").format(os.path.basename(path)))
            self.start_operation(password)

    def on_settings(self, event):
        with SettingsDialog(self, self.settings) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                ThemeManager.apply_theme(self, self.settings.get('theme'))
                self.update_history_list()
    
    def on_clear_history(self, event):
        if wx.MessageBox(_("Clear all password history? This cannot be undone."), _("Confirm Clear"), wx.YES_NO | wx.ICON_QUESTION) == wx.YES:
            self.password_history.clear_history()
            self.update_history_list()
            show_success_dialog(self, _("Password history cleared."))
    
    def on_about(self, event):
        info = wx.adv.AboutDialogInfo()
        info.SetName(_("File Locker"))
        info.SetVersion(APP_VERSION)
        info.SetDescription(_("A tool to encrypt/decrypt files and folders using AES-256."))
        wx.adv.AboutBox(info)
    
    def on_exit(self, event):
        self.Close()

    def on_close(self, event):
        if self.is_processing:
            if wx.MessageBox(_("An operation is in progress. Are you sure you want to quit?"), _("Confirm Exit"), wx.YES_NO | wx.ICON_WARNING) != wx.YES:
                return
        self.settings.save_settings()
        event.Skip()