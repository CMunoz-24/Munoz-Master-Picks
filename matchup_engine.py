# matchup_engine.py

import random

# Simulated matchup adjustment engine

def get_pitcher_profile(pitcher_name):
    # Simulate a pitcher's mix + weakness
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


def get_adjusted_hitter_props(hitter_name, pitcher_name, hitter_stats):
    pitcher = get_pitcher_profile(pitcher_name)

    # Apply adjustments based on matchup logic
    hits = hitter_stats.get("Hits", 0.6)
    hr = hitter_stats.get("HR", 0.2)
    walks = hitter_stats.get("Walks", 0.1)

    reason = []

    # Adjustment: HR prone pitcher
    if pitcher["HR_9"] > 1.0:
        hr += 0.03
        reason.append("Pitcher gives up a lot of home runs.")

    # Adjustment: Slider-heavy pitcher vs high Whiff hitter
    if pitcher["slider%"] > 20:
        whiff = hitter_stats.get("Whiff%", 30)
        if whiff > 28:
            hits -= 0.03
            reason.append("Pitcher's slider may challenge this hitter's swing-and-miss profile.")

    # Handedness adjustment (for future)
    if pitcher["throws"] == "L":
        reason.append("Facing a lefty—adjusts matchups based on splits (future).")

    return {
        "Hits": round(hits, 2),
        "HR": round(hr, 2),
        "Walks": round(walks, 2),
        "Reason": "; ".join(reason) if reason else "Standard projection."
    }