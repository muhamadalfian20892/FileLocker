import json
import sys
from pathlib import Path
from typing import Dict, Any

DEFAULT_SETTINGS = {
    "password_lengths": [8, 16, 32, 64, 128],
    "default_password_length": 16,
    "use_uppercase": True,
    "use_lowercase": True,
    "use_digits": True,
    "use_symbols": True,
    "remember_last_directory": True,
    "last_directory": "",
    "auto_launch_after_unlock": True,
    "default_password_mode": "generate",  # or "manual"
    "confirm_file_operations": True,
    "show_password_strength": True,
    "max_history_entries": 50,
    "theme": "default"
}

class Settings:
    def __init__(self):
        self.settings_file = self._get_settings_path()
        self.settings = self.load_settings()
    
    def _get_settings_path(self) -> Path:
        if getattr(sys, 'frozen', False):
            base_path = Path(sys.executable).parent
        else:
            base_path = Path(__file__).parent
        return base_path / 'settings.config'
    
    def load_settings(self) -> Dict[str, Any]:
        if self.settings_file.exists():
            try:
                with open(self.settings_file, 'r') as f:
                    loaded_settings = json.load(f)
                    # Merge with defaults to ensure all settings exist
                    return {**DEFAULT_SETTINGS, **loaded_settings}
            except json.JSONDecodeError:
                return DEFAULT_SETTINGS.copy()
        return DEFAULT_SETTINGS.copy()
    
    def save_settings(self):
        with open(self.settings_file, 'w') as f:
            json.dump(self.settings, f, indent=4)
    
    def get(self, key: str) -> Any:
        return self.settings.get(key, DEFAULT_SETTINGS.get(key))
    
    def set(self, key: str, value: Any):
        if key in DEFAULT_SETTINGS:
            self.settings[key] = value
            self.save_settings()
        else:
            raise KeyError(f"Unknown setting: {key}")
    
    def reset_to_defaults(self):
        self.settings = DEFAULT_SETTINGS.copy()
        self.save_settings()