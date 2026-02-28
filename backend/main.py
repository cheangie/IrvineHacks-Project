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
#  Output: (lat, lng) as floats
# ══════════════════════════════════════════════════════════════
async def geocode(address: str):
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
    return float(record["Latitude"]), float(record["Longitude"])


# ══════════════════════════════════════════════════════════════
#  SRISTI — Climate Risk API Calls
#  Input:  lat, lng as floats
#  Output: flood_zone string (e.g. "AE", "X"),
#          calfire_zone string (e.g. "Very High")
# ══════════════════════════════════════════════════════════════
async def get_flood_zone(lat: float, lng: float) -> str:
    async with httpx.AsyncClient() as client:
        res = await client.get(
            "https://hazards.fema.gov/gis/nfhl/rest/services/public/NFHL/MapServer/28/query",
            params={
                "geometry": f"{lng},{lat}",
                "geometryType": "esriGeometryPoint",
                "inSR": "4326",
                "spatialRel": "esriSpatialRelIntersects",
                "outFields": "FLD_ZONE",
                "returnGeometry": "false",
                "f": "json"
            }
        )
    features = res.json().get("features", [])
    if features:
        return features[0]["attributes"]["FLD_ZONE"]
    return "X"  # default = low risk

async def get_calfire_zone(lat: float, lng: float) -> str:
    # CalFire Fire Hazard Severity Zone lookup
    async with httpx.AsyncClient() as client:
        res = await client.get(
            "https://services1.arcgis.com/jUJYIo9tSA7EHvfZ/arcgis/rest/services/California_Fire_Hazard_Severity_Zones/FeatureServer/0/query",
            params={
                "geometry": f"{lng},{lat}",
                "geometryType": "esriGeometryPoint",
                "inSR": "4326",
                "spatialRel": "esriSpatialRelIntersects",
                "outFields": "HAZ_CLASS",
                "returnGeometry": "false",
                "f": "json"
            }
        )
    features = res.json().get("features", [])
    if features:
        return features[0]["attributes"].get("HAZ_CLASS", "Moderate")
    return "Low"  # default


# ══════════════════════════════════════════════════════════════
#  MAIN ENDPOINT — wires everything together
# ══════════════════════════════════════════════════════════════
@app.get("/")
def home():
    return {"message": "ClimateCheck API is running!"}

@app.get("/risk")
async def get_risk(address: str):
    # Nivedha's function
    lat, lng = await geocode(address)

    # Sristi's functions
    flood_zone = await get_flood_zone(lat, lng)
    calfire_zone = await get_calfire_zone(lat, lng)

    # Your scoring formula
    scores = calculate_risk(lat, lng, flood_zone, calfire_zone)

    # Cathryn's Gemini function
    ai = get_ai_analysis(address, flood_zone, calfire_zone, scores["flood"], scores["fire"])

    return {
        "address": address,
        "lat": lat,
        "lng": lng,
        "flood_zone": flood_zone,
        "calfire_zone": calfire_zone,
        **scores,
        **ai
    }