
from flask import Flask, render_template, request, redirect, session, url_for
from player_stats import get_player_stat_profile
import os
import requests
from dotenv import load_dotenv
from datetime import datetime

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
    games = []

    try:
        # MLB Schedule and Lineups
        schedule_url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={today}&hydrate=team,linescore,probablePitcher,person,stats,game(content(summary))"
        schedule_res = requests.get(schedule_url)
        schedule_data = schedule_res.json()

        # Odds API Pull
        odds_url = f"https://api.the-odds-api.com/v4/sports/baseball_mlb/odds/?regions=us&markets=h2h,spreads,totals&apiKey={ODDS_API_KEY}"
        odds_data = requests.get(odds_url).json()

        for date in schedule_data.get("dates", []):
            for game in date.get("games", []):
                home = game["teams"]["home"]["team"]["name"]
                away = game["teams"]["away"]["team"]["name"]
                game_id = game["gamePk"]
                matchup = f"{away} vs {home}"

                # Match to odds
                ml = spread = ou = 0.5
                for odds_game in odds_data:
                    if (home.lower() in odds_game["home_team"].lower() and
                        away.lower() in odds_game["away_team"].lower()):
                        try:
                            markets = {m["key"]: m for m in odds_game["bookmakers"][0]["markets"]}
                            if "h2h" in markets:
                                ml = 0.5 + 0.1 * int("1" in markets["h2h"]["outcomes"][0]["name"])  # Simulated
                            if "spreads" in markets:
                                spread = 0.6
                            if "totals" in markets:
                                ou = 0.7
                        except Exception:
                            pass
                        break

                 # Pull players using boxscore data (more complete)
                boxscore_url = f"https://statsapi.mlb.com/api/v1/game/{game_id}/boxscore"
                player_res = requests.get(boxscore_url)
                player_data = player_res.json()

                batters = []
                pitchers = []
                for team_key in ["home", "away"]:
                    team_info = player_data["teams"][team_key]
                    for pid, pinfo in team_info["players"].items():
                        full_name = pinfo["person"]["fullName"]
                        pos = pinfo.get("position", {}).get("abbreviation", "")

                        if pos == "P":
                            # Pitcher logic
                            pitching_stats = {
                                "ERA": round(random.uniform(2.50, 4.50), 2),
                                "K_percent": round(random.uniform(18.0, 32.0), 1),
                                "IP": round(random.uniform(4.0, 7.0), 1)
                            }
                            pitchers.append({
                                "name": full_name,
                                **pitching_stats
                            })
                        else:
                            # Batter logic
                            batting_stats = get_player_stat_profile(full_name)
                            batters.append({
                                "name": full_name,
                                **batting_stats
                            })




                games.append({
                    "id": game_id,
                    "teams": matchup,
                    "ml": ml,
                    "spread": spread,
                    "ou": ou,
                    "batters": batters,
                    "pitchers": pitchers
                })


    except Exception as e:
        print(f"Error fetching data: {e}")

    return games

@app.route("/game/<int:game_id>")
def game_detail(game_id):
    games = get_todays_games()
    game = next((g for g in games if g["id"] == game_id), None)

    @app.route("/game/<int:game_id>")
    def game_detail(game_id):
    games = get_todays_games()
    game = next((g for g in games if g["id"] == game_id), None)

    if not game:
        return "Game not found", 404

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
    games = get_todays_games()
    return render_template("home.html", games=games)

from flask import redirect

@app.route("/")
def index():
    return redirect("/home")

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
