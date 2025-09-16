from Crypto.Cipher import AES
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad
import base64
import os
from typing import Callable, Optional

from translate import _ # import for errors

class Encryption:
    def __init__(self):
        self.salt_length = 32
        self.iv_length = 16
        self.key_length = 32
        self.iterations = 100000
        self.chunk_size = 64 * 1024  # 64KB chunks

    def generate_key(self, password: str, salt: bytes) -> bytes:
        return PBKDF2(
            password.encode(),
            salt,
            dkLen=self.key_length,
            count=self.iterations
        )

    def encrypt_file(self, 
                    input_path: str, 
                    password: str, 
                    progress_callback: Optional[Callable[[float], None]] = None) -> bool:
        temp_path = input_path + '.locked'
        try:
            salt = get_random_bytes(self.salt_length)
            iv = get_random_bytes(self.iv_length)
            
            key = self.generate_key(password, salt)
            cipher = AES.new(key, AES.MODE_CBC, iv)

            file_size = os.path.getsize(input_path)
            processed = 0
            
            with open(input_path, 'rb') as in_file, open(temp_path, 'wb') as out_file:
                out_file.write(b'FLCK')
                out_file.write(salt)
                out_file.write(iv)
                
                while True:
                    chunk = in_file.read(self.chunk_size)
                    if not chunk:
                        break
                    
                    processed += len(chunk)
                    
                    if processed == file_size:
                        chunk = pad(chunk, AES.block_size)
                        out_file.write(cipher.encrypt(chunk))
                        break
                    
                    encrypted_chunk = cipher.encrypt(chunk)
                    out_file.write(encrypted_chunk)
                    
                    if progress_callback:
                        progress_callback((processed / file_size) * 100)

            os.remove(input_path)
            os.rename(temp_path, input_path)
            return True

        except Exception as e:
            print(f"Encryption error: {e}")
            if os.path.exists(temp_path):
                os.remove(temp_path)
            return False

    def decrypt_file(self, 
                    input_path: str, 
                    password: str, 
                    progress_callback: Optional[Callable[[float], None]] = None) -> bool:
        temp_path = input_path + '.unlocked'
        try:
            with open(input_path, 'rb') as in_file, open(temp_path, 'wb') as out_file:
                magic = in_file.read(4)
                if magic != b'FLCK':
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
                    
                    if processed_content == content_size:
                        try:
                            decrypted_chunk = unpad(decrypted_chunk, AES.block_size)
                        except ValueError:
                            raise ValueError(_("Incorrect password or corrupted file."))
                    
                    out_file.write(decrypted_chunk)
                    
                    if progress_callback:
                        progress = ((header_size + processed_content) / file_size) * 100
                        progress_callback(progress)

            os.remove(input_path)
            os.rename(temp_path, input_path)
            return True

        except ValueError as ve:
            print(f"Decryption error: {ve}")
            if os.path.exists(temp_path):
                os.remove(temp_path)
            return False
        except Exception as e:
            print(f"Decryption error: {e}")
            if os.path.exists(temp_path):
                os.remove(temp_path)
            return False