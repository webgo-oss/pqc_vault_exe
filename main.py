import os
import sys
import click
import yaml
import tempfile
import re
import subprocess
import pyperclip
import tkinter as tk
import time
from pathlib import Path
from rich.console import Console
from datetime import datetime
from crypto.pqc_keygen import generate_keys, load_private_key
from crypto.aes_encrypt import encrypt_file
from crypto.pqc_encrypt import generate_shared_secret
from crypto.aes_decrypt import decrypt_file
from crypto.pqc_decrypt import decrypt_aes_key
from crypto.signature import generate_signature_keys, generate_signature
from vault.bundle import create_bundle
from vault.load_bundle import load_bundle
from supabase_config import supabase, save_session, restore_session
from prompt_toolkit.application import Application
from prompt_toolkit.layout import Layout
from prompt_toolkit.widgets import Frame, TextArea
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.styles import Style
from tkinter import filedialog
from rich.table import Table

VAULT_ROOT = Path.home() / "PQCVault" 

KEYS_DIR = VAULT_ROOT / "keys"
RECOVERED_DIR = VAULT_ROOT / "recovered"
CONFIG_PATH = VAULT_ROOT / "config.yaml"
console = Console(force_terminal=True, color_system="truecolor", highlight=True)

def ensure_env():
    """Initializes paths, config, and the global Supabase client."""
    global supabase 

    for path in [VAULT_ROOT, KEYS_DIR, RECOVERED_DIR]:
        path.mkdir(parents=True, exist_ok=True)
    
    if not CONFIG_PATH.exists():
        default_config = {
            "supabase": {
                "url": "your url",
                "key": "your key " 
            },
            "auth": {"refresh_token": None, "email": None}
        }
        with open(CONFIG_PATH, "w") as f:
            yaml.dump(default_config, f)

    try:
        with open(CONFIG_PATH, "r") as f:
            cfg = yaml.safe_load(f)
            url = cfg["supabase"]["url"]
            key = cfg["supabase"]["key"]
            
            if supabase is None:
                from supabase import create_client
                supabase = create_client(url, key)
    except Exception as e:
        console.print(f"[bold red]ENV ERROR:[/] Could not initialize security client: {e}")

if getattr(sys, 'frozen', False):
    bundle_dir = sys._MEIPASS
else:
    bundle_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(bundle_dir)

if os.name == 'nt' and 'WT_SESSION' not in os.environ:
    try:
        if getattr(sys, 'frozen', False):
            cmd = [sys.executable]
        else:
            cmd = [sys.executable, os.path.abspath(sys.argv[0])]
        cmd.extend(sys.argv[1:])

        subprocess.Popen(["wt.exe", *cmd])
    except FileNotFoundError:
        pass
    sys.exit()

def normalize_filename(name):
    name = name.lower()
    name = name.strip().replace(" ", "_")
    return re.sub(r'[^a-z0-9._-]', '', name)

def get_uid():
    """Fetch current user UUID from Supabase Auth."""
    user = supabase.auth.get_user()
    return user.user.id if user and user.user else None

def logo():
 console.print("""
[bold #C77DFF]██╗   ██████╗  ██████╗  ██████╗   ██╗   ██╗ █████╗ ██╗   ██╗██╗  ████████╗[/bold #C77DFF]
[bold #9D4EDD]╚██╗  ██╔══██╗██╔═══██╗██╔════╝   ██║   ██║██╔══██╗██║   ██║██║  ╚══██╔══╝[/bold #9D4EDD]
[bold #7B2CBF] ╚██╗ ██████╔╝██║   ██║██║        ██║   ██║███████║██║   ██║██║     ██║   [/bold #7B2CBF]
[bold #5A189A] ██╔╝ ██╔═══╝ ██║▄▄ ██║██║        ██║   ██║██╔══██║██║   ██║██║     ██║   [/bold #5A189A]
[bold #3C096C]██╔╝  ██║     ╚██████╔╝╚██████╗   ╚██████╔╝██║  ██║╚██████╔╝███████╗██║   [/bold #3C096C]
[bold #3C096C]╚═╝   ╚═╝      ╚══▀▀═╝  ╚═════╝    ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝   [/bold #3C096C]

""")
def success(msg):
    console.print(f"[bold green]✔ {msg}[/bold green]")

def error(msg):
    console.print(f"[bold red]✖ {msg}[/bold red]")

def info(msg):
    console.print(f"[bold cyan]→ {msg}[/bold cyan]")

def warn(msg):
    console.print(f"[bold yellow]⚠ {msg}[/bold yellow]")

def force_auth():
    if restore_session(): 
        return True
    
    global supabase
    ensure_env()
    
    retries = 0
    while supabase is None and retries < 3:
        ensure_env()
        time.sleep(1)
        retries += 1

    console.print(f"\n[bold #C77DFF] VAULT ACCESS GATE [/][#3C096C] {'—'*36}[/]")

    try:
        with open(CONFIG_PATH, "r") as f: 
            config = yaml.safe_load(f) or {}
    except: 
        config = {}

    owner_email = config.get("auth", {}).get("email")
    
    if owner_email:
        console.print(f" [#3C096C]│[/] [#C0C0C0]Hardware Status :[/] [#ff5555]LOCKED[/]")
        console.print(f" [#3C096C]│[/] [#C0C0C0]Linked Account  :[/] [#9D4EDD]{owner_email[:3]}***{owner_email[-4:]}[/]")
    else:
        console.print(f" [#3C096C]│[/] [#C0C0C0]Hardware Status :[/] [#E1AD01]UNREGISTERED[/]")
        console.print(f" [#3C096C]│[/] [#6B7280]No local identity found. Please Register.[/]")

    console.print(f" [#3C096C]│[/]")

    raw_email = console.input(f" [#3C096C]│[/] [bold #C77DFF]EMAIL    : [/]")
    email = "".join(re.findall(r'[a-zA-Z0-9@._+-]', raw_email))

    if owner_email and email != owner_email:
        console.print(f" [#3C096C]╰─[/] [bold #ff5555]ACCESS DENIED:[/] Device linked to another identity.")
        return False

    password = console.input(f" [#3C096C]│[/] [bold #C77DFF]PASSWORD : [/]", password=True).strip()

    try:
        if supabase is None: raise ConnectionError("Client not ready")
        
        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
        if res.session:
            if not owner_email:
                config.setdefault("auth", {})["email"] = email
                with open(CONFIG_PATH, "w") as f: yaml.dump(config, f)
            
            save_session(res.session)
            console.print(f" [#3C096C]╰─[/] [bold #62baad]DECRYPTED:[/] Session authenticated successfully.")
            return True
            
    except Exception:
        if not owner_email:
            console.print(f" [#3C096C]│[/] [#C0C0C0]Identity not found. Initializing Genesis...[/]")
            
            if supabase is None:
                console.print(f" [#3C096C]╰─[/] [bold #ff5555]FATAL:[/] Supabase client failed to initialize.")
                return False

            try:
                reg = supabase.auth.sign_up({"email": email, "password": password})
                
                if reg and hasattr(reg, 'user') and reg.user:
                    if reg.session:
                        config.setdefault("auth", {})["email"] = email
                        with open(CONFIG_PATH, "w") as f: yaml.dump(config, f)
                        
                        save_session(reg.session)
                        console.print(f" [#3C096C]╰─[/] [bold #62baad]REGISTERED:[/] Genesis complete. Session active.")
                        return True
                    else:
                        console.print(f" [#3C096C]╰─[/] [#E1AD01]PENDING:[/] Confirm email link to activate vault.")
                        sys.exit(0)
                else:
                    console.print(f" [#3C096C]╰─[/] [bold #ff5555]CONFLICT:[/] Registration failed or email in use.")
                    return False

            except Exception as reg_err:
                err_msg = str(reg_err).lower()
                if "already" in err_msg:
                    console.print(f" [#3C096C]╰─[/] [bold #ff5555]IDENT-ERROR:[/] User exists. Check password.")
                else:
                    console.print(f" [#3C096C]╰─[/] [bold #ff5555]REGISTRY FAILED:[/] Connection timed out.")
                return False

    console.print(f" [#3C096C]╰─[/] [bold #ff5555]AUTH FAILED:[/] Invalid credentials.")
    return False
@click.group()
def cli():
    """Post-Quantum Secure Vault CLI"""
    pass

@cli.command()
def init():
    """Generate local Post-Quantum Cryptographic keys and signature identity."""
    
    console.print(f"\n[bold #E1AD01] IDENTITY GENESIS [/][#3C096C] {'—'*39}[/]")

    try:
        console.print(f" [#7B2CBF]█ PHASE 01[/] [#3C096C]│[/] [bold #C77DFF]PQC KEYPAIR GENERATION[/]")
        
        generate_keys()
        
        console.print(f" [#3C096C]          ╰─[/] [#C0C0C0]Kyber-1024 Crystals   [/] [#3C096C]──[/] [#62baad]ENCODED[/]")

        console.print(f"\n [#7B2CBF]█ PHASE 02[/] [#3C096C]│[/] [bold #9D4EDD]DIGITAL SIGNATURE ID[/]")
        
        generate_signature_keys()
        
        console.print(f" [#3C096C]          ╰─[/] [#C0C0C0]Dilithium-5 Identity [/] [#3C096C]──[/] [#62baad]STAMPED[/]")

        console.print(f"\n [#7B2CBF]█ PHASE 03[/] [#3C096C]│[/] [bold #E1AD01]LOCAL KEYRING STORAGE[/]")
        
        key_path = str(KEYS_DIR).replace(os.path.expanduser("~"), "~")
        console.print(f" [#3C096C]          ╰─[/] [#C0C0C0]Path: {key_path}[/] [#3C096C]──[/] [#62baad]LOCKED[/]")

        console.print(f"\n[#3C096C] {'—'*52}[/]")
        console.print(f" [bold #62baad]INITIALIZED[/] [#6B7280]| Local vault identity established and secured.[/]\n")

    except Exception as e:
        console.print(f"\n [#ff5555]█ GENESIS FAILURE[/] [#3C096C]│[/] [bold #ff5555]PERMISSION OR STORAGE ERROR[/]")
        console.print(f" [#3C096C]          ╰─[/] [#C0C0C0]{str(e)}[/]")
        console.print(f"\n[#3C096C] {'—'*52}[/]\n")
        
@cli.command()
@click.argument("file", nargs=-1)
def add(file):
    """Secure an asset and sync to the PQC Cloud."""
    file_path = " ".join(file)
    if not os.path.exists(file_path):
        console.print(f"\n [#ff5555]█ ERROR[/] [#3C096C]│[/] Source asset not located: {file_path}")
        return
    
    user_id = get_uid()
    file_name = normalize_filename(os.path.basename(file_path))
    
    console.print(f"\n[bold #C77DFF] SECURE UPLOAD [/][#3C096C] {'—'*38}[/]")
    
    try:
        check = supabase.table("files").select("id").eq("name", file_name).execute()
        
        if check.data:
            console.print(f" [#E1AD01]█ CONFLICT[/] [#3C096C]│[/] Asset already exists in cloud vault.")
            console.print(f" [#3C096C]          ╰─[/] [#C0C0C0]Trace found via audit index: {file_name}[/]")
            console.print(f"\n[#3C096C] {'—'*52}[/]\n")
            return

        console.print(f" [#7B2CBF]█ PHASE 01[/] [#3C096C]│[/] [bold #C77DFF]ENCRYPTION ENGINE[/]")
        
        ciphertext, shared_secret = generate_shared_secret()
        enc_data, nonce = encrypt_file(file_path, shared_secret)
        
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            create_bundle(enc_data, ciphertext, nonce, tmp.name)
            with open(tmp.name, "rb") as f: vault_bytes = f.read()
        
        sig = generate_signature(vault_bytes)
        
        console.print(f" [#3C096C]          │[/]")
        console.print(f" [#3C096C]          ╰─[/] [#62baad]PQC Bundle & Digital Signature Generated[/]")

        console.print(f"\n [#7B2CBF]█ PHASE 02[/] [#3C096C]│[/] [bold #9D4EDD]SYNCHRONIZATION[/]")
        opts = {"upsert": "true"}
        
        supabase.storage.from_("vault").upload(f"{user_id}/main/{file_name}.vault", vault_bytes, opts)
        console.print(f" [#3C096C]          │[/] [#C0C0C0]Primary Storage   [/] [#3C096C]──[/] [#62baad]OK[/]")
        
        supabase.storage.from_("vault").upload(f"{user_id}/sigs/{file_name}.sig", sig, opts)
        supabase.storage.from_("vault").upload(f"{user_id}/backups/{file_name}.vault", vault_bytes, opts)
        console.print(f" [#3C096C]          │[/] [#C0C0C0]Redundant Backup  [/] [#3C096C]──[/] [#62baad]OK[/]")

        db_res = supabase.table("files").insert({
            "name": file_name, 
            "size_kb": len(vault_bytes)/1024
        }).execute()
        
        if db_res.data:
            supabase.table("signatures").insert({
                "file_id": db_res.data[0]['id'], 
                "signature_path": f"{user_id}/sigs/{file_name}.sig"
            }).execute()
            console.print(f" [#3C096C]          ╰─[/] [#C0C0C0]Database Index    [/] [#3C096C]──[/] [#62baad]REGISTERED[/]")

        console.print(f"\n[#3C096C] {'—'*52}[/]")
        console.print(f" [bold #62baad]COMPLETED[/] [#6B7280]| Trace: {file_name}.vault secured.[/]\n")
        
    except Exception as e:
        console.print(f"\n [#ff5555]█ FAILURE[/] [#3C096C]│[/] [bold #ff5555]SYNC INTERRUPTED[/]")
        console.print(f" [#3C096C]          ╰─[/] [#C0C0C0]{str(e)}[/]")
        console.print(f"\n[#3C096C] {'—'*52}[/]\n")    
@cli.command()
def info():
    """Display current vault environment and list local assets."""
    
    console.print(f"\n[bold #E1AD01] VAULT ARCHITECTURE [/][#3C096C] {'—'*35}[/]")

    def clean_path(path_obj):
        return str(path_obj).replace(os.path.expanduser("~"), "~")

    console.print(f" [#7B2CBF]█ KEYRING STORAGE[/] [#3C096C]│[/] [#C0C0C0]{clean_path(KEYS_DIR)}[/]")
    
    if (KEYS_DIR / "private.key.enc").exists():
        console.print(f" [#3C096C]          ╰─[/] [#62baad]STATUS: ACTIVE IDENTITY FOUND[/]")
    else:
        console.print(f" [#3C096C]          ╰─[/] [#ff5555]STATUS: NO IDENTITY (Run 'init')[/]")

    console.print(f"\n [#7B2CBF]█ RECOVERY ROOT [/] [#3C096C]│[/] [#C0C0C0]{clean_path(RECOVERED_DIR)}[/]")
    
    if RECOVERED_DIR.exists():
        recovered_files = os.listdir(RECOVERED_DIR)
        file_count = len(recovered_files)
        console.print(f" [#3C096C]          ├─[/] [#C0C0C0]{file_count} total assets detected.[/]")
        if file_count > 0:
            console.print(f" [#3C096C]          │[/]")
            for idx, filename in enumerate(recovered_files, 1):
                connector = "└──" if idx == file_count else "├──"
                console.print(f" [#3C096C]          {connector}[/] [#C77DFF]{filename}[/]")
        else:
            console.print(f" [#3C096C]          ╰─[/] [#6B7280]No files currently in recovery.[/]")
    else:
        console.print(f" [#3C096C]          ╰─[/] [#ff5555]ERROR: Recovery directory missing.[/]")

    console.print(f"\n[#3C096C] {'—'*52}[/]\n")

@cli.command()
@click.argument("file", nargs=-1)
def extract(file):
    """Secure retrieval: Download, decrypt, and purge cloud record."""
    if not file:
        console.print(f"\n [#ff5555]█ ERROR[/] [#3C096C]│[/] Target identifier required.")
        return

    user_id = get_uid()
    file_name = normalize_filename(" ".join(file))
    
    console.print(f"\n[bold #9D4EDD] EXTRACTION PROTOCOL [/][#3C096C] {'—'*35}[/]")

    try:
        console.print(f" [#7B2CBF]█ PHASE 01[/] [#3C096C]│[/] [bold #C77DFF]VAULT DOWNLOAD[/]")
        
        res = supabase.storage.from_("vault").download(f"{user_id}/main/{file_name}.vault")
        
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(res)
            tmp_path = tmp.name
        
        console.print(f" [#3C096C]          ╰─[/] [#C0C0C0]PQC Bundle Downloaded[/] [#3C096C]──[/] [#62baad]OK[/]")

        console.print(f"\n [#7B2CBF]█ PHASE 02[/] [#3C096C]│[/] [bold #9D4EDD]DECRYPTION ENGINE[/]")
        
        try:
            enc_key, nonce, enc_data = load_bundle(tmp_path)
            shared_secret = decrypt_aes_key(enc_key) 
            original_data = decrypt_file(enc_data, nonce, shared_secret)

            output_path = RECOVERED_DIR / file_name
            with open(output_path, "wb") as f: 
                f.write(original_data)
            
            console.print(f" [#3C096C]          │[/] [#C0C0C0]AES Shared Secret   [/] [#3C096C]──[/] [#62baad]VERIFIED[/]")
            console.print(f" [#3C096C]          ╰─[/] [#C0C0C0]Local Export Path   [/] [#3C096C]──[/] [#62baad]CREATED[/]")

            console.print(f"\n [#7B2CBF]█ PHASE 03[/] [#3C096C]│[/] [bold #ff5555]SESSION TERMINATION[/]")
            
            supabase.storage.from_("vault").remove([
                f"{user_id}/main/{file_name}.vault", 
                f"{user_id}/sigs/{file_name}.sig"
            ])
            supabase.table("files").delete().eq("name", file_name).execute()
            
            console.print(f" [#3C096C]          ╰─[/] [#C0C0C0]Cloud Asset Purged  [/] [#3C096C]──[/] [#ff5555]CLEAN[/]")

        finally:
            if os.path.exists(tmp_path): os.remove(tmp_path)

        console.print(f"\n[#3C096C] {'—'*52}[/]")
        console.print(f" [bold #62baad]EXTRACTED[/] [#6B7280]| Vault closed. Asset exported to local disk.[/]\n")

    except Exception as e:
        console.print(f"\n [#ff5555]█ EXTRACTION FAILED[/] [#3C096C]│[/] [bold #ff5555]AUTHENTICATION OR NETWORK ERROR[/]")
        console.print(f" [#3C096C]          ╰─[/] [#C0C0C0]{str(e)}[/]")
        console.print(f"\n[#3C096C] {'—'*52}[/]\n")

@cli.command()
@click.argument("file", nargs=-1)
def restore(file):
    """Emergency Recovery from high-security cloud backups."""
    if not file:
        console.print(f"\n [#ff5555]█ ERROR[/] [#3C096C]│[/] Target identifier required.")
        return

    user_id = get_uid()
    file_name = normalize_filename(" ".join(file))
    
    console.print(f"\n[bold #62baad] RECOVERY PROTOCOL [/][#3C096C] {'—'*35}[/]")

    try:
        console.print(f" [#7B2CBF]█ PHASE 01[/] [#3C096C]│[/] [bold #C77DFF]BACKUP RETRIEVAL[/]")
        
        res = supabase.storage.from_("vault").download(f"{user_id}/backups/{file_name}.vault")
        
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(res)
            tmp_path = tmp.name
        
        console.print(f" [#3C096C]          ╰─[/] [#C0C0C0]Encrypted Asset Downloaded[/] [#3C096C]──[/] [#62baad]OK[/]")

        console.print(f"\n [#7B2CBF]█ PHASE 02[/] [#3C096C]│[/] [bold #9D4EDD]PQC DECRYPTION[/]")
        
        try:
            encrypted_key, nonce, encrypted_file_data = load_bundle(tmp_path)
            shared_secret = decrypt_aes_key(encrypted_key)
            original_data = decrypt_file(encrypted_file_data, nonce, shared_secret)
            
            output_path = RECOVERED_DIR / file_name
            with open(output_path, "wb") as f: 
                f.write(original_data)
                
            console.print(f" [#3C096C]          │[/] [#C0C0C0]AES-GCM Shared Secret[/] [#3C096C]──[/] [#62baad]RECONSTRUCTED[/]")
            console.print(f" [#3C096C]          ╰─[/] [#C0C0C0]Integrity Status     [/] [#3C096C]──[/] [#62baad]VERIFIED[/]")

        finally:
            if os.path.exists(tmp_path): os.remove(tmp_path)

        console.print(f"\n[#3C096C] {'—'*52}[/]")
        console.print(f" [bold #62baad]RESTORED[/] [#6B7280]| Asset: {output_path.name}[/]\n")

    except Exception as e:
        console.print(f"\n [#ff5555]█ RECOVERY FAILED[/] [#3C096C]│[/] [bold #ff5555]INTEGRITY BREACH OR KEY ERROR[/]")
        console.print(f" [#3C096C]          ╰─[/] [#C0C0C0]{str(e)}[/]")
        console.print(f"\n[#3C096C] {'—'*52}[/]\n")
@cli.command()
def audit():
    """High-fidelity system integrity & signature check."""
    user_id = get_uid()
    
    console.print(f"\n[bold #C77DFF] AUDIT LOG [/bold #C77DFF][#3C096C] {'—'*40}[/#3C096C]")

    try:
        db_res = supabase.table("files").select("name, size_kb, signatures(id)").execute()
        db_data = db_res.data or []
        db_names = [d['name'] for d in db_data]
        storage_files = supabase.storage.from_("vault").list(f"{user_id}/backups")

        console.print(f"\n [#7B2CBF]█ INDEXED ASSETS[/#7B2CBF]")
        
        if not db_data:
            console.print("   [#6B7280]No records found in database.[/#6B7280]")
        else:
            for f in db_data:
                sig_verified = f.get("signatures")
                status_color = "#62baad" if sig_verified else "#ff5555"
                sig_text = "VERIFIED" if sig_verified else "MISSING"
                
                console.print(
                    f"   [#3C096C]│[/#3C096C] [bold #fff6ff]{f['name'].ljust(28)}[/bold #fff6ff] "
                    f"[#3C096C]┃[/#3C096C] [#C0C0C0]{f['size_kb']:>7.1f} KB[/#C0C0C0] "
                    f"[#3C096C]┃[/#3C096C] [bold {status_color}]{sig_text}[/bold {status_color}]"
                )

        console.print(f"\n [#7B2CBF]█ PHYSICAL BACKUPS[/#7B2CBF]")
        
        valid_backups = [sf for sf in storage_files if sf['name'] != '.emptyFolderPlaceholder']
        
        if not valid_backups:
            console.print("   [#6B7280]No physical assets detected.[/#6B7280]")
        else:
            for sf in valid_backups:
                clean_name = sf['name'].replace('.vault', '')
                is_indexed = clean_name in db_names
                
                integrity_icon = "[#62baad]●[/#62baad]" if is_indexed else "[#E1AD01]○[/#E1AD01]"
                integrity_label = "SECURE" if is_indexed else "UNLINKED"
                
                console.print(
                    f"   [#3C096C]│[/#3C096C] {sf['name'].ljust(28)} "
                    f"[#3C096C]┃[/#3C096C] {integrity_icon} [#C0C0C0]{integrity_label}[/#C0C0C0]"
                )
        console.print(f"\n[#3C096C] {'—'*52}[/#3C096C]")
        console.print(f" [bold #62baad]COMPLETED[/bold #62baad] [#6B7280]| Trace ID: {user_id[:8]}[/#6B7280]\n")

    except Exception as e:
        console.print(f"[bold red]CRITICAL AUDIT FAILURE:[/bold red] {e}")@click.argument("file", nargs=-1)

@cli.command()
@click.argument("file", nargs=-1)
def delete(file):
    """De-index active records and transition to hidden backup."""
    if not file:
        console.print(f"\n [#ff5555]█ ERROR[/#ff5555] [#3C096C]│[/#3C096C] Target identifier required.")
        return

    user_id = get_uid()
    file_name = normalize_filename(" ".join(file))
    
    console.print(f"\n[bold #ff5555] PURGE PROTOCOL [/bold #ff5555][#3C096C] {'—'*38}[/#3C096C]")

    try:
        db_res = supabase.table("files").select("id").eq("name", file_name).execute()
        
        if not db_res.data:
            console.print(f" [#3C096C]│[/#3C096C] [#C0C0C0]Target Status:[/#C0C0C0] [bold #ff5555]NOT FOUND[/bold #ff5555]")
            console.print(f"\n[#3C096C] {'—'*52}[/#3C096C]\n")
            return

        console.print(f" [#3C096C]│[/#3C096C] [#C0C0C0]Target Asset :[/#C0C0C0] [bold #C77DFF]{file_name}[/bold #C77DFF]")
        console.print(f" [#3C096C]│[/#3C096C] [#C0C0C0]Action       :[/#C0C0C0] [#ff5555]ACTIVE PURGE[/#ff5555]")
        console.print(f" [#3C096C]│[/#3C096C] [#C0C0C0]Safety Net   :[/#C0C0C0] [#62baad]RETAIN CLOUD BACKUP[/#62baad]")
        console.print(f" [#3C096C]│[/#3C096C]")
        
        console.print(f"   [bold #ff5555]▶ AUTHORIZE PURGE?(YES/NO)[/bold #ff5555]", end="")
        if not click.confirm("", default=False, show_default=False):
            console.print(f"\n [bold #C0C0C0]ABORTED[/bold #C0C0C0] [#3C096C]│[/#3C096C] Protocol terminated by user.\n")
            return

        password = console.input(f" [#3C096C]│[/#3C096C] [bold #ff5555]MASTER KEY   : [/bold #ff5555]", password=True).strip()
        
        try:
            load_private_key(password) 
        except Exception:
            console.print(f" [#3C096C]╰─[/#3C096C] [bold #ff5555]ACCESS DENIED:[/#ff5555] Invalid Master Credentials.")
            console.print(f"\n[#3C096C] {'—'*52}[/#3C096C]\n")
            return

        console.print(f" [#3C096C]│[/#3C096C]")
        
        storage_paths = [f"{user_id}/main/{file_name}.vault", f"{user_id}/sigs/{file_name}.sig"]
        supabase.storage.from_("vault").remove(storage_paths)
        console.print(f" [#7B2CBF]█ PHASE 01[/#7B2CBF] [#3C096C]│[/#3C096C] [#C0C0C0]Primary Repository[/#C0C0C0] [#3C096C]───[/#3C096C] [#ff5555]PURGED[/#ff5555]")

        supabase.table("files").delete().eq("name", file_name).execute()
        console.print(f" [#7B2CBF]█ PHASE 02[/#7B2CBF] [#3C096C]│[/#3C096C] [#C0C0C0]Database Index    [/#C0C0C0] [#3C096C]───[/#3C096C] [#ff5555]DELETED[/#ff5555]")
        
        console.print(f" [#3C096C]          ╰─[/#3C096C] [#62baad]Cloud Backup Transitioned to Hidden Status[/#62baad]")
        console.print(f"\n[#3C096C] {'—'*52}[/#3C096C]")
        console.print(f" [bold #62baad]SUCCESS[/bold #62baad] [#6B7280]| {file_name} de-indexed successfully.[/#6B7280]\n")

    except Exception as e:
        console.print(f"\n [#ff5555]█ CRITICAL ERROR[/#ff5555] [#3C096C]│[/#3C096C] {str(e)}\n")
style = Style.from_dict({
    "frame.border": "#7B2CBF",
     "textarea": "#fff6ff",
     'selected-text': 'bg:#444444 #ffffff'
})
def get_input():
    textarea = TextArea(
        height=1,
        prompt="➜  ",
        style="class:textarea",
        multiline=False,
    )

    frame = Frame(
        textarea,
        title="C:\\Vault",
        style="class:frame"
    )

    kb = KeyBindings()

    @kb.add("c-a")
    def _(event):
        buffer = event.current_buffer
        buffer.cursor_position = 0
        buffer.start_selection()
        buffer.cursor_position = len(buffer.text)

    @kb.add("backspace")
    def _(event):
        buffer = event.current_buffer
        if buffer.selection_state:
            buffer.cut_selection()
        else:
            buffer.delete_before_cursor(count=1)

    @kb.add("c-o")
    def _(event):
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        file_path = filedialog.askopenfilename()
        if file_path:
            if textarea.buffer.selection_state:
                textarea.buffer.cut_selection()
            textarea.buffer.insert_text(file_path)
        root.destroy()

    @kb.add("c-c")
    def _(event):
        buffer = textarea.buffer
        if buffer.selection_state:
            copy_data = buffer.copy_selection()
            pyperclip.copy(copy_data.text)
            buffer.selection_state = None
        else:
            if textarea.text == "ARE YOU SURE? (y/n)": return
            old_text = textarea.text
            textarea.text = "ARE YOU SURE? (y/n)"
            
            @kb.add("y", eager=True)
            def _confirm(ev): ev.app.exit(result="exit")
            @kb.add("n", eager=True)
            def _cancel(ev):
                textarea.text = old_text
                try:
                    kb.remove("y")
                    kb.remove("n")
                except: pass

    @kb.add("c-v")
    def _(event):
        try:
            if textarea.buffer.selection_state:
                textarea.buffer.cut_selection()
            textarea.buffer.insert_text(pyperclip.paste())
        except: pass
    @kb.add("enter")
    def _(event):
        if textarea.text != "ARE YOU SURE? (y/n)":
            event.app.exit(result=textarea.text)

    app = Application(
        layout=Layout(frame),
        key_bindings=kb,
        style=style,
        full_screen=False,
        mouse_support=True,
    )
    
    app.layout.focus(textarea)
    return app.run()

if __name__ == "__main__":
    os.system('cls' if os.name == 'nt' else 'clear')
    
    logo()
    ensure_env()
    
    if not force_auth(): 
        sys.exit(1)

    if len(sys.argv) > 1:
        cli()
    else:
        os.chdir(VAULT_ROOT)
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        console.print(f"\n[bold #C77DFF]>> PQC VAULT SYSTEM <<[/][#3C096C] {'═'*49}[/]")
        console.print(f" [#3C096C]│[/]")
        console.print(f" [#3C096C]│[/] [bold #9D4EDD]System Time :[/] [#C0C0C0]{current_time}[/]")
        console.print(f" [#3C096C]│[/] [bold #9D4EDD]Status      :[/] [#62baad]ONLINE[/]")
        console.print(f" [#3C096C]│[/]")
        console.print(f" [#3C096C]│[/] [#6B7280]Type[/] [bold #C77DFF]HELP[/] [#6B7280]for command protocols[/]")
        console.print(f" [#3C096C]╰{'─'*69}[/]\n")

        while True:
            try:
                raw_input = get_input()
                
                if raw_input is None:
                    console.print(f"\n [#ff5555]█ SESSION TERMINATED[/] [#3C096C]│[/] Vault locked.\n")
                    break 

                cmd_line = raw_input.strip()
                
                if not cmd_line:
                    continue

                if cmd_line.lower() in ["exit", "quit", "q"]:
                    console.print(f"\n [#ff5555]█ SESSION TERMINATED[/] [#3C096C]│[/] Vault locked.\n")
                    break

                if cmd_line.lower() == "help":
                    console.print(f"\n [#7B2CBF]█ SYSTEM MANIFEST[/] [#3C096C] {'—'*52}[/]")
                    
                    protocol_table = Table(show_header=False, box=None, padding=(0, 2))
                    protocol_table.add_column("CMD", style="bold #9D4EDD", width=12)
                    protocol_table.add_column("SEP", style="#3C096C")
                    protocol_table.add_column("DESC", style="#C0C0C0")

                    protocols = {
                        "INIT": "Generate local PQC keys",
                        "ADD": "Encrypt & secure asset to vault",
                        "EXTRACT": "Decrypt asset & purge cloud",
                        "RESTORE": "Emergency cloud recovery",
                        "AUDIT": "Verify vault integrity logs",
                        "DELETE": "De-index asset (retains backup)",
                        "QUIT": "Terminate session & lock",
                        "INFO":"Show your current Keys&Recovred folders Status"
                    }
                    for cmd, desc in protocols.items():
                        protocol_table.add_row(cmd, "┃", desc)

                    console.print(f" [#7B2CBF]█ CORE PROTOCOLS[/]")
                    console.print(protocol_table)
                    console.print(f" [#3C096C]│[/]")

                    shortcut_table = Table(show_header=False, box=None, padding=(0, 2))
                    shortcut_table.add_column("KEY", style="bold #5A189A", width=12)
                    shortcut_table.add_column("SEP", style="#3C096C")
                    shortcut_table.add_column("DESC", style="#8B8B8B")

                    shortcuts = {
                        "CTRL + O": "Launch File Explorer (Quick Path)",
                        "CTRL + A": "Select all text in buffer",
                        "CTRL + V": "Paste from system clipboard",
                        "CTRL + C": "Copy Selection / Exit Prompt",
                        "BACKSPACE": "Delete character / selection"
                    }
                    for key, desc in shortcuts.items():
                        shortcut_table.add_row(key, "┃", desc)

                    console.print(f" [#7B2CBF]█ INTERFACE SHORTCUTS[/]")
                    console.print(shortcut_table)
                    console.print(f" [#3C096C]╰{'─'*69}[/]\n")
                    continue

                else:
                    console.print(f" [#7B2CBF]█ EXECUTE[/] [#3C096C]│[/] [bold #fff6ff]{cmd_line.upper()}[/]")
                    console.print(f" [#3C096C]│[/]")
                    
                    cli.main(args=cmd_line.split(), standalone_mode=False)
                    
                    console.print(f" [#3C096C]╰{'─'*69}[/]\n")
                
            except KeyboardInterrupt: 
                console.print(f"\n [#ff5555]█ INTERRUPT DETECTED[/] [#3C096C]│[/] Locking Vault.\n")
                break
            except Exception as e: 
                console.print(f" [#3C096C]│[/]")
                console.print(f" [#3C096C]╰─[/] [bold #ff5555]SYSTEM ERROR:[/] {e}\n")
                
    sys.exit(0)