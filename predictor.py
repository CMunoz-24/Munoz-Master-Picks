# utils/predictor.py

def average_team_offense(batters):
    total_hit = total_hr = total_walk = count = 0
    for player in batters:
        probs = player.get("Probabilities", {})
        total_hit += probs.get("Hit", 0)
        total_hr += probs.get("HR", 0)
        total_walk += probs.get("Walk", 0)
        count += 1
    if count == 0:
        return {"Hit": 0.0, "HR": 0.0, "Walk": 0.0}
    return {
        "Hit": total_hit / count,
        "HR": total_hr / count,
        "Walk": total_walk / count
    }

def average_team_pitching(pitchers):
    total_k = total_bb = total_er = count = 0
    for p in pitchers:
        probs = p.get("Probabilities", {})
        total_k += probs.get("Strikeout", 0)
        total_bb += probs.get("Walk Allowed", 0)
        total_er += probs.get("Earned Run", 0)
        count += 1
    if count == 0:
        return {"Strikeout": 0.0, "Walk": 0.0, "ER": 0.0}
    return {
        "Strikeout": total_k / count,
        "Walk": total_bb / count,
        "ER": total_er / count
    }

def compute_team_score(offense, pitching, park, weather):
    hr_boost = 1.10 if weather.get("HR Boost") == "+10%" else 1.00
    k_drop = 0.95 if weather.get("Strikeout Drop") == "-5%" else 1.00

    score = (
        offense["Hit"] * 1.5 +
        offense["HR"] * 3.0 * hr_boost +
        offense["Walk"] * 1.2 -
        pitching["ER"] * 2.0 +
        pitching["Strikeout"] * 1.5 * k_drop -
        pitching["Walk"] * 1.2
    )

    # Apply park adjustments
    score *= park.get("HR", 1.00)
    score -= (park.get("K", 1.00) - 1.00) * 3  # penalty for higher K parks
    return round(score, 2)

def safe_avg(lst):
    return round(sum(lst) / len(lst), 3) if lst else 0.0

def predict_game_outcome(batters_by_team, pitchers_by_team, park_factors, weather_adjustments, home_bullpen_score, away_bullpen_score):
    def team_offense_score(batters):
        total = 0
        count = 0
        for b in batters:
            probs = b.get("Probabilities", {})
            total += probs.get("Hit", 0) + (probs.get("HR", 0) * 3) + probs.get("Walk", 0)
            count += 1
        return round(total / count, 3) if count else 0.25

    def team_pitching_score(pitchers, bullpen_strength):
        total = 0
        count = 0
        for p in pitchers:
            probs = p.get("Probabilities", {})
            total += (probs.get("Strikeout", 0) * 1.2) - (probs.get("Walk Allowed", 0)) - (probs.get("Earned Run", 0) * 2)
            count += 1
        base_score = round(total / count, 3) if count else 0.0
        return round((base_score + bullpen_strength) / 2, 3)

    team_names = list(batters_by_team.keys())
    if len(team_names) != 2:
        return {
            "moneyline": {"pick": "N/A", "confidence": 50},
            "spread": {"pick": "N/A", "confidence": 50},
            "over_under": {"pick": "N/A", "confidence": 50}
        }

    team1, team2 = team_names
    offense1 = team_offense_score(batters_by_team[team1])
    offense2 = team_offense_score(batters_by_team[team2])

    pitching1 = team_pitching_score(pitchers_by_team.get(team1, []), home_bullpen_score)
    pitching2 = team_pitching_score(pitchers_by_team.get(team2, []), away_bullpen_score)

    park_hr = park_factors.get("HR", 1.0)
    park_k = park_factors.get("K", 1.0)

    weather_hr_boost = 0.10 if weather_adjustments.get("HR Boost") == "+10%" else 0.0
    weather_k_drop = -0.05 if weather_adjustments.get("Strikeout Drop") == "-5%" else 0.0

    score1 = offense1 + pitching1 + park_hr + weather_hr_boost
    score2 = offense2 + pitching2 + park_hr + weather_hr_boost

    spread_diff = abs(score1 - score2)
    total_combined = score1 + score2

    winner = team1 if score1 > score2 else team2
    spread_team = winner
    over_under_pick = "Over" if total_combined > 5.0 else "Under"

    return {
        "moneyline": {
            "pick": winner,
            "confidence": min(90, round(60 + (spread_diff * 10), 1))
        },
        "spread": {
            "pick": f"{spread_team} -1.5",
            "confidence": min(85, round(55 + (spread_diff * 15), 1))
        },
        "over_under": {
            "pick": over_under_pick,
            "confidence": min(90, round(50 + (total_combined - 4.5) * 8, 1))
        }
    }
