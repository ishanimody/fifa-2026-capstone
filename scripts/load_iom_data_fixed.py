"""
Load IOM Missing Migrants Data into Database - FIXED VERSION

Place in: scripts/load_iom_data_fixed.py
"""

import sys
import os
sys.path.append('src')

import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.models import Base, DataSource, SmugglingIncident
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

def load_iom_data(csv_file='data/processed/iom_processed.csv', db_url=None):
    """Load IOM data from CSV into database"""
    
    if db_url is None:
        db_url = os.getenv('DATABASE_URL', 'sqlite:///worldcup_intelligence.db')
    
    print("=" * 60)
    print("LOADING IOM DATA INTO DATABASE (FIXED)")
    print("=" * 60)
    
    # Check if file exists
    if not os.path.exists(csv_file):
        print(f"✗ Error: File not found: {csv_file}")
        return
    
    # Read CSV
    print(f"\n1. Reading CSV file: {csv_file}")
    df = pd.read_csv(csv_file)
    print(f"   ✓ Loaded {len(df)} records")
    print(f"   Columns: {df.columns.tolist()}")
    
    # Filter out records without coordinates
    df_with_coords = df[df['latitude'].notna() & df['longitude'].notna()]
    print(f"   ✓ Records with coordinates: {len(df_with_coords)}")
    
    # Create database connection
    print(f"\n2. Connecting to database...")
    engine = create_engine(db_url, echo=False)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Get or create IOM data source
    print("\n3. Getting IOM data source...")
    iom_source = session.query(DataSource).filter_by(name='IOM Missing Migrants').first()
    if not iom_source:
        iom_source = DataSource(
            name='IOM Missing Migrants',
            url='https://missingmigrants.iom.int/',
            description='IOM Missing Migrants Project',
            data_type='incidents',
            update_frequency='weekly',
            is_active=True,
            last_updated=datetime.utcnow()
        )
        session.add(iom_source)
        session.commit()
    print(f"   ✓ Data source ID: {iom_source.id}")
    
    # Clear existing IOM incidents (optional - for clean reload)
    print("\n4. Clearing existing IOM incidents...")
    deleted = session.query(SmugglingIncident).filter_by(source_id=iom_source.id).delete()
    session.commit()
    print(f"   ✓ Deleted {deleted} old records")
    
    # Load incidents
    print(f"\n5. Loading {len(df_with_coords)} incidents into database...")
    
    loaded_count = 0
    error_count = 0
    
    for idx, row in df_with_coords.iterrows():
        try:
            # Helper function to truncate strings
            def safe_str(value, max_length=None):
                if pd.isna(value):
                    return None
                s = str(value)
                if max_length and len(s) > max_length:
                    return s[:max_length]
                return s
            
            # Parse the data correctly based on actual CSV columns
            incident = SmugglingIncident(
                incident_type='migration_incident',
                
                # Dates
                incident_date=pd.to_datetime(row['incident_date']) if pd.notna(row.get('incident_date')) else None,
                incident_year=int(row['incident_year']) if pd.notna(row.get('incident_year')) else None,
                incident_month=int(row['incident_month']) if pd.notna(row.get('incident_month')) else None,
                
                # Location - THESE ARE THE KEY FIELDS
                latitude=float(row['latitude']),
                longitude=float(row['longitude']),
                location_description=safe_str(row.get('Location of Incident'), max_length=500),
                country=safe_str(row.get('Country of Incident'), max_length=50),
                region=safe_str(row.get('Region of Incident'), max_length=100),
                
                # Casualties
                number_dead=int(row.get('Number of Dead', 0)) if pd.notna(row.get('Number of Dead')) else 0,
                number_missing=int(row.get('number_missing', 0)) if pd.notna(row.get('number_missing')) else 0,
                number_survivors=int(row.get('number_survivors', 0)) if pd.notna(row.get('number_survivors')) else 0,
                
                # Demographics
                migrant_origin_countries=safe_str(row.get('Country of Origin')),
                
                # Additional details
                cause_of_death=safe_str(row.get('cause_of_death'), max_length=200),
                route_description=safe_str(row.get('migration_route')),
                
                # Source
                source_id=iom_source.id,
                source_url=safe_str(row.get('URL'), max_length=500),
                source_quality=safe_str(row.get('Source Quality', 'unverified'), max_length=20),
                is_verified=False,
                
                # Store original data as JSON
                raw_data={
                    'incident_id': str(row.get('incident_id', '')),
                    'incident_type': str(row.get('Incident Type', '')),
                    'information_source': str(row.get('Information Source', ''))
                }
            )
            
            session.add(incident)
            loaded_count += 1
            
            # Commit in batches of 100
            if loaded_count % 100 == 0:
                session.commit()
                print(f"   Progress: {loaded_count}/{len(df_with_coords)} records loaded...", end='\r')
                
        except Exception as e:
            error_count += 1
            session.rollback()  # Rollback the failed transaction
            if error_count < 5:  # Show first 5 errors
                print(f"\n   ⚠ Error loading row {idx}: {e}")
    
    # Final commit
    session.commit()
    
    print(f"\n   ✓ Loaded {loaded_count} records successfully")
    if error_count > 0:
        print(f"   ⚠ {error_count} records had errors")
    
    # Update data source timestamp
    iom_source.last_updated = datetime.utcnow()
    session.commit()
    
    # Verify data
    print("\n6. Verifying loaded data:")
    total_incidents = session.query(SmugglingIncident).count()
    with_coords = session.query(SmugglingIncident).filter(
        SmugglingIncident.latitude.isnot(None),
        SmugglingIncident.longitude.isnot(None)
    ).count()
    
    print(f"   - Total incidents in database: {total_incidents}")
    print(f"   - Incidents with coordinates: {with_coords}")
    
    # Show sample
    sample = session.query(SmugglingIncident).filter(
        SmugglingIncident.latitude.isnot(None)
    ).first()
    
    if sample:
        print(f"\n   Sample incident:")
        print(f"   - Date: {sample.incident_date}")
        print(f"   - Location: ({sample.latitude}, {sample.longitude})")
        print(f"   - Country: {sample.country}")
        print(f"   - Dead: {sample.number_dead}, Missing: {sample.number_missing}")
    
    session.close()
    
    print("\n" + "=" * 60)
    print("✓ DATA LOADING COMPLETE!")
    print("=" * 60)
    print(f"\nDatabase: {db_url.split('@')[1] if '@' in db_url else db_url}")
    print(f"Records loaded: {loaded_count}")
    print(f"Records with coordinates: {with_coords}")
    print("\nNext steps:")
    print("1. Run: python scripts/run_analysis.py (to analyze the data)")
    print("=" * 60)


if __name__ == "__main__":
    load_iom_data(
        csv_file='data/processed/iom_processed.csv'
    )