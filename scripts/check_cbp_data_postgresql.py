import sys
sys.path.append('src')

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

def check_cbp_data():
    """Check CBP drug seizures data in PostgreSQL database"""
    
    print("=" * 70)
    print("CBP DRUG SEIZURES DATABASE DIAGNOSTIC (PostgreSQL)")
    print("=" * 70)
    
    # Get database URL
    db_url = os.getenv('DATABASE_URL', 'postgresql://wcuser:password@localhost:5432/worldcup_intelligence')
    
    # Hide password in display
    display_url = db_url.split('@')[1] if '@' in db_url else db_url
    print(f"\n1. Database: {display_url}")
    
    try:
        # Create engine and session
        engine = create_engine(db_url, echo=False)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Check if table exists (PostgreSQL syntax)
        print("\n2. Checking if cbp_drug_seizures table exists...")
        result = session.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public'
                AND table_name = 'cbp_drug_seizures'
            )
        """)).scalar()
        
        if not result:
            print("   ❌ ERROR: Table 'cbp_drug_seizures' does NOT exist!")
            print("\n   📝 Solution:")
            print("   Run: python scripts/create_cbp_table.py")
            session.close()
            return False
        
        print("   ✓ Table exists")
        
        # Count total records
        print("\n3. Counting CBP records...")
        total_count = session.execute(text("""
            SELECT COUNT(*) FROM cbp_drug_seizures
        """)).scalar()
        
        print(f"   Total Records: {total_count:,}")
        
        if total_count == 0:
            print("\n   ⚠️  WARNING: Table is EMPTY!")
            print("\n   📝 Solution:")
            print("   1. Make sure you have CBP CSV files in data/cbp/ directory")
            print("   2. Run: python scripts/load_cbp_drug_data.py data/cbp/*.csv")
            session.close()
            return False
        
        # Get statistics
        print("\n4. CBP Statistics:")
        
        # Total events
        total_events = session.execute(text("""
            SELECT SUM(event_count) FROM cbp_drug_seizures
        """)).scalar() or 0
        print(f"   Total Events: {int(total_events):,}")
        
        # Total quantity
        total_lbs = session.execute(text("""
            SELECT SUM(quantity_lbs) FROM cbp_drug_seizures
        """)).scalar() or 0
        print(f"   Total Quantity: {float(total_lbs):,.2f} lbs")
        
        # Records with coordinates
        with_coords = session.execute(text("""
            SELECT COUNT(*) FROM cbp_drug_seizures
            WHERE latitude IS NOT NULL AND longitude IS NOT NULL
        """)).scalar()
        print(f"   Records with Coordinates: {with_coords:,}")
        
        # Breakdown by year
        print("\n5. Breakdown by Fiscal Year:")
        years = session.execute(text("""
            SELECT fiscal_year, COUNT(*) as count, SUM(event_count) as events
            FROM cbp_drug_seizures
            GROUP BY fiscal_year
            ORDER BY fiscal_year DESC
        """)).fetchall()
        
        if years:
            for year, count, events in years:
                print(f"   FY {year}: {count:,} records, {int(events):,} events")
        else:
            print("   (No data)")
        
        # Top drug types
        print("\n6. Top 5 Drug Types (by events):")
        top_drugs = session.execute(text("""
            SELECT drug_type, SUM(event_count) as events
            FROM cbp_drug_seizures
            GROUP BY drug_type
            ORDER BY events DESC
            LIMIT 5
        """)).fetchall()
        
        if top_drugs:
            for drug, events in top_drugs:
                print(f"   {drug}: {int(events):,} events")
        else:
            print("   (No data)")
        
        # Top field offices
        print("\n7. Top 5 Field Offices (by events):")
        top_offices = session.execute(text("""
            SELECT area_of_responsibility, SUM(event_count) as events
            FROM cbp_drug_seizures
            WHERE area_of_responsibility IS NOT NULL
            GROUP BY area_of_responsibility
            ORDER BY events DESC
            LIMIT 5
        """)).fetchall()
        
        if top_offices:
            for office, events in top_offices:
                print(f"   {office}: {int(events):,} events")
        else:
            print("   (No data)")
        
        # Test the API endpoint data
        print("\n8. Simulating API Response:")
        print(f"""
   Expected /api/cbp-statistics response:
   {{
       "success": true,
       "statistics": {{
           "total_records": {total_count},
           "total_events": {int(total_events)},
           "total_quantity_lbs": {float(total_lbs):.2f},
           "top_drugs": [...],
           "top_offices": [...]
       }}
   }}
        """)
        
        session.close()
        
        print("\n" + "=" * 70)
        print("✓ DIAGNOSTIC COMPLETE - CBP DATA IS LOADED!")
        print("=" * 70)
        print(f"\nThe Drug Seizures display should show: {int(total_events):,}")
        print("\nIf it still shows '-', check:")
        print("1. Flask server is running: python src/app.py")
        print("2. Browser console (F12) for API errors")
        print("3. Try: http://127.0.0.1:5000/api/cbp-statistics")
        print("=" * 70)
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print("\nTroubleshooting:")
        print("1. Check if PostgreSQL is running")
        print("   Windows: Check Services or run 'pg_ctl status'")
        print("   Check: Task Manager -> Services -> postgresql")
        print("\n2. Verify DATABASE_URL in .env file")
        print("   Should be: postgresql://username:password@localhost:5432/worldcup_intelligence")
        print("\n3. Test connection:")
        print("   psql -U wcuser -d worldcup_intelligence")
        print("\n4. Check if database exists:")
        print("   psql -U postgres -c '\\l' | grep worldcup")
        return False


if __name__ == "__main__":
    check_cbp_data()