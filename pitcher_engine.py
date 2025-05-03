
from player_stats_helper import fetch_pitcher_data_by_name

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

def get_adjusted_pitcher_props(pitcher_name, fallback_data=None):
    era = 4.50
    whip = 1.30
    k_rate = 8.0
    recommendations = {}

    if fallback_data:
        print(f"[FALLBACK] Generating pitcher props for {pitcher_name}")
        fg_df = fallback_data.get("fangraphs")

        if not fg_df.empty:
            fg_match = fg_df[fg_df["Name"].str.lower().str.contains(pitcher_name.lower())]
            if not fg_match.empty:
                row = fg_match.iloc[0]
                k_rate = float(row.get("K/9", k_rate))

        # Use defaults for ERA/WHIP in fallback mode
    else:
        data = fetch_pitcher_data_by_name(pitcher_name)
        era = data.get("era", era)
        whip = data.get("whip", whip)
        k_rate = data.get("so9", k_rate)

    # Recommendations
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
        "Reason": f"{'Fallback' if fallback_data else 'Live'}-adjusted for {pitcher_name} (ERA {era}, WHIP {whip}, K/9 {k_rate})"
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
