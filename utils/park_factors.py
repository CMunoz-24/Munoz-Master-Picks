
# utils/park_factors.py

# Park factors pulled from FanGraphs + MLB Statcast + 2024–25 changes
PARK_FACTORS = {
    "Chase Field": {"HR": 1.10, "K": 0.95},
    "Truist Park": {"HR": 1.05, "K": 1.00},
    "Oriole Park at Camden Yards": {"HR": 1.10, "K": 0.95},
    "Fenway Park": {"HR": 1.10, "K": 0.95},
    "Guaranteed Rate Field": {"HR": 1.08, "K": 1.02},
    "Wrigley Field": {"HR": 1.00, "K": 1.00},
    "Great American Ball Park": {"HR": 1.25, "K": 0.95},
    "Progressive Field": {"HR": 0.95, "K": 1.00},
    "Coors Field": {"HR": 1.25, "K": 0.90},
    "Comerica Park": {"HR": 0.92, "K": 1.03},
    "Minute Maid Park": {"HR": 1.04, "K": 1.00},
    "Kauffman Stadium": {"HR": 0.90, "K": 1.02},
    "Angel Stadium": {"HR": 1.00, "K": 1.00},
    "Dodger Stadium": {"HR": 1.05, "K": 1.00},
    "loanDepot Park": {"HR": 0.85, "K": 1.05},
    "American Family Field": {"HR": 1.10, "K": 0.98},
    "Target Field": {"HR": 0.92, "K": 1.00},
    "Yankee Stadium": {"HR": 1.15, "K": 0.97},
    "Citi Field": {"HR": 0.92, "K": 1.05},
    "Sutter Health Park": {"HR": 0.88, "K": 1.04},
    "Citizens Bank Park": {"HR": 1.10, "K": 0.96},
    "PNC Park": {"HR": 0.92, "K": 1.02},
    "Petco Park": {"HR": 0.75, "K": 1.10},
    "Oracle Park": {"HR": 0.80, "K": 1.05},
    "T-Mobile Park": {"HR": 0.92, "K": 1.00},
    "Busch Stadium": {"HR": 0.93, "K": 1.02},
    "George M. Steinbrenner Field": {"HR": 1.05, "K": 1.00},
    "Globe Life Field": {"HR": 1.00, "K": 1.00},
    "Rogers Centre": {"HR": 1.08, "K": 0.97},
    "Nationals Park": {"HR": 1.00, "K": 1.00},
    "default": {"HR": 1.00, "K": 1.00}
}

def get_park_adjustments(stadium_name):
    return PARK_FACTORS.get(stadium_name, PARK_FACTORS["default"])
