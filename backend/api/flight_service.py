from amadeus import Client, ResponseError
from django.conf import settings
import datetime
import re

amadeus = Client(
    client_id=settings.AMADEUS_API_KEY,
    client_secret=settings.AMADEUS_API_SECRET
)


def _iata_from_coords(lat, lon):
    """Return the nearest airport IATA code for a lat/lon pair, or None."""
    try:
        res = amadeus.reference_data.locations.airports.get(
            latitude=float(lat),
            longitude=float(lon)
        )
        if res.data:
            return res.data[0]['iataCode']
    except Exception as e:
        print(f"DEBUG: coord→IATA failed ({lat},{lon}): {e}")
    return None


def _iata_from_keyword(keyword):
    """Return the best-match IATA code for a city/airport keyword, or None."""
    try:
        clean = re.sub(r'[^a-zA-Z\s]', ' ', keyword).strip().split()[0]
        res = amadeus.reference_data.locations.get(
            keyword=clean, subType='CITY,AIRPORT'
        )
        if res.data:
            return res.data[0]['iataCode']
    except Exception as e:
        print(f"DEBUG: keyword→IATA failed ({keyword}): {e}")
    return None


def _parse_duration_minutes(iso_duration):
    """Convert Amadeus ISO 8601 duration (e.g. 'PT2H35M') to total minutes."""
    match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?', iso_duration or '')
    if not match:
        return float('inf')
    hours = int(match.group(1) or 0)
    minutes = int(match.group(2) or 0)
    return hours * 60 + minutes


def _total_duration(offer):
    """Sum durations of all itinerary legs for a flight offer."""
    total = 0
    for itinerary in offer.get('itineraries', []):
        total += _parse_duration_minutes(itinerary.get('duration', ''))
    return total


def _airline_name(offer, carriers):
    """Resolve a human-readable airline name from an offer."""
    code = None
    try:
        code = offer.get('validatingAirlineCode') \
               or offer['itineraries'][0]['segments'][0]['carrierCode']
    except (KeyError, IndexError):
        pass
    return carriers.get(code, f"Airline ({code})" if code else "Unknown Airline")


def get_flight_deals(destination_name, origin_input, lat=None, lon=None, origin_lat=None, origin_lon=None):
    """
    Returns a list with a 'Cheapest' and 'Fastest' flight offer dict,
    or a single-item list containing an error dict.
    """
    print(f"DEBUG PARAMS: dest={destination_name}, origin={origin_input}, lat={lat}, lon={lon}, origin_lat={origin_lat}, origin_lon={origin_lon}")
    try:
        depart_date = (datetime.date.today() + datetime.timedelta(days=14)).isoformat()

        # ── DESTINATION IATA ──────────────────────────────────────────────────
        dest_iata = None
        if lat is not None and lon is not None:
            try:
                if float(lat) != 0.0 or float(lon) != 0.0:
                    dest_iata = _iata_from_coords(lat, lon)
                    print(f"DEBUG: dest via coords → {dest_iata}")
            except (ValueError, TypeError):
                pass

        if not dest_iata:
            keyword = destination_name.replace('_', ' ').split()[-1]
            dest_iata = _iata_from_keyword(keyword)
            print(f"DEBUG: dest via keyword '{keyword}' → {dest_iata}")

        # ── ORIGIN IATA ───────────────────────────────────────────────────────
        origin_iata = None

        # Use GPS coords first if available (most accurate)
        if origin_lat and origin_lon:
            origin_iata = _iata_from_coords(origin_lat, origin_lon)
            print(f"DEBUG: origin via GPS coords → {origin_iata}")

        # Case 1: "Lat: 51.5, Lon: -0.12" style string from the UI
        if not origin_iata:
            origin_str = str(origin_input).strip()
            if 'lat:' in origin_str.lower():
                nums = re.findall(r"[-+]?\d*\.?\d+", origin_str)
                if len(nums) >= 2:
                    origin_iata = _iata_from_coords(nums[0], nums[1])
                    print(f"DEBUG: origin via coord string → {origin_iata}")

        # Case 2: Plain city name / airport code
        if not origin_iata:
            origin_iata = _iata_from_keyword(origin_str)
            print(f"DEBUG: origin via keyword '{origin_str}' → {origin_iata}")

        # ── VALIDATION ────────────────────────────────────────────────────────
        if not dest_iata or not origin_iata:
            return [{"error": f"Could not resolve airports — origin: {origin_iata}, dest: {dest_iata}"}]

        if origin_iata == dest_iata:
            return [{"error": f"Origin and destination resolved to the same airport ({origin_iata}). Please check your inputs."}]

        # ── FLIGHT SEARCH ─────────────────────────────────────────────────────
        print(f"DEBUG: searching {origin_iata} → {dest_iata} on {depart_date}")
        response = amadeus.shopping.flight_offers_search.get(
            originLocationCode=origin_iata,
            destinationLocationCode=dest_iata,
            departureDate=depart_date,
            adults=1,
            max=10,         # fetch more so we have a real fastest candidate
            currencyCode='USD'
        )

        if not response.data:
            return [{"error": "No flights found for this route and date."}]
        
        print(f"DEBUG OFFERS: {[(o['price']['total'], o['price']['currency'], o['itineraries'][0]['segments'][0].get('carrierCode', '?')) for o in response.data]}")

        carriers = response.result.get('dictionaries', {}).get('carriers', {})

        # Cheapest = lowest total price (results are already price-sorted by Amadeus)
        cheapest = response.data[0]

        # Fastest = shortest total flying time across all returned offers
        fastest = min(response.data, key=_total_duration)

        def build_deal(label, offer):
            depart_code = offer['itineraries'][0]['segments'][0]['departure']['iataCode']
            arrive_code = offer['itineraries'][-1]['segments'][-1]['arrival']['iataCode']
            booking_url = f"https://www.google.com/travel/flights?q=flights+from+{depart_code}+to+{arrive_code}+on+{depart_date}"
            return {
                "type": label,
                "site": _airline_name(offer, carriers),
                "price": offer['price']['total'],
                "currency": offer['price']['currency'],
                "duration_minutes": _total_duration(offer),
                "booking_url": booking_url,
                "from_airport": depart_code,
                "to_airport": arrive_code, 
            }

        return [
            build_deal("Cheapest", cheapest),
            build_deal("Fastest", fastest),
        ]

    except ResponseError as api_err:
        print(f"DEBUG: Amadeus API error: {api_err}")
        return [{"error": f"Amadeus API error: {api_err.response.body}"}]
    except Exception as fatal:
        print(f"CRITICAL: {fatal}")
        return [{"error": "Flight service encountered an unexpected error."}]