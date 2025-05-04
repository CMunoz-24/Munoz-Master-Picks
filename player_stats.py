from pybaseball import playerid_lookup, batting_stats_range, pitching_stats_range
import pandas as pd
from datetime import datetime

# fallback CSV path
FALLBACK_CSV = "fallback_stats.csv"

def get_player_stats(player_name):
    season_stats = {}

    try:
        # 1. Lookup player ID
        pid_df = playerid_lookup(*player_name.split())
        if pid_df.empty:
            raise ValueError("Player not found in lookup")

        player_id = pid_df.iloc[0]["key_mlbam"]
        today = datetime.today().strftime("%Y-%m-%d")
        season_start = "2024-03-20"

        # 2. Try as a batter
        bat_stats = batting_stats_range(season_start, today)
        row = bat_stats[bat_stats["Name"].str.contains(player_name, case=False)]

        if not row.empty:
            stats = row.iloc[0]

            # ✅ Fix string percentages like "12.3%"
            for key in ["BB%", "K%"]:
                if isinstance(stats.get(key), str) and "%" in stats.get(key):
                    stats[key] = float(stats[key].strip('%'))

            season_stats = {
                "BA": round(stats.get("AVG", 0.0), 3),
                "HR": int(stats.get("HR", 0)),
                "BB%": round(stats.get("BB%", 0.0) / 100, 3),
                "SO%": round(stats.get("K%", 0.0) / 100, 3),
                "OPS": round(stats.get("OPS", 0.0), 3)
            }

        else:
            # 3. Try as a pitcher
            pitch_stats = pitching_stats_range(season_start, today)
            row = pitch_stats[pitch_stats["Name"].str.contains(player_name, case=False)]

            if not row.empty:
                stats = row.iloc[0]
                season_stats = {
                    "ERA": round(stats.get("ERA", 0.0), 2),
                    "WHIP": round(stats.get("WHIP", 0.0), 2),
                    "K/9": round(stats.get("K/9", 0.0), 2),
                    "BB/9": round(stats.get("BB/9", 0.0), 2),
                }

    except Exception as e:
        print(f"[WARNING] pybaseball failed for {player_name}: {e}")
        # 4. Fallback to CSV
        try:
            df = pd.read_csv(FALLBACK_CSV)
            row = df[df["Name"].str.contains(player_name, case=False)]
            if not row.empty:
                stats = row.iloc[0].to_dict()
                season_stats = {k: stats[k] for k in stats if k != "Name"}
        except Exception as e2:
            print(f"[FALLBACK ERROR] {e2}")

    return {"SeasonStats": season_stats}
