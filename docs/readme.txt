Hello, and thank you for trying out File Locker!

This README contains all the information you need to get started with the program.

What is File Locker?

As the name suggests, File Locker lets you secure your private files and folders using a password of your choice. It's a simple, powerful tool for keeping your data safe.

How Does This Program Work?

File Locker encrypts your data using the AES-256 algorithm. This is a powerful, modern security technique trusted worldwide for protecting sensitive information.

Once an item is locked, it can only be accessed and unlocked by providing the correct password within the File Locker application.

Key Features.

File & Folder Encryption: Secure individual files or entire folders with all their contents.

Batch Processing: Drag and drop multiple files and folders at once to lock or unlock them in a single operation.

Command-Line Interface (CLI): Automate and script encryption tasks directly from your terminal.

Advanced Password Manager: Generate strong, random passwords or use your own.

Real-time Password Strength Meter: Get instant feedback on how secure your password is.

Password History: Quickly re-use passwords for items you've previously locked.

Drag & Drop Support: Simply drag your files or folders onto the application window to get started.

Getting Started

In the main directory, you’ll find:

Docs: folder, a folder contain readme and changelog.

FileLocker.exe: The main program.

First Steps:

Run FileLocker.exe.

The program will create a settings.config file on its first launch. This file stores your preferences for themes, password generation, and other application behaviors. You can manage these settings from within the app or edit the Config file directly if you're careful.

Main Interface

Select File/Folder Buttons: Choose an item to process.

Item Info Box: Displays details about the selected file or folder, including its lock status.

Recent Items List: Shows a history of recently processed items. Double-click an entry to quickly unlock it with its last used password.

Lock/Unlock Button: The main action button, which intelligently changes based on the selected item's status.

Menubar Options

Press Alt to focus the menubar.

File Menu:

Open File/Folder: Same as the selection buttons.

Exit: Closes the program.

Tools Menu:

Settings: Customize the program's behavior.

Clear Password History: Deletes all saved password history (this is irreversible).

Help Menu:

About File Locker: Shows version and program information.

Settings

Customize the program from the Settings window:

General

Remember Last Directory: The app will remember the last folder you browsed.

Auto-launch Files After Unlock: Automatically open files or folders after they are successfully decrypted.

Theme: Switch between a light (Default) and dark theme.

Language: Change the program language acording of your choice.

Password

Default Password Mode: Choose whether the password dialog defaults to generating a new password or expects manual entry.

Default Password Length: Set the default length for generated passwords. Longer is stronger!

Security

Confirm File Operations: Adds an extra confirmation step before locking or unlocking to prevent accidental operations.

Show Password Strength Meter: Toggles the visibility of the password strength feedback bar.

Maximum Password History Entries: Control how many items are kept in your history.

How to Use

Select an Item:

Click "Select File" or "Select Folder," or simply drag and drop your item(s) onto the window.

Note: You cannot lock items located in the program's own directory or in protected Windows system folders.

Check Status:

The info box will show whether the selected item is locked or unlocked. The main "Lock/Unlock" button will be enabled accordingly.

Lock an Item:

Select an unlocked file or folder and click "Lock/Unlock".

The Password Manager dialog will appear. You can generate a strong password or type your own.

A success message will confirm the operation. Remember your password!

Unlock an Item:

Select a locked item (.locked or .flka file) and click "Lock/Unlock".

You will be prompted to enter the password you used to lock it.

A dialog will confirm if the unlock was successful.

Command-Line Interface (CLI)

For advanced users and automation, File Locker includes a full CLI. Open a terminal (like Command Prompt or PowerShell) in the program's directory and run commands like:

Encrypt a file:
FileLocker.exe encrypt "C:\path\to\myfile.txt" -p "MySecretPassword"

Encrypt a folder:
FileLocker.exe encrypt "C:\path\to\my_folder" (You will be prompted for a password).

Decrypt an item:
FileLocker.exe decrypt "C:\path\to\myfile.txt.locked"

Get help:
FileLocker.exe --help or FileLocker.exe encrypt --help

Q&A

Q: Why did you create this program?
A: I wanted a simple, reliable, and open-source tool to secure my own files.

Q: Can I recover my file if I forget the password?
A: No. For security reasons, there are no backdoors. If you lose your password, the data is irreversibly encrypted and cannot be recovered. You can try to unlock an item from the "Recent Items List," which uses the last known password, but if that history is cleared, recovery is impossible.

Q: Will this program work on all file types?
A: Yes, it works with any file or folder. The program includes safeguards to prevent you from locking critical system files.

Q: Can I share a locked file with someone else?
A: Yes, but they will need a copy of the File Locker program and the correct password to unlock it.

This program is built with Python, wxPython for the GUI, and PyCryptodome for encryption. It is designed to be cross-platform, but the primary focus is on Windows.

Enjoy using File Locker, and keep your files secure!

Disclaimer

This program is provided under the Apache License Version 2.0 and for educational and practical purposes. The user assumes full responsibility for its use. Always keep backups of important data. The developer is not responsible for any data loss that may result from forgotten passwords, program misuse, or software errors.