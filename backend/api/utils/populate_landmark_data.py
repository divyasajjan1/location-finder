"""
⚠️ USE ONLY IF NEEDED
🛠️ LANDMARK DATA REPAIR & SEEDING UTILITY

PURPOSE:
This script ensures every landmark in your database has valid geographic coordinates. 
It targets records with 0.0 latitude/longitude and fetches real-world data using Geopy.

WHEN TO RUN THIS:
1. Fresh Setup: After you've manually added folders to 'data/raw/' but haven't 
   scraped them yet, run this to "prime" the database with locations.
2. Missing Data: If the frontend 'Distance Card' or 'Map' shows 0.0 or fails 
   to calculate distances for specific landmarks.

⚠️ CAUTION:
- You do NOT need to run this if you are using the 'Scrape & Train' feature in 
  the UI, as that process fetches coordinates automatically.
- Move this to the backend root folder and run it from there.  
- This script is rate-limited (1 request per second) to respect free API usage.
- It will NOT overwrite your existing summaries or delete any data.
"""

import os
import django
from geopy.geocoders import Nominatim
import time

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings') 
django.setup()

from api.models import Landmark

def populate_landmark_data():
    geolocator = Nominatim(user_agent="landmark_app")
    landmarks = Landmark.objects.filter(latitude=0.0) # Only fix the empty ones

    for landmark in landmarks:
        # Clean name for searching (e.g., "eiffel_tower" -> "Eiffel Tower")
        search_name = landmark.name.replace("_", " ").title()
        print(f"Searching coordinates for: {search_name}...")
        
        try:
            location = geolocator.geocode(search_name)
            if location:
                landmark.latitude = location.latitude
                landmark.longitude = location.longitude
                landmark.save()
                print(f"✅ Updated {search_name}: {location.latitude}, {location.longitude}")
            else:
                print(f"⚠️ Could not find coordinates for {search_name}")
            
            # Sleep to respect Nominatim's free usage policy
            time.sleep(1) 
        except Exception as e:
            print(f"❌ Error for {search_name}: {e}")

if __name__ == "__main__":
    populate_landmark_data()