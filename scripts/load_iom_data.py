"""
Load IOM Missing Migrants Data into Database

Run this script to load processed IOM data into the database:
python scripts/load_iom_data.py

Place in: scripts/load_iom_data.py
"""

import sys
import os
sys.path.append('src')

import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.models import Base, DataSource, SmugglingIncident
from datetime import datetime

def load_iom_data(csv_file='data/processed/iom_processed.csv', db_url=None):
    """
    Load IOM data from CSV into database
    
    Args:
        csv_file: Path to processed CSV file
        db_url: Database connection string
    """
    print("=" * 60)
    print("LOADING IOM DATA INTO DATABASE")
    print("=" * 60)
    
    # Check if file exists
    if not os.path.exists(csv_file):
        print(f"✗ Error: File not found: {csv_file}")
        print("\nPlease run: python scripts/process_iom_data.py first")
        return
    
    # Read CSV
    print(f"\n1. Reading CSV file: {csv_file}")
    df = pd.read_csv(csv_file)
    print(f"   ✓ Loaded {len(df)} records")
    
    # Create database connection
    print(f"\n2. Connecting to database: {db_url}")
    engine = create_engine(db_url, echo=False)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Get or create IOM data source
    print("\n3. Getting IOM data source...")
    iom_source = session.query(DataSource).filter_by(name='IOM Missing Migrants').first()
    if not iom_source:
        print("   Creating IOM data source...")
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
    
    # Load incidents
    print(f"\n4. Loading {len(df)} incidents into database...")
    
    loaded_count = 0
    error_count = 0
    
    for idx, row in df.iterrows():
        try:
            # Create incident object
            incident = SmugglingIncident(
                incident_type='migration_incident',
                incident_date=pd.to_datetime(row.get('incident_date')) if pd.notna(row.get('incident_date')) else None,
                incident_year=int(row.get('incident_year')) if pd.notna(row.get('incident_year')) else None,
                incident_month=int(row.get('incident_month')) if pd.notna(row.get('incident_month')) else None,
                
                # Location
                latitude=float(row.get('latitude')) if pd.notna(row.get('latitude')) else None,
                longitude=float(row.get('longitude')) if pd.notna(row.get('longitude')) else None,
                location_description=str(row.get('location_description')) if pd.notna(row.get('location_description')) else None,
                country=str(row.get('Region of Incident', '')) if pd.notna(row.get('Region of Incident')) else None,
                
                # Casualties
                number_dead=int(row.get('number_dead', 0)) if pd.notna(row.get('number_dead')) else 0,
                number_missing=int(row.get('number_missing', 0)) if pd.notna(row.get('number_missing')) else 0,
                number_survivors=int(row.get('number_survivors', 0)) if pd.notna(row.get('number_survivors')) else 0,
                
                # Additional details
                cause_of_death=str(row.get('cause_of_death')) if pd.notna(row.get('cause_of_death')) else None,
                migrant_origin_countries=str(row.get('origin_region')) if pd.notna(row.get('origin_region')) else None,
                
                # Source
                source_id=iom_source.id,
                source_quality=str(row.get('source_quality', 'unverified')),
                is_verified=False,
                
                # Store original data as JSON
                raw_data=row.to_dict()
            )
            
            session.add(incident)
            loaded_count += 1
            
            # Commit in batches of 100
            if loaded_count % 100 == 0:
                session.commit()
                print(f"   Progress: {loaded_count}/{len(df)} records loaded...", end='\r')
                
        except Exception as e:
            error_count += 1
            if error_count < 5:  # Show first 5 errors
                print(f"\n   ⚠ Error loading row {idx}: {e}")
    
    # Final commit
    session.commit()
    
    # Update data source timestamp
    iom_source.last_updated = datetime.utcnow()
    session.commit()
    
    print(f"\n   ✓ Loaded {loaded_count} records successfully")
    if error_count > 0:
        print(f"   ⚠ {error_count} records had errors")
    
    # Show summary
    print("\n5. Database Summary:")
    total_incidents = session.query(SmugglingIncident).count()
    print(f"   - Total incidents in database: {total_incidents}")
    
    # Show some statistics
    if total_incidents > 0:
        total_dead = session.query(SmugglingIncident).with_entities(
            SmugglingIncident.number_dead
        ).all()
        total_missing = session.query(SmugglingIncident).with_entities(
            SmugglingIncident.number_missing
        ).all()
        
        print(f"   - Total casualties (dead): {sum([x[0] for x in total_dead if x[0]])}")
        print(f"   - Total missing: {sum([x[0] for x in total_missing if x[0]])}")
    
    session.close()
    
    print("\n" + "=" * 60)
    print("✓ DATA LOADING COMPLETE!")
    print("=" * 60)
    print(f"\nDatabase: {db_url}")
    print(f"Records loaded: {loaded_count}")
    print("\nNext steps:")
    print("1. Run: python scripts/query_database.py (to test queries)")
    print("2. Start building the visualization!")
    print("=" * 60)


if __name__ == "__main__":
    # Load IOM data
    load_iom_data(
        csv_file='data/processed/iom_processed.csv',
        db_url='sqlite:///worldcup_intelligence.db'
    )