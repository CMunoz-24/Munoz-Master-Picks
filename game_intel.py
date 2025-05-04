# game_intel.py

from utils.weather import get_weather_adjustments
from utils.park_factors import get_park_adjustments

def score_team_offense(lineup_stats):
    if not lineup_stats:
        return 50.0

    avg = sum(p.get("AVG", 0.25) for p in lineup_stats) / len(lineup_stats)
    obp = sum(p.get("OBP", 0.32) for p in lineup_stats) / len(lineup_stats)
    hr = sum(p.get("HR", 1) for p in lineup_stats)
    k_rate = sum(p.get("K%", 0.20) for p in lineup_stats) / len(lineup_stats)

    score = 50.0
    score += (avg - 0.25) * 100  # +5 if AVG is .300
    score += (obp - 0.32) * 80
    score += (hr / 9.0) * 10
    score -= (k_rate - 0.20) * 50
    return round(score, 2)

def score_pitching(pitcher_stats, bullpen_stats):
    era = float(pitcher_stats.get("ERA", 4.0))
    whip = float(pitcher_stats.get("WHIP", 1.30))
    bullpen_era = float(bullpen_stats.get("ERA", 4.0))
    bullpen_whip = float(bullpen_stats.get("WHIP", 1.30))

    score = 50.0
    score -= (era - 4.0) * 6
    score -= (whip - 1.30) * 10
    score -= (bullpen_era - 4.0) * 5
    score -= (bullpen_whip - 1.30) * 8
    return round(score, 2)

def adjust_for_park_and_weather(score, park_name, home_team):
    park = get_park_adjustments(park_name)
    weather = get_weather_adjustments(home_team).get("adjustments", {})

    if park["HR"] > 1.10:
        score += 2
    elif park["HR"] < 0.90:
        score -= 2

    if weather.get("HR Boost") == "+10%":
        score += 2
    if weather.get("Strikeout Drop") == "-5%":
        score += 1

    return round(score, 2)

def get_team_game_score(team_offense_stats, pitcher_stats, bullpen_stats, park_name, home_team):
    offense_score = score_team_offense(team_offense_stats)
    pitching_score = score_pitching(pitcher_stats, bullpen_stats)
    total_score = (offense_score + pitching_score) / 2
    adjusted_score = adjust_for_park_and_weather(total_score, park_name, home_team)
    return adjusted_score

def get_game_prediction(home_score, away_score):
    diff = home_score - away_score
    
    if diff > 2:
        moneyline = "Home Win"
        spread = "Home -1.5"
    elif diff < -2:
        moneyline = "Away Win"
        spread = "Away -1.5"
    else:
        moneyline = "Too Close"
        spread = "Avoid Spread"

    total_combined = home_score + away_score
    if total_combined > 105:
        over_under = "Bet Over"
    elif total_combined < 95:
        over_under = "Bet Under"
    else:
        over_under = "Avoid OU"

    return {
        "Moneyline": moneyline,
        "Spread": spread,
        "OverUnder": over_under,
        "HomeScore": home_score,
        "AwayScore": away_score
    }
