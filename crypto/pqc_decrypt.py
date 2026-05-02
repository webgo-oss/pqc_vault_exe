from pqcrypto.kem.ml_kem_768 import decrypt
from security.key_protection import decrypt_private_key

def decrypt_aes_key(ciphertext):

    password = input("Enter master password: ")

    try:
        with open("keys/private.key.enc", "rb") as f:
            data = f.read()
    except FileNotFoundError:
        raise Exception("Encrypted private key not found.")

    nonce = data[:12]
    encrypted_private_key = data[12:]

    private_key = decrypt_private_key(
        encrypted_private_key,
        nonce,
        password
    )

    shared_secret = decrypt(private_key, ciphertext)

    return shared_secret