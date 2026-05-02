from pqcrypto.kem.ml_kem_768 import encrypt

def generate_shared_secret():

    try:
        with open("keys/public.key", "rb") as f:
            public_key = f.read()

    except FileNotFoundError:
        raise Exception("Public key not found. Generate keys first.")

    ciphertext, shared_secret = encrypt(public_key)

    return ciphertext, shared_secret