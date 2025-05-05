import json
import os
from datetime import datetime, timedelta

ODDS_CACHE_PATH = "data/cache/odds_cache.json"
CACHE_EXPIRY_MINUTES = 15

def get_cached_odds():
    if not os.path.exists(ODDS_CACHE_PATH):
        print("[CACHE] Odds cache not found.")
        return None

    try:
        with open(ODDS_CACHE_PATH, "r") as f:
            data = json.load(f)
            if not isinstance(data, dict) or "games" not in data or "timestamp" not in data:
                print("[CACHE] Malformed cache structure.")
                return None

            ts = datetime.fromisoformat(data["timestamp"])
            if datetime.now() - ts > timedelta(minutes=CACHE_EXPIRY_MINUTES):
                print("[CACHE] Odds cache expired.")
                return None

            print(f"[CACHE] Loaded {len(data['games'])} games from fresh cache.")
            return data["games"]

    except Exception as e:
        print(f"[ERROR] Failed to load odds cache: {e}")
        return None

def save_odds_cache(games_list):
    try:
        os.makedirs(os.path.dirname(ODDS_CACHE_PATH), exist_ok=True)
        payload = {
            "timestamp": datetime.now().isoformat(),
            "games": games_list
        }
        with open(ODDS_CACHE_PATH, "w") as f:
            json.dump(payload, f, indent=2)
        print(f"[CACHE] Odds saved to {ODDS_CACHE_PATH}")
    except Exception as e:
        print(f"[ERROR] Failed to save odds cache: {e}")
