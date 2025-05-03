# player_stats_helper.py

import requests

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