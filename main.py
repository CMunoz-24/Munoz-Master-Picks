from flask import Flask, render_template, request, redirect, session, url_for
from player_stats import get_player_stat_profile
from matchup_engine import get_adjusted_hitter_props
from pitcher_engine import get_adjusted_pitcher_props
from player_stats_helper import get_player_season_stats
import os
import requests
import pandas as pd
from dotenv import load_dotenv
from datetime import datetime
from utils.data_loader import get_live_or_fallback_data
from data.cache.odds_cache_helper import get_cached_odds
from data.cache.odds_cache_helper import save_odds_cache
from probability_engine import get_hitter_probabilities, get_pitcher_probabilities
from utils.weather_helper import get_combined_weather
from utils.weather import get_weather_adjustments

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "changeme")

USERNAME = os.getenv("APP_USERNAME", "admin")
PASSWORD = os.getenv("APP_PASSWORD", "munoz123")

ODDS_API_KEY = os.getenv("ODDS_API_KEY")
ODDS_API_URL = "https://api.the-odds-api.com/v4/sports/baseball_mlb/odds"
MLB_API_URL = "https://statsapi.mlb.com/api/v1/schedule"

def get_todays_games():
    from datetime import datetime
    import random

    today = datetime.now().strftime("%Y-%m-%d")
    print(f"[DEBUG] Date being fetched: {today}")
    games = []
    print("[DEBUG] get_todays_games() has started")

    try:
        schedule_url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={today}&hydrate=team,linescore,probablePitcher,person,stats,game(content(summary))"
        schedule_res = requests.get(schedule_url)
        print("[DEBUG] Schedule API status code:", schedule_res.status_code)
        schedule_data = schedule_res.json()

        fallback_mode = False
        fallback_data = {}

        # Always define remaining/used even if using cache
        remaining = "0"
        used = "0"

        odds_data = get_cached_odds()

        if odds_data:
            print("[CACHE] Loaded valid cached odds, skipping API call.")
        else:
            try:
                odds_url = f"https://api.the-odds-api.com/v4/sports/baseball_mlb/odds/?regions=us&markets=h2h,spreads,totals&apiKey={ODDS_API_KEY}"
                odds_res = requests.get(odds_url)
                odds_data = odds_res.json()
                save_odds_cache(odds_data)

                remaining = odds_res.headers.get("x-requests-remaining", "0")
                used = odds_res.headers.get("x-requests-used", "0")

                if not isinstance(odds_data, list):
                    raise ValueError("Odds API failed — switching to fallback.")
            except Exception as e:
                print(f"[FALLBACK TRIGGERED] Odds API failed or quota hit: {e}")
                fallback_mode = True
                fallback_data = get_live_or_fallback_data()
                odds_data = []

        for date in schedule_data.get("dates", []):
            for game in date.get("games", []):
                try:
                    home = game["teams"]["home"]["team"]["name"]
                    away = game["teams"]["away"]["team"]["name"]
                    game_id = game["gamePk"]
                    matchup = f"{away} vs {home}"

                    ml = spread = ou = 0.5

                    for odds_game in odds_data:
                        if (home.lower() in odds_game["home_team"].lower() and
                            away.lower() in odds_game["away_team"].lower()):
                            try:
                                bookmakers = odds_game.get("bookmakers", [])
                                if not bookmakers or "markets" not in bookmakers[0]:
                                    continue
                                markets = {m["key"]: m for m in bookmakers[0]["markets"]}
                                if "h2h" in markets:
                                    ml = 0.5 + 0.1 * int("1" in markets["h2h"]["outcomes"][0]["name"])
                                if "spreads" in markets:
                                    spread = 0.6
                                if "totals" in markets:
                                    ou = 0.7
                            except Exception:
                                pass
                            break

                    boxscore_url = f"https://statsapi.mlb.com/api/v1/game/{game_id}/boxscore"
                    player_res = requests.get(boxscore_url)
                    player_data = player_res.json()

                    batters_by_team = {}
                    pitchers_by_team = {}

                    for team_key in ["home", "away"]:
                        team_info = player_data["teams"][team_key]
                        team_name = team_info["team"]["name"]
                        opposing_key = "away" if team_key == "home" else "home"
                        opposing_pitcher = game["teams"][opposing_key].get("probablePitcher", {}).get("fullName", "Generic Pitcher")

                        for pinfo in team_info["players"].values():
                            full_name = pinfo["person"]["fullName"]
                            pos = pinfo.get("position", {}).get("abbreviation", "")

                            if pos == "P":
                                if "stats" not in pinfo:
                                    print(f"[SKIP] No stats available for pitcher: {full_name}")
                                    continue

                                props = get_adjusted_pitcher_props(full_name, fallback_data if fallback_mode else None)
                                pitcher_stats = {k: v for k, v in props.items() if k not in ["Recommendations", "Reason"]}
                                recommendations = props.get("Recommendations", {})
                                try:
                                    season_stats = get_player_season_stats(full_name)
                                except Exception as e:
                                    print(f"[WARNING] Season stats unavailable for {full_name}: {e}")
                                    season_stats = {}

                                pitchers_by_team.setdefault(team_name, []).append({
                                    "name": full_name,
                                    **pitcher_stats,
                                    "Probabilities": get_pitcher_probabilities(full_name, season_stats),
                                    "Recommendations": recommendations,
                                    "SeasonStats": season_stats
                                })

                            elif pos in ["LF", "CF", "RF", "1B", "2B", "3B", "SS", "C", "DH", "OF", "IF"]:
                                if "stats" not in pinfo:
                                    print(f"[SKIP] No stats available for batter: {full_name}")
                                    continue

                                base_stats = get_player_stat_profile(full_name)
                                adjusted = get_adjusted_hitter_props(full_name, opposing_pitcher, base_stats, fallback_data if fallback_mode else None)
                                batting_stats = {k: v for k, v in adjusted.items() if k not in ["Recommendations", "Reason"]}
                                try:
                                    season_stats = get_player_season_stats(full_name)
                                except Exception:
                                    season_stats = {}

                                batters_by_team.setdefault(team_name, []).append({
                                    "name": full_name,
                                    **batting_stats,
                                    "Probabilities": get_hitter_probabilities(full_name, season_stats),
                                    "Recommendations": adjusted.get("Recommendations", {}),
                                    "SeasonStats": season_stats
                                })

                    game_date = game.get("officialDate", today)

                    probable_pitchers = {
                        "home": game["teams"]["home"].get("probablePitcher", {}).get("fullName", "TBD"),
                        "away": game["teams"]["away"].get("probablePitcher", {}).get("fullName", "TBD")
                    }

                    lineups = {
                        "home": [
                            {
                                "name": p["person"]["fullName"],
                                "pos": p.get("position", {}).get("abbreviation", "N/A")
                            }
                            for p in player_data["teams"]["home"]["players"].values()
                            if p.get("position", {}).get("abbreviation", "") in ["LF", "CF", "RF", "1B", "2B", "3B", "SS", "C", "DH", "OF", "IF"]
                        ],
                        "away": [
                            {
                                "name": p["person"]["fullName"],
                                "pos": p.get("position", {}).get("abbreviation", "N/A")
                            }
                            for p in player_data["teams"]["away"]["players"].values()
                            if p.get("position", {}).get("abbreviation", "") in ["LF", "CF", "RF", "1B", "2B", "3B", "SS", "C", "DH", "OF", "IF"]
                        ]
                    }

                    games.append({
                        "id": game_id,
                        "teams": matchup,
                        "date": game_date,
                        "ml": ml,
                        "spread": spread,
                        "ou": ou,
                        "probable_pitchers": probable_pitchers,
                        "lineups": lineups,
                        "batters": batters_by_team,
                        "pitchers": pitchers_by_team
                    })

                except Exception as e:
                    print(f"[ERROR] Failed to process game {game.get('gamePk', '?')}: {e}")

        return games, {
            "remaining": int(remaining) if not fallback_mode and remaining.isdigit() else 0,
            "used": int(used) if not fallback_mode and used.isdigit() else 0
        }

    except Exception as e:
        print(f"[ERROR] Failed to fetch schedule/odds: {e}")
        return [], {"remaining": 0, "used": 0}

@app.route("/game/<int:game_id>")
def game_detail(game_id):
    games, _ = get_todays_games()
    game = next((g for g in games if g["id"] == game_id), None)

    if not game:
        return "Game not found", 404

    from utils.weather import get_weather_adjustments
    weather = get_weather_adjustments(game.get("teams", ""))

    # Apply weather adjustments
    for team_players in game["batters"].values():
        for player in team_players:
            if weather["adjustments"].get("HR Boost") == "+10%":
                original = player["Probabilities"]["HR"]
                player["Probabilities"]["HR"] = round(min(original * 1.10, 1.0), 2)
                player["Recommendations"]["Weather Impact"] = "HR ↑ due to warm weather & wind"
            if weather["adjustments"].get("Strikeout Drop") == "-5%":
                if "Strikeout" in player["Probabilities"]:
                    original = player["Probabilities"]["Strikeout"]
                    player["Probabilities"]["Strikeout"] = round(max(original * 0.95, 0.0), 2)
                    player["Recommendations"]["Weather Impact"] = "Strikeout ↓ due to wind"

    for team_pitchers in game["pitchers"].values():
        for pitcher in team_pitchers:
            if weather["adjustments"].get("Strikeout Drop") == "-5%":
                original = pitcher["Probabilities"]["Strikeout"]
                pitcher["Probabilities"]["Strikeout"] = round(max(original * 0.95, 0.0), 2)
                pitcher["Recommendations"]["Weather Impact"] = "Strikeout ↓ due to wind"

    return render_template("game_detail.html", game={
        "teams": game.get("teams", "N/A"),
        "date": game.get("date", "N/A"),
        "ml": game.get("ml", "N/A"),
        "spread": game.get("spread", "N/A"),
        "ou": game.get("ou", "N/A"),
        "batters": game.get("batters", []),
        "pitchers": game.get("pitchers", []),
        "lineups": game.get("lineups", {}),
        "probable_pitchers": game.get("probable_pitchers", {}),
        "weather": weather
    })

@app.route("/login", methods=["GET", "POST"])
def login_page():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if username == USERNAME and password == PASSWORD:
            session["logged_in"] = True
            return redirect(url_for("home"))
        else:
            return render_template("login.html", error="Invalid credentials.")
    return render_template("login.html")

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for("login_page"))

@app.route('/home')
def home():
    if not session.get("logged_in"):
        return redirect(url_for("login_page"))
    
    games, quota = get_todays_games()
    print(f"[DEBUG] Games fetched on /home: {games}")
    
    return render_template("home.html", games=games, quota=quota)

from flask import redirect

@app.route("/")
def index():
    return redirect("/home")

@app.route('/stats')
def stats_page():
    if not session.get("logged_in"):
        return redirect(url_for("login_page"))

    fallback_data = get_live_or_fallback_data()
    msf_df = fallback_data.get("mysportsfeeds")
    fg_df = fallback_data.get("fangraphs")

    msf_table = msf_df.head(20).to_dict(orient="records") if isinstance(msf_df, pd.DataFrame) and not msf_df.empty else []
    fg_table = fg_df.head(20).to_dict(orient="records") if isinstance(fg_df, pd.DataFrame) and not fg_df.empty else []

    return render_template("stats.html", msf_stats=msf_table, fg_stats=fg_table)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)

