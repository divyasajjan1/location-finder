# backend/api/utils/distance_to_landmark.py

import os
import json
from .user_location import get_user_location
from .distance import haversine, calculate_travel_cost 

def distance_to_landmark(landmark_instance, origin_city=None):
    """
    Returns a dictionary with distance and estimated cost using a Landmark DB instance.
    """
    # 1. Get user coordinates
    user_lat, user_lon = get_user_location(city_name=origin_city)

    if user_lat is None or user_lon is None:
        raise ValueError(f"Could not determine location for: {origin_city}")

    # 2. Get landmark coordinates
    landmark_lat = landmark_instance.latitude
    landmark_lon = landmark_instance.longitude

    # 3. Calculate distance
    distance_km = haversine(user_lat, user_lon, landmark_lat, landmark_lon)
    
    # 4. Calculate cost using the logic in distance.py
    cost = calculate_travel_cost(distance_km)

    # 5. Return the dictionary
    # This matches the metrics["distance_km"] and metrics["estimated_cost"] logic in views.py
    return {
        "distance_km": round(distance_km, 2),
        "estimated_cost": cost
    }