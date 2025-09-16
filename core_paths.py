import winreg
from pathlib import Path
import os
import sys

from translate import _ # import for reasons

def get_windows_restricted_paths():
    """Get a list of Windows system and restricted paths"""
    restricted_paths = set()
    
    windows_dir = os.environ.get('WINDIR', r'C:\Windows')
    restricted_paths.add(Path(windows_dir).resolve())
    
    program_files = [
        os.environ.get('PROGRAMFILES', r'C:\Program Files'),
        os.environ.get('PROGRAMFILES(X86)', r'C:\Program Files (x86)'),
        os.environ.get('PROGRAMDATA', r'C:\ProgramData'),
    ]
    
    for path in program_files:
        if path:
            restricted_paths.add(Path(path).resolve())
    
    system_paths = [
        Path(windows_dir) / 'System32',
        Path(windows_dir) / 'SysWOW64',
        Path(windows_dir) / 'WinSxS',
    ]
    
    for path in system_paths:
        if path.exists():
            restricted_paths.add(path.resolve())
    
    return restricted_paths

def is_path_restricted(filepath: str) -> tuple[bool, str]:
    """
    Check if a path is in a restricted Windows location
    Returns: (is_restricted, reason)
    """
    try:
        file_path = Path(filepath).resolve()
        restricted_paths = get_windows_restricted_paths()
        
        for restricted_path in restricted_paths:
            if restricted_path in file_path.parents or file_path == restricted_path:
                return True, _("Access to {} directory is restricted").format(restricted_path)
        
        if file_path.suffix.lower() in ['.sys', '.dll']:
            if any(p in file_path.parents for p in restricted_paths):
                return True, _("System files cannot be locked")
        
        return False, ""
        
    except Exception as e:
        return True, _("Error checking path: {}").format(str(e))

def register_shell_integration():
    """Register the application for shell integration"""
    try:
        if getattr(sys, 'frozen', False):
            executable_path = sys.executable
            command = f'"{executable_path}" "%1"'
        else:
            executable_path = sys.executable
            main_script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'main.py'))
            command = f'"{executable_path}" "{main_script_path}" "%1"'
        
        with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, "FileLocker") as key:
            winreg.SetValue(key, "", winreg.REG_SZ, "File Locker")
            winreg.SetValue(key, "DefaultIcon", winreg.REG_SZ, f"{executable_path},0")
            
            with winreg.CreateKey(key, "shell\\open\\command") as cmd_key:
                winreg.SetValue(cmd_key, "", winreg.REG_SZ, command)
        
        with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, "*\\OpenWithList\\FileLocker.exe") as key:
            winreg.SetValue(key, "", winreg.REG_SZ, "File Locker")
        
        with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, "*\\shell\\FileLocker") as key:
            winreg.SetValue(key, "", winreg.REG_SZ, "Lock/Unlock with File Locker")
            winreg.SetValue(key, "Icon", winreg.REG_SZ, f"{executable_path},0")
            
            with winreg.CreateKey(key, "command") as cmd_key:
                winreg.SetValue(cmd_key, "", winreg.REG_SZ, command)
        
        return True, _("Shell integration registered successfully")
    except Exception as e:
        return False, _("Failed to register shell integration: {}").format(str(e))