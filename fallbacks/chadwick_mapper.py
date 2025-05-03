
import pandas as pd
import os

def load_chadwick_register(register_path="data/cache/people.csv"):
    if not os.path.exists(register_path):
        print(f"[ERROR] Chadwick register not found at {register_path}")
        return pd.DataFrame()
    
    try:
        df = pd.read_csv(register_path)
        return df[[
            "name_first", "name_last", "key_mlbam", "key_fangraphs", 
            "key_retro", "mlb_played_first", "mlb_played_last"
        ]]
    except Exception as e:
        print("[ERROR] Failed to load Chadwick register:", e)
        return pd.DataFrame()

def match_player_name(df, name_first, name_last):
    matched = df[(df['name_first'].str.lower() == name_first.lower()) &
                 (df['name_last'].str.lower() == name_last.lower())]
    if not matched.empty:
        return matched.iloc[0].to_dict()
    return None
