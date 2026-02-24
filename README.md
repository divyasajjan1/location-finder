# TripPlanner — Backend (Django)

A Django REST API powering a full-stack landmark recognition and travel planning platform. Users can photograph a landmark, identify it using a custom-trained CNN model, estimate travel distance and cost from their location, and find real-time flight deals — all from one dashboard.

---

## Project Structure

The backend is split into two functional areas:

- **Admin pipeline** — Tools for scraping training images, bulk uploading datasets, and fine-tuning the CNN classification model
- **User-facing API** — Landmark identification, trip estimation, flight search, and an AI travel chat assistant

---

## Features

### Admin Pipeline
- **Image Scraping** — Scrapes training images from a user-provided URL. Falls back to the DDGS (DuckDuckGo Search) API if no URL is given
- **Bulk Upload** — Accepts multiple images via API and stores them for a target landmark class
- **Model Training** — Fine-tunes a ResNet-based CNN (PyTorch/TensorFlow) on uploaded landmark images. Tracks and returns accuracy, loss, image count, and epoch metrics per session. Currently trained on 11 landmarks

### User-Facing APIs
- **Landmark Identification** — Classifies an uploaded image using the trained ResNet model. Returns the landmark name, confidence score, and coordinates stored in the database
- **Landmark Summary** — Fetches structured facts from the Wikidata API and passes them to the Gemini API to generate a concise, readable landmark description
- **Trip Estimation** — Geocodes the user's typed city via Nominatim (OpenStreetMap) or parses GPS coordinates from the browser. Computes haversine distance to the landmark and estimates travel cost. Returns origin and destination coordinates for downstream use
- **Flight Deals** — Uses the Amadeus Flight Offers Search API to find the cheapest and fastest flights between the resolved origin and destination airports. Airport codes are resolved via coordinate lookup (with distance validation to reject incorrect Amadeus test environment results) and a city-to-IATA fallback map. Returns airline name, price, currency (USD), flight duration, and a Google Flights deep link
- **Landmark Chat** — A Gemini-powered conversational assistant that answers travel-related questions

---

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | Django + Django REST Framework |
| Database | PostgreSQL |
| ML Framework | PyTorch + TensorFlow |
| Model Architecture | ResNet (pretrained, fine-tuned) |
| Geocoding | Nominatim (OpenStreetMap) |
| Flight Data | Amadeus Flight Offers API |
| Landmark Facts | Wikidata API |
| AI Summarization & Chat | Google Gemini API |
| Image Scraping | DDGS (DuckDuckGo Search API) |

---

## Environment Variables

Create a `.env` file in the backend root with the following:

```env
SECRET_KEY=your_django_secret_key
DEBUG=True

# Database
DB_NAME=your_db_name
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=localhost
DB_PORT=5432

# Amadeus
AMADEUS_API_KEY=your_amadeus_key
AMADEUS_API_SECRET=your_amadeus_secret

# Google Gemini
GEMINI_API_KEY=your_gemini_key
```

---

## Setup

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Apply migrations
python manage.py migrate

# Run server
python manage.py runserver 8080
```

---

## Notes

- Trained ML model files are excluded from version control via `.gitignore`. You will need to train a model locally using the admin pipeline before landmark identification will work
- The Amadeus integration uses the **test environment** by default. In test mode, coordinate-to-airport resolution is less accurate for some regions (notably Canada) and more accurate for USA locations.
- Images are saved to the local filesystem under `data/raw/<landmark_name>/` and their relative paths are persisted to PostgreSQL via the `LandmarkImage` model. This folder is excluded from version control — images must be re-ingested via the Scrape or Bulk Upload cards after cloning.
