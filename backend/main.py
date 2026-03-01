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

HIGH_FLOOD_COUNTIES = {
    "Orleans", "Jefferson", "St. Bernard", "Plaquemines", "Terrebonne",
    "Lafourche", "St. Mary", "Iberia", "Cameron",
    "Miami-Dade", "Broward", "Palm Beach", "Monroe", "Collier", "Lee",
    "Charlotte", "Sarasota", "Pinellas", "Hillsborough",
    "Harris", "Galveston", "Brazoria", "Matagorda", "Jackson", "Victoria",
    "Sacramento", "San Joaquin", "Fresno", "Tulare", "Kings",
    "New Hanover", "Brunswick", "Dare", "Carteret", "Onslow",
    "Atlantic", "Cape May", "Ocean", "Monmouth",
}

MODERATE_FLOOD_COUNTIES = {
    "Ventura", "Los Angeles", "Orange", "San Diego", "Santa Barbara",
    "King", "Pierce", "Multnomah", "Clackamas",
    "Cook", "DuPage", "Will", "Lake",
    "Wayne", "Macomb", "Oakland",
    "Middlesex", "Essex", "Suffolk",
}

HIGH_WILDFIRE_COUNTIES = {
    "Ventura", "Santa Barbara", "San Luis Obispo", "Marin",
    "Kern", "Tuolumne", "Calaveras", "Amador", "Butte", "Plumas", "Tehama",
    "El Dorado", "Placer", "Nevada", "Shasta", "Trinity", "Humboldt",
    "Mendocino", "Lake", "Napa", "Sonoma",
    "Deschutes", "Klamath", "Douglas", "Josephine", "Jackson",
    "Okanogan", "Chelan", "Yakima", "Ferry",
    "Boulder", "Jefferson", "Clear Creek", "Gilpin", "Park", "Teller",
    "El Paso", "Larimer", "Grand", "Summit", "Eagle", "Pitkin",
    "Flathead", "Missoula", "Ravalli", "Fremont",
    "Coconino", "Yavapai", "Gila", "Catron", "Grant", "Hidalgo",
    "Travis", "Bastrop", "Caldwell", "Hays",
}

MODERATE_WILDFIRE_COUNTIES = {
    "Los Angeles", "Orange", "San Diego", "Riverside", "San Bernardino",
    "Santa Cruz", "Monterey", "San Mateo", "Contra Costa", "Alameda", "Santa Clara",
    "King", "Pierce", "Snohomish", "Spokane",
    "Arapahoe", "Douglas", "Weld",
    "Harris", "Fort Bend", "Montgomery", "Galveston", "Brazoria",
}

HIGH_LANDSLIDE_COUNTIES = {
    "Ventura", "Santa Barbara", "San Luis Obispo", "Marin", "Santa Cruz",
    "Monterey", "San Mateo", "Humboldt", "Del Norte", "Trinity", "Mendocino",
    "Los Angeles", "Orange", "San Bernardino", "Riverside", "San Diego",
    "King", "Pierce", "Snohomish", "Whatcom", "Skagit", "Clallam", "Jefferson",
    "Multnomah", "Clackamas", "Washington", "Hood River",
    "Summit", "Eagle", "Pitkin", "Gunnison", "San Juan", "Ouray", "La Plata",
    "Buncombe", "Henderson", "Haywood", "Jackson", "Macon", "Swain",
    "Allegheny", "Fayette", "Westmoreland",
    "Anchorage", "Juneau", "Ketchikan",
}

MODERATE_LANDSLIDE_COUNTIES = {
    "El Dorado", "Placer", "Nevada", "Amador", "Tuolumne", "Mariposa",
    "Shasta", "Tehama", "Glenn", "Lake",
    "Spokane", "Kittitas", "Yakima", "Chelan",
    "Jefferson", "Clear Creek", "Gilpin", "Boulder", "Larimer",
    "Sevier", "Blount", "Monroe", "Polk", "Bradley",
    "Kanawha", "Logan", "Mingo", "Wayne",
}


# 1. FEMA Flood Zone — with county-based fallback
async def get_flood_zone(lat: float, lng: float, elevation: float = 100.0, county: str = "") -> str:
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

    print(f"Using county-based flood zone fallback for: {county}")
    if county in HIGH_FLOOD_COUNTIES:
        if elevation < 0:  return "VE"
        if elevation < 30: return "AE"
        return "A"
    if county in MODERATE_FLOOD_COUNTIES:
        if elevation < 5:  return "AE"
        if elevation < 30: return "B"
        return "X"
    if elevation < 0:   return "VE"
    if elevation < 5:   return "AE"
    if elevation < 15:  return "A"
    if elevation < 50:  return "B"
    return "X"


# 2. USFS Wildfire Hazard — with county-based fallback
async def get_wildfire_hazard(lat: float, lng: float, county: str = "") -> str:
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
        print(f"Wildfire API error: {e}")

    print(f"Using county-based wildfire fallback for: {county}")
    if county in HIGH_WILDFIRE_COUNTIES:   return "Very High"
    if county in MODERATE_WILDFIRE_COUNTIES: return "High"
    return "Low"


# 3. Elevation — Open Topo Data with USGS backup
async def get_elevation(lat: float, lng: float) -> float:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.get(
                "https://api.opentopodata.org/v1/srtm90m",
                params={"locations": f"{lat},{lng}"}
            )
        val = res.json()["results"][0]["elevation"]
        if val is not None:
            print(f"OpenTopo elevation: {val}m")
            return float(val)
    except Exception as e:
        print(f"OpenTopo error: {e}")

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.get(
                "https://epqs.nationalmap.gov/v1/json",
                params={"x": lng, "y": lat, "units": "Meters", "wkid": "4326", "includeDate": "false"}
            )
        val = float(res.json().get("value", 0))
        if val > 0:
            return val
    except Exception as e:
        print(f"USGS elevation error: {e}")

    return 100.0


# 4. Landslide — county-based lookup + elevation fallback
async def get_landslide_history(lat: float, lng: float, elevation: float = 100.0, county: str = "") -> int:
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
        count = int(res.json().get("count", 0))
        print(f"USGS landslide count: {count}")
        return count
    except Exception as e:
        print(f"Landslide API error: {e}")

    print(f"Using county-based landslide fallback for: {county}")
    if county in HIGH_LANDSLIDE_COUNTIES:
        if elevation > 300: return 12
        if elevation > 100: return 8
        return 5
    if county in MODERATE_LANDSLIDE_COUNTIES:
        if elevation > 500: return 6
        if elevation > 200: return 3
        return 1
    if elevation > 1000: return 4
    if elevation > 500:  return 2
    return 0


# 5. NIFC Fire Perimeter Distance
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


# 6. NOAA Active Weather Alerts
async def get_noaa_alerts(lat: float, lng: float) -> list:
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

@app.get("/debug")
async def debug(lat: float, lng: float):
    elev = await get_elevation(lat, lng)
    return {"elevation": elev}

@app.get("/risk")
async def get_risk(address: str):
    location = await geocode(address)
    lat, lng = location["lat"], location["lng"]

    elevation = await get_elevation(lat, lng)

    flood_zone, wildfire_hazard, landslide_count, fire_distance_km, noaa_alerts = await asyncio.gather(
        get_flood_zone(lat, lng, elevation, location["county"]),
        get_wildfire_hazard(lat, lng, location["county"]),
        get_landslide_history(lat, lng, elevation, location["county"]),
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