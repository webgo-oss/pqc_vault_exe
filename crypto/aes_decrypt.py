from cryptography.hazmat.primitives.ciphers.aead import AESGCM

def decrypt_file(encrypted_data, nonce, key):

    aes = AESGCM(key)

    decrypted = aes.decrypt(nonce, encrypted_data, None)

    return decrypted