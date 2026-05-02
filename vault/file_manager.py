import json
import base64
import os


def load_vault(path):

    if not os.path.exists(path):
        return {}

    with open(path, "r") as f:
        return json.load(f)


def save_vault(path, data):

    os.makedirs(os.path.dirname(path), exist_ok=True)

    with open(path, "w") as f:
        json.dump(data, f)


def add_file(vault_path, name, encrypted_data, nonce, ciphertext):

    vault = load_vault(vault_path)

    vault[name] = {
        "data": base64.b64encode(encrypted_data).decode(),
        "nonce": base64.b64encode(nonce).decode(),
        "ciphertext": base64.b64encode(ciphertext).decode()
    }

    save_vault(vault_path, vault)

    print("File stored in vault")


def list_files(vault_path):

    vault = load_vault(vault_path)

    print("\nVault Files")
    print("-----------")

    for file in vault:
        print(file)


def extract_file(vault_path, name):

    vault = load_vault(vault_path)

    if name not in vault:
        raise Exception("File not found in vault")

    item = vault[name]

    encrypted_data = base64.b64decode(item["data"])
    nonce = base64.b64decode(item["nonce"])
    ciphertext = base64.b64decode(item["ciphertext"])

    return encrypted_data, nonce, ciphertext


def delete_file(vault_path, name):

    vault = load_vault(vault_path)

    if name in vault:
        del vault[name]
        save_vault(vault_path, vault)
        print("File deleted")