import wx
import wx.adv
import string
import random
import os
from datetime import datetime

from gui_utils import create_bold_label, PasswordStrengthMeter, ViewPasswordToggleButton
from translate import _
from nvda import speak

# my custom stuff
from variables import SUPPORTED_LANGUAGES
from paths import CONFIG_FILE

class PasswordGeneratorDialog(wx.Dialog):
    def __init__(self, parent, settings):
        super().__init__(
            parent,
            title=_("Password Manager"),
            size=(500, 500),
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER
        )
        self.settings = settings
        self.password = ""
        self.init_ui()
        self.Center()
        speak(_("Password Manager dialog"))
    
    def init_ui(self):
        panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Password entry area
        display_box = wx.StaticBox(panel, label=_("Password"))
        display_sizer = wx.StaticBoxSizer(display_box, wx.VERTICAL)
        
        # Password input with toggle
        pwd_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.password_ctrl = wx.TextCtrl(panel, style=wx.TE_PASSWORD, size=(-1, 30))
        self.password_ctrl.SetFont(
            wx.Font(12, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        )
        self.toggle_button = ViewPasswordToggleButton(panel, self.password_ctrl)
        
        pwd_sizer.Add(self.password_ctrl, 1, wx.EXPAND | wx.ALL, 5) # FIX: Removed wx.ALIGN_CENTER_VERTICAL
        pwd_sizer.Add(self.toggle_button, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 5)
        display_sizer.Add(pwd_sizer, 0, wx.EXPAND | wx.ALL, 5)

        self.password_ctrl.Bind(wx.EVT_TEXT, self.on_password_change)
        
        # Password strength meter
        self.strength_meter = PasswordStrengthMeter(panel)
        display_sizer.Add(self.strength_meter, 0, wx.EXPAND | wx.ALL, 5)
        
        # Generation options
        options_box = wx.StaticBox(panel, label=_("Password Generation Options"))
        options_sizer = wx.StaticBoxSizer(options_box, wx.VERTICAL)
        
        # Length selection with radio buttons
        length_label = wx.StaticText(panel, label=_("Password Length:"))
        self.length_choices = self.settings.get('password_lengths')
        self.length_radios = []
        length_sizer = wx.BoxSizer(wx.HORIZONTAL)
        length_sizer.Add(length_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
        
        for length in self.length_choices:
            radio = wx.RadioButton(panel, label=str(length))
            self.length_radios.append(radio)
            length_sizer.Add(radio, 0, wx.RIGHT, 10)
        
        default_length = self.settings.get('default_password_length')
        default_index = self.length_choices.index(default_length) if default_length in self.length_choices else 0
        self.length_radios[default_index].SetValue(True)
        
        options_sizer.Add(length_sizer, 0, wx.ALL, 5)
        
        # Character types
        types_sizer = wx.GridSizer(2, 2, 5, 5)
        self.use_upper = wx.CheckBox(panel, label=_("Uppercase (A-Z)"))
        self.use_lower = wx.CheckBox(panel, label=_("Lowercase (a-z)"))
        self.use_digits = wx.CheckBox(panel, label=_("Digits (0-9)"))
        self.use_symbols = wx.CheckBox(panel, label=_("Symbols (!@#$%^&*)"))
        
        for ctrl, setting_key in zip([self.use_upper, self.use_lower, self.use_digits, self.use_symbols],
                                     ['use_uppercase', 'use_lowercase', 'use_digits', 'use_symbols']):
            types_sizer.Add(ctrl, 0)
            ctrl.SetValue(self.settings.get(setting_key))
        
        options_sizer.Add(types_sizer, 0, wx.ALL | wx.EXPAND, 5)
        
        # Buttons
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        generate_btn = wx.Button(panel, label=_("Generate New Password"))
        generate_btn.Bind(wx.EVT_BUTTON, self.on_generate)
        
        copy_btn = wx.Button(panel, label=_("Copy to Clipboard"))
        copy_btn.Bind(wx.EVT_BUTTON, self.on_copy)
        
        use_btn = wx.Button(panel, wx.ID_OK, label=_("Use This Password"))
        cancel_btn = wx.Button(panel, wx.ID_CANCEL, label=_("Cancel"))
        
        btn_sizer.Add(generate_btn, 1, wx.ALL, 5)
        btn_sizer.Add(copy_btn, 1, wx.ALL, 5)
        btn_sizer.AddStretchSpacer()
        btn_sizer.Add(use_btn, 1, wx.ALL, 5)
        btn_sizer.Add(cancel_btn, 1, wx.ALL, 5)
        
        self.Bind(wx.EVT_BUTTON, self.on_use_password, id=wx.ID_OK)
        
        main_sizer.Add(display_sizer, 0, wx.EXPAND | wx.ALL, 10)
        main_sizer.Add(options_sizer, 0, wx.EXPAND | wx.ALL, 10)
        main_sizer.Add(btn_sizer, 0, wx.EXPAND | wx.ALL, 10)
        
        panel.SetSizer(main_sizer)
        self.on_generate(None)

    def on_password_change(self, event):
        password = self.toggle_button.get_value()
        self.strength_meter.set_strength(password)
        event.Skip()

    def on_use_password(self, event):
        self.password = self.toggle_button.get_value()
        if not self.password:
            show_error_dialog(self, _("Password cannot be empty!"))
            return
        self.EndModal(wx.ID_OK)

    def on_generate(self, event):
        selected_length = 16
        for radio, length in zip(self.length_radios, self.length_choices):
            if radio.GetValue():
                selected_length = length
                break
        
        chars = ""
        if self.use_upper.GetValue(): chars += string.ascii_uppercase
        if self.use_lower.GetValue(): chars += string.ascii_lowercase
        if self.use_digits.GetValue(): chars += string.digits
        if self.use_symbols.GetValue(): chars += string.punctuation
        
        if not chars:
            show_error_dialog(self, _("Please select at least one character type!"))
            return
        
        generated_password = ''.join(random.choice(chars) for _ in range(selected_length))
        self.toggle_button.set_value(generated_password)
        self.strength_meter.set_strength(generated_password)
    
    def on_copy(self, event):
        password_to_copy = self.toggle_button.get_value()
        if wx.TheClipboard.Open():
            wx.TheClipboard.SetData(wx.TextDataObject(password_to_copy))
            wx.TheClipboard.Close()
            msg = _("Password copied to clipboard!")
            speak(msg)
            wx.MessageBox(msg, _("Success"), wx.OK | wx.ICON_INFORMATION)

class ProgressDialog(wx.Dialog):
    def __init__(self, parent, title: str, message: str):
        super().__init__(
            parent,
            title=title,
            size=(400, 150),
            style=wx.DEFAULT_DIALOG_STYLE & ~wx.CLOSE_BOX
        )
        self.init_ui(message)
        speak(message)
    
    def init_ui(self, message: str):
        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)
        
        self.message = wx.StaticText(panel, label=message)
        vbox.Add(self.message, 0, wx.ALL | wx.EXPAND, 10)
        
        self.gauge = wx.Gauge(panel, range=100, size=(350, 25))
        vbox.Add(self.gauge, 0, wx.ALL | wx.EXPAND, 10)
        
        self.status = wx.StaticText(panel, label="0%")
        vbox.Add(self.status, 0, wx.ALL | wx.ALIGN_CENTER, 5)
        
        panel.SetSizer(vbox)
        self.Center()
    
    def update(self, value: float, status_text: str = None):
        wx.CallAfter(self._do_update, value, status_text)
    
    def _do_update(self, value: float, status_text: str = None):
        val_int = int(value)
        self.gauge.SetValue(val_int)
        
        if status_text is None:
            status_text = f"{val_int}%"
        self.status.SetLabel(status_text)
        
        if val_int == 100:
            speak(_("Completed"))

class SettingsDialog(wx.Dialog):
    def __init__(self, parent, settings):
        super().__init__(
            parent,
            title=_("Settings"),
            size=(500, 650),
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER
        )
        self.settings = settings
        
        self.original_lang = "en"
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    the_saved_lang = f.read().strip()
                    if the_saved_lang:
                        self.original_lang = the_saved_lang
            except:
                pass

        self.init_ui()
        speak(_("Settings dialog"))
    
    def init_ui(self):
        panel = wx.Panel(self)
        notebook = wx.Notebook(panel)
        
        general_panel = self.create_general_panel(notebook)
        notebook.AddPage(general_panel, _("General"))
        
        password_panel = self.create_password_panel(notebook)
        notebook.AddPage(password_panel, _("Password"))
        
        security_panel = self.create_security_panel(notebook)
        notebook.AddPage(security_panel, _("Security"))
        
        accessibility_panel = self.create_accessibility_panel(notebook)
        notebook.AddPage(accessibility_panel, _("Accessibility"))
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(notebook, 1, wx.EXPAND | wx.ALL, 5)
        
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        save_btn = wx.Button(panel, wx.ID_OK, _("Save"))
        cancel_btn = wx.Button(panel, wx.ID_CANCEL, _("Cancel"))
        defaults_btn = wx.Button(panel, label=_("Reset to Defaults"))
        
        btn_sizer.Add(defaults_btn, 0, wx.ALL, 5)
        btn_sizer.AddStretchSpacer()
        btn_sizer.Add(save_btn, 0, wx.ALL, 5)
        btn_sizer.Add(cancel_btn, 0, wx.ALL, 5)
        
        sizer.Add(btn_sizer, 0, wx.EXPAND | wx.ALL, 5)
        
        save_btn.Bind(wx.EVT_BUTTON, self.on_save)
        defaults_btn.Bind(wx.EVT_BUTTON, self.on_reset_defaults)
        
        panel.SetSizer(sizer)
    
    def create_general_panel(self, parent):
        panel = wx.Panel(parent)
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        box = wx.StaticBox(panel, label=_("Interface"))
        box_sizer = wx.StaticBoxSizer(box, wx.VERTICAL)
        
        self.remember_dir = wx.CheckBox(panel, label=_("Remember last directory"))
        self.remember_dir.SetValue(self.settings.get('remember_last_directory'))
        
        self.auto_launch = wx.CheckBox(panel, label=_("Auto-launch files after unlock"))
        self.auto_launch.SetValue(self.settings.get('auto_launch_after_unlock'))
        
        theme_label = wx.StaticText(panel, label=_("Theme:"))
        self.theme_choice = wx.Choice(panel, choices=[_("Default"), _("Dark")])
        self.theme_choice.SetSelection(0 if self.settings.get('theme') == 'default' else 1)
        
        theme_box = wx.BoxSizer(wx.HORIZONTAL)
        theme_box.Add(theme_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        theme_box.Add(self.theme_choice, 0)

        lang_label = wx.StaticText(panel, label=_("Language:"))
        self.the_lang_codes = list(SUPPORTED_LANGUAGES.keys())
        the_lang_names = list(SUPPORTED_LANGUAGES.values())
        self.lang_choice = wx.Choice(panel, choices=the_lang_names)
        
        try:
            current_idx = self.the_lang_codes.index(self.original_lang)
            self.lang_choice.SetSelection(current_idx)
        except ValueError:
            self.lang_choice.SetSelection(0) 
        
        lang_box = wx.BoxSizer(wx.HORIZONTAL)
        lang_box.Add(lang_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        lang_box.Add(self.lang_choice, 0)
        
        box_sizer.Add(self.remember_dir, 0, wx.ALL, 5)
        box_sizer.Add(self.auto_launch, 0, wx.ALL, 5)
        box_sizer.Add(theme_box, 0, wx.ALL, 5)
        box_sizer.Add(lang_box, 0, wx.ALL, 5)
        
        sizer.Add(box_sizer, 0, wx.EXPAND | wx.ALL, 5)
        panel.SetSizer(sizer)
        return panel
    
    def create_password_panel(self, parent):
        panel = wx.Panel(parent)
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        box = wx.StaticBox(panel, label=_("Password Generation"))
        box_sizer = wx.StaticBoxSizer(box, wx.VERTICAL)
        
        mode_box = wx.BoxSizer(wx.HORIZONTAL)
        mode_label = wx.StaticText(panel, label=_("Default password mode:"))
        self.pwd_mode = wx.Choice(panel, choices=[_("Generate Password"), _("Manual Entry")])
        self.pwd_mode.SetSelection(0 if self.settings.get('default_password_mode') == 'generate' else 1)
        
        mode_box.Add(mode_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        mode_box.Add(self.pwd_mode, 0)
        
        length_box = wx.BoxSizer(wx.HORIZONTAL)
        length_label = wx.StaticText(panel, label=_("Default password length:"))
        self.pwd_length = wx.Choice(panel, choices=[str(x) for x in self.settings.get('password_lengths')])
        current_length = self.settings.get('default_password_length')
        self.pwd_length.SetSelection(self.settings.get('password_lengths').index(current_length))
        
        length_box.Add(length_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        length_box.Add(self.pwd_length, 0)
        
        box_sizer.Add(mode_box, 0, wx.ALL, 5)
        box_sizer.Add(length_box, 0, wx.ALL, 5)
        
        sizer.Add(box_sizer, 0, wx.EXPAND | wx.ALL, 5)
        panel.SetSizer(sizer)
        return panel
    
    def create_security_panel(self, parent):
        panel = wx.Panel(parent)
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        box = wx.StaticBox(panel, label=_("Security"))
        box_sizer = wx.StaticBoxSizer(box, wx.VERTICAL)
        
        self.confirm_ops = wx.CheckBox(panel, label=_("Confirm file operations"))
        self.confirm_ops.SetValue(self.settings.get('confirm_file_operations'))
        
        self.show_strength = wx.CheckBox(panel, label=_("Show password strength meter"))
        self.show_strength.SetValue(self.settings.get('show_password_strength'))
        
        history_label = wx.StaticText(panel, label=_("Maximum password history entries:"))
        self.max_history = wx.SpinCtrl(panel, min=0, max=100)
        self.max_history.SetValue(self.settings.get('max_history_entries'))
        
        history_box = wx.BoxSizer(wx.HORIZONTAL)
        history_box.Add(history_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        history_box.Add(self.max_history, 0)
        
        box_sizer.Add(self.confirm_ops, 0, wx.ALL, 5)
        box_sizer.Add(self.show_strength, 0, wx.ALL, 5)
        box_sizer.Add(history_box, 0, wx.ALL, 5)
        
        clear_btn = wx.Button(panel, label=_("Clear Password History"))
        clear_btn.Bind(wx.EVT_BUTTON, self.on_clear_history)
        
        sizer.Add(box_sizer, 0, wx.EXPAND | wx.ALL, 5)
        sizer.Add(clear_btn, 0, wx.ALL, 5)
        
        panel.SetSizer(sizer)
        return panel

    def create_accessibility_panel(self, parent):
        panel = wx.Panel(parent)
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        box = wx.StaticBox(panel, label=_("Screen Reader (NVDA)"))
        box_sizer = wx.StaticBoxSizer(box, wx.VERTICAL)
        
        self.nvda_enabled = wx.CheckBox(panel, label=_("Enable NVDA Support"))
        self.nvda_enabled.SetValue(self.settings.get('nvda_enabled'))
        
        verbosity_label = wx.StaticText(panel, label=_("Verbosity Level:"))
        self.verbosity_choices = [_("Quiet"), _("Default"), _("Verbose")]
        self.verbosity_keys = ["quiet", "default", "verbose"]
        self.nvda_verbosity = wx.Choice(panel, choices=self.verbosity_choices)
        
        current_verbosity = self.settings.get('nvda_verbosity')
        try:
            current_idx = self.verbosity_keys.index(current_verbosity)
            self.nvda_verbosity.SetSelection(current_idx)
        except ValueError:
            self.nvda_verbosity.SetSelection(1)
        
        verbosity_box = wx.BoxSizer(wx.HORIZONTAL)
        verbosity_box.Add(verbosity_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        verbosity_box.Add(self.nvda_verbosity, 0)
        
        box_sizer.Add(self.nvda_enabled, 0, wx.ALL, 5)
        box_sizer.Add(verbosity_box, 0, wx.ALL, 5)
        
        sizer.Add(box_sizer, 0, wx.EXPAND | wx.ALL, 5)
        panel.SetSizer(sizer)
        return panel
    
    def on_save(self, event):
        selected_idx = self.lang_choice.GetSelection()
        new_code = self.the_lang_codes[selected_idx]
        
        if new_code != self.original_lang:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                f.write(new_code)
            
            msg = _("Please restart the application for the language change to take effect.")
            speak(msg)
            wx.MessageBox(
                msg,
                _("Restart Required"),
                wx.OK | wx.ICON_INFORMATION
            )
            self.original_lang = new_code
        
        self.settings.set('remember_last_directory', self.remember_dir.GetValue())
        self.settings.set('auto_launch_after_unlock', self.auto_launch.GetValue())
        self.settings.set('theme', 'dark' if self.theme_choice.GetSelection() == 1 else 'default')
        self.settings.set('default_password_mode', 'manual' if self.pwd_mode.GetSelection() == 1 else 'generate')
        self.settings.set('default_password_length', int(self.pwd_length.GetString(self.pwd_length.GetSelection())))
        self.settings.set('confirm_file_operations', self.confirm_ops.GetValue())
        self.settings.set('show_password_strength', self.show_strength.GetValue())
        self.settings.set('max_history_entries', self.max_history.GetValue())
        self.settings.set('nvda_enabled', self.nvda_enabled.GetValue())
        selected_verbosity_idx = self.nvda_verbosity.GetSelection()
        self.settings.set('nvda_verbosity', self.verbosity_keys[selected_verbosity_idx])
        
        speak(_("Settings saved."))
        self.EndModal(wx.ID_OK)
    
    def on_reset_defaults(self, event):
        msg = _("Are you sure you want to reset all settings to defaults?")
        title = _("Confirm Reset")
        speak(f"{title}. {msg}")
        if wx.MessageBox(
            msg, title,
            wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION
        ) == wx.YES:
            self.settings.reset_to_defaults()
            speak(_("Settings reset to defaults."))
            self.Close()
    
    def on_clear_history(self, event):
        msg = _("Are you sure you want to clear all password history?")
        title = _("Confirm Clear History")
        speak(f"{title}. {msg}")
        if wx.MessageBox(
            msg, title,
            wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION
        ) == wx.YES:
            from core_history import PasswordHistory
            history = PasswordHistory(self.settings.get('max_history_entries'))
            history.clear_history()
            success_msg = _("Password history cleared successfully!")
            speak(success_msg)
            wx.MessageBox(
                success_msg,
                _("Success"),
                wx.OK | wx.ICON_INFORMATION
            )