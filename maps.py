import os
import googlemaps

GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')

gmaps = googlemaps.Client(key=GOOGLE_API_KEY)

def get_addresses(latitude, longitude, result_type="political"):
    results = gmaps.reverse_geocode(
        (latitude, longitude), 
        result_type=[result_type] if result_type else None,
        language='ja'
    )
    addresses = []
    for result in results:
        addr = result['formatted_address']
        addresses.append(addr)
    print(f"{addresses}")
    return addresses
