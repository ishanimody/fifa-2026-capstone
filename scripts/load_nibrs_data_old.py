"""
Load NIBRS Crime Data into Database

This script loads FBI NIBRS crime statistics and geocodes agencies
for integration with World Cup 2026 venue security analysis.

Place in: scripts/load_nibrs_data.py

Usage:
    python scripts/load_nibrs_data.py [path_to_nibrs_csv]
"""

import sys
import os
sys.path.append('src')

import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from dotenv import load_dotenv
import re

load_dotenv()


def clean_column_name(col):
    """Clean column names from CSV (remove newlines and extra spaces)"""
    return col.replace('\n', ' ').strip()


def extract_city_from_agency(agency_name):
    """
    Extract city name from agency name
    E.g., "Apache Junction" from "Apache Junction Police Department"
    """
    if not agency_name or pd.isna(agency_name):
        return None
    
    agency_name = str(agency_name).strip()
    
    # Remove common suffixes
    suffixes = [
        r' Police Department$', r' PD$', r" Sheriff's Office$", r' Sheriff Office$',
        r' Sheriff$', r' Police$', r' Dept\.?$', r' Department$', 
        r' City$', r' Town$', r' Village$', r' Borough$', r' Township$',
        r' County$', r' Metro$', r' Metropolitan$'
    ]
    
    city = agency_name
    for suffix in suffixes:
        city = re.sub(suffix, '', city, flags=re.IGNORECASE).strip()
    
    return city if city and len(city) > 1 else None


def load_nibrs_data(csv_file, db_url=None):
    """
    Load NIBRS data from CSV into database
    
    Args:
        csv_file: Path to NIBRS CSV file
        db_url: Database URL (optional, uses .env if not provided)
    """
    
    print("=" * 80)
    print("LOADING FBI NIBRS CRIME DATA")
    print("=" * 80)
    
    # Check if file exists
    if not os.path.exists(csv_file):
        print(f"\n❌ ERROR: File not found: {csv_file}")
        return False
    
    # Get database URL
    if db_url is None:
        db_url = os.getenv('DATABASE_URL', 'postgresql://wcuser:password@localhost:5432/worldcup_intelligence')
    
    print(f"\n1. Reading CSV file: {csv_file}")
    
    try:
        # Read CSV
        df = pd.read_csv(csv_file)
        print(f"   ✓ Loaded {len(df):,} records")
        print(f"   ✓ Columns: {len(df.columns)}")
        
        # Clean column names
        df.columns = [clean_column_name(col) for col in df.columns]
        
        # Show sample
        print(f"\n2. Data Preview:")
        print(f"   Years: {df['year'].min()} - {df['year'].max()}")
        print(f"   States: {df['state'].nunique()} unique")
        print(f"   Agencies: {df['agency name'].nunique():,} unique")
        
        # Extract cities from agency names
        print(f"\n3. Extracting cities from agency names...")
        df['city'] = df['agency name'].apply(extract_city_from_agency)
        cities_extracted = df['city'].notna().sum()
        print(f"   ✓ Extracted {cities_extracted:,} cities ({cities_extracted/len(df)*100:.1f}%)")
        
        # Show top cities
        top_cities = df[df['city'].notna()]['city'].value_counts().head(5)
        print(f"\n   Top cities:")
        for city, count in top_cities.items():
            print(f"     - {city}: {count} records")
        
    except Exception as e:
        print(f"   ❌ Error reading CSV: {e}")
        return False
    
    # Connect to database
    print(f"\n4. Connecting to database...")
    
    try:
        engine = create_engine(db_url, echo=False)
        Session = sessionmaker(bind=engine)
        session = Session()
        print(f"   ✓ Connected to database")
    except Exception as e:
        print(f"   ❌ Database connection failed: {e}")
        return False
    
    # Create table if it doesn't exist
    print(f"\n5. Creating NIBRS table...")
    
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS nibrs_crime_data (
        id SERIAL PRIMARY KEY,
        year INTEGER NOT NULL,
        state VARCHAR(50) NOT NULL,
        agency_type VARCHAR(100),
        agency_name VARCHAR(200) NOT NULL,
        
        city VARCHAR(100),
        latitude FLOAT,
        longitude FLOAT,
        
        total_offenses INTEGER DEFAULT 0,
        crimes_against_persons INTEGER DEFAULT 0,
        crimes_against_property INTEGER DEFAULT 0,
        crimes_against_society INTEGER DEFAULT 0,
        
        assault_offenses INTEGER DEFAULT 0,
        aggravated_assault INTEGER DEFAULT 0,
        simple_assault INTEGER DEFAULT 0,
        intimidation INTEGER DEFAULT 0,
        
        homicide_offenses INTEGER DEFAULT 0,
        murder_nonnegligent_manslaughter INTEGER DEFAULT 0,
        negligent_manslaughter INTEGER DEFAULT 0,
        justifiable_homicide INTEGER DEFAULT 0,
        
        human_trafficking_offenses INTEGER DEFAULT 0,
        commercial_sex_acts INTEGER DEFAULT 0,
        involuntary_servitude INTEGER DEFAULT 0,
        
        kidnapping_abduction INTEGER DEFAULT 0,
        
        sex_offenses INTEGER DEFAULT 0,
        rape INTEGER DEFAULT 0,
        sodomy INTEGER DEFAULT 0,
        sexual_assault_with_object INTEGER DEFAULT 0,
        
        arson INTEGER DEFAULT 0,
        burglary INTEGER DEFAULT 0,
        larceny_theft INTEGER DEFAULT 0,
        motor_vehicle_theft INTEGER DEFAULT 0,
        robbery INTEGER DEFAULT 0,
        vandalism INTEGER DEFAULT 0,
        
        drug_narcotic_offenses INTEGER DEFAULT 0,
        drug_violations INTEGER DEFAULT 0,
        drug_equipment_violations INTEGER DEFAULT 0,
        
        gambling_offenses INTEGER DEFAULT 0,
        prostitution_offenses INTEGER DEFAULT 0,
        
        weapons_violations INTEGER DEFAULT 0,
        fraud_offenses INTEGER DEFAULT 0,
        identity_theft INTEGER DEFAULT 0,
        
        violent_crime_rate FLOAT,
        property_crime_rate FLOAT,
        overall_risk_score FLOAT,
        
        data_source VARCHAR(200) DEFAULT 'FBI NIBRS',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE INDEX IF NOT EXISTS idx_nibrs_year_state ON nibrs_crime_data(year, state);
    CREATE INDEX IF NOT EXISTS idx_nibrs_location ON nibrs_crime_data(latitude, longitude);
    CREATE INDEX IF NOT EXISTS idx_nibrs_agency ON nibrs_crime_data(agency_name, year);
    CREATE INDEX IF NOT EXISTS idx_nibrs_city ON nibrs_crime_data(city, state);
    """
    
    try:
        with engine.connect() as conn:
            conn.execute(text(create_table_sql))
            conn.commit()
        print(f"   ✓ Table created/verified")
    except Exception as e:
        print(f"   ⚠️  Table may already exist: {e}")
    
    # Ask about clearing existing data
    print(f"\n6. Checking existing NIBRS data...")
    
    try:
        existing_count = session.execute(text(
            "SELECT COUNT(*) FROM nibrs_crime_data"
        )).scalar()
        
        if existing_count > 0:
            print(f"   Found {existing_count:,} existing records")
            response = input("\n   Clear existing data? (yes/no) [no]: ").strip().lower()
            
            if response in ['yes', 'y']:
                print(f"   Deleting existing records...")
                session.execute(text("DELETE FROM nibrs_crime_data"))
                session.commit()
                print(f"   ✓ Cleared existing data")
            else:
                print(f"   Keeping existing data")
        else:
            print(f"   No existing data found")
    except Exception as e:
        print(f"   ⚠️  Could not check existing data: {e}")
    
    # Load data
    print(f"\n7. Loading {len(df):,} records into database...")
    
    loaded_count = 0
    error_count = 0
    
    # Column mapping from CSV to database (COMPLETE MAPPING)
    column_map = {
        # Basic categories
        'total offenses': 'total_offenses',
        'crimes against persons': 'crimes_against_persons',
        'crimes against property': 'crimes_against_property',
        'crimes against society': 'crimes_against_society',
        
        # Assault
        'assault offenses': 'assault_offenses',
        'aggravated assault': 'aggravated_assault',
        'simple assault': 'simple_assault',
        'intimidation': 'intimidation',
        
        # Homicide
        'homicide offenses': 'homicide_offenses',
        'murder and nonnegligent manslaughter': 'murder_nonnegligent_manslaughter',
        'negligent man- slaughter': 'negligent_manslaughter',
        'justifiable homicide': 'justifiable_homicide',
        
        # Human Trafficking
        'human trafficking offenses': 'human_trafficking_offenses',
        'commercial sex acts': 'commercial_sex_acts',
        'involuntary servitude': 'involuntary_servitude',
        
        # Kidnapping
        'kidnapping  abduction': 'kidnapping_abduction',
        
        # Sex Offenses
        'sex offenses': 'sex_offenses',
        'rape': 'rape',
        'sodomy': 'sodomy',
        'sexual assault with an object': 'sexual_assault_with_object',
        
        # Property Crimes
        'arson': 'arson',
        'burglary  breaking  entering': 'burglary',
        'larceny  theft offenses': 'larceny_theft',
        'motor vehicle theft': 'motor_vehicle_theft',
        'robbery': 'robbery',
        'destruction  damage  vandalism of property': 'vandalism',
        
        # Drug Crimes
        'drug  narcotic offenses': 'drug_narcotic_offenses',
        'drug  narcotic violations': 'drug_violations',
        'drug equipment violations': 'drug_equipment_violations',
        
        # Other Crimes
        'gambling offenses': 'gambling_offenses',
        'pros- titution offenses': 'prostitution_offenses',
        'weapon law violations': 'weapons_violations',
        'fraud offenses': 'fraud_offenses',
        'identity  theft': 'identity_theft',
    }
    
    try:
        for idx, row in df.iterrows():
            try:
                # Build insert data with defaults
                data = {
                    'year': int(row['year']),
                    'state': str(row['state']).strip().upper(),
                    'agency_type': str(row['agency type']) if pd.notna(row['agency type']) else None,
                    'agency_name': str(row['agency name']).strip(),
                    'city': row.get('city'),
                }
                
                # Initialize all crime statistics with 0 (in case CSV column is missing)
                all_crime_columns = [
                    'total_offenses', 'crimes_against_persons', 'crimes_against_property',
                    'crimes_against_society', 'assault_offenses', 'aggravated_assault',
                    'simple_assault', 'intimidation', 'homicide_offenses',
                    'murder_nonnegligent_manslaughter', 'negligent_manslaughter',
                    'justifiable_homicide', 'human_trafficking_offenses', 'commercial_sex_acts',
                    'involuntary_servitude', 'kidnapping_abduction', 'sex_offenses', 'rape',
                    'sodomy', 'sexual_assault_with_object', 'arson', 'burglary',
                    'larceny_theft', 'motor_vehicle_theft', 'robbery', 'vandalism',
                    'drug_narcotic_offenses', 'drug_violations', 'drug_equipment_violations',
                    'gambling_offenses', 'prostitution_offenses', 'weapons_violations',
                    'fraud_offenses', 'identity_theft'
                ]
                
                # Set defaults
                for col in all_crime_columns:
                    data[col] = 0
                
                # Add crime statistics from CSV (handle NaN and convert to int)
                for csv_col, db_col in column_map.items():
                    if csv_col in row.index:
                        val = row[csv_col]
                        data[db_col] = int(val) if pd.notna(val) and val != '' else 0
                
                # Insert record
                session.execute(text("""
                    INSERT INTO nibrs_crime_data (
                        year, state, agency_type, agency_name, city,
                        total_offenses, crimes_against_persons, crimes_against_property,
                        crimes_against_society, assault_offenses, aggravated_assault,
                        simple_assault, intimidation, homicide_offenses, murder_nonnegligent_manslaughter,
                        negligent_manslaughter, justifiable_homicide, human_trafficking_offenses,
                        commercial_sex_acts, involuntary_servitude, kidnapping_abduction,
                        sex_offenses, rape, sodomy, sexual_assault_with_object, arson, burglary,
                        larceny_theft, motor_vehicle_theft, robbery, vandalism,
                        drug_narcotic_offenses, drug_violations, drug_equipment_violations,
                        gambling_offenses, prostitution_offenses, weapons_violations,
                        fraud_offenses, identity_theft
                    ) VALUES (
                        :year, :state, :agency_type, :agency_name, :city,
                        :total_offenses, :crimes_against_persons, :crimes_against_property,
                        :crimes_against_society, :assault_offenses, :aggravated_assault,
                        :simple_assault, :intimidation, :homicide_offenses, :murder_nonnegligent_manslaughter,
                        :negligent_manslaughter, :justifiable_homicide, :human_trafficking_offenses,
                        :commercial_sex_acts, :involuntary_servitude, :kidnapping_abduction,
                        :sex_offenses, :rape, :sodomy, :sexual_assault_with_object, :arson, :burglary,
                        :larceny_theft, :motor_vehicle_theft, :robbery, :vandalism,
                        :drug_narcotic_offenses, :drug_violations, :drug_equipment_violations,
                        :gambling_offenses, :prostitution_offenses, :weapons_violations,
                        :fraud_offenses, :identity_theft
                    )
                """), data)
                
                loaded_count += 1
                
                # Commit in batches
                if loaded_count % 500 == 0:
                    session.commit()
                    print(f"   Progress: {loaded_count:,}/{len(df):,} records...", end='\r')
                    
            except Exception as e:
                error_count += 1
                if error_count <= 3:
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
    
    # Calculate risk scores
    print(f"\n8. Calculating risk scores...")
    
    try:
        # Update risk scores using SQL
        session.execute(text("""
            UPDATE nibrs_crime_data
            SET overall_risk_score = CASE 
                WHEN total_offenses > 0 THEN 
                    LEAST(
                        (
                            (murder_nonnegligent_manslaughter * 10.0) +
                            (aggravated_assault * 5.0) +
                            (rape * 5.0) +
                            (robbery * 3.0) +
                            (kidnapping_abduction * 8.0) +
                            (human_trafficking_offenses * 10.0) +
                            (drug_narcotic_offenses * 2.0) +
                            (burglary * 0.5)
                        ) / (total_offenses * 10.0) * 100,
                        100
                    )
                ELSE 0
            END
            WHERE overall_risk_score IS NULL
        """))
        session.commit()
        print(f"   ✓ Risk scores calculated")
    except Exception as e:
        print(f"   ⚠️  Could not calculate risk scores: {e}")
    
    # Show statistics
    print(f"\n9. Database Summary:")
    
    try:
        total = session.execute(text("SELECT COUNT(*) FROM nibrs_crime_data")).scalar()
        years = session.execute(text("""
            SELECT MIN(year), MAX(year) FROM nibrs_crime_data
        """)).fetchone()
        states = session.execute(text("""
            SELECT COUNT(DISTINCT state) FROM nibrs_crime_data
        """)).scalar()
        agencies = session.execute(text("""
            SELECT COUNT(DISTINCT agency_name) FROM nibrs_crime_data
        """)).scalar()
        
        print(f"   - Total records: {total:,}")
        print(f"   - Years: {years[0]} - {years[1]}")
        print(f"   - States: {states}")
        print(f"   - Agencies: {agencies:,}")
        
        # Top high-risk agencies
        print(f"\n10. Top 10 Highest Risk Agencies:")
        high_risk = session.execute(text("""
            SELECT agency_name, city, state, year, 
                   total_offenses, overall_risk_score
            FROM nibrs_crime_data
            WHERE overall_risk_score IS NOT NULL
            ORDER BY overall_risk_score DESC
            LIMIT 10
        """)).fetchall()
        
        for i, (agency, city, state, year, total, score) in enumerate(high_risk, 1):
            city_str = f"{city}, " if city else ""
            print(f"   {i}. {agency} ({city_str}{state}) - {year}")
            print(f"      Total Offenses: {total:,} | Risk Score: {score:.1f}/100")
    
    except Exception as e:
        print(f"   ⚠️  Could not generate summary: {e}")
    
    session.close()
    
    print("\n" + "=" * 80)
    print("✅ NIBRS DATA LOADING COMPLETE!")
    print("=" * 80)
    print(f"\nLoaded: {loaded_count:,} crime records")
    print(f"Years: 2020-2024")
    print(f"\n📋 Next steps:")
    print("1. Geocode agencies: python scripts/geocode_nibrs_agencies.py")
    print("2. Analyze crime near venues: python scripts/analyze_venue_crime.py")
    print("3. View in dashboard: http://127.0.0.1:5000/dashboard")
    print("=" * 80)
    
    return True


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Load NIBRS crime data into database')
    parser.add_argument(
        'csv_file',
        nargs='?',
        default='data/raw/NIBRS_master_2020_to_2024_refactored.csv',
        help='Path to NIBRS CSV file'
    )
    parser.add_argument(
        '--db',
        help='Database URL (default: from .env)',
        default=None
    )
    
    args = parser.parse_args()
    
    try:
        success = load_nibrs_data(args.csv_file, args.db)
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