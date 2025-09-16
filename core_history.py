import json
from pathlib import Path
import datetime
from typing import List, Dict, Optional
import os

class PasswordHistory:
    def __init__(self, max_entries: int = 50):
        self.history_file = Path.home() / '.file_locker_history.json'
        self.max_entries = max_entries
        self.history: Dict[str, List[Dict]] = self.load_history()
    
    def load_history(self) -> Dict:
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return {}
        return {}
    
    def save_history(self):
        with open(self.history_file, 'w') as f:
            json.dump(self.history, f, indent=4)
    
    def add_entry(self, filepath: str, password: str):
        filepath = os.path.abspath(filepath)
        if filepath not in self.history:
            self.history[filepath] = []
        
        # Add new entry
        entry = {
            'password': password,
            'timestamp': datetime.datetime.now().isoformat(),
            'filename': os.path.basename(filepath)
        }
        
        # Add to front of list
        self.history[filepath].insert(0, entry)
        
        # Trim to max entries
        if len(self.history[filepath]) > self.max_entries:
            self.history[filepath] = self.history[filepath][:self.max_entries]
        
        self.save_history()
    
    def get_history_for_file(self, filepath: str) -> List[Dict]:
        filepath = os.path.abspath(filepath)
        return self.history.get(filepath, [])
    
    def get_recent_passwords(self, limit: int = 10) -> List[Dict]:
        """Get most recently used passwords across all files"""
        all_entries = []
        for filepath, entries in self.history.items():
            for entry in entries:
                all_entries.append({
                    'filepath': filepath,
                    'filename': entry['filename'],
                    'password': entry['password'],
                    'timestamp': entry['timestamp']
                })
        
        # Sort by timestamp and return most recent
        all_entries.sort(key=lambda x: x['timestamp'], reverse=True)
        return all_entries[:limit]
    
    def clear_history(self):
        """Clear all history"""
        self.history = {}
        self.save_history()
    
    def remove_file_history(self, filepath: str):
        """Remove history for specific file"""
        filepath = os.path.abspath(filepath)
        if filepath in self.history:
            del self.history[filepath]
            self.save_history()