import wx
import os
from typing import Optional
from pathlib import Path
from zxcvbn import zxcvbn

# Local imports
from nvda import speak
from translate import _

def create_bold_label(parent, text: str) -> wx.StaticText:
    """Create a bold static text label"""
    label = wx.StaticText(parent, label=text)
    font = label.GetFont()
    font.SetWeight(wx.FONTWEIGHT_BOLD)
    label.SetFont(font)
    return label

def show_error_dialog(parent, message: str, title: Optional[str] = None):
    """Show error dialog with custom styling and screen reader announcement"""
    if title is None:
        title = _("Error")
    
    speak(f"{title}. {message}")
    
    dlg = wx.MessageDialog(
        parent,
        message,
        title,
        wx.OK | wx.ICON_ERROR
    )
    dlg.ShowModal()
    dlg.Destroy()

def show_success_dialog(parent, message: str, title: Optional[str] = None):
    """Show success dialog with custom styling and screen reader announcement"""
    if title is None:
        title = _("Success")
    
    speak(f"{title}. {message}")
    
    dlg = wx.MessageDialog(
        parent,
        message,
        title,
        wx.OK | wx.ICON_INFORMATION
    )
    dlg.ShowModal()
    dlg.Destroy()

def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format"""
    if size_bytes is None: return "N/A"
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.2f} PB"

class FileDropTarget(wx.FileDropTarget):
    """Handle file drag and drop"""
    def __init__(self, window):
        super().__init__()
        self.window = window
    
    def OnDropFiles(self, x: int, y: int, filenames: list) -> bool:
        self.window.handle_dropped_items(filenames)
        return True

class ThemeManager:
    """Manage application themes"""
    THEMES = {
        'default': {
            'background': None,  # Will be resolved to wx.SYS_COLOUR_WINDOW at runtime
            'foreground': None,  # Will be resolved to wx.SYS_COLOUR_WINDOWTEXT at runtime
            'accent': wx.Colour(0, 120, 215),
            'success': wx.Colour(0, 158, 115),
            'error': wx.Colour(213, 94, 0),
            'warning': wx.Colour(230, 159, 0)
        },
        'dark': {
            'background': wx.Colour(32, 32, 32),
            'foreground': wx.Colour(255, 255, 255),
            'accent': wx.Colour(0, 120, 215),
            'success': wx.Colour(40, 167, 69),
            'error': wx.Colour(220, 53, 69),
            'warning': wx.Colour(255, 193, 7)
        }
    }
    
    @classmethod
    def apply_theme_to_window(cls, window, theme):
        """Recursively apply theme to a window and its children."""
        bg_color = theme['background']
        fg_color = theme['foreground']
        
        window.SetBackgroundColour(bg_color)
        window.SetForegroundColour(fg_color)

        # Special handling for certain controls to look better in dark mode
        if isinstance(window, (wx.TextCtrl, wx.Choice, wx.SpinCtrl, wx.ListCtrl)):
            is_dark = bg_color.GetRed() < 128
            window.SetBackgroundColour(wx.Colour(50, 50, 50) if is_dark else wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW))
            window.SetForegroundColour(fg_color)

        if isinstance(window, wx.Button):
            # Let buttons keep their native look in default theme
            is_dark = bg_color.GetRed() < 128
            if is_dark:
                window.SetBackgroundColour(theme['accent'])
                window.SetForegroundColour(wx.Colour(255, 255, 255))
        
        for child in window.GetChildren():
            cls.apply_theme_to_window(child, theme)

    @classmethod
    def apply_theme(cls, window, theme_name: str = 'default'):
        # Get a copy of the theme dict to avoid modifying the class-level one
        theme = cls.THEMES.get(theme_name, cls.THEMES['default']).copy()

        # *** FIX IS HERE ***
        # Resolve the system colors now that the wx.App object exists.
        if theme['background'] is None:
            theme['background'] = wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW)
        if theme['foreground'] is None:
            theme['foreground'] = wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOWTEXT)

        cls.apply_theme_to_window(window, theme)
        window.Refresh()
        
class PasswordStrengthMeter(wx.Panel):
    """Password strength indicator using zxcvbn."""
    STRENGTH_LEVELS = {
        0: (_("Very Weak"), wx.Colour(220, 53, 69)),
        1: (_("Weak"), wx.Colour(240, 173, 78)),
        2: (_("Moderate"), wx.Colour(255, 193, 7)),
        3: (_("Strong"), wx.Colour(92, 184, 92)),
        4: (_("Very Strong"), wx.Colour(40, 167, 69)),
    }

    def __init__(self, parent):
        super().__init__(parent)
        self.score = 0
        self.feedback = ""
        self.SetMinSize((-1, 25))
        self.Bind(wx.EVT_PAINT, self.on_paint)
        
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.gauge = wx.Gauge(self, range=4, style=wx.GA_HORIZONTAL | wx.GA_SMOOTH)
        self.label = wx.StaticText(self, label="")
        
        sizer.Add(self.gauge, 1, wx.EXPAND | wx.RIGHT, 5)
        sizer.Add(self.label, 0, wx.ALIGN_CENTER_VERTICAL)
        self.SetSizer(sizer)

    def set_strength(self, password: str):
        """Calculate and display password strength."""
        if not password:
            self.score = 0
            self.feedback = ""
        else:
            results = zxcvbn(password)
            self.score = results['score']
            # Provide suggestions if strength is low
            if self.score < 3 and results['feedback']['suggestions']:
                self.feedback = f"{results['feedback']['suggestions'][0]}"
            else:
                self.feedback = ""
        self.update_ui()
    
    def update_ui(self):
        wx.CallAfter(self._update_ui)
        
    def _update_ui(self):
        level_text, color = self.STRENGTH_LEVELS[self.score]
        self.gauge.SetValue(self.score)
        
        # On some platforms, setting gauge colour is not supported, but we try anyway
        try:
            self.gauge.SetForegroundColour(color)
        except:
            pass # Ignore if not supported
        
        if self.feedback:
            self.label.SetLabel(f"{level_text} - {self.feedback}")
        else:
            self.label.SetLabel(level_text)
        
        self.GetParent().Layout()

    def on_paint(self, event):
        # We don't need custom drawing anymore, as we're using a wx.Gauge
        event.Skip()

class ViewPasswordToggleButton(wx.Panel):
    """A toggle button to show/hide a password in a TextCtrl."""
    def __init__(self, parent, text_ctrl: wx.TextCtrl):
        super().__init__(parent)
        self.text_ctrl = text_ctrl
        self.shown_ctrl = None
        self.password_visible = False

        # Use stock bitmaps for a more native feel
        self.show_bmp = wx.ArtProvider.GetBitmap(wx.ART_TIP, wx.ART_BUTTON, (16, 16))
        self.hide_bmp = wx.ArtProvider.GetBitmap(wx.ART_WARNING, wx.ART_BUTTON, (16, 16))

        self.button = wx.BitmapButton(self, bitmap=self.show_bmp, style=wx.BORDER_NONE)
        self.button.SetToolTip(_("Show Password"))
        self.button.Bind(wx.EVT_BUTTON, self.on_toggle)
        
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.button, 0, wx.ALIGN_CENTER_VERTICAL)
        self.SetSizer(sizer)
        
    def on_toggle(self, event):
        self.password_visible = not self.password_visible
        
        parent = self.text_ctrl.GetParent()
        sizer = self.text_ctrl.GetContainingSizer()
        
        if not sizer:
            return

        current_value = self.get_value() # Get value before swapping
        
        if self.password_visible:
            if not self.shown_ctrl:
                self.shown_ctrl = wx.TextCtrl(parent)
                self.shown_ctrl.SetFont(self.text_ctrl.GetFont())
                # Find the position of the password text control to insert the new one
                for i, item in enumerate(sizer.GetChildren()):
                    if item.GetWindow() == self.text_ctrl:
                        # FIX: Removed the conflicting wx.ALIGN_CENTER_VERTICAL flag
                        # We also add padding to match the fix from the previous step.
                        sizer.Insert(i, self.shown_ctrl, 1, wx.EXPAND | wx.ALL, 5)
                        break
            
            self.text_ctrl.Hide()
            self.shown_ctrl.SetValue(current_value)
            self.shown_ctrl.SetFocus()
            self.shown_ctrl.Show()
            self.button.SetBitmap(self.hide_bmp)
            self.button.SetToolTip(_("Hide Password"))
        else:
            if self.shown_ctrl:
                self.shown_ctrl.Hide()

            self.text_ctrl.SetValue(current_value)
            self.text_ctrl.Show()
            self.text_ctrl.SetFocus()
            self.button.SetBitmap(self.show_bmp)
            self.button.SetToolTip(_("Show Password"))

        sizer.Layout()

    def get_value(self) -> str:
        """Get the current password value from the active control."""
        if self.password_visible and self.shown_ctrl and self.shown_ctrl.IsShown():
            return self.shown_ctrl.GetValue()
        return self.text_ctrl.GetValue()

    def set_value(self, value: str):
        """Set the password value in both controls."""
        self.text_ctrl.SetValue(value)
        if self.shown_ctrl:
            self.shown_ctrl.SetValue(value)