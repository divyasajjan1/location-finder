import os
import requests
from ddgs import DDGS
from PIL import Image
from io import BytesIO

# ---------------- Config ----------------
# Only the first 5 weaker classes
LANDMARK_QUERIES = {
    "eiffel_tower": [
        "Eiffel Tower Paris",
        "Eiffel Tower night",
        "Eiffel Tower aerial view",
        "Eiffel Tower close up"
    ],
    "statue_of_liberty": [
        "Statue of Liberty New York",
        "Statue of Liberty USA",
        "Statue of Liberty monument",
        "Statue of Liberty tourist"
    ],
    "taj_mahal": [
        "Taj Mahal Agra",
        "Taj Mahal sunrise",
        "Taj Mahal side view",
        "Taj Mahal close up"
    ],
    "colosseum": [
        "Colosseum Rome",
        "Colosseum Italy",
        "Colosseum ancient",
        "Colosseum view"
    ],
    "big_ben": [
        "Big Ben London",
        "Big Ben UK",
        "Big Ben clock tower",
        "Big Ben view"
    ]
}

TARGET_IMAGES = 200          # Desired final count per class
SAVE_ROOT = "data/raw"
os.makedirs(SAVE_ROOT, exist_ok=True)

# ---------------- Scraping ----------------
with DDGS() as ddgs:
    for landmark, queries in LANDMARK_QUERIES.items():
        folder = os.path.join(SAVE_ROOT, landmark)
        os.makedirs(folder, exist_ok=True)

        existing_files = set(os.listdir(folder))
        count = len(existing_files)
        print(f"\n--- Scraping {landmark} (currently {count} images) ---")

        if count >= TARGET_IMAGES:
            print(f"{landmark} already has {count} images, skipping.")
            continue

        image_idx = count
        for q in queries:
            if count >= TARGET_IMAGES:
                break

            results = ddgs.images(query=q, max_results=60, safesearch="off")

            for r in results:
                if count >= TARGET_IMAGES:
                    break
                try:
                    img_url = r.get("image")
                    if not img_url:
                        continue

                    response = requests.get(img_url, timeout=8)
                    if response.status_code != 200:
                        continue

                    img = Image.open(BytesIO(response.content))
                    if img.width < 100 or img.height < 100:
                        continue  # Skip tiny images

                    # Save with neutral incremental filename
                    filename = os.path.join(folder, f"{image_idx}.jpg")
                    if not os.path.exists(filename):
                        img.save(filename)
                        count += 1
                        image_idx += 1

                    if count % 50 == 0:
                        print(f"{count} images downloaded for {landmark}...")

                except Exception:
                    continue

        print(f"Done with {landmark}: {count} images collected.")
