import json
import requests
from odds_cache import save_odds_cache

def fetch_today_odds():
    from datetime import datetime
    today = datetime.now().strftime("%Y-%m-%d")

    schedule_url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={today}&hydrate=team"
    res = requests.get(schedule_url)
    if res.status_code != 200:
        print(f"[ERROR] Failed to fetch schedule: {res.status_code}")
        return []

    schedule = res.json()
    games = []

    for date in schedule.get("dates", []):
        for game in date.get("games", []):
            try:
                home = game["teams"]["home"]["team"]["name"]
                away = game["teams"]["away"]["team"]["name"]
                game_id = game["gamePk"]
                ml = spread = ou = 0.5  # Default placeholders

                games.append({
                    "id": game_id,
                    "teams": {"home": home, "away": away},
                    "date": today,
                    "ml": ml,
                    "spread": spread,
                    "ou": ou
                })
            except Exception as e:
                print(f"[ERROR] Failed to parse game: {e}")
                continue

    return games

def validate_game_structure(game):
    return all(k in game for k in ["id", "teams", "date", "ml", "spread", "ou"])

if __name__ == "__main__":
    print("[INFO] Fetching today's games for odds caching...")
    raw_games = fetch_today_odds()
    valid_games = [g for g in raw_games if validate_game_structure(g)]

    if valid_games:
        save_odds_cache(valid_games)
        print(f"[SUCCESS] Odds cached at data/cache/odds_cache.json — {len(valid_games)} games saved.")
    else:
        print("[ERROR] No valid games to cache. Skipping odds_cache update.")
