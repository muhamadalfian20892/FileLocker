# paths.py
import os

# where we save the user's language choice
CONFIG_FILE = "lang.settings"

# gettext needs this folder structure, kinda lame but w/e
# it should look like:
# /locales/en/LC_MESSAGES/messages.mo
# /locales/es/LC_MESSAGES/messages.mo
LOCALE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "locales")