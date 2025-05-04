def calculate_probabilities(stats):
    """
    Calculate real-world event probabilities from player season stats.
    Expects a dictionary with at least: AB, H, HR, BB, SO.
    """
    try:
        ab = int(stats.get("AB", 0)) or 1
        hits = int(stats.get("H", 0))
        home_runs = int(stats.get("HR", 0))
        walks = int(stats.get("BB", 0))
        strikeouts = int(stats.get("SO", 0))

        return {
            "Hit": round(hits / ab, 3),
            "HR": round(home_runs / ab, 3),
            "Walk": round(walks / ab, 3),
            "Strikeout": round(strikeouts / ab, 3)
        }
    except Exception as e:
        print(f"[ERROR] Failed to calculate probabilities: {e}")
        return {
            "Hit": 0.0,
            "HR": 0.0,
            "Walk": 0.0,
            "Strikeout": 0.0
        }
