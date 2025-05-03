# matchup_engine.py

import random

def get_pitcher_profile(pitcher_name):
    profiles = {
        "Shohei Ohtani": {"throws": "R", "slider%": 25, "fastball%": 40, "HR_9": 1.1},
        "Max Fried": {"throws": "L", "slider%": 12, "fastball%": 50, "HR_9": 0.8}
    }
    return profiles.get(pitcher_name, {
        "throws": "R",
        "slider%": 20,
        "fastball%": 50,
        "HR_9": 1.0
    })

def get_recommendation(stat, value):
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

from player_stats_helper import get_pitcher_stats_by_name

def get_adjusted_hitter_props(hitter_name, opposing_pitcher_name, base_stats):
    pitcher_stats = get_pitcher_stats_by_name(opposing_pitcher_name)

    # Adjust base stats based on opposing pitcher ERA and handedness
    adjustment_factor = 1.0

    # Harder pitcher → decrease stats
    if pitcher_stats["ERA"] < 3.00:
        adjustment_factor -= 0.05
    elif pitcher_stats["ERA"] > 4.00:
        adjustment_factor += 0.05

    # Bonus for batter if facing opposite-handed pitcher
    if ("L" in base_stats.get("bats", "")) and pitcher_stats["handedness"] == "R":
        adjustment_factor += 0.03
    elif ("R" in base_stats.get("bats", "")) and pitcher_stats["handedness"] == "L":
        adjustment_factor += 0.03

    adjusted_props = {
        "AVG": round(base_stats.get("AVG", 0.250) * adjustment_factor, 3),
        "HR": round(base_stats.get("HR", 10) * adjustment_factor, 2),
        "RBI": round(base_stats.get("RBI", 40) * adjustment_factor, 2),
        "OPS": round(base_stats.get("OPS", 0.750) * adjustment_factor, 3),
        "SB": round(base_stats.get("SB", 5) * adjustment_factor, 2),
    }

    recommendation = {}
    if adjusted_props["HR"] > 15:
        recommendation["Home Run Prop"] = "Bet HR Over"
    if adjusted_props["AVG"] > 0.280:
        recommendation["Hit Prop"] = "Bet Over 1.5 Total Bases"
    if adjusted_props["SB"] > 10:
        recommendation["Steal Prop"] = "Bet Stolen Base Over"

    return {
        **adjusted_props,
        "Recommendations": recommendation,
        "Reason": f"Adjusted for pitcher {opposing_pitcher_name} (ERA {pitcher_stats['ERA']}, {pitcher_stats['handedness']}-handed)"
    }


# Key for interpretation:
BET_STRENGTH_KEY = {
    "🔥 Must Bet Over": "0.85 - 1.00",
    "✅ Strong Over": "0.65 - 0.84",
    "Lean Over": "0.50 - 0.64",
    "Lean Under": "0.35 - 0.49",
    "❌ Strong Under": "0.20 - 0.34",
    "🚫 Avoid Bet": "0.00 - 0.19"
}
