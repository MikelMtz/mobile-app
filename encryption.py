from cryptography.fernet import Fernet
import os
############################################################
#                                                          #
#                   Encryption functions                   #
#                                                          #
############################################################
KEY_FILE = "key.key"

def generate_key():
    """Generate a key and save it to a file if it doesn't exist."""
    if not os.path.exists(KEY_FILE):
        key = Fernet.generate_key()
        with open(KEY_FILE, "wb") as key_file:
            key_file.write(key)

def load_key():
    """Load the encryption key from the file."""
    if not os.path.exists(KEY_FILE):
        generate_key()
    with open(KEY_FILE, "rb") as key_file:
        return key_file.read()

# Load the encryption key
fernet = Fernet(load_key())

def encrypt_password(password: str) -> str:
    """Encrypts a password using Fernet encryption."""
    return fernet.encrypt(password.encode()).decode()

def decrypt_password(encrypted_password: str) -> str:
    """Decrypts an encrypted password."""
    return fernet.decrypt(encrypted_password.encode()).decode()

############################################################
#                                                          #
#               End of Encryption functions                #
#                                                          #
############################################################
