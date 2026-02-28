"""
YOU own this file.

Inputs:
  flood_zone      (str)   — FEMA flood zone e.g. "AE", "X", "VE"
  wildfire_hazard (str)   — USFS hazard class e.g. "Very High", "High"
  elevation       (float) — meters above sea level from USGS
  landslide_count (int)   — # of historical landslide incidents within 15km
  fire_distance_km(float) — km to nearest historical fire perimeter (NIFC)

Output:
  {
    "flood":     int (0-100),
    "fire":      int (0-100),
    "landslide": int (0-100),
    "overall":   int (0-100)
  }
"""

# ── Lookup tables ──────────────────────────────────────────────────────

FLOOD_ZONE_SCORES = {
    "VE": 95, "V": 95,                          # coastal high velocity
    "AE": 85, "AO": 82, "AH": 80, "A": 75,     # 100-year floodplain
    "AR": 70, "A99": 65,                         # protected but at risk
    "B":  40, "C": 20, "X": 15,                 # minimal risk
    "D":  50,                                    # undetermined
}

WILDFIRE_HAZARD_SCORES = {
    "Very High": 90,
    "High":      65,
    "Moderate":  35,
    "Low":       10,
}

# ── Sub-factor converters ──────────────────────────────────────────────

def elevation_to_score(elevation_m: float) -> int:
    """Lower elevation = higher flood + landslide risk"""
    if elevation_m < 10:   return 90
    if elevation_m < 50:   return 65
    if elevation_m < 150:  return 40
    if elevation_m < 500:  return 20
    return 10

def slope_proxy_score(elevation_m: float) -> int:
    """
    Proxy for slope steepness using elevation.
    Higher elevation areas in the US tend to have steeper terrain.
    Higher slope = faster fire spread + more landslide risk.
    """
    if elevation_m > 1000: return 85
    if elevation_m > 500:  return 65
    if elevation_m > 200:  return 40
    if elevation_m > 50:   return 20
    return 10

def fire_distance_to_score(distance_km: float) -> int:
    """Closer to historical fire perimeters = higher risk"""
    if distance_km < 1:    return 95
    if distance_km < 5:    return 80
    if distance_km < 15:   return 55
    if distance_km < 30:   return 30
    return 10

def landslide_count_to_score(count: int) -> int:
    """More historical landslide incidents nearby = higher risk"""
    if count > 10: return 90
    if count > 5:  return 70
    if count > 2:  return 50
    if count == 1: return 30
    return 10

# ── Main scoring function ──────────────────────────────────────────────

def calculate_risk(
    flood_zone:       str,
    wildfire_hazard:  str,
    elevation:        float,
    landslide_count:  int,
    fire_distance_km: float = 999.0  # default = far away if not provided
) -> dict:

    # Raw factor scores (0-100)
    fema        = FLOOD_ZONE_SCORES.get(flood_zone.upper(), 30)
    elev        = elevation_to_score(elevation)
    usfs        = WILDFIRE_HAZARD_SCORES.get(wildfire_hazard, 30)
    fire_hist   = fire_distance_to_score(fire_distance_km)
    slope       = slope_proxy_score(elevation)
    ls_hist     = landslide_count_to_score(landslide_count)

    # Component scores using our agreed formula
    flood     = round(fema      * 0.60 + elev     * 0.40)
    fire      = round(usfs      * 0.60 + fire_hist * 0.30 + slope * 0.10)
    landslide = round(slope     * 0.50 + elev      * 0.20 + ls_hist * 0.30)

    # Cap fire score when USFS zone is Low — slope shouldn't override zone rating
    if wildfire_hazard == "Low":
        fire = min(fire, 25)

    # Overall weighted score
    overall   = round(flood * 0.35 + fire * 0.40 + landslide * 0.25)

    return {
        "flood":     flood,
        "fire":      fire,
        "landslide": landslide,
        "overall":   overall
    }


# ── Test standalone ────────────────────────────────────────────────────
if __name__ == "__main__":
    # High risk property — flood zone AE, very high wildfire, low elevation, close to fires
    high_risk = calculate_risk(
        flood_zone       = "AE",
        wildfire_hazard  = "Very High",
        elevation        = 20.0,
        landslide_count  = 6,
        fire_distance_km = 3.0
    )
    print("High risk property:", high_risk)

    # Low risk property — zone X, low wildfire, high elevation, far from fires
    low_risk = calculate_risk(
        flood_zone       = "X",
        wildfire_hazard  = "Low",
        elevation        = 300.0,
        landslide_count  = 0,
        fire_distance_km = 50.0
    )
    print("Low risk property: ", low_risk)