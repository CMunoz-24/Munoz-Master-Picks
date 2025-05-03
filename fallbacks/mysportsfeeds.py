
import requests
import pandas as pd
import os
from base64 import b64encode

def get_mysportsfeeds_stats(season="2024-regular"):
    username = os.getenv("MSF_USERNAME")
    password = os.getenv("MSF_PASSWORD")
    if not username or not password:
        raise Exception("Missing MySportsFeeds API credentials in .env")

    credentials = b64encode(f"{username}:{password}".encode()).decode("utf-8")
    headers = {
        "Authorization": f"Basic {credentials}",
        "Accept": "application/json"
    }

    url = f"https://api.mysportsfeeds.com/v2.1/pull/mlb/{season}/player_gamelogs.json?team=*&date=latest"

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()

        gamelogs = data.get("gamelogs", [])
        stats_list = []

        for log in gamelogs:
            player = log.get("player", {})
            stats = log.get("stats", {}).get("batting", {})
            stats_list.append({
                "id": player.get("id"),
                "first_name": player.get("firstName"),
                "last_name": player.get("lastName"),
                "avg": stats.get("avg"),
                "hr": stats.get("hr"),
                "rbi": stats.get("rbi"),
                "obp": stats.get("obp"),
                "games_played": log.get("gamesPlayed")
            })

        df = pd.DataFrame(stats_list)
        df.to_csv("data/cache/mysportsfeeds_fallback.csv", index=False)
        return df

    except Exception as e:
        print("[ERROR] MySportsFeeds fallback failed:", e)
        return pd.DataFrame()
