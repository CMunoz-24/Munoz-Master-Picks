import requests
import json
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("ODDS_API_KEY")
CACHE_PATH = "data/cache/odds_cache.json"

def fetch_and_cache_odds():
    url = f"https://api.the-odds-api.com/v4/sports/baseball_mlb/odds/?regions=us&markets=spreads,totals,h2h&apiKey={API_KEY}"
    response = requests.get(url)
    if response.status_code != 200:
        print("[ERROR] Failed to fetch odds:", response.status_code, response.text)
        return

    odds_data = response.json()
    cached = {
        "timestamp": datetime.now().isoformat(),
        "odds": odds_data
    }

    os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)
    with open(CACHE_PATH, "w") as f:
        json.dump(cached, f, indent=2)

    print(f"[SUCCESS] Odds cached at {CACHE_PATH} — {len(odds_data)} games saved.")

if __name__ == "__main__":
    fetch_and_cache_odds()
