from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import os
import hashlib

def derive_key_from_password(password):
    return hashlib.sha256(password.encode()).digest()

def encrypt_private_key(private_key, password):

    key = derive_key_from_password(password)

    aes = AESGCM(key)

    nonce = os.urandom(12)

    encrypted_key = aes.encrypt(nonce, private_key, None)

    return encrypted_key, nonce


def decrypt_private_key(encrypted_key, nonce, password):

    key = derive_key_from_password(password)

    aes = AESGCM(key)

    decrypted = aes.decrypt(nonce, encrypted_key, None)

    return decrypted