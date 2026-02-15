
from cryptography.fernet import Fernet

key = Fernet.generate_key()
print(f"\nYour ENCRYPTION_KEY:\n{key.decode()}\n")
