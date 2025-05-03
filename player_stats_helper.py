# player_stats_helper.py

import requests

import requests

def fetch_pitcher_data_by_name(name):
    try:
        # Search player by name to get their ID
        search_url = f"https://statsapi.mlb.com/api/v1/people/search?name={name}"
        search_response = requests.get(search_url).json()
        results = search_response.get("people", [])
        if not results:
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
            if not splits:
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

