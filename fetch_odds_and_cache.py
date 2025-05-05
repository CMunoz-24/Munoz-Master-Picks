import json
import requests
from odds_cache import save_odds_cache
from datetime import datetime

def fetch_today_odds():
    today = datetime.now().strftime("%Y-%m-%d")
    schedule_url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={today}&hydrate=team"

    try:
        res = requests.get(schedule_url)
        res.raise_for_status()
        schedule = res.json()
    except Exception as e:
        print(f"[ERROR] Failed to fetch schedule: {e}")
        return []

    games = []

    for date in schedule.get("dates", []):
        for game in date.get("games", []):
            try:
                home = game["teams"]["home"]["team"]["name"]
                away = game["teams"]["away"]["team"]["name"]
                game_id = game["gamePk"]
                ml = spread = ou = 0.5  # Placeholder odds

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
    required_keys = {"id", "teams", "date", "ml", "spread", "ou"}
    return isinstance(game, dict) and required_keys.issubset(game.keys())

if __name__ == "__main__":
    print("[INFO] Fetching today's games for odds caching...")
    raw_games = fetch_today_odds()
    valid_games = [g for g in raw_games if validate_game_structure(g)]

    if valid_games:
        save_odds_cache(valid_games)
        print(f"[✅ SUCCESS] Odds cached at data/cache/odds_cache.json — {len(valid_games)} games saved.")
    else:
        print("[ERROR] No valid games to cache. Skipping odds_cache update.")

