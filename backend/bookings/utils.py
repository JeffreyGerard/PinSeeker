
from cryptography.fernet import Fernet
import os
import base64

def get_cipher_suite():
    key = os.getenv('ENCRYPTION_KEY')
    if not key:
        raise ValueError("No ENCRYPTION_KEY set in .env file")
    return Fernet(key.encode())

def encrypt_password(password):
    cipher = get_cipher_suite()
    encrypted_bytes = cipher.encrypt(password.encode('utf-8'))
    return base64.urlsafe_b64encode(encrypted_bytes).decode('utf-8')

def decrypt_password(encrypted_password):
    cipher = get_cipher_suite()
    encrypted_bytes = base64.urlsafe_b64decode(encrypted_password)
    decrypted_bytes = cipher.decrypt(encrypted_bytes)
    return decrypted_bytes.decode('utf-8')
