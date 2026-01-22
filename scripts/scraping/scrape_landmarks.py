import json
import requests
from pathlib import Path

# ---------------- Paths ----------------
CLASS_NAMES_PATH = Path("../../models/class_names.json")
OUTPUT_PATH = Path("../../models/landmark_locations.json")

# ---------------- Headers (REQUIRED) ----------------
HEADERS = {
    "User-Agent": "location-finder/1.0 (https://github.com/yourname/location-finder)"
}

# ---------------- Load landmark classes ----------------
with open(CLASS_NAMES_PATH, "r") as f:
    landmarks = json.load(f)

# ---------------- Wikidata API ----------------
WIKIDATA_API = "https://www.wikidata.org/w/api.php"

ALIASES = {
    "pyramids_of_giza": [
        "Giza pyramid complex",
        "Great Pyramid of Giza"
    ]
}

def get_coordinates(entity_id):
    params = {
        "action": "wbgetentities",
        "ids": entity_id,
        "props": "claims",
        "format": "json"
    }

    resp = requests.get(
        WIKIDATA_API,
        params=params,
        headers=HEADERS,
        timeout=10
    )

    data = resp.json()
    claims = data["entities"][entity_id].get("claims", {})

    if "P625" not in claims:
        return None

    coord = claims["P625"][0]["mainsnak"]["datavalue"]["value"]
    return {
        "lat": coord["latitude"],
        "lon": coord["longitude"]
    }


def search_wikidata(landmark_name):
    query = landmark_name.replace("_", " ").lower()

    params = {
        "action": "wbsearchentities",
        "search": query,
        "language": "en",
        "type": "item",
        "format": "json",
        "limit": 10
    }

    resp = requests.get(
        WIKIDATA_API,
        params=params,
        headers=HEADERS,
        timeout=10
    )

    results = resp.json().get("search", [])
    if not results:
        return None

    query_words = set(query.split())

    # 1️⃣ Exact label match
    for r in results:
        if r.get("label", "").lower() == query:
            coords = get_coordinates(r["id"])
            if coords:
                return coords

    # 2️⃣ Word containment match (FIXES PYRAMIDS OF GIZA)
    for r in results:
        label_words = set(r.get("label", "").lower().split())
        if query_words.issubset(label_words):
            coords = get_coordinates(r["id"])
            if coords:
                return coords

    # 3️⃣ Substring fallback
    for r in results:
        if query in r.get("label", "").lower():
            coords = get_coordinates(r["id"])
            if coords:
                return coords

    return None


# ---------------- Main ----------------
landmark_locations = {}

for landmark in landmarks:
    print(f"\n🔍 Searching Wikidata for {landmark}...")
    coords = search_wikidata(landmark)

    if not coords and landmark in ALIASES:
        for alias in ALIASES[landmark]:
            print(f"🔁 Retrying with alias: {alias}")
            coords = search_wikidata(alias.replace(" ", "_"))
            if coords:
                break
    if coords:
        landmark_locations[landmark] = coords
        print("✅ Coordinates saved")
    else:
        print("⚠️ No coordinates found")

# ---------------- Save ----------------
with open(OUTPUT_PATH, "w") as f:
    json.dump(landmark_locations, f, indent=4)

print(f"\n🎉 {OUTPUT_PATH} generated with {len(landmark_locations)} landmarks")
