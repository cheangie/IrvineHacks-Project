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

# ── Geocode address → lat/lng ──────────────────────────────────────────
async def geocode(address: str):
    async with httpx.AsyncClient() as client:
        res = await client.get(
            "https://personator.melissadata.net/v3/WEB/ContactVerify/doContactVerify",
            params={"id": MELISSA_KEY, "act": "GeoCode", "full": address, "format": "json"}
        )
    record = res.json()["Records"][0]
    return float(record["Latitude"]), float(record["Longitude"])

# ── Get FEMA flood zone ────────────────────────────────────────────────
async def get_flood_zone(lat: float, lng: float):
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

# ── Main endpoint ──────────────────────────────────────────────────────
@app.get("/")
def home():
    return {"message": "ClimateCheck API is running!"}

@app.get("/risk")
async def get_risk(address: str):
    # 1. Geocode
    lat, lng = await geocode(address)

    # 2. FEMA flood zone
    flood_zone = await get_flood_zone(lat, lng)

    # 3. Risk scores (Nivedha's file)
    scores = calculate_risk(lat, lng, flood_zone)

    # 4. AI analysis (Cathryn's file)
    ai = get_ai_analysis(address, flood_zone, scores["flood"], scores["fire"])

    return {
        "address": address,
        "lat": lat,
        "lng": lng,
        "flood_zone": flood_zone,
        **scores,
        **ai
    }