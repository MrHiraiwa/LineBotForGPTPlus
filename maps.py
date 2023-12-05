import os
import googlemaps
from googlemaps.exceptions import ApiError, HTTPError, Timeout, TransportError

GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')
gmaps = googlemaps.Client(key=GOOGLE_API_KEY)

def get_addresses(latitude, longitude, result_type="sublocality"):
    try:
        results = gmaps.reverse_geocode(
            (latitude, longitude), 
            result_type=[result_type] if result_type else None,
            language='ja'
        )
        addresses = [result['formatted_address'] for result in results]
        return addresses[1]
    except ApiError as e:
        print(f"API Error: {e}")
    except HTTPError as e:
        print(f"HTTP Error: {e}")
    except Timeout as e:
        print(f"Timeout Error: {e}")
    except TransportError as e:
        print(f"Transport Error: {e}")
    except Exception as e:
        print(f"General Error: {e}")
    return []
