# refresh_fallback_stats.py

import requests
import json
import csv
import os
from datetime import datetime

def get_all_team_ids():
    url = "https://statsapi.mlb.com/api/v1/teams?sportId=1"
    response = requests.get(url)
    data = response.json()
    return [team["id"] for team in data.get("teams", [])]

def get_team_roster(team_id):
    url = f"https://statsapi.mlb.com/api/v1/teams/{team_id}/roster"
    response = requests.get(url)
    return response.json().get("roster", [])

def get_player_stats(player_id):
    url = f"https://statsapi.mlb.com/api/v1/people/{player_id}?hydrate=stats(group=[hitting,pitching],type=season)"
    response = requests.get(url)
    data = response.json()
    person = data.get("people", [{}])[0]
    name = person.get("fullName", "Unknown Player")
    stats_blocks = person.get("stats", [])

    stats = {"Name": name}
    for block in stats_blocks:
        group = block.get("group", {}).get("displayName", "").lower()
        if not block.get("splits"):
            continue
        s = block["splits"][0].get("stat", {})
        if group == "hitting":
            stats.update({
                "G": s.get("gamesPlayed", 0),
                "AB": s.get("atBats", 0),
                "H": s.get("hits", 0),
                "HR": s.get("homeRuns", 0),
                "K": s.get("strikeOuts", 0),
                "BB": s.get("baseOnBalls", 0)
            })
        elif group == "pitching":
            stats.update({
                "ERA": s.get("era", 0.0),
                "K_per_9": s.get("strikeOutsPer9Inn", 0.0),
                "IP": s.get("inningsPitched", 0.0)
            })
    return stats

def refresh_fallback_stats():
    print("[INFO] Starting fallback stat refresh...")
    all_team_ids = get_all_team_ids()
    players = []
    for tid in all_team_ids:
        print(f"[INFO] Fetching roster for team {tid}...")
        roster = get_team_roster(tid)
        for player in roster:
            player_id = player["person"]["id"]
            try:
                stats = get_player_stats(player_id)
                players.append(stats)
            except Exception as e:
                print(f"[ERROR] Could not fetch stats for player ID {player_id}: {e}")

    print(f"[INFO] Found {len(players)} players.")
    out_path = "data/fallback_stats.csv"
    os.makedirs("data", exist_ok=True)

    if players:
        keys = set().union(*(d.keys() for d in players))
        with open(out_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=sorted(keys))
            writer.writeheader()
            writer.writerows(players)
        print(f"[✅ DONE] Fallback stats saved to {out_path}")
    else:
        print("[⚠️ WARNING] No player data written.")

if __name__ == "__main__":
    refresh_fallback_stats()
