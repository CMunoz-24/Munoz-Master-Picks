import os
import json
from datetime import datetime, timedelta

CACHE_FILE = "odds_cache.json"
CACHE_EXPIRATION_MINUTES = 15

def is_cache_valid():
    """Check if the cached file exists and is not too old."""
    if not os.path.exists(CACHE_FILE):
        return False

    modified_time = datetime.fromtimestamp(os.path.getmtime(CACHE_FILE))
    if datetime.now() - modified_time > timedelta(minutes=CACHE_EXPIRATION_MINUTES):
        print("[CACHE] Cache is too old.")
        return False

    return True

def get_cached_odds():
    """Load odds from cache if valid."""
    if is_cache_valid():
        try:
            with open(CACHE_FILE, "r") as f:
                data = json.load(f)
                print("[CACHE] Loaded odds from cache.")
                return data
        except Exception as e:
            print(f"[CACHE ERROR] Failed to load: {e}")
    return []

def save_odds_cache(data):
    """Save odds to cache."""
    try:
        with open(CACHE_FILE, "w") as f:
            json.dump(data, f)
            print("[CACHE] Odds cached successfully.")
    except Exception as e:
        print(f"[CACHE ERROR] Failed to save: {e}")
