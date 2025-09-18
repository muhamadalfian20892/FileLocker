from Crypto.Cipher import AES
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad
import base64
import os
import shutil
import io
import zipfile
from pathlib import Path
from typing import Callable, Optional, Tuple

from translate import _ # import for errors

class Encryption:
    def __init__(self):
        self.salt_length = 32
        self.iv_length = 16
        self.key_length = 32
        self.iterations = 100000
        self.chunk_size = 64 * 1024  # 64KB chunks
        self.file_magic = b'FLCK'
        self.folder_magic = b'FLKA' # File Locker Archive

    def generate_key(self, password: str, salt: bytes) -> bytes:
        return PBKDF2(
            password.encode(),
            salt,
            dkLen=self.key_length,
            count=self.iterations
        )

    def get_operation_type(self, path: str) -> Optional[str]:
        """Check if a path is an encrypted file, folder, or neither."""
        if not os.path.exists(path):
            return None
        if os.path.isdir(path):
            return "encrypt_folder"
        
        try:
            with open(path, 'rb') as f:
                magic = f.read(4)
                if magic == self.file_magic:
                    return "decrypt_file"
                if magic == self.folder_magic:
                    return "decrypt_folder"
        except IOError:
            return None # Can't read file
            
        # If no magic bytes, assume it's a regular file to be encrypted
        return "encrypt_file"


    def encrypt_file(self, 
                    input_path: str, 
                    password: str, 
                    progress_callback: Optional[Callable[[float], None]] = None) -> Tuple[bool, Optional[str]]:
        output_path = input_path + '.locked'
        try:
            salt = get_random_bytes(self.salt_length)
            iv = get_random_bytes(self.iv_length)
            
            key = self.generate_key(password, salt)
            cipher = AES.new(key, AES.MODE_CBC, iv)

            file_size = os.path.getsize(input_path)
            processed = 0
            
            with open(input_path, 'rb') as in_file, open(output_path, 'wb') as out_file:
                out_file.write(self.file_magic)
                out_file.write(salt)
                out_file.write(iv)
                
                while True:
                    chunk = in_file.read(self.chunk_size)
                    if not chunk:
                        break
                    
                    processed += len(chunk)
                    
                    if processed >= file_size:
                        chunk = pad(chunk, AES.block_size)
                        out_file.write(cipher.encrypt(chunk))
                        break
                    
                    encrypted_chunk = cipher.encrypt(chunk)
                    out_file.write(encrypted_chunk)
                    
                    if progress_callback:
                        progress_callback((processed / file_size) * 100)

            os.remove(input_path)
            return True, None

        except Exception as e:
            if os.path.exists(output_path):
                os.remove(output_path)
            return False, str(e)

    def decrypt_file(self, 
                    input_path: str, 
                    password: str, 
                    progress_callback: Optional[Callable[[float], None]] = None) -> Tuple[bool, Optional[str]]:
        
        # Ensure we're removing the .locked suffix correctly
        output_path = input_path
        if input_path.endswith('.locked'):
            output_path = input_path[:-7]
        else:
            # Fallback for files that might not have the extension
            output_path = input_path + '.unlocked'

        try:
            with open(input_path, 'rb') as in_file, open(output_path, 'wb') as out_file:
                magic = in_file.read(4)
                if magic != self.file_magic:
                    raise ValueError(_("Not a valid locked file or incorrect password"))
                
                salt = in_file.read(self.salt_length)
                iv = in_file.read(self.iv_length)
                
                key = self.generate_key(password, salt)
                cipher = AES.new(key, AES.MODE_CBC, iv)
                
                file_size = os.path.getsize(input_path)
                header_size = 4 + self.salt_length + self.iv_length
                content_size = file_size - header_size
                processed_content = 0

                while True:
                    chunk = in_file.read(self.chunk_size)
                    if not chunk:
                        break
                    
                    processed_content += len(chunk)
                    decrypted_chunk = cipher.decrypt(chunk)
                    
                    if processed_content >= content_size:
                        try:
                            decrypted_chunk = unpad(decrypted_chunk, AES.block_size)
                        except ValueError:
                            raise ValueError(_("Incorrect password or corrupted file."))
                    
                    out_file.write(decrypted_chunk)
                    
                    if progress_callback:
                        progress = ((header_size + processed_content) / file_size) * 100
                        progress_callback(min(progress, 100.0))

            os.remove(input_path)
            return True, None

        except ValueError as ve:
            if os.path.exists(output_path):
                os.remove(output_path)
            return False, str(ve)
        except Exception as e:
            if os.path.exists(output_path):
                os.remove(output_path)
            return False, str(e)
            
    def encrypt_folder(self,
                     input_path: str,
                     password: str,
                     progress_callback: Optional[Callable[[float], None]] = None) -> Tuple[bool, Optional[str]]:
        output_path = input_path + '.flka'
        try:
            # Step 1: Create an in-memory zip archive
            zip_buffer = io.BytesIO()
            
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
                p = Path(input_path)
                for file in p.glob('**/*'):
                    if file.is_file():
                        zipf.write(file, file.relative_to(p))

            zip_data = zip_buffer.getvalue()
            
            # Step 2: Encrypt the zip data
            salt = get_random_bytes(self.salt_length)
            iv = get_random_bytes(self.iv_length)
            key = self.generate_key(password, salt)
            cipher = AES.new(key, AES.MODE_CBC, iv)
            
            padded_data = pad(zip_data, AES.block_size)
            encrypted_data = cipher.encrypt(padded_data)
            
            # Step 3: Write to output file
            with open(output_path, 'wb') as out_file:
                out_file.write(self.folder_magic)
                out_file.write(salt)
                out_file.write(iv)
                out_file.write(encrypted_data)

            if progress_callback:
                progress_callback(100) # Simplified progress for now

            shutil.rmtree(input_path)
            return True, None
            
        except Exception as e:
            if os.path.exists(output_path):
                os.remove(output_path)
            return False, str(e)

    def decrypt_folder(self,
                     input_path: str,
                     password: str,
                     progress_callback: Optional[Callable[[float], None]] = None) -> Tuple[bool, Optional[str]]:
        output_path = input_path
        if input_path.endswith('.flka'):
            output_path = input_path[:-5]
            
        try:
            # Step 1: Read and decrypt the file content
            with open(input_path, 'rb') as in_file:
                magic = in_file.read(4)
                if magic != self.folder_magic:
                    raise ValueError(_("Not a valid locked folder archive or incorrect password"))
                
                salt = in_file.read(self.salt_length)
                iv = in_file.read(self.iv_length)
                encrypted_data = in_file.read()
            
            key = self.generate_key(password, salt)
            cipher = AES.new(key, AES.MODE_CBC, iv)
            
            decrypted_padded_data = cipher.decrypt(encrypted_data)
            try:
                decrypted_data = unpad(decrypted_padded_data, AES.block_size)
            except ValueError:
                raise ValueError(_("Incorrect password or corrupted file."))
            
            # Step 2: Extract the in-memory zip archive
            zip_buffer = io.BytesIO(decrypted_data)
            
            if not os.path.exists(output_path):
                os.makedirs(output_path)
                
            with zipfile.ZipFile(zip_buffer, 'r') as zipf:
                zipf.extractall(output_path)

            if progress_callback:
                progress_callback(100) # Simplified progress for now

            os.remove(input_path)
            return True, None

        except ValueError as ve:
            # Don't delete partial extraction for data recovery reasons
            return False, str(ve)
        except Exception as e:
            return False, str(e)