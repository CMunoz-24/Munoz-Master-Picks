# refresh_fallback_stats.py

import pandas as pd
import requests
import time
import json
from datetime import datetime
from pybaseball import statcast_batter, playerid_lookup

START_DATE = "2024-03-01"
END_DATE = "2024-10-01"

def get_active_players():
    print("[INFO] Fetching all active MLB players...")
    url = "https://statsapi.mlb.com/api/v1/people?season=2024&hydrate=stats(group=[hitting,pitching],type=season)&sportId=1&active=true"
    response = requests.get(url)

    print("[DEBUG] Raw player API response:")
    print(json.dumps(response.json(), indent=2))  # 👈 Add this line

    return response.json().get("people", [])

players = get_active_players()
print(f"[INFO] Found {len(players)} players")

batter_records = []
pitcher_records = []
id_cache = {}

for person in players:
    try:
        name = person["fullName"]
        player_id = person["id"]
        position = person.get("primaryPosition", {}).get("abbreviation", "")
        id_cache[name] = player_id

        print(f"[FETCHING] {name} ({position})")

        if position == "P":
            stats_url = f"https://statsapi.mlb.com/api/v1/people/{player_id}/stats?stats=season&group=pitching"
            res = requests.get(stats_url).json()
            splits = res.get("stats", [{}])[0].get("splits", [])
            if splits:
                stat = splits[0]["stat"]
                pitcher_records.append({
                    "Name": name,
                    "ERA": float(stat.get("era", 0.0)),
                    "K_per_9": float(stat.get("strikeOutsPer9Inn", 0.0)),
                    "IP": float(stat.get("inningsPitched", 0.0))
                })
        else:
            df = statcast_batter(START_DATE, END_DATE, player_id)
            time.sleep(1)  # Rate limiting
            games = df.shape[0]
            hr = df[df["events"] == "home_run"].shape[0]
            hits = df[df["events"].isin(["single", "double", "triple", "home_run"])].shape[0]
            strikeouts = df[df["events"] == "strikeout"].shape[0]
            walks = df[df["events"] == "walk"].shape[0]

            batter_records.append({
                "Name": name,
                "G": games,
                "AB": games,
                "H": hits,
                "HR": hr,
                "K": strikeouts,
                "BB": walks
            })

    except Exception as e:
        print(f"[SKIP] {name}: {e}")

# Save fallback stats
all_records = pd.concat([pd.DataFrame(batter_records), pd.DataFrame(pitcher_records)], ignore_index=True)
all_records.to_csv("data/fallback_stats.csv", index=False)

# Save player ID cache
with open("data/player_ids.json", "w") as f:
    json.dump(id_cache, f, indent=2)

print("[✅ DONE] Fallback stats and player IDs updated.")
