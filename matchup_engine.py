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

def get_adjusted_hitter_props(name, opposing_pitcher, base_stats, fallback_data=None):
    if fallback_data:
        print(f"[FALLBACK] Generating hitter props for", name)

        msf_df = fallback_data.get("mysportsfeeds")
        fg_df = fallback_data.get("fangraphs")

        avg = 0.250
        obp = 0.320
        hr = 1

        # Match by last name (from MySportsFeeds)
        if not msf_df.empty:
            last_name = name.split()[-1].lower()
            matched = msf_df[msf_df["last_name"].str.lower().str.contains(last_name)]
            if not matched.empty:
                row = matched.iloc[0]
                avg = float(row.get("avg", avg))
                obp = float(row.get("obp", obp))
                hr = int(row.get("hr", hr))

        # Try to enrich with FanGraphs advanced stats
        if not fg_df.empty:
            fg_match = fg_df[fg_df["Name"].str.lower().str.contains(name.lower())]
            if not fg_match.empty:
                fg_row = fg_match.iloc[0]
                obp = float(fg_row.get("OBP", obp))
                hr = int(fg_row.get("HR", hr))

        # Recommend based on values
        recommendations = {}

        if avg >= 0.320:
            recommendations["Total Bases"] = "🔥 Must Bet Over"
        elif avg >= 0.290:
            recommendations["Total Bases"] = "✅ Strong Over"
        elif avg <= 0.210:
            recommendations["Total Bases"] = "❌ Strong Under"

        if obp >= 0.400:
            recommendations["On-Base Prop"] = "🔥 Bet OBP Over"
        elif obp <= 0.290:
            recommendations["On-Base Prop"] = "❌ Avoid OBP Over"

        if hr >= 2:
            recommendations["Home Run Prop"] = "🔥 Bet HR Over"
        elif hr == 0:
            recommendations["Home Run Prop"] = "❌ Avoid HR Over"

        return {
            "AVG": avg,
            "OBP": obp,
            "HR": hr,
            "Recommendations": recommendations,
            "Reason": f"Fallback-adjusted for {name} (AVG {avg}, OBP {obp}, HR {hr})"
        }

    # Live default logic (unchanged)
    obp = base_stats.get("obp", 0.320)
    avg = base_stats.get("avg", 0.250)
    hr = base_stats.get("hr", 1)

    recommendations = {}

    if avg >= 0.320:
        recommendations["Total Bases"] = "🔥 Must Bet Over"
    elif avg >= 0.290:
        recommendations["Total Bases"] = "✅ Strong Over"
    elif avg <= 0.210:
        recommendations["Total Bases"] = "❌ Strong Under"

    if obp >= 0.400:
        recommendations["On-Base Prop"] = "🔥 Bet OBP Over"
    elif obp <= 0.290:
        recommendations["On-Base Prop"] = "❌ Avoid OBP Over"

    if hr >= 2:
        recommendations["Home Run Prop"] = "🔥 Bet HR Over"
    elif hr == 0:
        recommendations["Home Run Prop"] = "❌ Avoid HR Over"

    return {
        "AVG": avg,
        "OBP": obp,
        "HR": hr,
        "Recommendations": recommendations,
        "Reason": f"Live-adjusted from MLB API for {name} (AVG {avg}, OBP {obp}, HR {hr})"
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
