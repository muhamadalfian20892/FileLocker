import wx
import sys
import os
import argparse
from getpass import getpass

from gui_main import MainWindow
from core_settings import Settings
from core_encryption import Encryption
import nvda
from translate import _

def run_cli():
    """Handles command-line interface operations."""
    parser = argparse.ArgumentParser(
        description=_("File Locker CLI - Encrypt and decrypt files and folders from the command line.")
    )
    subparsers = parser.add_subparsers(dest="command", required=True, help=_("Available commands"))

    # Encrypt command
    parser_encrypt = subparsers.add_parser("encrypt", help=_("Encrypt a file or folder."))
    parser_encrypt.add_argument("path", help=_("Path to the file or folder to encrypt."))
    parser_encrypt.add_argument("-p", "--password", help=_("Password for encryption. If not provided, you will be prompted."))

    # Decrypt command
    parser_decrypt = subparsers.add_parser("decrypt", help=_("Decrypt a file or folder."))
    parser_decrypt.add_argument("path", help=_("Path to the .locked or .flka file to decrypt."))
    parser_decrypt.add_argument("-p", "--password", help=_("Password for decryption. If not provided, you will be prompted."))
    
    # Shell registration command
    subparsers.add_parser("register-shell", help=_("Register shell integration (Windows only)."))

    args = parser.parse_args()

    if args.command == "register-shell":
        if sys.platform == 'win32':
            from core_paths import register_shell_integration
            success, message = register_shell_integration()
            print(message)
            sys.exit(0 if success else 1)
        else:
            print(_("Shell integration is only available on Windows."))
            sys.exit(1)

    # --- Handle Encrypt/Decrypt ---
    if not os.path.exists(args.path):
        print(_("Error: The specified path does not exist: {}").format(args.path))
        sys.exit(1)

    password = args.password
    if not password:
        password = getpass(_("Enter password: "))
        if not password:
            print(_("Error: Password cannot be empty."))
            sys.exit(1)
            
    encryption = Encryption()
    success = False
    
    try:
        if args.command == "encrypt":
            if os.path.isdir(args.path):
                print(_("Encrypting folder: {}").format(args.path))
                success = encryption.encrypt_folder(args.path, password)
            else:
                print(_("Encrypting file: {}").format(args.path))
                success = encryption.encrypt_file(args.path, password)
        
        elif args.command == "decrypt":
            op_type = encryption.get_operation_type(args.path)
            if op_type == "decrypt_folder":
                print(_("Decrypting folder: {}").format(args.path))
                success = encryption.decrypt_folder(args.path, password)
            elif op_type == "decrypt_file":
                print(_("Decrypting file: {}").format(args.path))
                success = encryption.decrypt_file(args.path, password)
            else:
                print(_("Error: Not a valid encrypted file or folder: {}").format(args.path))
                sys.exit(1)

        if success:
            print(_("Operation completed successfully."))
            sys.exit(0)
        else:
            print(_("Operation failed. Please check the password or file integrity."))
            sys.exit(1)
            
    except Exception as e:
        print(_("An unexpected error occurred: {}").format(e))
        sys.exit(1)

def main():
    """Main entry point for the application."""
    # Check if CLI arguments are provided (and it's not just the script name)
    # A simple check to see if a command like 'encrypt' or 'decrypt' is present.
    cli_commands = {'encrypt', 'decrypt', 'register-shell'}
    if len(sys.argv) > 1 and sys.argv[1] in cli_commands:
        run_cli()
    else:
        # Launch the GUI application
        app = wx.App()
        settings = Settings()
        frame = MainWindow(settings)
        frame.Show()
        
        nvda.speak(_("Application started."))
        
        # This argument is now handled by the CLI parser, but we keep it for backward compatibility.
        if len(sys.argv) > 1 and sys.argv[1] == '--register':
            from core_paths import register_shell_integration
            register_shell_integration()
        
        app.MainLoop()

if __name__ == '__main__':
    main()