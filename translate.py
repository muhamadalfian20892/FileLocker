# translate.py
import os
import gettext

# my new sick files
from paths import CONFIG_FILE, LOCALE_DIR
from variables import DEFAULT_LANG

# global state is kinda cringe but it's the fastest way
# so who cares ¯\_(ツ)_/¯
current_translation_thing = None


def set_language(lang_code=None):
    global current_translation_thing
    
    # if no lang is passed, we figure it out
    if lang_code is None:
        lang_code = DEFAULT_LANG
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    saved_stuff = f.read().strip()
                    if saved_stuff:
                        lang_code = saved_stuff
            except Exception:
                # if it's borked just move on
                pass

    # try to load the translation file
    try:
        language = gettext.translation(
            "messages",
            localedir=LOCALE_DIR,
            languages=[lang_code],
            fallback=True, 
        )
        current_translation_thing = language
    except FileNotFoundError:
        # lol if the file is missing just use a dummy
        print(f"WARN: could not find language files for '{lang_code}', falling back")
        current_translation_thing = gettext.NullTranslations()


def _(text):
    # this is the magic function
    if current_translation_thing is None:
        set_language() # run it once on first call
    return current_translation_thing.gettext(text)


# run this when the module is imported
set_language()