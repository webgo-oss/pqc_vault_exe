#  PQC Vault — Post-Quantum cryptography Vault

A **terminal-based secure file vault** powered by **Post-Quantum Cryptography (PQC)**.  
It allows you to encrypt, store, and manage files and other media securely using **Kyber (encryption)** and **Dilithium (signatures)** with cloud synchronization.

---

##  Download The App

-  Website: https://pqc-vault-live.vercel.app  
-  Download (Windows): https://github.com/webgo-oss/pqc_vault_exe/releases/latest/download/pqc-vault-1.0-setup-x64.exe  

---

##  Features

-  **Post-Quantum Key Generation**
  - Kyber-1024 for encryption
  - Dilithium-5 for digital signatures

-  **Secure File Encryption**
  - AES-GCM encryption with PQC shared secret
  - File bundling + signature protection

-  **Cloud Sync (Supabase)**
  - Upload encrypted vault files
  - Backup & restore support
  - Signature verification storage

-  **Smart CLI Interface**
  - Interactive terminal UI
  - Keyboard shortcuts (Ctrl+O, Ctrl+C, etc.)
  - Command-based workflow

-  **Security Layers**
  - Local keyring storage
  - Signed vault bundles
  - Session-based authentication

---

##  Project Structure

```
PQC-Vault/
│
├── main.py                <- Main CLI application
├── crypto/               <- Cryptographic modules
│   ├── pqc_keygen.py
│   ├── pqc_encrypt.py
│   ├── pqc_decrypt.py
│   ├── aes_encrypt.py
│   ├── aes_decrypt.py
│   └── signature.py
│
├── utils/
│   └── hash_utils.py     
│   
├── security/
│   ├── key_protection.py
│   └── password.py
│
├── vault/
│   ├── bundle.py
│   └── load_bundle.py
│
├── supabase_config.py    <- Supabase client & session
└── setup.py           <- setup configuration
```

---

## Installation

### 1. Clone the repo
```bash
git clone https://github.com/webgo-oss/pqc_vault_exe.git
cd pqc_vault_exe
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Add Your own URL(if seprate creation)
```bash
                "url": "database url",
                "key": "database key" 
```

---

##  Running the App

```bash
python main.py
```

On first run:
- Enter email & password
- Account will be created or logged in
- Session will be stored locally

---

##  Commands

| Command | Description |
|--------|------------|
| `init` | Generate PQC keys |
| `add <file>` | Encrypt & upload file |
| `extract <file>` | Download & decrypt file |
| `restore <file>` | Recover from backup |
| `audit` | Verify vault integrity |
| `delete <file>` | Remove file from vault |
| `info` | Show local vault status |
| `help` | Show all commands |
| `exit` | Exit vault |

---

##  Example Usage

```bash
init
add myfile.txt
extract myfile.txt
audit
```

---

##  Security Workflow

1. File is encrypted using **AES-GCM**
2. AES key is secured using **Kyber PQC**
3. Bundle is created with:
   - encrypted file
   - encrypted key
   - nonce
4. Bundle is digitally signed using **Dilithium**
5. Uploaded to secure cloud storage

---

##  Local Storage

- Keys: `~/PQCVault/keys`
- Recovered files: `~/PQCVault/recovered`
- Config: `~/PQCVault/config.yaml`

---

##  Keyboard Shortcuts

| Shortcut | Action |
|---------|--------|
| Ctrl + O | Open file picker |
| Ctrl + A | Select all |
| Ctrl + C | Copy / Exit prompt |
| Ctrl + V | Paste |
| Enter | Execute command |

---

##  Notes

- Do **NOT** share your config file (contains API keys)
- Keep your **master password safe**
- Lost keys = **data cannot be recovered**

---

##  Future Improvements

- GUI version
- File preview support
- Role-based access
- End-to-end sharing

---
