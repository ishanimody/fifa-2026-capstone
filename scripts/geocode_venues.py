"""
World Cup 2026 Venues - Geocoding Script (Free - No API Key)
Uses OpenStreetMap's Nominatim API to fetch coordinates

Place in: scripts/geocode_venues.py
"""

import requests
import time
import pandas as pd
import json
import os
from typing import Dict, Optional

class VenueGeocoder:
    """Geocode World Cup 2026 venues using free Nominatim API"""
    
    def __init__(self):
        self.base_url = "https://nominatim.openstreetmap.org/search"
        self.headers = {
            'User-Agent': 'WorldCup2026VenueMapper/1.0 (Educational Capstone Project)'
        }
    
    def geocode_venue(self, venue_name: str, city: str, state: str, country: str) -> Optional[Dict]:
        """Geocode a single venue"""
        query = f"{venue_name}, {city}, {state}, {country}"
        
        params = {
            'q': query,
            'format': 'json',
            'limit': 1,
            'addressdetails': 1
        }
        
        try:
            print(f"Geocoding: {query}...")
            response = requests.get(
                self.base_url,
                params=params,
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            
            if data and len(data) > 0:
                result = data[0]
                print(f"  ✓ Success: ({float(result['lat']):.6f}, {float(result['lon']):.6f})")
                return {
                    'latitude': float(result['lat']),
                    'longitude': float(result['lon']),
                    'formatted_address': result.get('display_name', ''),
                    'osm_id': result.get('osm_id', ''),
                }
            else:
                print(f"  ⚠ No results found")
                return None
                
        except Exception as e:
            print(f"  ✗ Error: {e}")
            return None
        
        finally:
            # MUST respect rate limit: 1 request per second
            time.sleep(1.5)
    
    def geocode_all_venues(self, venues_list: list) -> pd.DataFrame:
        """Geocode all venues"""
        results = []
        
        print("=" * 80)
        print("GEOCODING WORLD CUP 2026 VENUES (FREE API)")
        print("=" * 80)
        print(f"Total venues: {len(venues_list)}")
        print("Note: Rate limited to 1 request/second - this will take ~25 seconds\n")
        
        for idx, venue in enumerate(venues_list, 1):
            print(f"[{idx}/{len(venues_list)}] ", end="")
            
            geo_data = self.geocode_venue(
                venue['venue_name'],
                venue['city'],
                venue['state_province'],
                venue['country']
            )
            
            if geo_data:
                venue.update({
                    'latitude': geo_data['latitude'],
                    'longitude': geo_data['longitude'],
                    'formatted_address': geo_data['formatted_address'],
                    'geocoded': True
                })
            else:
                venue.update({
                    'latitude': None,
                    'longitude': None,
                    'formatted_address': None,
                    'geocoded': False
                })
            
            results.append(venue)
        
        print("\n" + "=" * 80)
        df = pd.DataFrame(results)
        success_count = df['geocoded'].sum()
        print(f"Complete: {success_count}/{len(venues_list)} successful")
        print("=" * 80 + "\n")
        
        return df


# World Cup 2026 Venues Data
venues_base_data = [
    {'venue_id': 1, 'venue_name': 'MetLife Stadium', 'city': 'East Rutherford', 'state_province': 'New Jersey', 'country': 'USA', 'capacity': 82500, 'host_matches': 8},
    {'venue_id': 2, 'venue_name': 'Mercedes-Benz Stadium', 'city': 'Atlanta', 'state_province': 'Georgia', 'country': 'USA', 'capacity': 71000, 'host_matches': 8},
    {'venue_id': 3, 'venue_name': 'Hard Rock Stadium', 'city': 'Miami Gardens', 'state_province': 'Florida', 'country': 'USA', 'capacity': 65326, 'host_matches': 7},
    {'venue_id': 4, 'venue_name': 'Arrowhead Stadium', 'city': 'Kansas City', 'state_province': 'Missouri', 'country': 'USA', 'capacity': 76416, 'host_matches': 6},
    {'venue_id': 5, 'venue_name': 'AT&T Stadium', 'city': 'Arlington', 'state_province': 'Texas', 'country': 'USA', 'capacity': 80000, 'host_matches': 9},
    {'venue_id': 6, 'venue_name': 'NRG Stadium', 'city': 'Houston', 'state_province': 'Texas', 'country': 'USA', 'capacity': 72220, 'host_matches': 7},
    {'venue_id': 7, 'venue_name': 'Levi\'s Stadium', 'city': 'Santa Clara', 'state_province': 'California', 'country': 'USA', 'capacity': 68500, 'host_matches': 6},
    {'venue_id': 8, 'venue_name': 'SoFi Stadium', 'city': 'Inglewood', 'state_province': 'California', 'country': 'USA', 'capacity': 70240, 'host_matches': 8},
    {'venue_id': 9, 'venue_name': 'Lincoln Financial Field', 'city': 'Philadelphia', 'state_province': 'Pennsylvania', 'country': 'USA', 'capacity': 67594, 'host_matches': 6},
    {'venue_id': 10, 'venue_name': 'Lumen Field', 'city': 'Seattle', 'state_province': 'Washington', 'country': 'USA', 'capacity': 68740, 'host_matches': 6},
    {'venue_id': 11, 'venue_name': 'Gillette Stadium', 'city': 'Foxborough', 'state_province': 'Massachusetts', 'country': 'USA', 'capacity': 65878, 'host_matches': 7},
    {'venue_id': 12, 'venue_name': 'BMO Field', 'city': 'Toronto', 'state_province': 'Ontario', 'country': 'Canada', 'capacity': 30000, 'host_matches': 6},
    {'venue_id': 13, 'venue_name': 'BC Place', 'city': 'Vancouver', 'state_province': 'British Columbia', 'country': 'Canada', 'capacity': 54500, 'host_matches': 7},
    {'venue_id': 14, 'venue_name': 'Estadio Azteca', 'city': 'Mexico City', 'state_province': 'CDMX', 'country': 'Mexico', 'capacity': 87523, 'host_matches': 5},
    {'venue_id': 15, 'venue_name': 'Estadio BBVA', 'city': 'Monterrey', 'state_province': 'Nuevo León', 'country': 'Mexico', 'capacity': 53500, 'host_matches': 4},
    {'venue_id': 16, 'venue_name': 'Estadio Akron', 'city': 'Guadalajara', 'state_province': 'Jalisco', 'country': 'Mexico', 'capacity': 46232, 'host_matches': 4}
]


def save_results(df: pd.DataFrame, prefix: str = 'worldcup_2026_venues'):
    """Save geocoded results to multiple formats"""
    
    # Create data directory if needed
    os.makedirs('data/geojson', exist_ok=True)
    os.makedirs('data/processed', exist_ok=True)
    
    print("\n" + "=" * 80)
    print("SAVING RESULTS...")
    print("=" * 80)
    
    # CSV
    csv_file = f'data/processed/{prefix}.csv'
    df.to_csv(csv_file, index=False)
    print(f"✓ CSV saved: {csv_file}")
    
    # JSON
    json_file = f'data/processed/{prefix}.json'
    df.to_json(json_file, orient='records', indent=2)
    print(f"✓ JSON saved: {json_file}")
    
    # GeoJSON (only geocoded venues)
    features = []
    for _, row in df[df['geocoded']].iterrows():
        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [row['longitude'], row['latitude']]
            },
            "properties": {
                "venue_id": int(row['venue_id']),
                "venue_name": row['venue_name'],
                "city": row['city'],
                "state_province": row['state_province'],
                "country": row['country'],
                "capacity": int(row['capacity']),
                "host_matches": int(row['host_matches']),
                "formatted_address": row.get('formatted_address', '')
            }
        }
        features.append(feature)
    
    geojson = {"type": "FeatureCollection", "features": features}
    
    geojson_file = f'data/geojson/{prefix}.geojson'
    with open(geojson_file, 'w') as f:
        json.dump(geojson, f, indent=2)
    print(f"✓ GeoJSON saved: {geojson_file}")
    
    print("=" * 80)


def main():
    """Main execution"""
    
    print("\n" + "=" * 80)
    print("WORLD CUP 2026 VENUES GEOCODING TOOL")
    print("=" * 80)
    print("\nUsing Free Nominatim API (OpenStreetMap)")
    print("No API key needed!")
    
    geocoder = VenueGeocoder()
    venues_df = geocoder.geocode_all_venues(venues_base_data)
    save_results(venues_df, 'worldcup_2026_venues')
    
    # Display summary
    print("\n" + "=" * 80)
    print("GEOCODING SUMMARY")
    print("=" * 80)
    print(venues_df[['venue_name', 'city', 'country', 'latitude', 'longitude', 'geocoded']].to_string(index=False))
    print("\n" + "=" * 80)
    print("✓ GEOCODING COMPLETE!")
    print("=" * 80)
    
    return venues_df


if __name__ == "__main__":
    """
    USAGE:
    1. Make sure you're in the project root with venv activated
    2. Run: python scripts/geocode_venues.py
    3. Wait ~25 seconds for all venues to be geocoded
    4. Files will be saved to data/processed/ and data/geojson/
    """
    main()