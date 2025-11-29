"""
Geocode NIBRS Crime Data Records
Adds latitude/longitude to records that don't have coordinates

This uses a simple geocoding approach:
1. Uses geopy with Nominatim (free, no API key needed)
2. Geocodes by city + state
3. Adds rate limiting to respect service limits
4. Saves progress periodically
"""

import sys
import time
from datetime import datetime

# Add src to path
sys.path.insert(0, 'src')

from app import app
from extensions import db
from models.models import NIBRSCrimeData
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError

print("=" * 70)
print("🗺️  NIBRS Data Geocoding Script")
print("=" * 70)

# Initialize geocoder
geolocator = Nominatim(user_agent="worldcup_intelligence_platform")

def geocode_location(city, state, retry_count=0):
    """
    Geocode a city, state combination
    Returns (latitude, longitude) or (None, None) if failed
    """
    if not city or not state:
        return None, None
    
    try:
        # Create location string
        location_string = f"{city}, {state}, USA"
        
        # Geocode
        location = geolocator.geocode(location_string, timeout=10)
        
        if location:
            return location.latitude, location.longitude
        else:
            return None, None
            
    except GeocoderTimedOut:
        if retry_count < 3:
            time.sleep(2)
            return geocode_location(city, state, retry_count + 1)
        return None, None
    except GeocoderServiceError:
        return None, None
    except Exception as e:
        print(f"   ⚠️  Error geocoding {city}, {state}: {e}")
        return None, None

def main():
    with app.app_context():
        # Count records without coordinates
        total_records = db.session.query(NIBRSCrimeData).count()
        records_without_coords = db.session.query(NIBRSCrimeData).filter(
            NIBRSCrimeData.latitude.is_(None)
        ).count()
        
        print(f"\n📊 Database Status:")
        print(f"   Total NIBRS records: {total_records:,}")
        print(f"   Records without coordinates: {records_without_coords:,}")
        print(f"   Records with coordinates: {total_records - records_without_coords:,}")
        
        if records_without_coords == 0:
            print("\n✅ All records already have coordinates!")
            return
        
        # Ask for confirmation
        print(f"\n⚠️  This will geocode {records_without_coords:,} records.")
        print("   This will take approximately:", end=" ")
        estimated_minutes = (records_without_coords / 60) + 5  # ~1 per second + buffer
        print(f"{estimated_minutes:.0f} minutes")
        print("\n   Note: Uses free Nominatim service with rate limiting")
        print("         Progress is saved every 100 records")
        
        response = input("\nContinue? (yes/no): ")
        if response.lower() not in ['yes', 'y']:
            print("Cancelled.")
            return
        
        print("\n🚀 Starting geocoding...")
        print("=" * 70)
        
        # Get unique city/state combinations to geocode
        unique_locations = db.session.query(
            NIBRSCrimeData.city,
            NIBRSCrimeData.state
        ).filter(
            NIBRSCrimeData.latitude.is_(None),
            NIBRSCrimeData.city.isnot(None),
            NIBRSCrimeData.state.isnot(None)
        ).distinct().all()
        
        print(f"\n📍 Found {len(unique_locations)} unique city/state combinations to geocode")
        
        # Cache for geocoded locations
        geocode_cache = {}
        
        # Geocode unique locations first (much faster!)
        print("\n🔍 Phase 1: Geocoding unique locations...")
        for idx, (city, state) in enumerate(unique_locations, 1):
            cache_key = f"{city}|{state}"
            
            if idx % 10 == 0:
                print(f"   Progress: {idx}/{len(unique_locations)} ({idx/len(unique_locations)*100:.1f}%)")
            
            lat, lon = geocode_location(city, state)
            geocode_cache[cache_key] = (lat, lon)
            
            # Rate limiting (1 request per second for Nominatim)
            time.sleep(1)
        
        successful_geocodes = sum(1 for lat, lon in geocode_cache.values() if lat is not None)
        print(f"\n✅ Geocoded {successful_geocodes}/{len(unique_locations)} locations")
        
        # Update records with geocoded coordinates
        print("\n📝 Phase 2: Updating database records...")
        updated_count = 0
        failed_count = 0
        
        for idx, (city, state) in enumerate(unique_locations, 1):
            cache_key = f"{city}|{state}"
            lat, lon = geocode_cache.get(cache_key, (None, None))
            
            if lat is not None and lon is not None:
                # Update all records with this city/state
                records = db.session.query(NIBRSCrimeData).filter(
                    NIBRSCrimeData.city == city,
                    NIBRSCrimeData.state == state,
                    NIBRSCrimeData.latitude.is_(None)
                ).all()
                
                for record in records:
                    record.latitude = lat
                    record.longitude = lon
                    updated_count += 1
                
                # Commit every 100 records
                if idx % 100 == 0:
                    db.session.commit()
                    print(f"   Updated: {updated_count:,} records ({idx/len(unique_locations)*100:.1f}% complete)")
            else:
                # Count failed records
                failed_records = db.session.query(NIBRSCrimeData).filter(
                    NIBRSCrimeData.city == city,
                    NIBRSCrimeData.state == state,
                    NIBRSCrimeData.latitude.is_(None)
                ).count()
                failed_count += failed_records
        
        # Final commit
        db.session.commit()
        
        print("\n" + "=" * 70)
        print("✅ GEOCODING COMPLETE!")
        print("=" * 70)
        print(f"\n📊 Results:")
        print(f"   ✅ Successfully geocoded: {updated_count:,} records")
        print(f"   ❌ Failed to geocode: {failed_count:,} records")
        print(f"   📈 Success rate: {updated_count/(updated_count+failed_count)*100:.1f}%")
        
        # Verify final count
        final_with_coords = db.session.query(NIBRSCrimeData).filter(
            NIBRSCrimeData.latitude.isnot(None)
        ).count()
        
        print(f"\n✅ Database now has {final_with_coords:,} records with coordinates")
        print(f"   (out of {total_records:,} total records)")
        
        if final_with_coords > 0:
            print("\n🎉 Your map will now show NIBRS crime data!")
            print("\nNext steps:")
            print("   1. Restart Flask: python src/app.py")
            print("   2. Refresh browser: Ctrl+Shift+R")
            print("   3. Check map: http://localhost:5000/map")
            print("   4. You should see colored circles for crime data!")
        else:
            print("\n⚠️  WARNING: No records were successfully geocoded")
            print("   This might be a connection issue with the geocoding service")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        print("Progress has been saved up to this point")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
