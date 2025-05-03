
import pandas as pd
import os
from datetime import datetime

def fetch_fangraphs_csv(save_path="data/cache/fangraphs_fallback.csv"):
    # Example static CSV export (update this to latest downloadable FanGraphs CSV)
    url = "https://www.fangraphs.com/leaders.aspx?pos=all&stats=bat&lg=all&qual=0&type=8&season=2024&month=0&season1=2024&ind=0&team=0&rost=0&age=0&filter=&players=0&export=1"

    try:
        df = pd.read_csv(url)
        df['last_updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        df.to_csv(save_path, index=False)
        return df
    except Exception as e:
        print("[ERROR] Failed to fetch FanGraphs CSV:", e)
        return pd.DataFrame()
