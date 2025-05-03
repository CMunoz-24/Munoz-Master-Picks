# pitcher_engine.py

import random

def get_pitcher_prop_recommendation(stat, value):
    if value >= 0.85:
        return "🔥 Must Bet Over"
    elif value >= 0.65:
        return "✅ Strong Over"
    elif value >= 0.50:
        return "Lean Over"
    elif value >= 0.35:
        return "Lean Under"
    elif value >= 0.20:
        return "❌ Strong Under"
    else:
        return "🚫 Avoid Bet"

from player_stats_helper import fetch_pitcher_data_by_name

def get_adjusted_pitcher_props(pitcher_name):
    data = fetch_pitcher_data_by_name(pitcher_name)

    era = data.get("era", 4.50)
    whip = data.get("whip", 1.30)
    k_rate = data.get("so9", 8.0) if "so9" in data else 8.0

    recommendations = {}

    if era <= 2.80:
        recommendations["Earned Runs Prop"] = "🔥 Must Bet Under"
    elif era <= 3.50:
        recommendations["Earned Runs Prop"] = "✅ Strong Under"
    elif era >= 4.50:
        recommendations["Earned Runs Prop"] = "❌ Strong Over"

    if whip <= 1.00:
        recommendations["Hits Allowed Prop"] = "✅ Bet Under"
    elif whip >= 1.40:
        recommendations["Hits Allowed Prop"] = "❌ Bet Over"

    if k_rate >= 10:
        recommendations["Strikeouts Prop"] = "🔥 Bet K Over"
    elif k_rate <= 6:
        recommendations["Strikeouts Prop"] = "❌ Avoid K Over"

    return {
        "ERA": era,
        "WHIP": whip,
        "K/9": k_rate,
        "Recommendations": recommendations,
        "Reason": f"Live-adjusted from MLB API for {pitcher_name} (ERA {era}, WHIP {whip}, K/9 {k_rate})"
    }


# Confidence key (same as batter engine)
PITCHER_BET_KEY = {
    "🔥 Must Bet Over": "0.85 – 1.00",
    "✅ Strong Over": "0.65 – 0.84",
    "Lean Over": "0.50 – 0.64",
    "Lean Under": "0.35 – 0.49",
    "❌ Strong Under": "0.20 – 0.34",
    "🚫 Avoid Bet": "0.00 – 0.19"
}
