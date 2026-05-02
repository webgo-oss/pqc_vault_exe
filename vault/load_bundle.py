import json
import hashlib
from security.password import verify_password
from crypto.signature import verify_signature


def load_bundle(path):

    with open(path, "r") as f:
        bundle = json.load(f)

    password = input("Enter vault password: ")

    if not verify_password(bundle["password_hash"], password):
        raise Exception("Wrong password!")

    signature = bytes.fromhex(bundle["signature"])

    unsigned_bundle = dict(bundle)
    del unsigned_bundle["signature"]

    bundle_bytes = json.dumps(unsigned_bundle, sort_keys=True).encode()

    if not verify_signature(bundle_bytes, signature):
        raise Exception("Signature verification failed!")

    encrypted_key = bytes.fromhex(bundle["encrypted_key"])
    nonce = bytes.fromhex(bundle["nonce"])
    encrypted_file = bytes.fromhex(bundle["file_data"])

    stored_hash = bytes.fromhex(bundle["integrity_hash"])

    integrity_hash = hashlib.sha256(encrypted_file).digest()

    if integrity_hash != stored_hash:
        raise Exception("Vault file corrupted!")

    return encrypted_key, nonce, encrypted_file