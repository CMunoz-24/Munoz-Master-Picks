# pitcher_engine.py

from utils.park_factors import get_park_adjustments

def generate_pitcher_probabilities(season_stats):
    era = season_stats.get("ERA", 0.0)
    whip = season_stats.get("WHIP", 1.0)
    k9 = season_stats.get("K/9", 7.5)
    bb9 = season_stats.get("BB/9", 2.0)

    return {
        "Strikeout": round(k9 / 9, 2),        # Ks per inning
        "Walk Allowed": round(bb9 / 9, 2),    # BB per inning
        "Earned Run": round(era / 9, 2)       # ER per inning
    }

def generate_pitcher_recommendations(probabilities):
    recs = {}

    k_rate = probabilities.get("Strikeout", 0)
    bb_rate = probabilities.get("Walk Allowed", 0)
    er_rate = probabilities.get("Earned Run", 0)

    # 🔍 Strikeout suggestions
    if k_rate > 1.1:
        recs["Strikeout"] = "🔥 Take Over Ks"
    elif k_rate < 0.8:
        recs["Strikeout"] = "❌ Avoid Ks Prop"

    # 🔍 Walk suggestions
    if bb_rate < 0.3:
        recs["Walk Allowed"] = "✅ Lean Under Walks"
    elif bb_rate > 0.6:
        recs["Walk Allowed"] = "⚠️ Avoid Walk Under"

    # 🔍 Earned Run suggestions
    if er_rate < 0.6:
        recs["Earned Run"] = "✅ Strong Under ER"
    elif er_rate > 1.2:
        recs["Earned Run"] = "❌ Avoid Under ER"

    return recs

def generate_pitcher_probabilities(season_stats, opposing_lineup=None, park_factors=None, weather_adjustments=None):
    era = season_stats.get("ERA", 0.0)
    whip = season_stats.get("WHIP", 1.0)
    k9 = season_stats.get("K/9", 7.5)
    bb9 = season_stats.get("BB/9", 2.0)

    k_per_inning = k9 / 9
    bb_per_inning = bb9 / 9
    er_per_inning = era / 9

    # Opposing lineup adjustments
    if opposing_lineup is not None and len(opposing_lineup) > 0:
        team_avg = opposing_lineup.get("AVG", 0.250)
        team_obp = opposing_lineup.get("OBP", 0.320)
        team_k_rate = opposing_lineup.get("K%", 0.20)

        if team_avg > 0.275:
            er_per_inning *= 1.15
        if team_obp > 0.340:
            bb_per_inning *= 1.10
        if team_k_rate < 0.18:
            k_per_inning *= 0.90
        elif team_k_rate > 0.26:
            k_per_inning *= 1.10

    # Park adjustments
    if park_factors is not None:
        k_per_inning *= park_factors.get("K", 1.0)
        er_per_inning *= 2 - park_factors.get("HR", 1.0)

    # Weather adjustments
    if weather_adjustments is not None:
        if weather_adjustments.get("Strikeout Drop") == "-5%":
            k_per_inning *= 0.95

    return {
        "Strikeout": round(k_per_inning, 2),
        "Walk Allowed": round(bb_per_inning, 2),
        "Earned Run": round(er_per_inning, 2)
    }

