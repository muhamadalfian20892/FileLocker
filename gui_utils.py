import wx
import os
from typing import Optional
from pathlib import Path

def create_bold_label(parent, text: str) -> wx.StaticText:
    """Create a bold static text label"""
    label = wx.StaticText(parent, label=text)
    font = label.GetFont()
    font.SetWeight(wx.FONTWEIGHT_BOLD)
    label.SetFont(font)
    return label

def show_error_dialog(parent, message: str, title: str = "Error"):
    """Show error dialog with custom styling"""
    dlg = wx.MessageDialog(
        parent,
        message,
        title,
        wx.OK | wx.ICON_ERROR
    )
    dlg.ShowModal()
    dlg.Destroy()

def show_success_dialog(parent, message: str, title: str = "Success"):
    """Show success dialog with custom styling"""
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
        if len(filenames) > 0:
            self.window.handle_dropped_file(filenames[0])
        return True

class ThemeManager:
    """Manage application themes"""
    THEMES = {
        'default': {
            'background': wx.Colour(255, 255, 255),
            'foreground': wx.Colour(0, 0, 0),
            'accent': wx.Colour(0, 120, 215),
            'success': wx.Colour(0, 158, 115),
            'error': wx.Colour(213, 94, 0),
            'warning': wx.Colour(230, 159, 0)
        },
        'dark': {
            'background': wx.Colour(32, 32, 32),
            'foreground': wx.Colour(255, 255, 255),
            'accent': wx.Colour(0, 120, 215),
            'success': wx.Colour(0, 158, 115),
            'error': wx.Colour(213, 94, 0),
            'warning': wx.Colour(230, 159, 0)
        }
    }
    
    @classmethod
    def apply_theme(cls, window, theme_name: str = 'default'):
        theme = cls.THEMES.get(theme_name, cls.THEMES['default'])
        window.SetBackgroundColour(theme['background'])
        window.SetForegroundColour(theme['foreground'])
        window.Refresh()

class PasswordStrengthMeter(wx.Panel):
    """Password strength indicator"""
    def __init__(self, parent):
        super().__init__(parent)
        self.strength = 0
        self.SetMinSize((100, 5))
        self.Bind(wx.EVT_PAINT, self.on_paint)
    
    def set_strength(self, password: str):
        """Calculate password strength (0-100)"""
        strength = 0
        if len(password) >= 8: strength += 20
        if any(c.isupper() for c in password): strength += 20
        if any(c.islower() for c in password): strength += 20
        if any(c.isdigit() for c in password): strength += 20
        if any(not c.isalnum() for c in password): strength += 20
        
        self.strength = strength
        self.Refresh()
    
    def on_paint(self, event):
        dc = wx.PaintDC(self)
        width, height = self.GetSize()
        
        # Draw background
        dc.SetBrush(wx.Brush(wx.Colour(200, 200, 200)))
        dc.DrawRectangle(0, 0, width, height)
        
        # Draw strength bar
        if self.strength > 0:
            color = wx.Colour(
                int(255 * (100 - self.strength) / 100),
                int(255 * self.strength / 100),
                0
            )
            dc.SetBrush(wx.Brush(color))
            dc.DrawRectangle(0, 0, int(width * self.strength / 100), height)