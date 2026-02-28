import os, json
from google import genai
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_KEY"))

def get_ai_analysis(address: str, flood_zone: str, wildfire_hazard: str, flood_score: int, fire_score: int, landslide_score: int) -> dict:
    prompt = f"""
You are a climate risk analyst. A property has been assessed with the following data:
- Address: {address}
- FEMA Flood Zone: {flood_zone}
- Wildfire Hazard: {wildfire_hazard}
- Flood Risk Score: {flood_score}/100
- Wildfire Risk Score: {fire_score}/100
- Landslide Risk Score: {landslide_score}/100

Return ONLY a valid JSON object with exactly these fields:
{{
  "explanation": "3-4 sentence plain English summary of the property risk for a homebuyer",
  "recommendations": ["recommendation 1", "recommendation 2", "recommendation 3"],
  "wildfire_probability": {{"1_year": int, "5_year": int, "10_year": int, "30_year": int}},
  "flood_probability": {{"1_year": int, "5_year": int, "10_year": int, "30_year": int}},
  "landslide_probability": {{"1_year": int, "5_year": int, "10_year": int, "30_year": int}}
}}

Probabilities should be realistic percentages (0-100) reflecting risk growth over time.
Return absolutely nothing except the JSON object. No markdown, no backticks, no explanation.
"""

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash-lite",
            contents=prompt
        )
        raw = (response.text or "").strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        return json.loads(raw)
    except Exception as e:
        print(f"AI error: {e}")
        return {
            "explanation": "AI analysis unavailable at this time.",
            "recommendations": [
                "Consult a local risk assessor for detailed analysis.",
                "Review FEMA flood maps at msc.fema.gov",
                "Check wildfire hazard zones at apps.fs.usda.gov"
            ],
            "wildfire_probability":  {"1_year": 0, "5_year": 0, "10_year": 0, "30_year": 0},
            "flood_probability":     {"1_year": 0, "5_year": 0, "10_year": 0, "30_year": 0},
            "landslide_probability": {"1_year": 0, "5_year": 0, "10_year": 0, "30_year": 0}
        }


# ── Test standalone ────────────────────────────────────────────────────
if __name__ == "__main__":
    load_dotenv()
    print("KEY:", os.getenv("GEMINI_KEY"))
    result = get_ai_analysis("123 Main St, Irvine CA", "AE", "Very High", 82, 74, 45)
    print(json.dumps(result, indent=2))