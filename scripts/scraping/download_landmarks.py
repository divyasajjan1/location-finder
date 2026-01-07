import os
import requests
from ddgs import DDGS
from PIL import Image
from io import BytesIO

# ---------------- Config ----------------
landmarks = {
    "eiffel_tower": [
        "Eiffel Tower Paris",
        "Eiffel Tower monument",
        "Eiffel Tower tourist",
        "Eiffel Tower view",
        "Eiffel Tower night"
    ],
    "statue_of_liberty": [
        "Statue of Liberty New York",
        "Statue of Liberty USA",
        "Statue of Liberty monument",
        "Statue of Liberty tourist",
        "Statue of Liberty view"
    ],
    "taj_mahal": [
        "Taj Mahal India",
        "Taj Mahal monument",
        "Taj Mahal Agra",
        "Taj Mahal view",
        "Taj Mahal tourist"
    ],
    "colosseum": [
        "Colosseum Rome",
        "Colosseum Italy",
        "Colosseum ancient",
        "Colosseum view",
        "Colosseum tourist"
    ],
    "big_ben": [
        "Big Ben London",
        "Big Ben UK",
        "Big Ben clock tower",
        "Big Ben view",
        "Big Ben tourist"
    ],
    "pyramids_of_giza": [
        "Pyramids of Giza Egypt",
        "Giza pyramids",
        "Great Pyramid",
        "Pyramids desert",
        "Pyramids tourist"
    ],
    "sydney_opera_house": [
        "Sydney Opera House Australia",
        "Opera House Sydney",
        "Sydney Opera House view",
        "Sydney Opera House tourist",
        "Sydney Opera House landmark"
    ],
    "burj_khalifa": [
        "Burj Khalifa Dubai",
        "Burj Khalifa UAE",
        "Burj Khalifa tallest",
        "Burj Khalifa view",
        "Burj Khalifa tourist"
    ]
}

images_per_class = 250          # target images per landmark
save_root = "data/raw"
os.makedirs(save_root, exist_ok=True)

# ---------------- Download Images ----------------
with DDGS() as ddgs:
    for landmark_name, keywords in landmarks.items():
        print(f"\n--- Scraping for: {landmark_name} ---")
        folder = os.path.join(save_root, landmark_name)
        os.makedirs(folder, exist_ok=True)

        existing_files = set(os.listdir(folder))
        count = len(existing_files)
        image_idx = count

        for kw in keywords:
            if count >= images_per_class:
                break

            results = ddgs.images(query=kw, max_results=images_per_class, safesearch="off")

            for r in results:
                if count >= images_per_class:
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
                        continue  # skip tiny images

                    # Save with neutral incremental filename
                    filename = os.path.join(folder, f"{image_idx}.jpg")
                    if not os.path.exists(filename):
                        img.save(filename)
                        count += 1
                        image_idx += 1

                    if count % 50 == 0:
                        print(f"{count} images downloaded for {landmark_name}...")

                except Exception:
                    continue

        print(f"Done with {landmark_name}: {count} images collected.")
