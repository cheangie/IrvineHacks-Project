from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import httpx, anthropic

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

MELISSA_KEY = "your_key"
ANTHROPIC_KEY = "your_key"

@app.get("/risk")
async def get_risk(address: str):
    # 1. Melissa geocode
    melissa = await fetch_melissa(address)
    lat, lng = melissa["lat"], melissa["lng"]

    # 2. Get risk factors
    flood_score = await fetch_flood_risk(lat, lng)      # FEMA
    fire_score = await fetch_fire_risk(lat, lng)        # CalFire

    # 3. Score
    overall = round(flood_score * 0.4 + fire_score * 0.6)

    # 4. Claude explanation
    explanation = await get_claude_explanation(address, flood_score, fire_score, overall)

    return {
        "address": address,
        "overall": overall,
        "flood": flood_score,
        "fire": fire_score,
        "explanation": explanation,
        "lat": lat,
        "lng": lng
    }