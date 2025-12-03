"""
Geocode CBP Drug Seizures
Adds lat/lon coordinates based on city/state or area_of_responsibility
"""

import sys
sys.path.insert(0, 'src')

from app import app
from extensions import db
from models.models import CBPDrugSeizure

print("=" * 70)
print("🗺️  CBP Drug Seizures Geocoding")
print("=" * 70)

# Field office locations from models.py
FIELD_OFFICE_LOCATIONS = {
    'ATLANTA': {'lat': 33.7490, 'lon': -84.3880, 'city': 'Atlanta', 'state': 'GA'},
    'BALTIMORE': {'lat': 39.2904, 'lon': -76.6122, 'city': 'Baltimore', 'state': 'MD'},
    'BOSTON': {'lat': 42.3601, 'lon': -71.0589, 'city': 'Boston', 'state': 'MA'},
    'BUFFALO': {'lat': 42.8864, 'lon': -78.8784, 'city': 'Buffalo', 'state': 'NY'},
    'CHICAGO': {'lat': 41.8781, 'lon': -87.6298, 'city': 'Chicago', 'state': 'IL'},
    'DETROIT': {'lat': 42.3314, 'lon': -83.0458, 'city': 'Detroit', 'state': 'MI'},
    'EL PASO': {'lat': 31.7619, 'lon': -106.4850, 'city': 'El Paso', 'state': 'TX'},
    'HOUSTON': {'lat': 29.7604, 'lon': -95.3698, 'city': 'Houston', 'state': 'TX'},
    'LAREDO': {'lat': 27.5306, 'lon': -99.4803, 'city': 'Laredo', 'state': 'TX'},
    'LOS ANGELES': {'lat': 34.0522, 'lon': -118.2437, 'city': 'Los Angeles', 'state': 'CA'},
    'MIAMI': {'lat': 25.7617, 'lon': -80.1918, 'city': 'Miami', 'state': 'FL'},
    'NEW ORLEANS': {'lat': 29.9511, 'lon': -90.0715, 'city': 'New Orleans', 'state': 'LA'},
    'NEW YORK': {'lat': 40.7128, 'lon': -74.0060, 'city': 'New York', 'state': 'NY'},
    'NOGALES': {'lat': 31.3404, 'lon': -110.9342, 'city': 'Nogales', 'state': 'AZ'},
    'PHILADELPHIA': {'lat': 39.9526, 'lon': -75.1652, 'city': 'Philadelphia', 'state': 'PA'},
    'SAN DIEGO': {'lat': 32.7157, 'lon': -117.1611, 'city': 'San Diego', 'state': 'CA'},
    'SAN FRANCISCO': {'lat': 37.7749, 'lon': -122.4194, 'city': 'San Francisco', 'state': 'CA'},
    'SEATTLE': {'lat': 47.6062, 'lon': -122.3321, 'city': 'Seattle', 'state': 'WA'},
    'TAMPA': {'lat': 27.9506, 'lon': -82.4572, 'city': 'Tampa', 'state': 'FL'},
    'TUCSON': {'lat': 32.2226, 'lon': -110.9747, 'city': 'Tucson', 'state': 'AZ'},
}

def find_office_location(area_name):
    """Try to match area_of_responsibility to a field office"""
    if not area_name:
        return None
    
    area_upper = area_name.upper()
    
    # Try exact match first
    for office_key in FIELD_OFFICE_LOCATIONS:
        if office_key in area_upper:
            return FIELD_OFFICE_LOCATIONS[office_key]
    
    return None

with app.app_context():
    # Count records
    total = db.session.query(CBPDrugSeizure).count()
    without_coords = db.session.query(CBPDrugSeizure).filter(
        CBPDrugSeizure.latitude.is_(None)
    ).count()
    
    print(f"\n📊 Statistics:")
    print(f"   Total records: {total:,}")
    print(f"   Without coordinates: {without_coords:,}")
    print(f"   With coordinates: {total - without_coords:,}")
    
    if without_coords == 0:
        print("\n✅ All records already have coordinates!")
        sys.exit(0)
    
    print(f"\n🚀 Geocoding {without_coords:,} records...")
    print("=" * 70)
    
    # Get unique areas without coordinates
    areas = db.session.query(CBPDrugSeizure.area_of_responsibility).filter(
        CBPDrugSeizure.latitude.is_(None)
    ).distinct().all()
    
    area_lookup = {}
    for (area,) in areas:
        if area:
            loc = find_office_location(area)
            if loc:
                area_lookup[area] = loc
    
    print(f"\n📍 Matched {len(area_lookup)} areas to field offices")
    
    # Update records
    updated = 0
    for area, loc in area_lookup.items():
        records = db.session.query(CBPDrugSeizure).filter(
            CBPDrugSeizure.area_of_responsibility == area,
            CBPDrugSeizure.latitude.is_(None)
        ).all()
        
        for record in records:
            record.latitude = loc['lat']
            record.longitude = loc['lon']
            if not record.city:
                record.city = loc['city']
            if not record.state:
                record.state = loc['state']
            updated += 1
        
        if updated % 1000 == 0:
            db.session.commit()
            print(f"   Updated: {updated:,} records...")
    
    # Final commit
    db.session.commit()
    
    # Final count
    final_with_coords = db.session.query(CBPDrugSeizure).filter(
        CBPDrugSeizure.latitude.isnot(None)
    ).count()
    
    print("\n" + "=" * 70)
    print("✅ GEOCODING COMPLETE!")
    print("=" * 70)
    print(f"\n📊 Results:")
    print(f"   Records geocoded: {updated:,}")
    print(f"   Total with coordinates: {final_with_coords:,}")
    print(f"   Still missing: {total - final_with_coords:,}")
    
    if final_with_coords > 0:
        print("\n🎉 Your drug seizures will now show on the map!")
        print("\nNext steps:")
        print("   1. Restart Flask: python src/app.py")
        print("   2. Refresh browser: Ctrl+Shift+R")
        print("   3. Check 'Drug Seizures (CBP)' checkbox")
        print("   4. You should see colored circles!")
    
print("\n" + "=" * 70)
