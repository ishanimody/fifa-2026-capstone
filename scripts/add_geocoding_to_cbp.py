

import sys
sys.path.append('../src')

from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()

# Field Office Location Mapping (from models.py)
CBP_FIELD_OFFICE_LOCATIONS = {
    'ATLANTA FIELD OFFICE': {'city': 'Atlanta', 'state': 'GA', 'lat': 33.7490, 'lon': -84.3880},
    'BALTIMORE FIELD OFFICE': {'city': 'Baltimore', 'state': 'MD', 'lat': 39.2904, 'lon': -76.6122},
    'BOSTON FIELD OFFICE': {'city': 'Boston', 'state': 'MA', 'lat': 42.3601, 'lon': -71.0589},
    'BUFFALO FIELD OFFICE': {'city': 'Buffalo', 'state': 'NY', 'lat': 42.8864, 'lon': -78.8784},
    'CHICAGO FIELD OFFICE': {'city': 'Chicago', 'state': 'IL', 'lat': 41.8781, 'lon': -87.6298},
    'DETROIT FIELD OFFICE': {'city': 'Detroit', 'state': 'MI', 'lat': 42.3314, 'lon': -83.0458},
    'EL PASO FIELD OFFICE': {'city': 'El Paso', 'state': 'TX', 'lat': 31.7619, 'lon': -106.4850},
    'HOUSTON FIELD OFFICE': {'city': 'Houston', 'state': 'TX', 'lat': 29.7604, 'lon': -95.3698},
    'LAREDO FIELD OFFICE': {'city': 'Laredo', 'state': 'TX', 'lat': 27.5306, 'lon': -99.4803},
    'LOS ANGELES FIELD OFFICE': {'city': 'Los Angeles', 'state': 'CA', 'lat': 34.0522, 'lon': -118.2437},
    'MIAMI FIELD OFFICE': {'city': 'Miami', 'state': 'FL', 'lat': 25.7617, 'lon': -80.1918},
    'NEW ORLEANS FIELD OFFICE': {'city': 'New Orleans', 'state': 'LA', 'lat': 29.9511, 'lon': -90.0715},
    'NEW YORK FIELD OFFICE': {'city': 'New York', 'state': 'NY', 'lat': 40.7128, 'lon': -74.0060},
    'NOGALES FIELD OFFICE': {'city': 'Nogales', 'state': 'AZ', 'lat': 31.3404, 'lon': -110.9342},
    'PHILADELPHIA FIELD OFFICE': {'city': 'Philadelphia', 'state': 'PA', 'lat': 39.9526, 'lon': -75.1652},
    'PHOENIX FIELD OFFICE': {'city': 'Phoenix', 'state': 'AZ', 'lat': 33.4484, 'lon': -112.0740},
    'PORTLAND FIELD OFFICE': {'city': 'Portland', 'state': 'OR', 'lat': 45.5152, 'lon': -122.6784},
    'SAN DIEGO FIELD OFFICE': {'city': 'San Diego', 'state': 'CA', 'lat': 32.7157, 'lon': -117.1611},
    'SAN FRANCISCO FIELD OFFICE': {'city': 'San Francisco', 'state': 'CA', 'lat': 37.7749, 'lon': -122.4194},
    'SAN JUAN FIELD OFFICE': {'city': 'San Juan', 'state': 'PR', 'lat': 18.4655, 'lon': -66.1057},
    'SEATTLE FIELD OFFICE': {'city': 'Seattle', 'state': 'WA', 'lat': 47.6062, 'lon': -122.3321},
    'TUCSON FIELD OFFICE': {'city': 'Tucson', 'state': 'AZ', 'lat': 32.2226, 'lon': -110.9747},
    'WASHINGTON FIELD OFFICE': {'city': 'Washington', 'state': 'DC', 'lat': 38.9072, 'lon': -77.0369},
}

def add_geocoding_columns():
    """Add geocoding columns to CBP table and populate them"""
    
    print("=" * 70)
    print("ADD GEOCODING TO CBP DRUG SEIZURES TABLE")
    print("=" * 70)
    
    db_url = os.getenv('DATABASE_URL')
    
    if not db_url:
        print("\n❌ ERROR: DATABASE_URL not found in .env file")
        return False
    
    print(f"\nDatabase: {db_url.split('@')[1] if '@' in db_url else db_url}")
    
    try:
        engine = create_engine(db_url, echo=False)
        
        with engine.connect() as conn:
            # Step 1: Add columns if they don't exist
            print("\n1. Adding geocoding columns...")
            
            columns_to_add = [
                ('latitude', 'FLOAT'),
                ('longitude', 'FLOAT'),
                ('city', 'VARCHAR(100)'),
                ('state', 'VARCHAR(50)')
            ]
            
            for col_name, col_type in columns_to_add:
                try:
                    conn.execute(text(f"""
                        ALTER TABLE cbp_drug_seizures 
                        ADD COLUMN IF NOT EXISTS {col_name} {col_type}
                    """))
                    conn.commit()
                    print(f"   ✓ Added column: {col_name}")
                except Exception as e:
                    if 'already exists' in str(e).lower():
                        print(f"   - Column {col_name} already exists")
                    else:
                        print(f"   ⚠️  {col_name}: {e}")
            
            # Step 2: Populate geocoding data
            print("\n2. Populating geocoding data from field office locations...")
            
            updated_count = 0
            not_found_offices = set()
            
            for office_name, location in CBP_FIELD_OFFICE_LOCATIONS.items():
                try:
                    result = conn.execute(text("""
                        UPDATE cbp_drug_seizures
                        SET latitude = :lat,
                            longitude = :lon,
                            city = :city,
                            state = :state
                        WHERE area_of_responsibility = :office
                    """), {
                        'lat': location['lat'],
                        'lon': location['lon'],
                        'city': location['city'],
                        'state': location['state'],
                        'office': office_name
                    })
                    conn.commit()
                    
                    if result.rowcount > 0:
                        updated_count += result.rowcount
                        print(f"   ✓ {office_name}: {result.rowcount} records updated")
                    
                except Exception as e:
                    print(f"   ⚠️  Error updating {office_name}: {e}")
            
            # Step 3: Check for offices not in our mapping
            print("\n3. Checking for unmapped field offices...")
            
            unmapped = conn.execute(text("""
                SELECT DISTINCT area_of_responsibility, COUNT(*) as count
                FROM cbp_drug_seizures
                WHERE latitude IS NULL 
                AND area_of_responsibility IS NOT NULL
                GROUP BY area_of_responsibility
                ORDER BY count DESC
            """)).fetchall()
            
            if unmapped:
                print(f"   Found {len(unmapped)} unmapped offices:")
                for office, count in unmapped[:10]:  # Show top 10
                    print(f"   - {office}: {count} records")
                    not_found_offices.add(office)
            else:
                print("   ✓ All offices are mapped!")
            
            # Step 4: Show statistics
            print("\n4. Geocoding Statistics:")
            
            total = conn.execute(text("""
                SELECT COUNT(*) FROM cbp_drug_seizures
            """)).scalar()
            
            with_coords = conn.execute(text("""
                SELECT COUNT(*) FROM cbp_drug_seizures
                WHERE latitude IS NOT NULL AND longitude IS NOT NULL
            """)).scalar()
            
            without_coords = total - with_coords
            
            print(f"   Total records: {total:,}")
            print(f"   With coordinates: {with_coords:,} ({with_coords/total*100:.1f}%)")
            print(f"   Without coordinates: {without_coords:,} ({without_coords/total*100:.1f}%)")
            
            # Step 5: Sample of geocoded data
            print("\n5. Sample of geocoded data:")
            
            samples = conn.execute(text("""
                SELECT area_of_responsibility, city, state, latitude, longitude, 
                       COUNT(*) as record_count
                FROM cbp_drug_seizures
                WHERE latitude IS NOT NULL
                GROUP BY area_of_responsibility, city, state, latitude, longitude
                ORDER BY record_count DESC
                LIMIT 5
            """)).fetchall()
            
            for office, city, state, lat, lon, count in samples:
                print(f"   {office[:30]:30} | {city:15} {state:2} | ({lat:7.4f}, {lon:8.4f}) | {count:,} records")
        
        print("\n" + "=" * 70)
        print("✓ GEOCODING COMPLETE!")
        print("=" * 70)
        
        if not_found_offices:
            print("\n⚠️  WARNING: Some offices were not geocoded")
            print(f"   {len(not_found_offices)} offices need manual geocoding")
            print("\n   To add missing offices, update the CBP_FIELD_OFFICE_LOCATIONS")
            print("   dictionary in this script and run again.")
        
        print(f"\n✓ {with_coords:,} records now have coordinates!")
        print(f"✓ Ready for map visualization!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print("\nTroubleshooting:")
        print("1. Check if PostgreSQL is running")
        print("2. Verify DATABASE_URL in .env file")
        print("3. Ensure you have write permissions on the database")
        return False


if __name__ == "__main__":
    print("\nThis script will:")
    print("1. Add latitude, longitude, city, state columns to cbp_drug_seizures")
    print("2. Populate them based on field office locations")
    print("3. Show statistics on geocoding coverage")
    
    response = input("\nContinue? (yes/no) [yes]: ").strip().lower()
    
    if response in ['', 'yes', 'y']:
        success = add_geocoding_columns()
        
        if success:
            print("\n✅ Next steps:")
            print("   1. Run: python check_cbp_data_postgresql.py")
            print("   2. Verify coordinates are populated")
            print("   3. Start Flask: python ../src/app.py")
            print("   4. View map: http://127.0.0.1:5000/map")
        else:
            print("\n❌ Geocoding failed. Please fix errors and try again.")
    else:
        print("\nCancelled by user.")