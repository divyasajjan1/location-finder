import requests
import re

def get_user_location(city_name=None):
    """
    Returns (latitude, longitude) by either:
    1. Parsing coordinate strings ("Lat: X, Lon: Y")
    2. Geocoding city names using Nominatim
    """
    if not city_name:
        return None, None

    # 1. Handle "Current Location" coordinates (from your button)
    if "Lat:" in city_name:
        try:
            # Extracts numbers from the "Lat: 42.25, Lon: -82.98" string
            numbers = re.findall(r"[-+]?\d*\.\d+|\d+", city_name)
            if len(numbers) >= 2:
                return float(numbers[0]), float(numbers[1])
        except Exception as e:
            print(f"Coordinate parsing error: {e}")

    # 2. Handle City Name Geocoding (typed by user)
    try:
        url = f"https://nominatim.openstreetmap.org/search?q={city_name}&format=json&limit=1"
        headers = {'User-Agent': 'LocationFinderApp/1.0'}
        response = requests.get(url, headers=headers).json()
        
        if response:
            return float(response[0]['lat']), float(response[0]['lon'])
    except Exception as e:
        print(f"Geocoding error: {e}")

    return None, None