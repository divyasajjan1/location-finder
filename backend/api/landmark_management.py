import requests
import json
import os
from .models import Landmark
from typing import Union # New import for Python 3.9 type hinting

# ---------------- Headers (REQUIRED) ----------------
HEADERS = {
    "User-Agent": "location-finder/1.0 (https://github.com/yourname/location-finder)"
}

# ---------------- Wikidata API ----------------
WIKIDATA_API = "https://www.wikidata.org/w/api.php"

ALIASES = {
    "pyramids_of_giza": [
        "Giza pyramid complex",
        "Great Pyramid of Giza"
    ]
}

def _get_coordinates(entity_id):
    params = {
        "action": "wbgetentities",
        "ids": entity_id,
        "props": "claims",
        "format": "json"
    }

    try:
        resp = requests.get(
            WIKIDATA_API,
            params=params,
            headers=HEADERS,
            timeout=10
        )
        resp.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
        data = resp.json()
        claims = data["entities"][entity_id].get("claims", {})

        if "P625" not in claims:
            return None

        coord = claims["P625"][0]["mainsnak"]["datavalue"]["value"]
        return {
            "lat": coord["latitude"],
            "lon": coord["longitude"]
        }
    except requests.exceptions.RequestException as e:
        print(f"Error fetching coordinates from Wikidata for {entity_id}: {e}")
        return None

def _search_wikidata(landmark_name):
    query = landmark_name.replace("_", " ").lower()

    params = {
        "action": "wbsearchentities",
        "search": query,
        "language": "en",
        "type": "item",
        "format": "json",
        "limit": 10
    }

    try:
        resp = requests.get(
            WIKIDATA_API,
            params=params,
            headers=HEADERS,
            timeout=10
        )
        resp.raise_for_status()
        results = resp.json().get("search", [])
        if not results:
            return None

        query_words = set(query.split())

        # 1️⃣ Exact label match
        for r in results:
            if r.get("label", "").lower() == query:
                coords = _get_coordinates(r["id"])
                if coords:
                    return coords

        # 2️⃣ Word containment match
        for r in results:
            label_words = set(r.get("label", "").lower().split())
            if query_words.issubset(label_words):
                coords = _get_coordinates(r["id"])
                if coords:
                    return coords

        # 3️⃣ Substring fallback
        for r in results:
            if query in r.get("label", "").lower():
                coords = _get_coordinates(r["id"])
                if coords:
                    return coords

    except requests.exceptions.RequestException as e:
        print(f"Error searching Wikidata for {landmark_name}: {e}")
    
    return None

def get_or_create_landmark(standardized_landmark_name: str) -> Union[Landmark, None]:
    """
    Gets a Landmark object by its standardized name. If it doesn't exist,
    it attempts to find its coordinates using Wikidata and create a new entry.
    Returns the Landmark object or None if it cannot be found/created.
    """
    try:
        return Landmark.objects.get(name=standardized_landmark_name)
    except Landmark.DoesNotExist:
        print(f"Landmark '{standardized_landmark_name}' not found in DB. Attempting to fetch from Wikidata...")

        coords = _search_wikidata(standardized_landmark_name)

        if not coords and standardized_landmark_name in ALIASES:
            for alias in ALIASES[standardized_landmark_name]:
                print(f"Retrying with alias: {alias}")
                coords = _search_wikidata(alias.replace(" ", "_")) # standardize alias for search
                if coords:
                    break

        if coords:
            new_landmark = Landmark.objects.create(
                name=standardized_landmark_name,
                latitude=coords["lat"],
                longitude=coords["lon"]
            )
            print(f"Successfully created new landmark: {new_landmark.name}")
            return new_landmark
        else:
            print(f"Could not find coordinates for '{standardized_landmark_name}' on Wikidata.")
            return None
    except Exception as e:
        print(f"An unexpected error occurred in get_or_create_landmark: {e}")
        return None
