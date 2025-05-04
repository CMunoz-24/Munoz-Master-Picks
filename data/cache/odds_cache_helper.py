
import json
import os
from datetime import datetime, timedelta

CACHE_PATH = os.path.join("data", "cache", "odds_cache.json")
CACHE_TTL = timedelta(minutes=15)

def get_cached_odds():
    if os.path.exists(CACHE_PATH):
        with open(CACHE_PATH, "r") as f:
            data = json.load(f)
        timestamp = datetime.fromisoformat(data.get("timestamp", "1970-01-01T00:00:00"))
        if datetime.now() - timestamp < CACHE_TTL:
            print("[CACHE] Using cached odds data.")
            return data.get("odds", [])
    return None

def save_odds_cache(odds):
    with open(CACHE_PATH, "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "odds": odds
        }, f)
    print("[CACHE] Odds data cached.")
