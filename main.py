
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
    from datetime import datetime
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

                # Simulated top players — replace this later with real Statcast pull
                players = [
                    {"name": "Juan Soto", "Hits": 0.71, "HR": 0.34, "Walks": 0.14},
                    {"name": "Aaron Judge", "Hits": 0.74, "HR": 0.39, "Walks": 0.12}
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
        print(f"Error fetching data: {e}")

    return games

@app.route("/game/<int:game_id>")
def game_detail(game_id):
    games = get_todays_games()
    game = next((g for g in games if g["id"] == game_id), None)

    if not game:
        return "Game not found", 404

    # Build fake props for each player (next upgrade: statcast-powered props)
    for p in game["players"]:
        # These values are already simulated from get_todays_games()
        # You could enhance this further later with historical splits
        p["Hits"] = p.get("Hits", 0.6)
        p["HR"] = p.get("HR", 0.25)
        p["Walks"] = p.get("Walks", 0.1)

    return render_template("game_detail.html", game=game)

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

from flask import redirect

@app.route("/")
def index():
    return redirect("/home")


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
