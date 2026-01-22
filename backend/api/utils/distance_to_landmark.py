# backend/api/utils/distance_to_landmark.py

import os
import json
from .user_location import get_user_location
from .distance import haversine  # use relative import

# Load landmark coordinates once
LANDMARK_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "..", "models", "landmark_locations.json")
with open(LANDMARK_FILE) as f:
    landmark_coords = json.load(f)

def distance_to_landmark(predicted_landmark: str):
    """
    Returns the distance in km between the user and the predicted landmark.
    """
    # 1. Get user coordinates
    user_lat, user_lon = get_user_location()

    # 2. Get landmark coordinates
    if predicted_landmark not in landmark_coords:
        raise ValueError(f"No coordinates found for {predicted_landmark}")

    landmark_lat = landmark_coords[predicted_landmark]["lat"]
    landmark_lon = landmark_coords[predicted_landmark]["lon"]

    # 3. Calculate distance
    distance_km = haversine(user_lat, user_lon, landmark_lat, landmark_lon)
    return distance_km
