import os
from PIL import Image
import imagehash

data_root = "data/raw"

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
