import ctypes
import os
import sys
import time
from typing import Optional

# Local application imports
from core_settings import Settings

# --- Global NVDA Controller Instance ---
nvdaControllerClient: Optional[ctypes.CDLL] = None
settings_instance: Optional[Settings] = None

# Constants for verbosity levels
NVDA_VERBOSITY_QUIET = "quiet"
NVDA_VERBOSITY_DEFAULT = "default"
NVDA_VERBOSITY_VERBOSE = "verbose"

NVDA_VERBOSITY_LEVELS = {
    NVDA_VERBOSITY_QUIET: 0,
    NVDA_VERBOSITY_DEFAULT: 1,
    NVDA_VERBOSITY_VERBOSE: 2,
}

def load_nvda_dll():
    """
    Attempts to load the NVDA Controller DLL from the 'libs' subfolder.
    """
    global nvdaControllerClient
    if nvdaControllerClient:
        return # Already loaded

    try:
        # Determine the base path (for both frozen and script execution)
        if getattr(sys, 'frozen', False):
            base_path = os.path.dirname(sys.executable)
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))
        
        # The DLL should be in a 'libs' subfolder
        DLL_NAME = "nvdaControllerClient32.dll"
        local_dll_path = os.path.join(base_path, "libs", DLL_NAME)

        if os.path.exists(local_dll_path):
            nvdaControllerClient = ctypes.cdll.LoadLibrary(local_dll_path)
            print(f"NVDA Controller DLL loaded successfully from: {local_dll_path}")
        else:
            print(f"Warning: NVDA DLL not found at {local_dll_path}. NVDA speech is disabled.")
            nvdaControllerClient = None

    except OSError as e:
        print(f"Warning: Could not load the NVDA Controller DLL. NVDA speech output will be disabled. Error: {e}")
        nvdaControllerClient = None
    except Exception as e:
        print(f"An unexpected error occurred loading NVDA Controller DLL: {e}")
        nvdaControllerClient = None

def _get_settings() -> Settings:
    """
    Gets the application settings instance, creating it if it doesn't exist.
    """
    global settings_instance
    if settings_instance is None:
        settings_instance = Settings()
    return settings_instance

def speak(text: str, verbosity: str = NVDA_VERBOSITY_DEFAULT, cancel: bool = True):
    """
    Speaks the given text using the loaded NVDA controller, respecting settings.
    
    Args:
        text (str): The text to be spoken.
        verbosity (str): The verbosity level required for this message to be spoken.
        cancel (bool): If True, cancels any previous speech before speaking.
    """
    settings = _get_settings()
    
    if not nvdaControllerClient or not text or not settings.get('nvda_enabled'):
        return

    required_level = NVDA_VERBOSITY_LEVELS.get(verbosity, 1)
    
    current_verbosity_str = settings.get('nvda_verbosity')
    current_level = NVDA_VERBOSITY_LEVELS.get(current_verbosity_str, 1)

    if current_level >= required_level:
        try:
            text_str = str(text)  # Ensure text is a string
            if cancel:
                nvdaControllerClient.nvdaController_cancelSpeech()
                # A slight delay can help prevent issues with rapid calls
                time.sleep(0.01)
            nvdaControllerClient.nvdaController_speakText(ctypes.c_wchar_p(text_str))
        except Exception as e:
            print(f"Error calling nvdaController_speakText: {e}")

# --- Initial Load Attempt ---
# Load the DLL when this module is imported.
load_nvda_dll()