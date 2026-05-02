# from pqcrypto.kem.ml_kem_768 import generate_keypair
# from security.key_protection import encrypt_private_key
# import os

# def generate_keys():

#     print("Generating Post-Quantum keys...")

#     public_key, private_key = generate_keypair()

#     password = input("Create master password: ")

#     encrypted_private, nonce = encrypt_private_key(private_key, password)

#     os.makedirs("keys", exist_ok=True)

#     with open("keys/public.key", "wb") as f:
#         f.write(public_key)

#     with open("keys/private.key.enc", "wb") as f:
#         f.write(nonce + encrypted_private)

#     print("Keys generated successfully")
import os
from pathlib import Path
from pqcrypto.kem.ml_kem_768 import generate_keypair
from security.key_protection import encrypt_private_key, decrypt_private_key

# Dynamically find the User's Home folder to avoid "C:/vault" permission issues
VAULT_ROOT = Path.home() / "PQCVault"
KEY_PATH = str(VAULT_ROOT / "keys" / "private.key.enc")
PUB_PATH = str(VAULT_ROOT / "keys" / "public.key")

def generate_keys():
    print("Generating Post-Quantum keys (ML-KEM-768)...")
    
    public_key, private_key = generate_keypair()
    password = input("Create Master Vault Password: ")

    # Encrypt the private key using your protection module
    encrypted_private, nonce = encrypt_private_key(private_key, password)

    # Ensure the directory exists
    os.makedirs(os.path.dirname(KEY_PATH), exist_ok=True)

    with open(PUB_PATH, "wb") as f:
        f.write(public_key)

    with open(KEY_PATH, "wb") as f:
        # Saving nonce + ciphertext so we can split it later during decryption
        f.write(nonce + encrypted_private)

    print(f"Keys generated successfully in {os.path.dirname(KEY_PATH)}")

def load_private_key(password: str):
    # Check if file exists to prevent crash
    if not os.path.exists(KEY_PATH):
        print("Error: Private key file not found!")
        return None

    with open(KEY_PATH, "rb") as f:
        data = f.read()
    
    print(f"DEBUG: Total file size: {len(data)} bytes")
    
    # Using 12 for the standard AES-GCM nonce
    nonce = data[:12] 
    ciphertext = data[12:]
    
    print(f"DEBUG: Nonce length: {len(nonce)}")
    print(f"DEBUG: Ciphertext length: {len(ciphertext)}")
    
    return decrypt_private_key(ciphertext, nonce, password)