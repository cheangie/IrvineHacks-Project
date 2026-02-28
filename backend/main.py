from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import httpx, os, math, asyncio
from dotenv import load_dotenv
from risk_scorer import calculate_risk
from ai_service import get_ai_analysis

load_dotenv()

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

MELISSA_KEY = os.getenv("MELISSA_KEY")


# ══════════════════════════════════════════════════════════════
#  NIVEDHA — Melissa Geocoding
# ══════════════════════════════════════════════════════════════
async def geocode(address: str):
    try:
        parts   = [p.strip() for p in address.split(",")]
        a1      = parts[0]
        loc     = parts[1] if len(parts) > 1 else ""
        admarea = parts[2] if len(parts) > 2 else ""
        postal  = parts[3] if len(parts) > 3 else ""
    except IndexError:
        raise ValueError("Address must be: Street, City, State, Zip")

    async with httpx.AsyncClient() as client:
        res = await client.get(
            "https://address.melissadata.net/v3/WEB/GlobalAddress/doGlobalAddress",
            params={
                "format":  "JSON",
                "opt":     "USPreferredCityNames:ON,OutputGeo:ON",
                "a1":      a1,
                "loc":     loc,
                "admarea": admarea,
                "postal":  postal,
                "ctry":    "US",
                "id":      MELISSA_KEY
            }
        )

    record  = res.json()["Records"][0]
    lat_str = record.get("Latitude", "").strip()
    lng_str = record.get("Longitude", "").strip()

    if not lat_str or not lng_str:
        raise ValueError(f"Melissa returned no coordinates for: {address}")

    return {
        "lat":          float(lat_str),
        "lng":          float(lng_str),
        "county":       record.get("SubAdministrativeArea", ""),
        "fips":         record.get("CensusKey", ""),
        "neighborhood": record.get("Locality", ""),
    }


# ══════════════════════════════════════════════════════════════
#  SRISTI — Climate Risk API Calls
# ══════════════════════════════════════════════════════════════

# 1. FEMA Flood Zone — with elevation-based fallback
async def get_flood_zone(lat: float, lng: float, elevation: float = 100.0) -> str:
    # Try FEMA first
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.get(
                "https://hazards.fema.gov/gis/nfhl/rest/services/public/NFHL/MapServer/28/query",
                params={
                    "geometry":       f"{lng},{lat}",
                    "geometryType":   "esriGeometryPoint",
                    "inSR":           "4326",
                    "spatialRel":     "esriSpatialRelIntersects",
                    "outFields":      "FLD_ZONE",
                    "returnGeometry": "false",
                    "f":              "json"
                }
            )
        features = res.json().get("features", [])
        if features:
            return features[0]["attributes"]["FLD_ZONE"]
    except Exception as e:
        print(f"FEMA error: {e}")

    # Fallback — estimate flood zone from elevation
    print("Using elevation-based flood zone fallback")
    if elevation < 0:    return "VE"   # below sea level = coastal/extreme risk
    if elevation < 5:    return "AE"   # very low = high risk
    if elevation < 15:   return "A"    # low = moderate-high risk
    if elevation < 50:   return "B"    # moderate elevation
    return "X"                          # high elevation = minimal risk

# 2. USFS Wildfire Hazard Potential
async def get_wildfire_hazard(lat: float, lng: float) -> str:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.get(
                "https://apps.fs.usda.gov/arcx/rest/services/EDW/EDW_WildfireHazardPotential_01/MapServer/0/query",
                params={
                    "geometry":       f"{lng},{lat}",
                    "geometryType":   "esriGeometryPoint",
                    "inSR":           "4326",
                    "spatialRel":     "esriSpatialRelIntersects",
                    "outFields":      "WHP_CLASS",
                    "returnGeometry": "false",
                    "f":              "json"
                }
            )
        features = res.json().get("features", [])
        if features:
            return features[0]["attributes"].get("WHP_CLASS", "Moderate")
    except Exception as e:
        print(f"Wildfire error: {e}")
    return "Low"

# 3. USGS Elevation — with Open Elevation API as backup
async def get_elevation(lat: float, lng: float) -> float:
    # Try USGS first
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.get(
                "https://epqs.nationalmap.gov/v1/json",
                params={"x": lng, "y": lat, "units": "Meters", "wkid": "4326", "includeDate": "false"}
            )
        val = float(res.json().get("value", 0))
        if val != 0:  # 0 could be a failed response
            return val
    except Exception as e:
        print(f"USGS elevation error: {e}")

    # Backup — Open Elevation API (free, no key)
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.post(
                "https://api.open-elevation.com/api/v1/lookup",
                json={"locations": [{"latitude": lat, "longitude": lng}]}
            )
        return float(res.json()["results"][0]["elevation"])
    except Exception as e:
        print(f"Open Elevation error: {e}")

    return 100.0  # last resort default

# 4. USGS Landslide Inventory — with elevation-based fallback
async def get_landslide_history(lat: float, lng: float, elevation: float = 100.0) -> int:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.get(
                "https://services.nationalmap.gov/arcgis/rest/services/LandslideInventory/MapServer/0/query",
                params={
                    "geometry":        f"{lng},{lat}",
                    "geometryType":    "esriGeometryPoint",
                    "inSR":            "4326",
                    "spatialRel":      "esriSpatialRelWithin",
                    "distance":        15000,
                    "units":           "esriSRUnit_Meter",
                    "outFields":       "OBJECTID",
                    "returnCountOnly": "true",
                    "f":               "json"
                }
            )
        return int(res.json().get("count", 0))
    except Exception as e:
        print(f"Landslide error: {e}")

    # Fallback — estimate from elevation (higher + steeper = more landslide risk)
    print("Using elevation-based landslide fallback")
    if elevation > 1000: return 8
    if elevation > 500:  return 5
    if elevation > 200:  return 2
    return 0

# 5. NIFC Historical Fire Perimeter Distance
async def get_fire_distance(lat: float, lng: float) -> float:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.get(
                "https://services3.arcgis.com/T4QMspbfLg3qTGWY/arcgis/rest/services/WFIGS_Interagency_Perimeters/FeatureServer/0/query",
                params={
                    "geometry":       f"{lng},{lat}",
                    "geometryType":   "esriGeometryPoint",
                    "inSR":           "4326",
                    "spatialRel":     "esriSpatialRelIntersects",
                    "distance":       50000,
                    "units":          "esriSRUnit_Meter",
                    "outFields":      "OBJECTID",
                    "orderByFields":  "Shape__Area DESC",
                    "returnGeometry": "true",
                    "outSR":          "4326",
                    "f":              "json"
                }
            )
        features = res.json().get("features", [])
        if not features:
            return 999.0

        def haversine(lat1, lng1, lat2, lng2):
            R = 6371
            dlat = math.radians(lat2 - lat1)
            dlng = math.radians(lng2 - lng1)
            a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng/2)**2
            return R * 2 * math.asin(math.sqrt(a))

        min_dist = 999.0
        for f in features:
            rings = f.get("geometry", {}).get("rings", [])
            if rings:
                pt = rings[0][0]
                dist = haversine(lat, lng, pt[1], pt[0])
                if dist < min_dist:
                    min_dist = dist
        return round(min_dist, 2)
    except Exception as e:
        print(f"Fire distance error: {e}")
    return 999.0

# 6. SRISTI BONUS — NOAA Active Weather Alerts
async def get_noaa_alerts(lat: float, lng: float) -> list:
    """Returns list of active flood/weather alerts from NOAA. Bonus data point."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            res = await client.get(
                f"https://api.weather.gov/alerts/active?point={lat},{lng}",
                headers={"User-Agent": "ClimateCheckApp/1.0"}
            )
        if res.status_code == 200:
            alerts = res.json().get("features", [])
            return [
                a["properties"].get("headline", "")
                for a in alerts
                if a["properties"].get("headline")
            ]
    except Exception as e:
        print(f"NOAA error: {e}")
    return []


# ══════════════════════════════════════════════════════════════
#  MAIN ENDPOINT
# ══════════════════════════════════════════════════════════════
@app.get("/")
def home():
    return {"message": "ClimateCheck API is running!"}

@app.get("/risk")
async def get_risk(address: str):
    # Geocode first (needed for everything else)
    location = await geocode(address)
    lat, lng = location["lat"], location["lng"]

    # Get elevation first — needed for flood + landslide fallbacks
    elevation = await get_elevation(lat, lng)

    # Run remaining 5 API calls in parallel
    flood_zone, wildfire_hazard, landslide_count, fire_distance_km, noaa_alerts = await asyncio.gather(
        get_flood_zone(lat, lng, elevation),
        get_wildfire_hazard(lat, lng),
        get_landslide_history(lat, lng, elevation),
        get_fire_distance(lat, lng),
        get_noaa_alerts(lat, lng),
    )

    landslide_count = int(landslide_count)

    scores = calculate_risk(
        flood_zone       = flood_zone,
        wildfire_hazard  = wildfire_hazard,
        elevation        = elevation,
        landslide_count  = landslide_count,
        fire_distance_km = fire_distance_km
    )

    ai = get_ai_analysis(
        address         = address,
        flood_zone      = flood_zone,
        wildfire_hazard = wildfire_hazard,
        flood_score     = scores["flood"],
        fire_score      = scores["fire"],
        landslide_score = scores["landslide"]
    )

    return {
        "address":          address,
        "county":           location["county"],
        "neighborhood":     location["neighborhood"],
        "lat":              lat,
        "lng":              lng,
        "flood_zone":       flood_zone,
        "wildfire_hazard":  wildfire_hazard,
        "elevation_m":      elevation,
        "landslide_nearby": landslide_count,
        "fire_distance_km": fire_distance_km,
        "active_alerts":    noaa_alerts,
        **scores,
        **ai
    }