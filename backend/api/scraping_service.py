import os
import requests
from ddgs import DDGS
from PIL import Image
from io import BytesIO
from bs4 import BeautifulSoup # New import
import re # New import for URL validation
import urllib.parse # New import for URL joining

# User-Agent header to mimic a browser for scraping
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# ---------------- Config ----------------
DEFAULT_KEYWORDS = {
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

IMAGES_PER_CLASS_TARGET = 250
SAVE_ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "raw")
os.makedirs(SAVE_ROOT, exist_ok=True)

# Regex for a simple URL validation
URL_REGEX = re.compile(
    r'^(?:http|ftp)s?://' # http:// or https://
    r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' # domain...
    r'localhost|' # localhost...
    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
    r'(?::\d+)?' # optional port
    r'(?:/?|[/?]\S+)$'
    , re.IGNORECASE)

def _is_valid_url(url):
    return re.match(URL_REGEX, url) is not None

def scrape_images_from_url_and_save(
    target_url: str,
    landmark_name: str,
    images_to_scrape: int
) -> int:
    """
    Scrapes images from a single given URL and saves them to the landmark's folder.
    Returns the number of images successfully scraped.
    """
    print(f"\n--- Scraping images from URL: {target_url} for {landmark_name} ---")
    folder = os.path.join(SAVE_ROOT, landmark_name)
    os.makedirs(folder, exist_ok=True)

    initial_count = len(os.listdir(folder))
    count = initial_count
    image_idx = initial_count

    try:
        response = requests.get(target_url, timeout=15, headers=HEADERS)
        response.raise_for_status() # Raise an exception for HTTP errors
        soup = BeautifulSoup(response.text, 'html.parser')
        
        img_tags = soup.find_all('img')
        for img_tag in img_tags:
            if count - initial_count >= images_to_scrape:
                break

            img_url = img_tag.get('src')
            if not img_url:
                continue
            
            # Resolve relative URLs
            if not img_url.startswith(('http://', 'https://')):
                img_url = urllib.parse.urljoin(target_url, img_url)

            try:
                img_response = requests.get(img_url, timeout=15, headers=HEADERS)
                img_response.raise_for_status()
                
                img = Image.open(BytesIO(img_response.content))
                if img.mode == 'RGBA':
                    img = img.convert('RGB')
                if img.width < 100 or img.height < 100:
                    continue
                
                filename = os.path.join(folder, f"{image_idx}.jpg")
                while os.path.exists(filename):
                    image_idx += 1
                    filename = os.path.join(folder, f"{image_idx}.jpg")

                img.save(filename)
                count += 1
                image_idx += 1

            except Exception as e:
                print(f"Error downloading image from {img_url}: {e}")
                continue

    except Exception as e:
        print(f"Error scraping URL {target_url}: {e}")
        return 0

    print(f"Done with URL scraping for {landmark_name}: {count - initial_count} new images collected.")
    return count - initial_count

def scrape_images_for_landmark(
    landmark_name: str,
    source_input: str = None, # Can be URL or keyword
    images_to_scrape: int = IMAGES_PER_CLASS_TARGET
) -> int:
    """
    Scrapes images for a given landmark. Prioritizes URL scraping if source_input is a valid URL,
    otherwise falls back to DuckDuckGo image search using keywords.
    Returns the number of images successfully scraped.
    """
    if source_input and _is_valid_url(source_input):
        print(f"Detected valid URL: {source_input}")
        return scrape_images_from_url_and_save(source_input, landmark_name, images_to_scrape)
    else:
        # Fallback to DDGS if no valid URL or if source_input is a keyword
        print(f"Falling back to keyword search for {landmark_name} with query: {source_input or 'default keywords'}")
        folder = os.path.join(SAVE_ROOT, landmark_name)
        os.makedirs(folder, exist_ok=True)

        existing_files = set(os.listdir(folder))
        initial_count = len(existing_files)
        count = initial_count
        image_idx = initial_count

        search_keywords = DEFAULT_KEYWORDS.get(landmark_name, [landmark_name.replace("_", " ")])
        if source_input:
            search_keywords.insert(0, source_input) # Use source_input as an additional keyword
        
        unique_keywords = list(set(search_keywords))

        with DDGS() as ddgs:
            for kw in unique_keywords:
                if count - initial_count >= images_to_scrape:
                    break

                remaining_needed = images_to_scrape - (count - initial_count)
                if remaining_needed <= 0:
                    break

                results = ddgs.images(query=kw, max_results=remaining_needed, safesearch="off")

                for r in results:
                    if count - initial_count >= images_to_scrape:
                        break
                    try:
                        img_url = r.get("image")
                        if not img_url:
                            continue

                        response = requests.get(img_url, timeout=15)
                        if response.status_code != 200:
                            continue

                        img = Image.open(BytesIO(response.content))
                        if img.mode == 'RGBA':
                            img = img.convert('RGB')
                        if img.width < 100 or img.height < 100:
                            continue
                        
                        filename = os.path.join(folder, f"{image_idx}.jpg")
                        while os.path.exists(filename):
                            image_idx += 1
                            filename = os.path.join(folder, f"{image_idx}.jpg")

                        img.save(filename)
                        count += 1
                        image_idx += 1

                    except Exception as e:
                        print(f"Error downloading image from {img_url}: {e}")
                        continue

        print(f"Done with keyword scraping for {landmark_name}: {count - initial_count} new images collected.")
        return count - initial_count
