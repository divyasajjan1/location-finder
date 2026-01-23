import os
import json
from .models import Landmark

def populate_landmarks():
    # Clear existing landmarks to prevent duplicates on re-run
    Landmark.objects.all().delete()

    # Load landmark coordinates from the JSON file
    LANDMARK_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "models", "landmark_locations.json")
    with open(LANDMARK_FILE) as f:
        landmark_coords = json.load(f)

    for landmark_name, coords in landmark_coords.items():
        Landmark.objects.create(
            name=landmark_name,
            latitude=coords["lat"],
            longitude=coords["lon"]
        )
    print(f"Populated {Landmark.objects.count()} landmarks.")

if __name__ == '__main__':
    import django
    django.setup()
    populate_landmarks()

