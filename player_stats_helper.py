# player_stats_helper.py

import requests
import pandas as pd
import requests
from pybaseball import playerid_lookup, statcast_batter

def safe_player_lookup(player_name):
    try:
        name_parts = player_name.strip().replace('.', '').split()
        if len(name_parts) >= 2:
            first, last = name_parts[0], " ".join(name_parts[1:])
            results = playerid_lookup(last, first)
            if results is not None and not results.empty:
                return results.iloc[0]['key_mlbam']
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
        df = pd.read_csv("data/batter_vs_pitcher.csv")  # Must match project path
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

def get_batter_stats(player_name):
    try:
        pid_df = safe_player_lookup(player_name)
        if pid_df.empty:
            raise ValueError("No player ID found")

        mlbam_id = safe_player_lookup(player_name)
        df = statcast_batter("2024-03-01", "2024-10-01", player_id)
        games = df.shape[0]
        hr = df[df["events"] == "home_run"].shape[0]
        hits = df[df["events"].isin(["single", "double", "triple", "home_run"])].shape[0]
        strikeouts = df[df["events"] == "strikeout"].shape[0]
        walks = df[df["events"] == "walk"].shape[0]
        at_bats = df.shape[0]

        return {
            "G": games,
            "AB": at_bats,
            "H": hits,
            "HR": hr,
            "K": strikeouts,
            "BB": walks
        }

    except Exception:
        # Fallback to CSV if pybaseball fails
        fallback_df = pd.read_csv("data/fallback_stats.csv")

        # Normalize player names for matching
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
        else:
            print(f"[FALLBACK ERROR] No match for: {player_name}")
            return None
        
def get_pitcher_stats(player_name):
    try:
        # Try live data
        pid_df = safe_player_lookup(player_name)
        if pid_df.empty:
            raise ValueError("Player not found in lookup")
        mlbam_id = safe_player_lookup(player_name)
        stats = pitching_stats(player_id)
        return {
            "K/9": float(stats.get("k_per_9", 0)),
            "ERA": float(stats.get("era", 0)),
            "IP": float(stats.get("ip", 0))
        }
    except Exception as e:
        print(f"[FALLBACK ERROR] {e}")
        try:
            fallback = pd.read_csv("data/fallback_stats.csv")
            fallback["name_clean"] = fallback["Name"].str.lower().str.strip()
            match = fallback[fallback["name_clean"] == player_name.lower().strip()]
            if not match.empty:
                row = match.iloc[0]
                return {
                    "K/9": float(row.get("K_per_9", 0)),
                    "ERA": float(row.get("ERA", 0)),
                    "IP": float(row.get("IP", 0))
                }
        except Exception as fe:
            print(f"[FALLBACK CSV ERROR] {fe}")
        return {"K/9": 0, "ERA": 0, "IP": 0}

def fetch_pitcher_data_by_name(name):
    try:
        # Search player by name to get their ID
        search_url = f"https://statsapi.mlb.com/api/v1/people/search?name={name}"
        search_response = requests.get(search_url).json()
        results = search_response.get("people", [])
        if results is None:
            raise ValueError(f"No player found with name: {name}")
        
        player_id = results[0]["id"]

        # Get player stats by ID
        stats_url = f"https://statsapi.mlb.com/api/v1/people/{player_id}?hydrate=stats(group=[pitching],type=season)"
        stats_response = requests.get(stats_url).json()
        player = stats_response["people"][0]

        era = float(player["stats"][0]["splits"][0]["stat"]["era"])
        whip = float(player["stats"][0]["splits"][0]["stat"]["whip"])
        handedness = player["pitchHand"]["code"]

        return {
            "era": era,
            "whip": whip,
            "throws": handedness
        }
    except Exception as e:
        print(f"[ERROR] Failed to fetch pitcher data for {name}: {e}")
        return {
            "era": 4.50,
            "whip": 1.30,
            "throws": "R"
        }

def get_player_season_stats(player_name):
    try:
        search_url = f"https://statsapi.mlb.com/api/v1/people/search?name={player_name}"
        res = requests.get(search_url)
        data = res.json()

        if "people" not in data or not data["people"]:
            return {}

        player_id = data["people"][0]["id"]
        stat_url = f"https://statsapi.mlb.com/api/v1/people/{player_id}/stats?stats=season&group=hitting,pitching"
        stat_res = requests.get(stat_url).json()

        stats = {}

        for record in stat_res.get("stats", []):
            splits = record.get("splits", [])
            if splits is None or len(splits) == 0:
                continue
            stat_type = record.get("group", {}).get("displayName", "").lower()
            stat_data = splits[0].get("stat", {})
            if stat_type == "hitting":
                stats = {
                    "AVG": stat_data.get("avg", "-"),
                    "HR": stat_data.get("homeRuns", "-"),
                    "RBI": stat_data.get("rbi", "-"),
                    "OBP": stat_data.get("obp", "-")
                }
            elif stat_type == "pitching":
                stats = {
                    "ERA": stat_data.get("era", "-"),
                    "WHIP": stat_data.get("whip", "-"),
                    "SO/9": stat_data.get("strikeOutsPer9Inn", "-"),
                    "W-L": f"{stat_data.get('wins', '-')}-{stat_data.get('losses', '-')}"
                }

        return stats
    except Exception as e:
        print(f"Failed to get stats for {player_name}: {e}")
        return {}

def get_pitcher_stats_by_name(name):
    data = fetch_pitcher_data_by_name(name)
    return {
        "ERA": round(data.get("era", 4.00), 2),
        "handedness": data.get("throws", "R")
    }

def load_batter_vs_pitcher_data():
    try:
        return pd.read_csv("data/batter_vs_pitcher.csv")
    except FileNotFoundError:
        print("[ERROR] Batter vs. Pitcher data file missing.")
        return pd.DataFrame()

