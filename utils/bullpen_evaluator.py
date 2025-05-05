# utils/bullpen_evaluator.py

from player_stats import get_player_stats

def evaluate_bullpen_strength(players, fallback_data=None):
    """
    Accepts a dictionary of players (from boxscore["players"]) and evaluates bullpen strength.
    Returns a bullpen score between 0 and 1, where 1 is elite.
    """
    relievers = []

    for p in players.values():
        pos = p.get("position", {}).get("abbreviation", "")
        if pos == "P" and p.get("stats") and not p.get("gameStatus", {}).get("isStarter", False):
            name = p["person"]["fullName"]
            try:
                stats = get_player_stats(name).get("SeasonStats", {})
                era = float(stats.get("ERA", 4.00))
                whip = float(stats.get("WHIP", 1.30))
                so9 = float(stats.get("SO/9", 7.5))
                relievers.append({"ERA": era, "WHIP": whip, "SO9": so9})
            except Exception:
                # Try fallback
                if isinstance(fallback_data, dict) and fallback_data:
                    fg_df = fallback_data.get("fangraphs", None)
                    if fg_df is not None:
                        match = fg_df[fg_df["Name"].str.lower().str.contains(name.lower())]
                        if not match.empty:
                            row = match.iloc[0]
                            era = float(row.get("ERA", 4.00))
                            whip = float(row.get("WHIP", 1.30))
                            so9 = float(row.get("K/9", 7.5))
                            relievers.append({"ERA": era, "WHIP": whip, "SO9": so9})

    if not relievers:
        return 0.5  # Neutral score if nothing found

    avg_era = sum(r["ERA"] for r in relievers) / len(relievers)
    avg_whip = sum(r["WHIP"] for r in relievers) / len(relievers)
    avg_so9 = sum(r["SO9"] for r in relievers) / len(relievers)

    # Convert to a normalized bullpen score
    score = 1.0
    if avg_era < 3.50:
        score += 0.1
    elif avg_era > 4.50:
        score -= 0.1

    if avg_whip < 1.20:
        score += 0.1
    elif avg_whip > 1.40:
        score -= 0.1

    if avg_so9 > 9.0:
        score += 0.1
    elif avg_so9 < 6.5:
        score -= 0.1

    return min(max(round(score, 2), 0.0), 1.0)
