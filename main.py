from flask import Flask, render_template, request, redirect, session, url_for
import os
import requests
import pandas as pd
from dotenv import load_dotenv
from datetime import datetime
import sys
import os
sys.path.append(os.path.dirname(__file__))
from datetime import datetime, timedelta

games_today = []
last_fetched = None

# Map team name to actual stadium name for park factors
stadium_map = {
    "Arizona Diamondbacks": "Chase Field",
    "Atlanta Braves": "Truist Park",
    "Baltimore Orioles": "Oriole Park at Camden Yards",
    "Boston Red Sox": "Fenway Park",
    "Chicago White Sox": "Guaranteed Rate Field",
    "Chicago Cubs": "Wrigley Field",
    "Cincinnati Reds": "Great American Ball Park",
    "Cleveland Guardians": "Progressive Field",
    "Colorado Rockies": "Coors Field",
    "Detroit Tigers": "Comerica Park",
    "Houston Astros": "Minute Maid Park",
    "Kansas City Royals": "Kauffman Stadium",
    "Los Angeles Angels": "Angel Stadium",
    "Los Angeles Dodgers": "Dodger Stadium",
    "Miami Marlins": "loanDepot park",
    "Milwaukee Brewers": "American Family Field",
    "Minnesota Twins": "Target Field",
    "New York Yankees": "Yankee Stadium",
    "New York Mets": "Citi Field",
    "Oakland Athletics": "Sutter Health Park",  # ➤ Temporary (Sacramento)
    "Philadelphia Phillies": "Citizens Bank Park",
    "Pittsburgh Pirates": "PNC Park",
    "San Diego Padres": "Petco Park",
    "San Francisco Giants": "Oracle Park",
    "Seattle Mariners": "T-Mobile Park",
    "St. Louis Cardinals": "Busch Stadium",
    "Tampa Bay Rays": "George M. Steinbrenner Field",  # ➤ Temporary (Tampa)
    "Texas Rangers": "Globe Life Field",
    "Toronto Blue Jays": "Rogers Centre",
    "Washington Nationals": "Nationals Park"
}

# 🔌 Internal modules
from utils.data_loader import get_live_or_fallback_data
from data.cache.odds_cache_helper import get_cached_odds, save_odds_cache
from utils.weather import get_weather_adjustments
from utils.park_factors import get_park_adjustments
from predictor import predict_game_outcome

# 🧠 Engines
from matchup_engine import (
    generate_adjusted_batter_probabilities,
    generate_batter_recommendations
)
from pitcher_engine import (
    generate_pitcher_probabilities,
    generate_pitcher_recommendations
)
from predictor import predict_game_outcome

# 📊 Stats helpers
from player_stats import get_player_stats
from player_stats_helper import (
    get_player_season_stats,
    get_vs_pitcher_history
)

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "changeme")

USERNAME = os.getenv("APP_USERNAME", "admin")
PASSWORD = os.getenv("APP_PASSWORD", "munoz123")

ODDS_API_KEY = os.getenv("ODDS_API_KEY")
ODDS_API_URL = "https://api.the-odds-api.com/v4/sports/baseball_mlb/odds"
MLB_API_URL = "https://statsapi.mlb.com/api/v1/schedule"

def get_cached_or_fresh_games():
    global games_today, last_fetched
    now = datetime.now()

    if not games_today or not last_fetched or (now - last_fetched > timedelta(minutes=15)):
        print("[INFO] Refreshing games_today cache")
        from utils.game_processing import get_todays_games
        games_today, _ = get_todays_games()
        last_fetched = now
    else:
        print("[INFO] Using cached games_today")

    return games_today

def get_todays_games():
    from datetime import datetime
    from utils.data_loader import get_mlb_schedule_fallback
    from odds_cache import get_cached_odds
    from utils.weather import get_weather_adjustments
    from utils.park_factors import get_park_adjustments
    from predictor import predict_game_outcome
    from player_stats import get_player_stats  # ✅ Add this
    from player_stats_helper import (
        get_vs_pitcher_history,
        generate_adjusted_batter_probabilities,
        generate_batter_recommendations,
        generate_pitcher_probabilities,
        generate_pitcher_recommendations,
        get_player_season_stats,
    )
    import requests
    import os
    
    today = datetime.now().strftime("%Y-%m-%d")
    print(f"[DEBUG] Date being fetched: {today}")

    # Attempt to load cached odds
    games = get_cached_odds()
    if games:
        print("[CACHE] Loaded valid cached odds, skipping API call.")
        return games, {"remaining": "0", "used": "0"}

    # Fallback path starts here
    print("[FALLBACK] Odds cache failed — calling live API + fallback schedule")
    try:
        schedule_url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={today}&hydrate=team,linescore,probablePitcher,person,stats,game(content(summary))"
        schedule_res = requests.get(schedule_url)
        print("[DEBUG] Schedule API status code:", schedule_res.status_code)
        schedule_data = schedule_res.json()
    except Exception as e:
        print(f"[ERROR] Failed to fetch schedule: {e}")
        return [], {"remaining": 0, "used": 0}

    games = []
    for date in schedule_data.get("dates", []):
        for game in date.get("games", []):
            try:
                home = game["teams"]["home"]["team"]["name"]
                away = game["teams"]["away"]["team"]["name"]
                game_id = game["gamePk"]
                matchup = f"{away} vs {home}"

                # Default dummy odds
                ml = spread = ou = 0.5

                # Get boxscore data
                boxscore_url = f"https://statsapi.mlb.com/api/v1/game/{game_id}/boxscore"
                player_res = requests.get(boxscore_url)
                player_data = player_res.json()

                # Process players
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
                                continue
                            season_stats = get_player_season_stats(full_name)
                            lineup_avg = {"AVG": 0.250, "OBP": 0.320, "K%": 0.200}  # You can enhance this with actual lineup parsing

                            park_factors = get_park_adjustments(home)
                            weather_adj = get_weather_adjustments(home)

                            probabilities = generate_pitcher_probabilities(season_stats, lineup_avg, park_factors, weather_adj["adjustments"])
                            recommendations = generate_pitcher_recommendations(probabilities)

                            pitchers_by_team.setdefault(team_name, []).append({
                                "name": full_name,
                                "Probabilities": probabilities,
                                "Recommendations": recommendations,
                                "SeasonStats": season_stats
                            })

                        elif pos in ["LF", "CF", "RF", "1B", "2B", "3B", "SS", "C", "DH", "OF", "IF"]:
                            season_stats = get_player_stats(full_name)["SeasonStats"]
                            pitcher_stats = get_player_stats(opposing_pitcher)["SeasonStats"]
                            vs_history = get_vs_pitcher_history(full_name, opposing_pitcher)
                            park_factors = get_park_adjustments(home)
                            weather_adj = get_weather_adjustments(home).get("adjustments", {})

                            probabilities = generate_adjusted_batter_probabilities(season_stats, pitcher_stats, vs_history, park_factors, weather_adj)
                            recommendations = generate_batter_recommendations(probabilities)

                            batters_by_team.setdefault(team_name, []).append({
                                "name": full_name,
                                "Probabilities": probabilities,
                                "Recommendations": recommendations,
                                "SeasonStats": season_stats
                            })

                # Build game object
                game_prediction = predict_game_outcome(
                    batters_by_team,
                    pitchers_by_team,
                    get_park_adjustments(home),
                    weather_adj.get("adjustments", {}),
                    home_bullpen_score=0.5,
                    away_bullpen_score=0.5
                )

                games.append({
                    "id": game_id,
                    "teams": {"home": home, "away": away},
                    "date": today,
                    "ml": ml,
                    "spread": spread,
                    "ou": ou,
                    "probable_pitchers": {
                        "home": game["teams"]["home"].get("probablePitcher", {}).get("fullName", "TBD"),
                        "away": game["teams"]["away"].get("probablePitcher", {}).get("fullName", "TBD")
                    },
                    "batters": batters_by_team,
                    "pitchers": pitchers_by_team,
                    "game_predictions": game_prediction
                })

            except Exception as e:
                print(f"[ERROR] Failed to process game {game.get('gamePk', '?')}: {e}")

    return games, {"remaining": 0, "used": 0}

@app.route("/game/<int:game_id>")
def game_detail(game_id):
    from utils.weather import get_weather_adjustments
    from predictor import predict_game_outcome

    game = next((g for g in games_today if g["id"] == game_id), None)


    if not game:
        return "Game not found", 404

    home_team = game["teams"].get("home", "Unknown")
    try:
        weather = get_weather_adjustments(home_team)
    except Exception as e:
        print(f"[ERROR] Weather fetch failed: {e}")
        weather = {"adjustments": {}, "description": "Unavailable"}

    # 🌤️ Apply weather adjustments to batters
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

    # 🌤️ Apply weather adjustments to pitchers
    for team_pitchers in game["pitchers"].values():
        for pitcher in team_pitchers:
            if weather["adjustments"].get("Strikeout Drop") == "-5%":
                original = pitcher["Probabilities"]["Strikeout"]
                pitcher["Probabilities"]["Strikeout"] = round(max(original * 0.95, 0.0), 2)
                pitcher["Recommendations"]["Weather Impact"] = "Strikeout ↓ due to wind"

    # 🧠 Run core intelligence model for moneyline/spread/OU
    game_predictions = predict_game_outcome(game)
    game["GamePredictions"] = game_predictions

    return render_template("game_detail.html", game=game)

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

@app.route("/top-picks")
def top_picks():
    return render_template("top_picks.html")

@app.route("/search")
def search():
    return render_template("search.html")

@app.route("/lines")
def lines():
    return render_template("lines.html")

@app.route("/settings")
def settings():
    return render_template("settings.html")

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

import sys

if __name__ == '__main__':
    port = 5000  # default
    if len(sys.argv) > 1 and sys.argv[1].startswith("--port="):
        try:
            port = int(sys.argv[1].split("=")[1])
        except ValueError:
            print("Invalid port. Using default 5000.")
    app.run(host="0.0.0.0", port=port, debug=True)
