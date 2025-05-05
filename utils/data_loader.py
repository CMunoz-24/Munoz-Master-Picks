
import os
import pandas as pd
from fallbacks.fangraphs import get_fangraphs_stats
from fallbacks.chadwick import load_chadwick_player_mapping
import requests
from datetime import datetime

def is_primary_data_available():
    # Later you can make this check dynamic (e.g., test API responses)
    return os.getenv("ODDS_API_WORKING", "false").lower() == "true"

def get_combined_fallback_data():
    print("[WARNING] Primary data unavailable. Using fallback sources.")

    print("[INFO] Fetching FanGraphs data...")
    fg_df = get_fangraphs_stats()

    print("[INFO] Loading Chadwick player registry...")
    chadwick_df = load_chadwick_player_mapping()

    return {
        "fangraphs": fg_df,
        "chadwick": chadwick_df
    }

def get_live_or_fallback_data():
    if is_primary_data_available():
        print("[INFO] Using primary MLB Stats + Odds API data.")
        return {"primary": "Data from Odds + MLB Stats API"}
    else:
        return get_combined_fallback_data()
    
def load_fallback_stats():
    try:
        return pd.read_csv("data/fallback_stats.csv")
    except FileNotFoundError:
        print("[ERROR] Fallback stats file missing.")
        return pd.DataFrame()
    
def get_mlb_schedule_fallback():
    today = datetime.now().strftime("%Y-%m-%d")
    url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={today}"
    response = requests.get(url)
    if response.status_code != 200:
        print("[ERROR] Failed to fetch fallback schedule.")
        return []

    data = response.json()
    games = []

    for date in data.get("dates", []):
        for game in date.get("games", []):
            games.append({
                "id": str(game.get("gamePk")),
                "teams": f"{game['teams']['away']['team']['name']} vs {game['teams']['home']['team']['name']}",
                "venue": game['venue']['name'],
                "commence_time": game['gameDate'],
                "source": "MLB Schedule Fallback"
            })

    print(f"[INFO] Loaded {len(games)} games from MLB fallback.")
    return games
