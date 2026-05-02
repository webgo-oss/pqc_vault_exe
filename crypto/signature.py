import os
from nacl.signing import SigningKey, VerifyKey
from nacl.exceptions import BadSignatureError

KEY_DIR = "keys"

PRIVATE_KEY_FILE = "keys/sign_private.key"
PUBLIC_KEY_FILE = "keys/sign_public.key"


def generate_signature_keys():

    os.makedirs(KEY_DIR, exist_ok=True)

    signing_key = SigningKey.generate()
    verify_key = signing_key.verify_key

    with open(PRIVATE_KEY_FILE, "wb") as f:
        f.write(signing_key.encode())

    with open(PUBLIC_KEY_FILE, "wb") as f:
        f.write(verify_key.encode())

    print("Signature keys generated")


def generate_signature(data):

    with open(PRIVATE_KEY_FILE, "rb") as f:
        signing_key = SigningKey(f.read())

    return signing_key.sign(data).signature


def verify_signature(data, signature):

    try:

        with open(PUBLIC_KEY_FILE, "rb") as f:
            verify_key = VerifyKey(f.read())

        verify_key.verify(data, signature)

        return True

    except BadSignatureError:
        return False