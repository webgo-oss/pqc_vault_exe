from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import os

def encrypt_file(file_path, key):

    with open(file_path, "rb") as f:
        data = f.read()

    aes = AESGCM(key)

    nonce = os.urandom(12)

    encrypted = aes.encrypt(nonce, data, None)

    print("File encrypted successfully")

    return encrypted, nonce