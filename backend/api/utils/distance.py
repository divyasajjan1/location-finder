from math import radians, cos, sin, asin, sqrt

def haversine(lat1, lon1, lat2, lon2):
    """
    Returns distance in kilometers between two lat/lon points
    """
    R = 6371  # Earth radius in km

    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))

    return R * c

def calculate_travel_cost(distance_km):
    """Returns estimated travel cost based on $0.12 per km"""
    if distance_km < 100:
        return 50  # Minimum flat rate for very close travel
    
    # $0.15 per km is the base
    cost_per_km = 0.15
    estimated_cost = distance_km * cost_per_km
    
    # Add a small fixed "booking & tax" fee of $45
    total = estimated_cost + 45
    
    return round(total)