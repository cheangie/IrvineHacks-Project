"""
YOU own this file.
Input:  lat, lng, flood_zone (from FEMA), calfire_zone (from CalFire)
Output: {"flood": int, "fire": int, "overall": int}  all scores 0-100
"""

# FEMA flood zone → risk score
FLOOD_ZONE_SCORES = {
    "AE": 90, "A": 85, "AO": 80, "AH": 80,
    "AR": 75, "A99": 70,
    "V": 95,  "VE": 95,
    "B": 40,  "C": 20, "X": 15, "D": 50,
}

# CalFire hazard zone → risk score
CALFIRE_SCORES = {
    "Very High": 90,
    "High": 65,
    "Moderate": 35,
    "Low": 15,
}

def flood_score(zone: str) -> int:
    return FLOOD_ZONE_SCORES.get(zone.upper(), 30)

def fire_score(calfire_zone: str) -> int:
    return CALFIRE_SCORES.get(calfire_zone, 30)

def calculate_risk(lat: float, lng: float, flood_zone: str, calfire_zone: str) -> dict:
    flood = flood_score(flood_zone)
    fire = fire_score(calfire_zone)
    overall = round(flood * 0.45 + fire * 0.55)
    return {
        "flood": flood,
        "fire": fire,
        "overall": overall
    }


# ── Test it standalone ─────────────────────────────────────────────────
if __name__ == "__main__":
    result = calculate_risk(33.6, -117.8, "AE", "Very High")
    print(result)  # should print scores for a high risk property