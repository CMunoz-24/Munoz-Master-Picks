
import requests

def get_player_stat_profile(player_name):
    print(f"[INFO] Fetching base stats for {player_name}")
    return {
        "avg": 0.270,
        "obp": 0.340,
        "hr": 2,
        "rbi": 6,
        "runs": 5,
        "sb": 1
    }
