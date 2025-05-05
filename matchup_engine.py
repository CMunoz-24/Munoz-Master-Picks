# matchup_engine.py

from player_stats_helper import get_vs_pitcher_history
from utils.park_factors import get_park_adjustments
import pandas as pd

def generate_batter_probabilities(season_stats):
    ba = season_stats.get("BA", 0.0)
    hr_rate = season_stats.get("HR", 0) / 500  # Simplified HR probability estimate
    walk_rate = season_stats.get("BB%", 0.0)

    return {
        "Hit": round(ba, 3),
        "HR": round(hr_rate, 3),
        "Walk": round(walk_rate, 3)
    }

def generate_batter_recommendations(probabilities):
    recs = {}

    hit_prob = probabilities.get("Hit", 0)
    hr_prob = probabilities.get("HR", 0)
    walk_prob = probabilities.get("Walk", 0)

    # 🔍 Hit recommendations
    if hit_prob > 0.27:
        recs["Hit"] = "Take Hit Prop"
    elif hit_prob < 0.22:
        recs["Hit"] = "Avoid Hit Prop"

    # 🔍 Home Run recommendations
    if hr_prob > 0.05:
        recs["HR"] = "Consider HR Prop"

    # 🔍 Walk recommendations
    if walk_prob > 0.12:
        recs["Walk"] = "Take Walk Prop"
    elif walk_prob < 0.06:
        recs["Walk"] = "Avoid Walk Prop"

    return recs

def generate_adjusted_batter_probabilities(season_stats, pitcher_stats, vs_history=None, park_adjustment=None, weather_adjustment=None):
    ba = season_stats.get("BA", 0.0)
    hr_raw = season_stats.get("HR", 0)
    bb_rate = season_stats.get("BB%", 0.0)

    era = pitcher_stats.get("ERA", 4.00)
    k9 = pitcher_stats.get("K/9", 7.5)
    bb9 = pitcher_stats.get("BB/9", 2.8)

    # Baseline adjustments from pitcher performance
    if era < 3.00:
        ba *= 0.92
    elif era > 4.50:
        ba *= 1.08

    hr_rate = hr_raw / 500
    if k9 > 9.0:
        hr_rate *= 0.9
    elif k9 < 6.0:
        hr_rate *= 1.15

    if bb9 < 2.0:
        bb_rate *= 0.85
    elif bb9 > 3.5:
        bb_rate *= 1.15

    # Historical batter vs pitcher adjustments
    if vs_history and vs_history["AB"] >= 5:
        ba = (ba + vs_history["BA"]) / 2
        hr_rate *= (1 + (vs_history["HR"] / vs_history["AB"]) * 3)
        bb_rate *= (1 + (vs_history["BB"] / vs_history["AB"]))

    # Park adjustments
    if park_adjustment:
        hr_factor = park_adjustment.get("HR", 1.0)
        k_factor = park_adjustment.get("K", 1.0)
        hr_rate *= hr_factor
        ba *= 1 - ((k_factor - 1.0) * 0.5)

    # Weather adjustments
    if weather_adjustment:
        if weather_adjustment.get("HR Boost") == "+10%":
            hr_rate *= 1.10
        if weather_adjustment.get("Strikeout Drop") == "-5%":
            ba *= 1.05

    return {
        "Hit": round(ba, 3),
        "HR": round(min(hr_rate, 1.0), 3),
        "Walk": round(min(bb_rate, 1.0), 3)
    }

def get_adjusted_hitter_props(name, opposing_pitcher, base_stats, fallback_data=None):
    if fallback_data:
        print(f"[FALLBACK] Generating hitter props for {name}")

        msf_df = fallback_data.get("mysportsfeeds")
        fg_df = fallback_data.get("fangraphs")

        avg = 0.250
        obp = 0.320
        hr = 1

        # ✅ Match by last name (from MySportsFeeds)
        if isinstance(msf_df, pd.DataFrame) and not msf_df.empty and "last_name" in msf_df.columns:
            last_name = name.split()[-1].lower()
            matched = msf_df[msf_df["last_name"].fillna("").str.lower().str.contains(last_name)]
            if not matched.empty:
                row = matched.iloc[0]
                avg = float(row.get("avg", avg))
                obp = float(row.get("obp", obp))
                hr = int(row.get("hr", hr))

        # ✅ Try to enrich with FanGraphs advanced stats
        if isinstance(fg_df, pd.DataFrame) and not fg_df.empty and "Name" in fg_df.columns:
            fg_match = fg_df[fg_df["Name"].fillna("").str.lower().str.contains(name.lower())]
            if not fg_match.empty:
                fg_row = fg_match.iloc[0]
                obp = float(fg_row.get("OBP", obp))
                hr = int(fg_row.get("HR", hr))

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

    # 🔄 Live logic
    avg = base_stats.get("AVG", 0.250)
    obp = base_stats.get("OBP", 0.320)
    hr = base_stats.get("HR", 1)

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

