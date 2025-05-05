import sys
import os
sys.path.append(os.path.abspath("."))  # <-- Add this to fix import issues

import json
import requests
import subprocess
from flask import Flask
from multiprocessing import Process
import time

games = []
def test_odds_cache_structure():
    print("[🔍] Testing odds_cache.json structure...")
    path = "data/cache/odds_cache.json"
    if not os.path.exists(path):
        raise FileNotFoundError("❌ odds_cache.json not found!")

    with open(path) as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("❌ odds_cache.json is not a list!")

    required_keys = {"id", "teams", "date", "ml", "spread", "ou"}
    for game in data:
        if not required_keys.issubset(set(game.keys())):
            raise ValueError(f"❌ Missing keys in odds_cache game: {game}")
    print("✅ odds_cache.json format is valid.\n")

def test_fallback_stats_structure():
    print("[🔍] Testing fallback_stats.csv structure...")
    import pandas as pd
    df = pd.read_csv("data/fallback_stats.csv")
    required_cols = {"Name", "G", "AB", "H", "HR", "K", "BB"}
    if not required_cols.issubset(set(df.columns)):
        raise ValueError("❌ Missing columns in fallback_stats.csv")
    print("✅ fallback_stats.csv format is valid.\n")

def test_game_detail_route():
    print("[🔍] Testing Flask /game/<id> route...")

    # Start Flask in a subprocess
    flask_process = subprocess.Popen(["python3", "main.py", "--host=127.0.0.1", "--port=5000"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    time.sleep(4)  # Give Flask time to spin up

    try:
        from main import get_cached_or_fresh_games
        global games
        games = get_cached_or_fresh_games()

        if not games:
            raise ValueError("❌ odds_cache.json is empty.")

        test_game_id = games[0]["id"]
        url = f"http://127.0.0.1:5000/game/{test_game_id}"
        response = requests.get(url)

        # 🔍 Debugging output
        print("Status code:", response.status_code)
        print("Response body preview:", response.text[:500])

        assert response.status_code == 200
        assert "Player Probabilities" in response.text or "Recommendations" in response.text
        print(f"✅ /game/{test_game_id} route loaded successfully.\n")
    finally:
        flask_process.terminate()

def run_tests():
    print("\n🧪 Running Full Muñoz Master Picks Integration Test...\n")
    test_odds_cache_structure()
    test_fallback_stats_structure()
    test_game_detail_route()
    print("✅✅✅ All system checks passed. You're good to go!")

if __name__ == "__main__":
    run_tests()
