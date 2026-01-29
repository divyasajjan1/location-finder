# backend/api/utils/distance_to_landmark.py

import os
import json
from .user_location import get_user_location
# 1. Import BOTH functions from distance.py
from .distance import haversine, calculate_travel_cost 

# Load landmark coordinates once
LANDMARK_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "..", "models", "landmark_locations.json")
with open(LANDMARK_FILE) as f:
    landmark_coords = json.load(f)

def distance_to_landmark(predicted_landmark: str, origin_city=None):
    """
    Returns a dictionary with distance and estimated cost.
    """
    # 2. Get user coordinates (Using origin_city for manual input or IP for default)
    user_lat, user_lon = get_user_location(city_name=origin_city)

    if user_lat is None or user_lon is None:
        raise ValueError(f"Could not determine location for: {origin_city}")

    # 3. Get landmark coordinates
    if predicted_landmark not in landmark_coords:
        raise ValueError(f"No coordinates found for {predicted_landmark}")

    landmark_lat = landmark_coords[predicted_landmark]["lat"]
    landmark_lon = landmark_coords[predicted_landmark]["lon"]

    # 4. Calculate distance
    distance_km = haversine(user_lat, user_lon, landmark_lat, landmark_lon)
    
    # 5. Calculate cost using the logic in distance.py
    cost = calculate_travel_cost(distance_km)

    # 6. RETURN A DICTIONARY
    # This matches the metrics["distance_km"] and metrics["estimated_cost"] logic in views.py
    return {
        "distance_km": round(distance_km, 2),
        "estimated_cost": cost
    }