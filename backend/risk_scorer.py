"""
YOU own this file.
Inputs:  flood_zone, wildfire_hazard, elevation, landslide_count
Output:  {"flood": int, "fire": int, "landslide": int, "overall": int}
"""

# FEMA flood zone → base score
FLOOD_ZONE_SCORES = {
    "VE": 95, "V": 95,
    "AE": 85, "AO": 80, "AH": 80, "A": 75, "AR": 70, "A99": 65,
    "B":  40, "C":  20, "X":  15, "D": 50,
}

# USFS wildfire hazard → base score
WILDFIRE_SCORES = {
    "Very High": 90,
    "High":      65,
    "Moderate":  35,
    "Low":       10,
}

def elevation_score(elevation_m: float) -> int:
    """Lower elevation = higher flood/landslide risk"""
    if elevation_m < 10:   return 90
    if elevation_m < 50:   return 60
    if elevation_m < 150:  return 30
    return 10

def slope_proxy_score(elevation_m: float) -> int:
    """
    We don't have slope directly, so we use elevation as a proxy.
    Higher elevation areas in the US tend to have steeper terrain.
    Replace with real slope data if available.
    """
    if elevation_m > 500:  return 80
    if elevation_m > 200:  return 55
    if elevation_m > 50:   return 30
    return 15

def landslide_history_score(count: int) -> int:
    """More historical incidents nearby = higher risk"""
    if count > 10: return 90
    if count > 5:  return 70
    if count > 1:  return 45
    if count == 1: return 25
    return 10

def calculate_risk(flood_zone: str, wildfire_hazard: str, elevation: float, landslide_count: int) -> dict:
    # Sub-scores
    fema     = FLOOD_ZONE_SCORES.get(flood_zone.upper(), 30)
    elev     = elevation_score(elevation)
    fire_raw = WILDFIRE_SCORES.get(wildfire_hazard, 30)
    slope    = slope_proxy_score(elevation)
    ls_hist  = landslide_history_score(landslide_count)

    # Component scores (0-100)
    flood     = round(fema     * 0.60 + elev  * 0.40)
    fire      = round(fire_raw * 0.50 + ls_hist * 0.30 + slope * 0.20)
    landslide = round(slope    * 0.50 + elev  * 0.20 + ls_hist * 0.30)

    # Overall weighted score
    overall = round(flood * 0.35 + fire * 0.40 + landslide * 0.25)

    return {
        "flood":     flood,
        "fire":      fire,
        "landslide": landslide,
        "overall":   overall
    }


# ── Test standalone ────────────────────────────────────────────────────
if __name__ == "__main__":
    result = calculate_risk(
        flood_zone      = "AE",
        wildfire_hazard = "Very High",
        elevation       = 120.0,
        landslide_count = 3
    )
    print(result)