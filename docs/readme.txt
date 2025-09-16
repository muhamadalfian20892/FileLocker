Hello, and thank you for trying out this program!

This ReadMe contains all the information you need about the program.

What is File Locker?

As the name suggests, this program lets you lock and unlock your secret files using a password of your choice.

How Does This Program Work?

Basically, this program encrypts your file using powerful techniques like AES-256 along with some additional modern security measures by choosing to also using sha512 for better cryptography security (not only on the main file data transfer also with password encryption/decryption, it's up to you in settings mode).

Once locked, the file can only be accessed and unlocked by File Locker, which can be opened and the same password.

Getting Started

In the main directory, you’ll find these files:

readme.txt: This file, with all the details.
changelog.txt: Notes on updates and changes to the program.
FileLocker.exe : The program executable.

First Steps:

1. Open the FileLocker.exe.

2.  The program will automatically create a `settings.config` file for manual configuration if needed.
      this setting contains all user configurations about look of program, usability preference or cryptography settings preference and saved next launch if done on application setting, you can also configure manually with editor but take more attention not break the `json` format in the settings file, that could result into loading problem on startup

Menu Options

Main Interface

When you launch the program, you’ll see:

* Browse Button: Use this to select a file (pretty self-explanatory).
* ReadOnly Box: Displays details of the selected file, including its lock/unlock status.
* Recent Files List: Shows the history of files you've locked/unlocked with it, along with it type such as lock/unlock event

Menubar Options
Access more options through the menubar. Simply press the Alt key on your keyboard to go to it.

1. File Menu:
    * Open: Same as the Browse button.
    * Exit: Closes the program.

2. Tools Menu:
    * Settings: Adjust program configurations (read more details at sections "Settings").
    * Clear Password History: Deletes all saved password history.

3. Help Menu:
    * Help: Opens the help box for basic information

Settings
Access the Settings menu to customize the program. It includes the following categories:

General:

  *  Remember Last Directory: When enabled, the program remembers the last folder you accessed when browse your folders for encrypting/decrypting.
  * AutoLaunch File After Unlock: Decide whether the program should open files automatically after unlocking (default set as true).
 *  Auto Remove Files after Unlock (be very, very careful): decide if automatically remove selected and processed after a successfully unlock event by setting into True state and saving configuration (note, when use this it is irreversible).
  * Theme: Customize the program’s appearance with pre made themes, more like light (Default) or dark.
Save: Save your settings by pressing `save button` at right down window section.
 Reset to Defaults: Revert all settings back to default. (by clicking this setting you wont loose any of existing file protection made by this software as these process is fully saved).

Password:

  * Default Password Mode: Choose between manual entry (using custom set password from a keyboard ) or automatically generating a password.
 * Default Password Length: Set the length of generated passwords using the choices (for more longer stronger more secure, less is not recomended to user but still acceptable using this software functionality for educational purpose as well)

Security:

  *  Confirm File Operations: Enable confirmation prompts for locking/unlocking files by dialog showing up.
    * This adds one additional step and could protect accidental operation from mis-input, as default the security has `enabled confirmation`.
  * Password Strength Meter: Displays the strength of your password.
* Maximum Password History: Define how many passwords to save in the history, less than `100`.
  * Clear Password History: Clears the saved password history, it deletes data irreversibly.
Encryption:

* Select Stronger or Fast Password Creation Mode by key derivation selection process.
 *   PBKDF2 is the classic for fast process for secure level data
 *  SHA512 is a secure hashing algorithm making the key derive a better strength and it should be choosen rather than PBKDF2 as best cryptography practise when data is sensitive
   * For the beginner user who are less familiar on cryptographic security `SHA512` is highly recommended and its best choice.
 * Enable compression level by compression, it helps make size more lesser and increase data transformation on both encrypt/decrypt (if the machine is capable to high speeds), the file data still as secured level for this, just helps performance by selecting the `compress` option if need.
    * Compression has an `on` and `off` checkbox so use wisely

How to Use?

1. Select a File:
    * Click the "Browse" button and choose the file you want to lock.
    * Note: You cannot lock files located in the same directory as this program, or on protected window folder

2. Check File Status:
  *   The status of your selected file (locked or unlocked) will be displayed in the ReadOnly box along other details.
  *  If the file is already locked, the "Lock" button won’t be available, and vice versa.

3. Lock the File:
   * Import an unlocked file and click the "Lock" button.
    *  A menu window of selection password choice either generate random password based on option on menu settings or using your input of password.
    *  A successful window message will pop-up containing generated password or manual password and information about file encryption success.

4. Unlock the File:
    * Import a locked file and click the "Unlock" button.
   * You will prompted to use password which you already set on the lock step.
  * A success or failure dialog should be appear at completion (successful unlock or decryption).

Q&A
 Q: Why did you create this program?
 A: I wanted an easy way to secure my own secret files.
 Q: What protections does this program have?
 A: You cannot lock files located in the program’s directory, and I've also tried to prevent locking files in sensitive Windows directories and using most common techniques such as modern high encryption.
Q: Can I recover my file if I forget the password?
 A: There’s only one option: you can click the locked item in the "Recent Files List" to bypass the password or use last lock / unlock action you had previously used. However, if your history is lost, unfortunately, no. For security reasons, files are irreversibly encrypted, and without the correct password, they can’t be unlocked.

Q: Will this program work on all file types?
A: Yes, it works with any file type, but make sure you don’t lock essential system files (also I included restriction by using protected Windows directory path).

Q: Can I share my lock file with someone else?
A: Yes, but they won’t be able to do anything with the file unless they have this program and the correct password that was created or used before (make sure keep in mind SHA512 key derivate may prevent another user which dont have right setting even right password for security protection in that case)

For more tech-savy User; We did create program using Python using wxPython pycryptodome libaries and so, this program could easily be adapted to most modern operative system. i'm focused on code and cryptography level on implementing SHA512 as highest priority option

This program is still in its early stages. I’m looking forward to adding more features in future updates!


Enjoy using File Locker, and keep your files secure!

Disclaimer

 This program provide under “MIT” and educational purposes, the user have its full rights when accessing and using, the risk and consequences always should be kept by users, do not use without acknowledging. and have full responsibility for any potential harm doing from improper use by unexperienced people or for misuse (we added additional options, please user use care before using option provided).