"""
⚠️ USE ONLY IF NEEDED
🛠️ DUPLICATE IMAGE REMOVAL UTILITY
PURPOSE:
This script scans through your 'data/raw/' folders for each landmark and removes duplicate images.
WHEN TO RUN THIS:
1. After you've run the scraper or manually added images  to 'data/raw/' but before you run training process.
2. If you notice that your dataset has many identical images, which can skew training results.
⚠️ CAUTION:
- This will permanently delete files, so make a backup if you're unsure.
- It uses perceptual hashing (via the 'imagehash' library) to identify duplicates, which is more robust than simple file hashing for images.
- Run this from the backend root folder to ensure it correctly accesses the 'data/raw/' directory.
"""
import os
from PIL import Image
import imagehash

data_root = "../../../data/raw"

for landmark in os.listdir(data_root):
    folder = os.path.join(data_root, landmark)
    if not os.path.isdir(folder):
        continue

    print(f"\nChecking duplicates for {landmark}...")
    hashes = {}
    duplicates = 0

    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        try:
            img = Image.open(file_path)
            img_hash = imagehash.average_hash(img)

            if img_hash in hashes:
                os.remove(file_path)
                duplicates += 1
            else:
                hashes[img_hash] = filename
        except Exception:
            continue

    print(f"Removed {duplicates} duplicates in {landmark}")