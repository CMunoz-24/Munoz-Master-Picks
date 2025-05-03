import pandas as pd
import io
import requests

def get_fangraphs_stats():
    url = "https://www.fangraphs.com/projections?pos=all&stats=bat&type=bat&team=0&lg=all&players=0&sort=5,d"
    try:
        print("[INFO] Downloading FanGraphs CSV...")
        response = requests.get("https://cdn.fangraphs.com/projections.csv")
        df = pd.read_csv(io.StringIO(response.text))
        print(f"[INFO] FanGraphs rows loaded: {len(df)}")
        return df
    except Exception as e:
        print(f"[ERROR] Failed to load FanGraphs data: {e}")
        return pd.DataFrame()
