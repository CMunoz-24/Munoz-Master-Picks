
from flask import Flask, render_template, request, redirect, session, url_for
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
    today = datetime.now().strftime("%Y-%m-%d")
    games = []
    try:
        schedule_res = requests.get(
            f"{MLB_API_URL}?sportId=1&date={today}&hydrate=team,linescore,probablePitcher"
        )
        schedule_data = schedule_res.json()
        odds_res = requests.get(f"{ODDS_API_URL}?regions=us&markets=h2h,spreads,totals&apiKey={ODDS_API_KEY}")
        odds_data = odds_res.json()

        for date in schedule_data.get("dates", []):
            for game in date.get("games", []):
                home = game["teams"]["home"]["team"]["name"]
                away = game["teams"]["away"]["team"]["name"]
                game_id = game["gamePk"]
                matchup = f"{away} vs {home}"
                ml, spread, ou = 0.5, 0.5, 0.5

                for odds_game in odds_data:
                    if (home.lower() in odds_game["home_team"].lower() and
                        away.lower() in odds_game["away_team"].lower()):
                        markets = {m["key"]: m for m in odds_game["bookmakers"][0]["markets"]}
                        if "h2h" in markets:
                            ml = 0.65
                        if "spreads" in markets:
                            spread = 0.6
                        if "totals" in markets:
                            ou = 0.7
                        break

                # Simulated real players and logic — replace with full stat model
                players = [
                    {"name": "Aaron Judge", "Hits": 0.72, "HR": 0.38, "Walks": 0.11},
                    {"name": "Gleyber Torres", "Hits": 0.65, "HR": 0.22, "Walks": 0.14}
                ]

                games.append({
                    "id": game_id,
                    "teams": matchup,
                    "ml": ml,
                    "spread": spread,
                    "ou": ou,
                    "players": players
                })
    except Exception as e:
        print(f"Error fetching game data: {e}")
    return games

@app.route('/', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form["username"] == USERNAME and request.form["password"] == PASSWORD:
            session["logged_in"] = True
            return redirect(url_for("home"))
        return "Invalid credentials. Try again."
    return render_template("login.html")

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route('/home')
def home():
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    games = get_todays_games()
    return render_template("home.html", games=games)

@app.route('/game/<int:game_id>')
def game_detail(game_id):
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    games = get_todays_games()
    game = next((g for g in games if g["id"] == game_id), None)
    return render_template("game_detail.html", game=game)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
