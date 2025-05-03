import pandas as pd

def load_chadwick_player_mapping():
    try:
        url = "https://raw.githubusercontent.com/chadwickbureau/register/master/data/people.csv"
        print("[INFO] Fetching Chadwick player ID map...")
        df = pd.read_csv(url)
        print(f"[INFO] Chadwick player count: {len(df)}")
        return df
    except Exception as e:
        print(f"[ERROR] Failed to load Chadwick registry: {e}")
        return pd.DataFrame()

