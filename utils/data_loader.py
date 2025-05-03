
import os
from fallbacks.mysportsfeeds import get_mysportsfeeds_stats
from fallbacks.fangraphs_scraper import fetch_fangraphs_csv
from fallbacks.chadwick_mapper import load_chadwick_register

def get_combined_fallback_data():
    print("[INFO] Fetching MySportsFeeds data...")
    msf_df = get_mysportsfeeds_stats()

    print("[INFO] Fetching FanGraphs CSV...")
    fg_df = fetch_fangraphs_csv()

    print("[INFO] Loading Chadwick Register...")
    chadwick_df = load_chadwick_register()

    return {
        "mysportsfeeds": msf_df,
        "fangraphs": fg_df,
        "chadwick": chadwick_df
    }

def is_primary_data_available():
    # Placeholder logic: eventually check live API response status
    return os.getenv("ODDS_API_WORKING", "false").lower() == "true"

def get_live_or_fallback_data():
    if is_primary_data_available():
        print("[INFO] Using primary MLB Stats + Odds API data.")
        # Placeholder: integrate primary pipeline
        return {"primary": "Data from Odds + MLB Stats API"}
    else:
        print("[WARNING] Primary data unavailable. Using fallback sources.")
        return get_combined_fallback_data()
