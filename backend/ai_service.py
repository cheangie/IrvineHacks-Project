import google.generativeai as genai
import json, os
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")  # free tier model

def get_ai_analysis(address: str, fema_zone: str, flood_score: int, fire_score: int) -> dict:
    prompt = f"""
You are a climate risk analyst. A property has been assessed with the following data:
- Address: {address}
- FEMA Flood Zone: {fema_zone}
- Flood Risk Score: {flood_score}/100
- Wildfire Risk Score: {fire_score}/100

Return ONLY a valid JSON object with exactly these fields:
{{
  "explanation": "3-4 sentence plain English summary of the property risk for a homebuyer",
  "recommendations": ["recommendation 1", "recommendation 2", "recommendation 3"],
  "wildfire_probability": {{"1_year": int, "5_year": int, "10_year": int, "30_year": int}},
  "flood_probability": {{"1_year": int, "5_year": int, "10_year": int, "30_year": int}}
}}

Probabilities should be realistic percentages (0-100) reflecting risk growth over time.
Return absolutely nothing except the JSON object. No markdown, no backticks.
"""

    try:
        response = model.generate_content(prompt)
        raw = response.text.strip()
        # Strip markdown code fences if Gemini adds them anyway
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        return json.loads(raw)
    except Exception as e:
        print(f"Gemini error: {e}")
        # Fallback so the app doesn't crash
        return {
            "explanation": "AI analysis unavailable at this time.",
            "recommendations": [
                "Consult a local risk assessor for detailed analysis.",
                "Review FEMA flood maps at msc.fema.gov",
                "Check CalFire hazard zones at osfm.fire.ca.gov"
            ],
            "wildfire_probability": {"1_year": 0, "5_year": 0, "10_year": 0, "30_year": 0},
            "flood_probability": {"1_year": 0, "5_year": 0, "10_year": 0, "30_year": 0}
        }


# ── Test it standalone ─────────────────────────────────────────────────
if __name__ == "__main__":
    result = get_ai_analysis("123 Main St, Irvine CA", "AE", 82, 74)
    print(json.dumps(result, indent=2))