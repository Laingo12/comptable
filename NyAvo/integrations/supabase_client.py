from supabase import create_client, Client
from config import get_settings
from functools import lru_cache

settings = get_settings()

@lru_cache()
def get_supabase_client() -> Client:
    """Mamerina client Supabase voatokana."""
    if not settings.supabase_url or not settings.supabase_key:
        raise RuntimeError("Supabase non configuré (supabase_url na supabase_key vide)")
    return create_client(settings.supabase_url, settings.supabase_key)

def get_supabase_admin() -> Client:
    """Mamerina client Supabase admin (service_role) ho an'ny scripts."""
    if not settings.supabase_url or not settings.supabase_service_key:
        raise RuntimeError("Supabase admin non configuré")
    return create_client(settings.supabase_url, settings.supabase_service_key)