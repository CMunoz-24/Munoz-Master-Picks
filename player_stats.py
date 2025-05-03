# 🔧 Helper Module: player_stats.py

import requests
import random

# This is a stub — in future we can replace it with real Statcast API logic
# For now, this uses player name matching to simulate fetching real stats

def get_player_stat_profile(player_name):
    # Simulate stat-based logic (later: match to player_id and fetch real splits)
    sample_profiles = {
        "Aaron Judge": {
            "Hits": 0.71,
            "HR": 0.38,
            "Walks": 0.16,
            "Barrel%": 17.1,
            "HardHit%": 51.4,
        },
        "Juan Soto": {
            "Hits": 0.68,
            "HR": 0.32,
            "Walks": 0.21,
            "Barrel%": 13.3,
            "HardHit%": 43.9,
        },
        "Shohei Ohtani": {
            "Hits": 0.64,
            "HR": 0.36,
            "Walks": 0.11,
            "Barrel%": 15.5,
            "HardHit%": 47.2,
        }
    }

    if player_name in sample_profiles:
        return sample_profiles[player_name]

    # If unknown, simulate with average range
    return {
        "Hits": round(random.uniform(0.55, 0.7), 2),
        "HR": round(random.uniform(0.1, 0.3), 2),
        "Walks": round(random.uniform(0.05, 0.2), 2),
        "Barrel%": round(random.uniform(6, 13), 1),
        "HardHit%": round(random.uniform(30, 45), 1),
    }