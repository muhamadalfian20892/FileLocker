# core.py
import os
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
import base64

from translate import _ # gotta import this for the error messages

def _derive_key(password: bytes, salt: bytes) -> bytes:
    """Derives a key from the password and salt."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
        backend=default_backend()
    )
    return base64.urlsafe_b64encode(kdf.derive(password))

def encrypt_file(file_path: str, password: str):
    """Encrypts a file and saves it with a .locked extension."""
    if not password:
        raise ValueError(_("Password cannot be empty."))
        
    salt = os.urandom(16)
    key = _derive_key(password.encode(), salt)
    
    with open(file_path, "rb") as f:
        data = f.read()
        
    fernet = Fernet(key)
    encrypted_data = fernet.encrypt(data)
    
    with open(file_path + ".locked", "wb") as f:
        f.write(salt)
        f.write(encrypted_data)
        
    os.remove(file_path)

def decrypt_file(file_path: str, password: str):
    """Decrypts a .locked file."""
    if not password:
        raise ValueError(_("Password cannot be empty."))
    if not file_path.endswith(".locked"):
        raise ValueError(_("File is not a .locked file."))

    with open(file_path, "rb") as f:
        salt = f.read(16)
        encrypted_data = f.read()
        
    key = _derive_key(password.encode(), salt)
    fernet = Fernet(key)
    
    try:
        decrypted_data = fernet.decrypt(encrypted_data)
    except InvalidToken:
        raise ValueError(_("Invalid password or corrupted file."))

    original_file_path = file_path[:-7] # Remove '.locked'
    with open(original_file_path, "wb") as f:
        f.write(decrypted_data)
        
    os.remove(file_path)