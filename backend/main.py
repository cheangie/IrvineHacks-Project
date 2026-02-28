from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import httpx, os
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
#  Input:  address string
#  Output: dict with lat, lng, county, fips, neighborhood
# ══════════════════════════════════════════════════════════════
async def geocode(address: str) -> dict:
    async with httpx.AsyncClient() as client:
        res = await client.get(
            "https://personator.melissadata.net/v3/WEB/ContactVerify/doContactVerify",
            params={
                "id": MELISSA_KEY,
                "act": "GeoCode",
                "full": address,
                "format": "json"
            }
        )
    record = res.json()["Records"][0]
    return {
        "lat":          float(record["Latitude"]),
        "lng":          float(record["Longitude"]),
        "county":       record.get("CountyName", ""),
        "fips":         record.get("CountyFIPS", ""),
        "neighborhood": record.get("UrbanizationName", ""),
    }


# ══════════════════════════════════════════════════════════════
#  SRISTI — Climate Risk API Calls
#  All 4 functions take lat + lng, return a string label or float
# ══════════════════════════════════════════════════════════════

# 1. FEMA Flood Zone
async def get_flood_zone(lat: float, lng: float) -> str:
    async with httpx.AsyncClient() as client:
        res = await client.get(
            "https://hazards.fema.gov/gis/nfhl/rest/services/public/NFHL/MapServer/28/query",
            params={
                "geometry":         f"{lng},{lat}",
                "geometryType":     "esriGeometryPoint",
                "inSR":             "4326",
                "spatialRel":       "esriSpatialRelIntersects",
                "outFields":        "FLD_ZONE",
                "returnGeometry":   "false",
                "f":                "json"
            }
        )
    features = res.json().get("features", [])
    if features:
        return features[0]["attributes"]["FLD_ZONE"]
    return "X"  # default = minimal risk

# 2. USFS Wildfire Hazard Potential (nationwide)
async def get_wildfire_hazard(lat: float, lng: float) -> str:
    async with httpx.AsyncClient() as client:
        res = await client.get(
            "https://apps.fs.usda.gov/arcx/rest/services/EDW/EDW_WildfireHazardPotential_01/MapServer/0/query",
            params={
                "geometry":         f"{lng},{lat}",
                "geometryType":     "esriGeometryPoint",
                "inSR":             "4326",
                "spatialRel":       "esriSpatialRelIntersects",
                "outFields":        "WHP_CLASS",
                "returnGeometry":   "false",
                "f":                "json"
            }
        )
    features = res.json().get("features", [])
    if features:
        return features[0]["attributes"].get("WHP_CLASS", "Moderate")
    return "Low"

# 3. USGS Elevation
async def get_elevation(lat: float, lng: float) -> float:
    async with httpx.AsyncClient() as client:
        res = await client.get(
            "https://epqs.nationalmap.gov/v1/json",
            params={
                "x": lng,
                "y": lat,
                "units": "Meters",
                "wkid": "4326",
                "includeDate": "false"
            }
        )
    return float(res.json().get("value", 100))

# 4. USGS Landslide Inventory (historical incidents near point)
async def get_landslide_history(lat: float, lng: float) -> float:
    # Query landslide incidents within ~15km radius
    async with httpx.AsyncClient() as client:
        res = await client.get(
            "https://services.nationalmap.gov/arcgis/rest/services/LandslideInventory/MapServer/0/query",
            params={
                "geometry":         f"{lng},{lat}",
                "geometryType":     "esriGeometryPoint",
                "inSR":             "4326",
                "spatialRel":       "esriSpatialRelWithin",
                "distance":         15000,  # 15km in meters
                "units":            "esriSRUnit_Meter",
                "outFields":        "OBJECTID",
                "returnCountOnly":  "true",
                "f":                "json"
            }
        )
    return res.json().get("count", 0)


# ══════════════════════════════════════════════════════════════
#  MAIN ENDPOINT — wires everything together
# ══════════════════════════════════════════════════════════════
@app.get("/")
def home():
    return {"message": "ClimateCheck API is running!"}

@app.get("/risk")
async def get_risk(address: str):
    # Nivedha's function
    location = await geocode(address)
    lat, lng = location["lat"], location["lng"]

    # Sristi's functions
    flood_zone        = await get_flood_zone(lat, lng)
    wildfire_hazard   = await get_wildfire_hazard(lat, lng)
    elevation         = await get_elevation(lat, lng)
    landslide_count   = await get_landslide_history(lat, lng)

    # Your scoring formula
    scores = calculate_risk(
        flood_zone      = flood_zone,
        wildfire_hazard = wildfire_hazard,
        elevation       = elevation,
        landslide_count = landslide_count
    )

    # Cathryn's Gemini function
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
        **scores,
        **ai
    }