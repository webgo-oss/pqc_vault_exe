import yaml
import sys
from pathlib import Path
from supabase import create_client, Client

CONFIG_PATH = Path.home() / "PQCVault" / "config.yaml"

def get_supabase_client() -> Client:
    """Safely initializes the Supabase client."""
    if not CONFIG_PATH.exists():
        return None
    
    with open(CONFIG_PATH, "r") as f:
        config = yaml.safe_load(f)
    
    url = config.get("supabase", {}).get("url")
    key = config.get("supabase", {}).get("key")

    if not url or not key or "your-public-anon-key" in key:
        return None
        
    return create_client(url, key)

supabase: Client = get_supabase_client()

def save_session(session):
    """Saves tokens to YAML."""
    if not CONFIG_PATH.exists(): return
    with open(CONFIG_PATH, "r") as f:
        config = yaml.safe_load(f)
    
    config["auth"] = {
        "refresh_token": session.refresh_token,
        "email": session.user.email
    }
    with open(CONFIG_PATH, "w") as f:
        yaml.dump(config, f)

def restore_session():
    """Tries to restore session using refresh token."""
    global supabase
    try:
        if supabase is None:
            supabase = get_supabase_client()
            
        if supabase is None: return False

        with open(CONFIG_PATH, "r") as f:
            config = yaml.safe_load(f)
        
        token = config.get("auth", {}).get("refresh_token")
        if not token: return False
        
        res = supabase.auth.set_session(token)
        save_session(res.session)
        return True
    except:
        return False