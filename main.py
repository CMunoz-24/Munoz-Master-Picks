from flask import Flask, render_template, request, redirect, session, url_for
from player_stats import get_player_stat_profile
from matchup_engine import get_adjusted_hitter_props
from pitcher_engine import get_adjusted_pitcher_props
from player_stats_helper import get_player_season_stats
import os
import requests
from dotenv import load_dotenv
from datetime import datetime
from utils.data_loader import get_live_or_fallback_data

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
    today = datetime.now().strftime("%Y-%m-%d")
    print(f"[DEBUG] Date being fetched: {today}")
    games = []
    print("[DEBUG] get_todays_games() has started")

    try:
        schedule_url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={today}&hydrate=team,linescore,probablePitcher,person,stats,game(content(summary))"
        schedule_res = requests.get(schedule_url)
        print("[DEBUG] Schedule API status code:", schedule_res.status_code)
        print("[DEBUG] Schedule API response text:", schedule_res.text[:300])  # first 300 chars only
        schedule_data = schedule_res.json()
        print("[DEBUG] Raw schedule data keys:", schedule_data.keys())
        print("[DEBUG] Raw schedule 'dates':", schedule_data.get("dates", []))

        # ✅ CORRECT indentation here
        fallback_mode = False
        fallback_data = {}

        try:
            odds_url = f"https://api.the-odds-api.com/v4/sports/baseball_mlb/odds/?regions=us&markets=h2h,spreads,totals&apiKey={ODDS_API_KEY}"
            odds_res = requests.get(odds_url)
            odds_data = odds_res.json()

            remaining = odds_res.headers.get("x-requests-remaining")
            used = odds_res.headers.get("x-requests-used")

            print(f"[DEBUG] Odds API quota — Remaining: {remaining}, Used: {used}")
            print("[DEBUG] Odds data type:", type(odds_data))

            if not isinstance(odds_data, list):
                raise ValueError("Odds API failed — switching to fallback.")

        except Exception as e:
            print(f"[FALLBACK TRIGGERED] Odds API failed or quota hit: {e}")
            fallback_mode = True
            fallback_data = get_live_or_fallback_data()
            odds_data = []  # Odds not available

        for date in schedule_data.get("dates", []):
            for game in date.get("games", []):
                try:
                    home = game["teams"]["home"]["team"]["name"]
                    away = game["teams"]["away"]["team"]["name"]
                    game_id = game["gamePk"]
                    matchup = f"{away} vs {home}"
                    print(f"[DEBUG] Processing game: {away} vs {home} | ID: {game_id}")

                    ml = spread = ou = 0.5  # Default values

                    for odds_game in odds_data:
                        if (home.lower() in odds_game["home_team"].lower() and
                            away.lower() in odds_game["away_team"].lower()):
                            try:
                                markets = {m["key"]: m for m in odds_game["bookmakers"][0]["markets"]}
                                if "h2h" in markets:
                                    ml = 0.5 + 0.1 * int("1" in markets["h2h"]["outcomes"][0]["name"])
                                if "spreads" in markets:
                                    spread = 0.6
                                if "totals" in markets:
                                    ou = 0.7
                            except Exception:
                                pass
                            break

                    # Get boxscore data
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

                        print(f"[DEBUG] team_info['players'] type: {type(team_info['players'])}")

                        for pinfo in team_info["players"].values():
                            full_name = pinfo["person"]["fullName"]
                            pos = pinfo.get("position", {}).get("abbreviation", "")

                            if pos == "P":
                                props = get_adjusted_pitcher_props(full_name, fallback_data if fallback_mode else None)
                                pitcher_stats = {k: v for k, v in props.items() if k not in ["Recommendations", "Reason"]}
                                recommendations = props.get("Recommendations", {})

                                try:
                                    season_stats = get_player_season_stats(full_name)
                                except Exception as e:
                                    print(f"[ERROR] Pitcher stats fetch failed for {full_name}: {e}")
                                    season_stats = {}

                                pitchers_by_team.setdefault(team_name, []).append({
                                    "name": full_name,
                                    **pitcher_stats,
                                    "Probabilities": {
                                        "Strikeout": round(random.uniform(0.3, 0.7), 2),
                                        "Walk Allowed": round(random.uniform(0.1, 0.5), 2),
                                        "Earned Run": round(random.uniform(0.2, 0.6), 2),
                                    },
                                    "Recommendations": recommendations,
                                    "SeasonStats": season_stats
                                })

                            elif pos in ["LF", "CF", "RF", "1B", "2B", "3B", "SS", "C", "DH", "OF", "IF"]:
                                base_stats = get_player_stat_profile(full_name)
                                adjusted = get_adjusted_hitter_props(full_name, opposing_pitcher, base_stats, fallback_data if fallback_mode else None)
                                batting_stats = {k: v for k, v in adjusted.items() if k not in ["Recommendations", "Reason"]}

                                try:
                                    season_stats = get_player_season_stats(full_name)
                                except Exception as e:
                                    print(f"[ERROR] Batter stats fetch failed for {full_name}: {e}")
                                    season_stats = {}

                                batters_by_team.setdefault(team_name, []).append({
                                    "name": full_name,
                                    **batting_stats,
                                    "Probabilities": {
                                        "Hit": round(random.uniform(0.2, 0.8), 2),
                                        "HR": round(random.uniform(0.05, 0.3), 2),
                                        "Walk": round(random.uniform(0.1, 0.4), 2),
                                    },
                                    "Recommendations": adjusted.get("Recommendations", {}),
                                    "SeasonStats": season_stats
                                })

                    games.append({
                        "id": game_id,
                        "teams": matchup,
                        "ml": ml,
                        "spread": spread,
                        "ou": ou,
                        "batters": batters_by_team,
                        "pitchers": pitchers_by_team
                    })

                except Exception as e:
                    print(f"[ERROR] Failed to process game {game.get('gamePk', '?')}: {e}")

        print(f"[DEBUG] Total games processed: {len(games)}")
        print(f"[DEBUG] Final games list length: {len(games)}")
        for g in games:
            print(f"[DEBUG] Game: {g.get('teams')} — ID: {g.get('id')}")

        remaining = int(odds_res.headers.get("x-requests-remaining", 0)) if not fallback_mode else 0
        used = int(odds_res.headers.get("x-requests-used", 0)) if not fallback_mode else 0
        return games, {"remaining": remaining, "used": used}

    except Exception as e:
        print(f"[ERROR] Failed to fetch schedule/odds: {e}")
        return [], {"remaining": 0, "used": 0}

@app.route("/game/<int:game_id>")
def game_detail(game_id):
    games = get_todays_games()
    game = next((g for g in games if g["id"] == game_id), None)

    if not game:
        return "Game not found", 404

    print(f"[DEBUG] Loaded game object: {game}")
    print(f"[DEBUG] Batters: {game.get('batters')}")
    print(f"[DEBUG] Pitchers: {game.get('pitchers')}")

    return render_template("game_detail.html", game={
        "teams": game.get("teams", "N/A"),
        "ml": game.get("ml", "N/A"),
        "spread": game.get("spread", "N/A"),
        "ou": game.get("ou", "N/A"),
        "batters": game.get("batters", []),
        "pitchers": game.get("pitchers", [])
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

    # Show just a few top rows
    msf_table = msf_df.head(20).to_dict(orient="records") if not msf_df.empty else []
    fg_table = fg_df.head(20).to_dict(orient="records") if not fg_df.empty else []

    return render_template("stats.html", msf_stats=msf_table, fg_stats=fg_table)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)

