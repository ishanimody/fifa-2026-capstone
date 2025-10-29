"""
Load IOM Missing Migrants Data into Database - FIXED VERSION

Run this script to load processed IOM data into the database:
python load_iom_data.py

Place in: scripts/load_iom_data.py
"""

import sys
import os

# Add the src directory to the path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
src_dir = os.path.join(project_root, 'src')
sys.path.insert(0, src_dir)

import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.models import Base, DataSource, SmugglingIncident
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def load_iom_data(csv_file=None, db_url=None):
    """
    Load IOM data from CSV into database
    
    Args:
        csv_file: Path to processed CSV file
        db_url: Database connection string
    """
    print("=" * 60)
    print("LOADING IOM DATA INTO DATABASE")
    print("=" * 60)
    
    # Determine which file to use
    if csv_file is None:
        # Try Americas filtered file first, then full processed
        possible_files = [
            'data/processed/iom_americas_filtered.csv',
            'data/processed/iom_processed.csv',
            '../data/processed/iom_americas_filtered.csv',
            '../data/processed/iom_processed.csv',
        ]
        
        for filepath in possible_files:
            if os.path.exists(filepath):
                csv_file = filepath
                break
        
        if csv_file is None:
            print("\n❌ Error: No processed IOM file found!")
            print("\nLooked in:")
            for fp in possible_files:
                print(f"  - {fp}")
            print("\nPlease run one of these first:")
            print("  python setup_iom_americas.py")
            print("  python scripts/process_iom_data.py")
            return False
    
    # Check if file exists
    if not os.path.exists(csv_file):
        print(f"❌ Error: File not found: {csv_file}")
        return False
    
    # Read CSV
    print(f"\n1. Reading CSV file: {csv_file}")
    df = pd.read_csv(csv_file)
    print(f"   ✓ Loaded {len(df):,} records")
    
    # Show what regions are included
    if 'region_of_incident' in df.columns:
        regions = df['region_of_incident'].value_counts()
        print(f"\n   Regions in file:")
        for region, count in regions.head(5).items():
            print(f"     - {region}: {count:,} records")
        if len(regions) > 5:
            print(f"     ... and {len(regions) - 5} more")
    
    # Get database URL
    if db_url is None:
        db_url = os.getenv('DATABASE_URL', 'sqlite:///worldcup_intelligence.db')
    
    # Create database connection
    print(f"\n2. Connecting to database...")
    try:
        engine = create_engine(db_url, echo=False)
        Session = sessionmaker(bind=engine)
        session = Session()
        print(f"   ✓ Connected to database")
    except Exception as e:
        print(f"   ❌ Database connection failed: {e}")
        return False
    
    # Get or create IOM data source
    print("\n3. Setting up IOM data source...")
    try:
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
    except Exception as e:
        print(f"   ❌ Error setting up data source: {e}")
        session.rollback()
        return False
    
    # Ask about clearing old data
    print(f"\n4. Checking existing IOM data...")
    try:
        existing_count = session.query(SmugglingIncident).filter_by(
            source_id=iom_source.id
        ).count()
        
        if existing_count > 0:
            print(f"   Found {existing_count:,} existing IOM records")
            response = input("\n   Clear existing data before loading? (yes/no) [yes]: ").strip().lower()
            
            if response in ['', 'yes', 'y']:
                print(f"   Deleting {existing_count:,} old records...")
                session.query(SmugglingIncident).filter_by(
                    source_id=iom_source.id
                ).delete()
                session.commit()
                print(f"   ✓ Deleted old records")
            else:
                print(f"   Keeping existing data (may create duplicates!)")
        else:
            print(f"   No existing IOM data found")
    except Exception as e:
        print(f"   ⚠️  Warning: Could not check existing data: {e}")
    
    # Load incidents
    print(f"\n5. Loading {len(df):,} incidents into database...")
    
    loaded_count = 0
    error_count = 0
    
    try:
        for idx, row in df.iterrows():
            try:
                # Prepare incident data
                incident_data = {
                    'incident_type': 'migration_incident',
                    'source_id': iom_source.id,
                    'source_quality': str(row.get('source_quality', 'unverified'))[:20],
                    'is_verified': False,
                }
                
                # Add date fields
                if 'incident_date' in row and pd.notna(row['incident_date']):
                    try:
                        incident_data['incident_date'] = pd.to_datetime(row['incident_date'])
                    except:
                        pass
                
                if 'incident_year' in row and pd.notna(row['incident_year']):
                    incident_data['incident_year'] = int(row['incident_year'])
                
                if 'incident_month' in row and pd.notna(row['incident_month']):
                    incident_data['incident_month'] = int(row['incident_month'])
                
                # Add location fields
                for field in ['latitude', 'longitude']:
                    if field in row and pd.notna(row[field]):
                        incident_data[field] = float(row[field])
                
                for field in ['location_description']:
                    if field in row and pd.notna(row[field]):
                        incident_data[field] = str(row[field])[:500]
                
                # Country/region - try different column names
                country_val = None
                for col in ['region_of_incident', 'Region of Incident', 'country', 'Country']:
                    if col in row and pd.notna(row[col]):
                        country_val = str(row[col])[:50]
                        break
                if country_val:
                    incident_data['country'] = country_val
                
                # Add casualty fields
                for field in ['number_dead', 'number_missing', 'number_survivors']:
                    if field in row and pd.notna(row[field]):
                        incident_data[field] = int(row[field])
                
                # Add other fields
                for field in ['cause_of_death']:
                    if field in row and pd.notna(row[field]):
                        incident_data[field] = str(row[field])[:200]
                
                for field in ['origin_region']:
                    if field in row and pd.notna(row[field]):
                        incident_data['migrant_origin_countries'] = str(row[field])[:200]
                
                # Create incident
                incident = SmugglingIncident(**incident_data)
                session.add(incident)
                loaded_count += 1
                
                # Commit in batches
                if loaded_count % 100 == 0:
                    session.commit()
                    print(f"   Progress: {loaded_count:,}/{len(df):,} records...", end='\r')
                    
            except Exception as e:
                error_count += 1
                if error_count <= 3:  # Show first 3 errors
                    print(f"\n   ⚠️  Error on row {idx}: {e}")
        
        # Final commit
        session.commit()
        
        print(f"\n   ✓ Loaded {loaded_count:,} records successfully")
        if error_count > 0:
            print(f"   ⚠️  {error_count} records had errors (skipped)")
    
    except Exception as e:
        print(f"\n   ❌ Error during loading: {e}")
        session.rollback()
        return False
    
    # Update data source timestamp
    try:
        iom_source.last_updated = datetime.utcnow()
        session.commit()
    except:
        pass
    
    # Show summary
    print("\n6. Database Summary:")
    try:
        total_incidents = session.query(SmugglingIncident).count()
        iom_incidents = session.query(SmugglingIncident).filter_by(
            source_id=iom_source.id
        ).count()
        
        print(f"   - Total incidents in database: {total_incidents:,}")
        print(f"   - IOM incidents: {iom_incidents:,}")
        
        # Show some statistics
        if iom_incidents > 0:
            from sqlalchemy import func
            
            total_dead = session.query(
                func.sum(SmugglingIncident.number_dead)
            ).filter_by(source_id=iom_source.id).scalar() or 0
            
            total_missing = session.query(
                func.sum(SmugglingIncident.number_missing)
            ).filter_by(source_id=iom_source.id).scalar() or 0
            
            print(f"   - Total casualties (dead): {int(total_dead):,}")
            print(f"   - Total missing: {int(total_missing):,}")
    except Exception as e:
        print(f"   ⚠️  Could not generate summary: {e}")
    
    session.close()
    
    print("\n" + "=" * 60)
    print("✅ DATA LOADING COMPLETE!")
    print("=" * 60)
    print(f"\nLoaded: {loaded_count:,} IOM incidents")
    print(f"File: {csv_file}")
    print("\n📋 Next steps:")
    print("1. Start Flask: python src/app.py")
    print("2. View map: http://127.0.0.1:5000/map")
    print("3. Check statistics: http://127.0.0.1:5000/api/statistics")
    print("=" * 60)
    
    return True


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Load IOM data into database')
    parser.add_argument(
        '--file',
        help='CSV file to load (default: auto-detect)',
        default=None
    )
    parser.add_argument(
        '--db',
        help='Database URL (default: from .env or SQLite)',
        default=None
    )
    
    args = parser.parse_args()
    
    try:
        success = load_iom_data(csv_file=args.file, db_url=args.db)
        if not success:
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)