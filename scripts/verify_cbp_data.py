"""
Quick Database Verification Script
Run this to check if CBP data is in your database

Usage:
    python verify_cbp_data.py
"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

def verify_cbp_data():
    """Check if CBP drug seizures data exists"""
    
    print("=" * 70)
    print("CBP DATA VERIFICATION")
    print("=" * 70)
    
    # Get database URL
    db_url = os.getenv('DATABASE_URL', 'postgresql://wcuser:password@localhost:5432/worldcup_intelligence')
    
    try:
        # Connect to database
        engine = create_engine(db_url, echo=False)
        
        with engine.connect() as conn:
            # Check if table exists
            table_check = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public'
                    AND table_name = 'cbp_drug_seizures'
                )
            """)).scalar()
            
            if not table_check:
                print("\n❌ ERROR: Table 'cbp_drug_seizures' does NOT exist!")
                print("\n🔧 Solution:")
                print("   1. Run: python scripts/create_cbp_table.py")
                print("   2. Then: python scripts/load_cbp_drug_data.py data/cbp/*.csv")
                return False
            
            print("\n✅ Table exists")
            
            # Get record count
            count_result = conn.execute(text("SELECT COUNT(*) FROM cbp_drug_seizures"))
            total_records = count_result.scalar()
            
            print(f"📊 Total records: {total_records:,}")
            
            if total_records == 0:
                print("\n⚠️  WARNING: Table is EMPTY!")
                print("\n🔧 Solution:")
                print("   Load data: python scripts/load_cbp_drug_data.py data/cbp/*.csv")
                return False
            
            # Get statistics
            stats_result = conn.execute(text("""
                SELECT COALESCE(SUM(event_count), 0) as total_events,
                       COALESCE(SUM(quantity_lbs), 0) as total_quantity
                FROM cbp_drug_seizures
            """))
            stats = stats_result.fetchone()
            
            total_events = int(stats[0])
            total_quantity = float(stats[1])
            
            print(f"📈 Total events: {total_events:,}")
            print(f"⚖️  Total quantity: {total_quantity:,.2f} lbs")
            
            # Check records with coordinates
            coords_result = conn.execute(text("""
                SELECT COUNT(*) FROM cbp_drug_seizures
                WHERE latitude IS NOT NULL AND longitude IS NOT NULL
            """))
            with_coords = coords_result.scalar()
            
            print(f"📍 Records with coordinates: {with_coords:,} ({with_coords/total_records*100:.1f}%)")
            
            if with_coords == 0:
                print("\n⚠️  WARNING: No records have coordinates!")
                print("\n🔧 Solution:")
                print("   Add geocoding: python scripts/add_geocoding_to_cbp.py")
                return False
            
            # Test the API query
            print("\n🧪 Testing API Query...")
            api_result = conn.execute(text("""
                SELECT COALESCE(SUM(event_count), 0) as total_events
                FROM cbp_drug_seizures
            """))
            api_total = int(api_result.fetchone()[0])
            
            print(f"✅ API will return: {api_total:,} total events")
            
            print("\n" + "=" * 70)
            print("✅ VERIFICATION COMPLETE - DATA IS READY!")
            print("=" * 70)
            print(f"\nYour Drug Seizures card should show: {total_events:,}")
            print("\nIf it still shows 0:")
            print("1. Apply the fixed api_routes.py")
            print("2. Restart Flask: python src/app.py")
            print("3. Clear browser cache (Ctrl+F5)")
            print("=" * 70)
            
            return True
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print("\n🔧 Troubleshooting:")
        print("1. Check if PostgreSQL is running")
        print("2. Verify DATABASE_URL in .env file")
        print("3. Test connection: psql -U wcuser -d worldcup_intelligence")
        return False


if __name__ == "__main__":
    verify_cbp_data()