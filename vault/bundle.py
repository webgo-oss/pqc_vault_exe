import json
import hashlib
from security.password import hash_password
from crypto.signature import generate_signature


def create_bundle(file_data, encrypted_key, nonce, output_path):

    password = input("Set vault password: ")

    password_hash = hash_password(password)

    integrity_hash = hashlib.sha256(file_data).digest()

    bundle = {
        "password_hash": password_hash,
        "encrypted_key": encrypted_key.hex(),
        "nonce": nonce.hex(),
        "file_data": file_data.hex(),
        "integrity_hash": integrity_hash.hex()
    }

    bundle_bytes = json.dumps(bundle, sort_keys=True).encode()

    signature = generate_signature(bundle_bytes)

    bundle["signature"] = signature.hex()

    with open(output_path, "w") as f:
        json.dump(bundle, f)

    print("Vault bundle created with digital signature")