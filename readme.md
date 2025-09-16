# File Locker

### Overview

This app is just a random project. It started out for my own personal use because I needed a dead-simple way to encrypt files, but I figured others might find it useful too. So, here it is.

File Locker is a straightforward desktop app that lets you lock (encrypt) and unlock (decrypt) your files with a password. Everything is done offline, on your computer, so your data never leaves your machine.

Drop me a question or some feedback at: **hafiyanajah@gmail.com**

### Behind the Story

Honestly, I just wanted a tool to secure some personal documents. I looked around and found a lot of complex software or cloud-based solutions, but I just wanted something simple: run it, pick a file, set a password, and be done.

So, I decided to build it myself. It became a fun personal project to dive deeper into Python, particularly with the `wxPython` library for the GUI and `pycryptodome` for the heavy lifting on the encryption side. It started as a basic command-line script, but I kept adding features like a user interface, drag-and-drop support, and a password history until it became what you see today.

A big thumbs up also has to go to Google's Gemini AI. It was a massive help for brainstorming logic, debugging tricky parts of the code, and even generating some of the initial boilerplate. It's a seriously powerful tool. You should really check out what it can do:
-   [Gemini](https://gemini.google.com)
-   [Google AI Studio](https://aistudio.google.com)

### What It Can Do (Feature List)

This app has a handful of key features designed to make file security easy:

*   **Strong Encryption:** Uses the battle-tested AES-256 algorithm to make sure your files are securely locked.
*   **Password Generator:** If you're not sure what password to use, the app can generate a strong, random one for you.
*   **Password History:** The app remembers the most recent passwords you've used for your files, making it quick to unlock them again. You can clear this history at any time.
*   **Drag & Drop Support:** Don't want to use the "Browse" button? Just drag a file directly onto the app window.
*   **Windows Shell Integration:** You can add a "Lock/Unlock with File Locker" option to your right-click menu in Windows Explorer for super-fast access.
*   **Built-in Safeguards:** The app is designed to prevent you from accidentally locking critical system files or files located within its own program directory.
*   **Light & Dark Themes:** You can switch between a light (default) and dark theme to suit your preference.

### How to Get It Working

#### 1. The Easy Way (Recommended)
You don't need to install anything. Just grab the ready-to-use version.

➡️ **[Download the latest version from the Releases page!](https://github.com/muhamadalfian20892/FileLocker/releases)** ⬅️

Download the `.exe` file, and you're good to go.

#### 2. Running from the Source Code (For Developers)
If you want to run the app from its Python source code, follow these steps:

1.  **Clone this repository:**
    ```bash
    git clone https://github.com/your-username/your-repo.git
    cd your-repo
    ```
    <!-- Replace the URL above with your repository's URL -->

2.  **Install the required libraries:**
    You'll need Python 3. Then, run this command in your terminal:
    ```bash
    pip install wxPython pycryptodomex
    ```

3.  **Run the app:**
    ```bash
    python main.py
    ```
    The app will automatically create a `settings.config` file on its first run.

### A Very Important Warning

**PLEASE READ THIS CAREFULLY.**

This application performs irreversible encryption. That means **IF YOU FORGET YOUR PASSWORD, YOUR FILE IS GONE FOREVER.** There is no "Forgot Password" feature. There is no way to recover the file.

The password history feature can help, but if that history is cleared or lost, your memory is the only key. Please store your passwords in a safe and secure place. Use this tool responsibly.

### Project Structure (For Contributors)

If you're interested in contributing or just want to understand how the code is organized, here's a quick breakdown:

```
/
├── core_encryption.py     # Handles all the AES encryption/decryption logic.
├── core_history.py        # Manages loading and saving password history.
├── core_paths.py          # Handles path restrictions and shell integration.
├── core_settings.py       # Manages the settings.config file.
├── gui_main.py            # The main application window and its UI logic.
├── gui_dialogs.py         # All pop-up dialogs (Password Generator, Settings, etc.).
├── gui_utils.py           # Helper functions and classes for the GUI.
└── main.py                # The entry point to launch the application.
```

### Final Words

That's pretty much it. Thanks for checking out File Locker. I hope it proves to be a simple and useful tool for you.

If you have any ideas or run into any issues, feel free to open an issue here on GitHub or drop me an email.

Happy locking
