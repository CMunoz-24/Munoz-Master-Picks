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

def get_adjusted_hitter_props(hitter_name, pitcher_name, hitter_stats):
    pitcher = get_pitcher_profile(pitcher_name)

    hits = hitter_stats.get("Hits", 0.6)
    hr = hitter_stats.get("HR", 0.2)
    walks = hitter_stats.get("Walks", 0.1)

    reason = []

    if pitcher["HR_9"] > 1.0:
        hr += 0.03
        reason.append("Pitcher gives up a lot of home runs.")

    if pitcher["slider%"] > 20:
        whiff = hitter_stats.get("Whiff%", 30)
        if whiff > 28:
            hits -= 0.03
            reason.append("Pitcher's slider may challenge this hitter's swing-and-miss profile.")

    if pitcher["throws"] == "L":
        reason.append("Facing a lefty—adjusts matchups based on splits (future).")

    return {
        "Hits": round(hits, 2),
        "HR": round(hr, 2),
        "Walks": round(walks, 2),
        "Recommendations": {
            "Hits": get_recommendation("Hits", hits),
            "HR": get_recommendation("HR", hr),
            "Walks": get_recommendation("Walks", walks)
        },
        "Reason": "; ".join(reason) if reason else "Standard projection."
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