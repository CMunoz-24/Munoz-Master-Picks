
import requests

def fetch_pitcher_data_by_name(name):
    # Placeholder for live API lookup
    print(f"[INFO] Fetching live pitcher stats for {name}")
    return {
        "era": 3.75,
        "whip": 1.25,
        "so9": 8.2
    }

def get_player_season_stats(name):
    # Placeholder for live player season stats
    print(f"[INFO] Fetching live season stats for {name}")
    return {
        "avg": 0.260,
        "obp": 0.330,
        "hr": 1,
        "rbi": 5,
        "runs": 6,
        "sb": 2
    }

def get_pitcher_stats_by_name(name):
    return fetch_pitcher_data_by_name(name)
