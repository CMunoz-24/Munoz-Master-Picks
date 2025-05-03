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

def get_adjusted_pitcher_props(pitcher_name, raw_stats=None):
    # You can pass in real stats later. For now, we simulate.
    k_rate = round(random.uniform(0.5, 0.9), 2)  # Strikeout probability
    outs = round(random.uniform(0.5, 0.95), 2)
    walks = round(random.uniform(0.2, 0.8), 2)
    hits_allowed = round(random.uniform(0.2, 0.85), 2)
    earned_runs = round(random.uniform(0.1, 0.75), 2)

    props = {
        "Strikeouts": k_rate,
        "Outs": outs,
        "Walks Allowed": walks,
        "Hits Allowed": hits_allowed,
        "Earned Runs": earned_runs
    }

    recommendations = {stat: get_pitcher_prop_recommendation(stat, value) for stat, value in props.items()}

    return {
        **props,
        "Recommendations": recommendations
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