import json
import os
from datetime import datetime, timedelta

ODDS_CACHE_PATH = "data/cache/odds_cache.json"
CACHE_EXPIRY_MINUTES = 15

def get_cached_odds():
    """Reads the cached odds file from the correct location."""
    if not os.path.exists(ODDS_CACHE_PATH):
        print("[CACHE] Odds cache not found.")
        return None

    try:
        with open(ODDS_CACHE_PATH, "r") as f:
            data = json.load(f)
            if isinstance(data, list) and len(data) > 0:
                print(f"[CACHE] Loaded {len(data)} cached games.")
                return data
            else:
                print("[CACHE] Cache exists but is empty or malformed.")
                return None
    except Exception as e:
        print(f"[ERROR] Failed to load odds cache: {e}")
        return None

def save_odds_cache(games):
    """Writes a clean list of game dicts to the cache file."""
    try:
        os.makedirs(os.path.dirname(ODDS_CACHE_PATH), exist_ok=True)
        with open(ODDS_CACHE_PATH, "w") as f:
            json.dump(games, f, indent=2)
        print(f"[CACHE] Odds saved to {ODDS_CACHE_PATH}")
    except Exception as e:
        print(f"[ERROR] Failed to save odds cache: {e}")

