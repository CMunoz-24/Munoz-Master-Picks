# player_stats_helper.py

import requests
import pandas as pd
import signal
from pybaseball import playerid_lookup, statcast_batter
import json
import os
import json
with open("data/player_ids.json", "r") as f:
    CACHED_IDS = json.load(f)

# Load cached IDs if available
def load_cached_ids():
    path = "data/player_ids.json"
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return {}

CACHED_IDS = load_cached_ids()

# Timeout handler for statcast
def timeout_handler(signum, frame):
    raise TimeoutError("Statcast timed out")

signal.signal(signal.SIGALRM, timeout_handler)

def safe_player_lookup(player_name):
    player_name_clean = player_name.strip()
    if player_name_clean in CACHED_IDS:
        return CACHED_IDS[player_name_clean]

    try:
        name_parts = player_name_clean.replace('.', '').split()
        if len(name_parts) >= 2:
            first, last = name_parts[0], " ".join(name_parts[1:])
            results = playerid_lookup(last, first)
            if not results.empty:
                mlbam_id = results.iloc[0]['key_mlbam']
                return mlbam_id
    except Exception as e:
        print(f"[LOOKUP ERROR] Could not resolve {player_name}: {e}")
    return None

def get_vs_pitcher_history(batter_name, pitcher_name):
    try:
        df = pd.read_csv("data/batter_vs_pitcher.csv")
        df = df[df["Batter"] == batter_name]
        df = df[df["Pitcher"] == pitcher_name]
        return df
    except Exception as e:
        print(f"[ERROR] BvP fallback failed: {e}")
        return pd.DataFrame()

def get_batter_vs_pitcher(batter_name, pitcher_name):
    try:
        df = pd.read_csv("data/batter_vs_pitcher.csv")
        batter_name_clean = batter_name.strip().lower()
        pitcher_name_clean = pitcher_name.strip().lower()
        df["Batter_cleaned"] = df["Batter"].str.strip().str.lower()
        df["Pitcher_cleaned"] = df["Pitcher"].str.strip().str.lower()
        match = df[
            (df["Batter_cleaned"] == batter_name_clean) &
            (df["Pitcher_cleaned"] == pitcher_name_clean)
        ]
        if not match.empty:
            return match.iloc[0].to_dict()
        return None
    except Exception as e:
        print(f"[ERROR] Batter vs Pitcher data missing or broken: {e}")
        return None
    
def get_pitcher_stats(player_name):
    try:
        # First try fallback CSV
        fallback = pd.read_csv("data/fallback_stats.csv")
        fallback["Name_cleaned"] = fallback["Name"].str.lower().str.strip()
        match = fallback[fallback["Name_cleaned"] == player_name.lower().strip()]
        if not match.empty:
            row = match.iloc[0]
            return {
                "ERA": float(row.get("ERA", 0.0)),
                "K/9": float(row.get("K_per_9", 0.0)),
                "IP": float(row.get("IP", 0.0))
            }

        # Else try live MLB API
        search_url = f"https://statsapi.mlb.com/api/v1/people/search?name={player_name}"
        search_response = requests.get(search_url).json()
        results = search_response.get("people", [])
        if not results:
            raise ValueError("Pitcher not found in MLB API")

        player_id = results[0]["id"]
        stats_url = f"https://statsapi.mlb.com/api/v1/people/{player_id}/stats?stats=season&group=pitching"
        stats_response = requests.get(stats_url).json()

        splits = stats_response["stats"][0]["splits"]
        if not splits:
            raise ValueError("No pitching stats available")

        stat = splits[0]["stat"]
        return {
            "ERA": float(stat.get("era", 0.0)),
            "K/9": float(stat.get("strikeOutsPer9Inn", 0.0)),
            "IP": float(stat.get("inningsPitched", 0.0))
        }

    except Exception as e:
        print(f"[PITCHER FALLBACK ERROR] {player_name}: {e}")
        return {
            "ERA": 4.50,
            "K/9": 7.5,
            "IP": 50.0
        }
    
def get_batter_stats(player_name):
    try:
        # FIRST: check fallback CSV
        fallback_df = pd.read_csv("data/fallback_stats.csv")
        fallback_df["Name_cleaned"] = fallback_df["Name"].str.strip().str.lower()
        player_name_clean = player_name.strip().lower()
        match = fallback_df[fallback_df["Name_cleaned"] == player_name_clean]
        if not match.empty:
            stats = match.iloc[0]
            return {
                "G": stats.get("G", 0),
                "AB": stats.get("AB", 0),
                "H": stats.get("H", 0),
                "HR": stats.get("HR", 0),
                "K": stats.get("K", 0),
                "BB": stats.get("BB", 0)
            }

        # ELSE try Statcast live
        mlbam_id = safe_player_lookup(player_name)
        if not mlbam_id:
            raise ValueError("Player ID not found")

        signal.alarm(3)  # max 3 seconds
        df = statcast_batter("2024-03-01", "2024-10-01", mlbam_id)
        signal.alarm(0)

        games = df.shape[0]
        hr = df[df["events"] == "home_run"].shape[0]
        hits = df[df["events"].isin(["single", "double", "triple", "home_run"])].shape[0]
        strikeouts = df[df["events"] == "strikeout"].shape[0]
        walks = df[df["events"] == "walk"].shape[0]

        return {
            "G": games,
            "AB": games,
            "H": hits,
            "HR": hr,
            "K": strikeouts,
            "BB": walks
        }

    except Exception as e:
        print(f"[FALLBACK ERROR] get_batter_stats: {e}")
        return {
            "G": 0, "AB": 0, "H": 0, "HR": 0, "K": 0, "BB": 0
        }

def load_batter_vs_pitcher_data():
    try:
        return pd.read_csv("data/batter_vs_pitcher.csv")
    except FileNotFoundError:
        print("[ERROR] Batter vs. Pitcher data file missing.")
        return pd.DataFrame()
