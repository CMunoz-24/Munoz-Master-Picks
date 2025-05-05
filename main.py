from flask import Flask, render_template, request, redirect, session, url_for
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
from matchup_engine import generate_adjusted_batter_probabilities, generate_batter_recommendations
from pitcher_engine import generate_pitcher_probabilities, generate_pitcher_recommendations
from utils.weather_teams import get_coordinates_for_team
from player_stats_helper import get_vs_pitcher_history
from utils.park_factors import get_park_adjustments
from utils.predictor import predict_game_outcome
from utils.bullpen_evaluator import evaluate_bullpen_strength

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

                                try:
                                    season_stats = get_player_season_stats(full_name)
                                except Exception as e:
                                    print(f"[WARNING] Season stats unavailable for {full_name}: {e}")
                                    season_stats = {}

                                try:
                                    opposing_batters = player_data["teams"][opposing_key]["players"]
                                    avg_list, obp_list, k_list = [], [], []
                                    for b in opposing_batters.values():
                                        b_pos = b.get("position", {}).get("abbreviation", "")
                                        if b_pos in ["LF", "CF", "RF", "1B", "2B", "3B", "SS", "C", "DH", "OF", "IF"]:
                                            b_name = b["person"]["fullName"]
                                            try:
                                                b_stats = get_player_stats(b_name).get("SeasonStats", {})
                                                avg = float(b_stats.get("AVG", 0.250))
                                                obp = float(b_stats.get("OBP", 0.320))
                                                k_pct = float(b_stats.get("K%", 0.20))
                                                avg_list.append(avg)
                                                obp_list.append(obp)
                                                k_list.append(k_pct)
                                            except Exception:
                                                continue
                                    lineup_avg = {
                                        "AVG": round(sum(avg_list)/len(avg_list), 3) if avg_list else 0.250,
                                        "OBP": round(sum(obp_list)/len(obp_list), 3) if obp_list else 0.320,
                                        "K%": round(sum(k_list)/len(k_list), 3) if k_list else 0.20
                                    }
                                except Exception as e:
                                    print(f"[LINEUP ERROR] Could not evaluate opposing lineup: {e}")
                                    lineup_avg = None

                                park_name = game["teams"].split(" vs ")[1]
                                park_factors = get_park_adjustments(park_name)
                                weather_adj = get_weather_adjustments(park_name)

                                probabilities = generate_pitcher_probabilities(
                                    season_stats,
                                    opposing_lineup=lineup_avg,
                                    park_factors=park_factors,
                                    weather_adjustments=weather_adj.get("adjustments", {})
                                )
                                recommendations = generate_pitcher_recommendations(probabilities)

                                pitchers_by_team.setdefault(team_name, []).append({
                                    "name": full_name,
                                    "Probabilities": probabilities,
                                    "Recommendations": recommendations,
                                    "SeasonStats": season_stats
                                })

                            elif pos in ["LF", "CF", "RF", "1B", "2B", "3B", "SS", "C", "DH", "OF", "IF"]:
                                if "stats" not in pinfo:
                                    print(f"[SKIP] No stats available for batter: {full_name}")
                                    continue

                                try:
                                    season_stats = get_player_stats(full_name)["SeasonStats"]
                                except Exception:
                                    season_stats = {}

                                try:
                                    pitcher_stats = get_player_stats(opposing_pitcher)["SeasonStats"]
                                except Exception:
                                    pitcher_stats = {}

                                vs_history = get_vs_pitcher_history(full_name, opposing_pitcher)
                                park_name = game.get("venue", {}).get("name", "default")
                                park_factor = get_park_adjustments(park_name)
                                home_team = game["teams"].split(" vs ")[1]
                                weather_adj = get_weather_adjustments(home_team).get("adjustments", {})

                                probabilities = generate_adjusted_batter_probabilities(
                                    season_stats,
                                    pitcher_stats,
                                    vs_history=vs_history,
                                    park_adjustment=park_factor,
                                    weather_adjustment=weather_adj
                                )
                                recommendations = generate_batter_recommendations(probabilities)

                                batters_by_team.setdefault(team_name, []).append({
                                    "name": full_name,
                                    "Probabilities": probabilities,
                                    "Recommendations": recommendations,
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

                    game_prediction = predict_game_outcome(
                        batters_by_team,
                        pitchers_by_team,
                        park_factors,
                        weather_adj.get("adjustments", {})
                    )

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
                        "pitchers": pitchers_by_team,
                        "game_predictions": game_prediction
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
    from utils.weather import get_weather_adjustments
    from game_intelligence import predict_game_outcome

    games, _ = get_todays_games()
    game = next((g for g in games if g["id"] == game_id), None)

    if not game:
        return "Game not found", 404

    home_team = game["teams"].split(" vs ")[1]
    weather = get_weather_adjustments(home_team)

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
        "weather": weather,
        "game_predictions": game.get("GamePredictions", {})
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

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)

