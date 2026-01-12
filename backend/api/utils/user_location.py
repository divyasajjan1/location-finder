import geocoder

def get_user_location():
    """
    Returns (latitude, longitude) using user's IP.
    Returns (None, None) if location cannot be determined.
    """
    try:
        g = geocoder.ip("me")

        if g.ok and g.latlng:
            lat, lon = g.latlng
            return lat, lon

    except Exception:
        pass

    return None, None
