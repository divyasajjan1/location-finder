import os
import requests
import re
import urllib.parse
from ddgs import DDGS
from PIL import Image
from io import BytesIO
from bs4 import BeautifulSoup

# --- 1. CONFIGURATION & CONSTANTS ---

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

IMAGES_PER_CLASS_TARGET = 250

# Path logic: ensures data is saved in the correct data/raw folder
SAVE_ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "raw")
os.makedirs(SAVE_ROOT, exist_ok=True)

URL_REGEX = re.compile(
    r'^(?:http|ftp)s?://' 
    r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' 
    r'localhost|' 
    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' 
    r'(?::\d+)?' 
    r'(?:/?|[/?]\S+)$', re.IGNORECASE)

DEFAULT_KEYWORDS = {
    "eiffel_tower": ["Eiffel Tower Paris", "Eiffel Tower view"],
    "statue_of_liberty": ["Statue of Liberty New York", "Statue of Liberty USA"],
    "taj_mahal": ["Taj Mahal India", "Taj Mahal Agra"],
    "colosseum": ["Colosseum Rome", "Colosseum Italy"],
    "big_ben": ["Big Ben London", "Big Ben clock tower"],
    "pyramids_of_giza": ["Pyramids of Giza Egypt", "Giza pyramids"],
    "sydney_opera_house": ["Sydney Opera House Australia", "Opera House Sydney"],
    "burj_khalifa": ["Burj Khalifa Dubai", "Burj Khalifa UAE"]
}

# --- 2. UTILITY FUNCTIONS ---

def _is_valid_url(url):
    return re.match(URL_REGEX, url) is not None

# --- 3. MAIN SCRAPING FUNCTIONS ---

def scrape_images_from_url_and_save(target_url: str, landmark_name: str, images_to_scrape: int) -> list:
    """
    Scrapes images from a single URL. Returns list of saved filenames.
    """
    print(f"\n--- Scraping images from URL: {target_url} for {landmark_name} ---")
    folder = os.path.join(SAVE_ROOT, landmark_name)
    os.makedirs(folder, exist_ok=True)

    initial_count = len(os.listdir(folder))
    count = initial_count
    image_idx = initial_count
    saved_filenames = []

    try:
        response = requests.get(target_url, timeout=15, headers=HEADERS)
        response.raise_for_status() 
        soup = BeautifulSoup(response.text, 'html.parser')
        
        img_tags = soup.find_all('img')
        for img_tag in img_tags:
            if count - initial_count >= images_to_scrape:
                break

            img_url = img_tag.get('src')
            if not img_url: continue
            
            if not img_url.startswith(('http://', 'https://')):
                img_url = urllib.parse.urljoin(target_url, img_url)

            try:
                img_response = requests.get(img_url, timeout=15, headers=HEADERS)
                img_response.raise_for_status()
                
                img = Image.open(BytesIO(img_response.content))
                if img.mode == 'RGBA': img = img.convert('RGB')
                if img.width < 100 or img.height < 100: continue
                
                base_name = f"{image_idx}.jpg"
                filename = os.path.join(folder, base_name)
                while os.path.exists(filename):
                    image_idx += 1
                    base_name = f"{image_idx}.jpg"
                    filename = os.path.join(folder, base_name)

                img.save(filename)
                saved_filenames.append(base_name)
                count += 1
                image_idx += 1
            except Exception as e:
                print(f"Skipping image: {e}")
                continue
    except Exception as e:
        print(f"Error scraping URL {target_url}: {e}")
        return []

    return saved_filenames


def scrape_images_for_landmark(landmark_name: str, source_input: str = None, images_to_scrape: int = IMAGES_PER_CLASS_TARGET) -> list:
    """
    Scrapes images using URL or Search Engine. Returns list of saved filenames.
    """
    if source_input and _is_valid_url(source_input):
        return scrape_images_from_url_and_save(source_input, landmark_name, images_to_scrape)
    else:
        folder = os.path.join(SAVE_ROOT, landmark_name)
        os.makedirs(folder, exist_ok=True)

        initial_count = len(os.listdir(folder))
        count = initial_count
        image_idx = initial_count
        saved_filenames = []

        search_keywords = DEFAULT_KEYWORDS.get(landmark_name, [landmark_name.replace("_", " ")])
        if source_input: search_keywords.insert(0, source_input)
        
        unique_keywords = list(set(search_keywords))

        with DDGS() as ddgs:
            for kw in unique_keywords:
                if count - initial_count >= images_to_scrape: break
                
                remaining = images_to_scrape - (count - initial_count)
                results = ddgs.images(query=kw, max_results=remaining, safesearch="off")

                for r in results:
                    if count - initial_count >= images_to_scrape: break
                    try:
                        img_url = r.get("image")
                        if not img_url: continue

                        response = requests.get(img_url, timeout=15)
                        img = Image.open(BytesIO(response.content))
                        if img.mode == 'RGBA': img = img.convert('RGB')
                        if img.width < 100 or img.height < 100: continue
                        
                        base_name = f"{image_idx}.jpg"
                        filename = os.path.join(folder, base_name)
                        while os.path.exists(filename):
                            image_idx += 1
                            base_name = f"{image_idx}.jpg"
                            filename = os.path.join(folder, base_name)

                        img.save(filename)
                        saved_filenames.append(base_name)
                        count += 1
                        image_idx += 1
                    except Exception as e:
                        continue
        return saved_filenames