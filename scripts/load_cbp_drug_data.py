import sys
import os
sys.path.append('src')

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from models.models import Base
from datetime import datetime
from dotenv import load_dotenv
import glob
import re

load_dotenv()


def parse_fiscal_year(fy_string):
    """Parse fiscal year, handling '2025 (FYTD)' format"""
    if pd.isna(fy_string):
        return None
    
    # Convert to string and extract just the year number
    fy_str = str(fy_string).strip()
    
    # Extract first 4-digit number
    match = re.search(r'(\d{4})', fy_str)
    if match:
        return int(match.group(1))
    
    return None


def load_cbp_drug_data(files):
    """Load CBP drug seizure data from CSV files"""
    
    db_url = os.getenv('DATABASE_URL', 'sqlite:///worldcup_intelligence.db')
    engine = create_engine(db_url, echo=False)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Create table if it doesn't exist
    from sqlalchemy import Column, Integer, String, Float, DateTime, Index
    from sqlalchemy.ext.declarative import declarative_base
    
    print("=" * 80)
    print("LOADING CBP DRUG SEIZURE DATA")
    print("=" * 80)
    
    # Check if table exists, if not create it
    # Check if table exists
    from sqlalchemy import inspect
    inspector = inspect(engine)
    if 'cbp_drug_seizures' not in inspector.get_table_names():
        session.execute(text("""
            CREATE TABLE cbp_drug_seizures (
                id SERIAL PRIMARY KEY,
                fiscal_year INTEGER,
                month VARCHAR(20),
                component VARCHAR(100),
                region VARCHAR(100),
                land_filter VARCHAR(100),
                area_of_responsibility VARCHAR(200),
                drug_type VARCHAR(100),
                event_count INTEGER,
                quantity_lbs FLOAT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(fiscal_year, month, component, area_of_responsibility, drug_type)
            )
        """))
        session.commit()
        print("✓ Table created: cbp_drug_seizures")
    
    print(f"\nFound {len(files)} files to process:")
    for f in files:
        print(f"  - {os.path.basename(f)}")
    
    total_loaded = 0
    total_duplicates = 0
    total_errors = 0
    total_rows = 0
    
    for filepath in files:
        print(f"\n{'='*80}")
        print(f"Processing: {os.path.basename(filepath)}")
        print(f"{'='*80}")
        
        try:
            df = pd.read_csv(filepath)
            print(f"  Rows in file: {len(df)}")
            total_rows += len(df)
            
            file_loaded = 0
            file_duplicates = 0
            file_errors = 0
            
            for idx, row in df.iterrows():
                try:
                    # Parse fiscal year
                    fy = parse_fiscal_year(row.get('FY'))
                    
                    if fy is None:
                        file_errors += 1
                        if file_errors <= 3:
                            print(f"\n    ⚠ Error on row {idx}: Could not parse fiscal year: {row.get('FY')}")
                        continue
                    
                    # Check for duplicate
                    existing = session.execute(text("""
                        SELECT COUNT(*) FROM cbp_drug_seizures 
                        WHERE fiscal_year = :fy 
                        AND month = :month 
                        AND component = :component 
                        AND area_of_responsibility = :area 
                        AND drug_type = :drug
                    """), {
                        'fy': fy,
                        'month': str(row.get('Month (abbv)', '')),
                        'component': str(row.get('Component', '')),
                        'area': str(row.get('Area of Responsibility', '')),
                        'drug': str(row.get('Drug Type', ''))
                    }).scalar()
                    
                    if existing > 0:
                        file_duplicates += 1
                        continue
                    
                    # Insert record
                    session.execute(text("""
                        INSERT INTO cbp_drug_seizures 
                        (fiscal_year, month, component, region, land_filter, 
                         area_of_responsibility, drug_type, event_count, quantity_lbs)
                        VALUES (:fy, :month, :component, :region, :land_filter,
                                :area, :drug, :events, :qty)
                    """), {
                        'fy': fy,
                        'month': str(row.get('Month (abbv)', '')),
                        'component': str(row.get('Component', '')),
                        'region': str(row.get('Region', '')),
                        'land_filter': str(row.get('Land Filter', '')),
                        'area': str(row.get('Area of Responsibility', '')),
                        'drug': str(row.get('Drug Type', '')),
                        'events': int(row.get('Count of Event', 0)) if pd.notna(row.get('Count of Event')) else 0,
                        'qty': float(row.get('Sum Qty (lbs)', 0)) if pd.notna(row.get('Sum Qty (lbs)')) else 0.0
                    })
                    
                    file_loaded += 1
                    
                    if file_loaded % 100 == 0:
                        session.commit()
                        print(f"    Progress: {file_loaded} records loaded...", end='\r')
                
                except Exception as e:
                    file_errors += 1
                    if file_errors <= 3:
                        print(f"\n    ⚠ Error on row {idx}: {e}")
                    continue
            
            session.commit()
            
            print(f"\n  ✓ File complete:")
            print(f"    - Loaded: {file_loaded}")
            print(f"    - Duplicates skipped: {file_duplicates}")
            print(f"    - Errors: {file_errors}")
            
            total_loaded += file_loaded
            total_duplicates += file_duplicates
            total_errors += file_errors
            
        except Exception as e:
            print(f"  ✗ Error processing file: {e}")
            continue
    
    # Summary
    print(f"\n{'='*80}")
    print("LOADING SUMMARY")
    print(f"{'='*80}")
    print(f"Total rows processed: {total_rows:,}")
    print(f"Total records loaded: {total_loaded:,}")
    print(f"Total duplicates skipped: {total_duplicates:,}")
    print(f"Total errors: {total_errors:,}")
    
    # Get total count
    total_count = session.execute(text("SELECT COUNT(*) FROM cbp_drug_seizures")).scalar()
    print(f"\nTotal CBP records in database: {total_count:,}")
    
    # Breakdown by year
    print(f"\nBreakdown by Year:")
    years = session.execute(text("""
        SELECT fiscal_year, COUNT(*) as count, SUM(quantity_lbs) as total_lbs
        FROM cbp_drug_seizures 
        GROUP BY fiscal_year 
        ORDER BY fiscal_year
    """)).fetchall()
    
    for year, count, lbs in years:
        print(f"  FY{year}: {count:,} records, {lbs:,.2f} lbs seized")
    
    # Top drug types
    print(f"\nTop 5 Drug Types:")
    drugs = session.execute(text("""
        SELECT drug_type, SUM(quantity_lbs) as total_lbs
        FROM cbp_drug_seizures 
        GROUP BY drug_type 
        ORDER BY total_lbs DESC 
        LIMIT 5
    """)).fetchall()
    
    for drug, lbs in drugs:
        print(f"  {drug}: {lbs:,.2f} lbs")
    
    session.close()
    
    print(f"\n{'='*80}")
    print("✓ LOADING COMPLETE!")
    print(f"{'='*80}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/load_cbp_drug_data.py data/cbp/*.csv")
        sys.exit(1)
    
    # Get all CSV files from command line
    files = []
    for pattern in sys.argv[1:]:
        files.extend(glob.glob(pattern))
    
    if not files:
        print("No CSV files found!")
        sys.exit(1)
    
    load_cbp_drug_data(files)