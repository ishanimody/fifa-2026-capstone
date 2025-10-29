"""
Filter IOM Missing Migrants Data for Americas Only
Filters for: North America, Central America, South America, and Caribbean

Usage:
    python filter_iom_americas.py

This script will:
1. Read the processed IOM data
2. Filter for Americas regions only
3. Save the filtered data
4. Optionally update the database
"""

import sys
sys.path.append('src')

import pandas as pd
import os
from datetime import datetime

def filter_americas_regions(input_file='data/processed/iom_processed.csv'):
    """
    Filter IOM data for Americas regions only
    
    Args:
        input_file: Path to processed IOM CSV file
    """
    
    print("=" * 70)
    print("FILTERING IOM DATA FOR AMERICAS REGIONS")
    print("=" * 70)
    
    # Check if file exists
    if not os.path.exists(input_file):
        print(f"\n❌ Error: File not found: {input_file}")
        print("\nPlease run this first:")
        print("  python scripts/process_iom_data.py")
        return None
    
    # Read the data
    print(f"\n1. Reading data from: {input_file}")
    df = pd.read_csv(input_file)
    print(f"   ✓ Loaded {len(df):,} total records")
    
    # Show available columns
    print(f"\n2. Available columns:")
    print(f"   {', '.join(df.columns[:10])}...")
    
    # Try to identify the region column
    region_col = None
    possible_region_cols = ['Region of Incident', 'region', 'migration_route', 
                           'Region', 'incident_region', 'Country of Incident']
    
    for col in possible_region_cols:
        if col in df.columns:
            region_col = col
            print(f"\n3. Found region column: '{region_col}'")
            break
    
    if region_col is None:
        print("\n⚠️  Warning: Could not find region column!")
        print("   Available columns:", df.columns.tolist())
        print("\n   Trying to filter by coordinates instead...")
        # Filter by geographic coordinates for Americas
        df_americas = filter_by_coordinates(df)
    else:
        # Get unique regions
        unique_regions = df[region_col].dropna().unique()
        print(f"\n4. Unique regions in data ({len(unique_regions)}):")
        for region in sorted(unique_regions):
            count = len(df[df[region_col] == region])
            print(f"   - {region}: {count:,} records")
        
        # Define Americas regions to keep
        americas_regions = [
            'North America',
            'Central America',
            'South America',
            'Caribbean',
            'US-Mexico Border',
            'Mexico'
        ]
        
        print(f"\n5. Filtering for Americas regions:")
        for region in americas_regions:
            print(f"   - {region}")
        
        # Filter - case insensitive partial match
        df_americas = df[df[region_col].apply(
            lambda x: any(region.lower() in str(x).lower() 
                         for region in americas_regions) if pd.notna(x) else False
        )]
    
    print(f"\n6. Filtering results:")
    print(f"   Original records: {len(df):,}")
    print(f"   Filtered records: {len(df_americas):,}")
    print(f"   Removed: {len(df) - len(df_americas):,}")
    print(f"   Percentage kept: {(len(df_americas)/len(df)*100):.1f}%")
    
    # Show breakdown by region
    if region_col and region_col in df_americas.columns:
        print(f"\n7. Breakdown of filtered data:")
        region_counts = df_americas[region_col].value_counts()
        for region, count in region_counts.items():
            print(f"   - {region}: {count:,} records")
    
    # Statistics
    print(f"\n8. Casualty statistics (filtered data):")
    if 'number_dead' in df_americas.columns:
        total_dead = df_americas['number_dead'].sum()
        print(f"   Total dead: {int(total_dead):,}")
    if 'number_missing' in df_americas.columns:
        total_missing = df_americas['number_missing'].sum()
        print(f"   Total missing: {int(total_missing):,}")
    if 'number_survivors' in df_americas.columns:
        total_survivors = df_americas['number_survivors'].sum()
        print(f"   Total survivors: {int(total_survivors):,}")
    
    # Date range
    if 'incident_date' in df_americas.columns:
        df_americas['incident_date'] = pd.to_datetime(df_americas['incident_date'], errors='coerce')
        print(f"\n9. Date range:")
        print(f"   Earliest: {df_americas['incident_date'].min()}")
        print(f"   Latest: {df_americas['incident_date'].max()}")
    
    # Save filtered data
    output_dir = 'data/processed'
    os.makedirs(output_dir, exist_ok=True)
    
    output_file = os.path.join(output_dir, 'iom_americas_filtered.csv')
    df_americas.to_csv(output_file, index=False)
    
    print(f"\n10. Saved filtered data:")
    print(f"   ✓ {output_file}")
    print(f"   {len(df_americas):,} records")
    
    # Also save with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = os.path.join(output_dir, f'iom_americas_filtered_{timestamp}.csv')
    df_americas.to_csv(backup_file, index=False)
    print(f"   ✓ Backup: {backup_file}")
    
    print("\n" + "=" * 70)
    print("✓ FILTERING COMPLETE!")
    print("=" * 70)
    
    return df_americas


def filter_by_coordinates(df):
    """
    Filter by geographic coordinates for Americas
    Latitude: roughly -60 to 80 (covers all Americas)
    Longitude: roughly -170 to -30 (covers all Americas)
    """
    print("\n   Filtering by coordinates (Americas region):")
    print("   - Latitude: -60 to 80")
    print("   - Longitude: -170 to -30")
    
    if 'latitude' not in df.columns or 'longitude' not in df.columns:
        print("   ❌ No coordinate columns found!")
        return df
    
    df_americas = df[
        (df['latitude'].between(-60, 80)) & 
        (df['longitude'].between(-170, -30))
    ]
    
    print(f"   ✓ Filtered {len(df_americas):,} records by coordinates")
    return df_americas


def update_database_with_filtered_data(df, db_url=None):
    """
    Optional: Update database with filtered data only
    
    Args:
        df: Filtered DataFrame
        db_url: Database URL (optional, will use default if not provided)
    """
    print("\n" + "=" * 70)
    print("UPDATING DATABASE WITH FILTERED DATA")
    print("=" * 70)
    
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    if db_url is None:
        db_url = os.getenv('DATABASE_URL', 'sqlite:///worldcup_intelligence.db')
    
    print(f"\nDatabase: {db_url.split('@')[1] if '@' in db_url else db_url}")
    
    try:
        engine = create_engine(db_url, echo=False)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Clear existing IOM data
        print("\n1. Clearing existing IOM incidents...")
        deleted = session.execute(text("""
            DELETE FROM smuggling_incidents 
            WHERE source_id IN (
                SELECT id FROM data_sources WHERE name = 'IOM Missing Migrants'
            )
        """))
        session.commit()
        print(f"   ✓ Deleted {deleted.rowcount} old records")
        
        # Get IOM source ID
        iom_source = session.execute(text("""
            SELECT id FROM data_sources WHERE name = 'IOM Missing Migrants'
        """)).fetchone()
        
        if not iom_source:
            print("\n   Creating IOM data source...")
            session.execute(text("""
                INSERT INTO data_sources (name, url, description, data_type, update_frequency, is_active)
                VALUES ('IOM Missing Migrants', 'https://missingmigrants.iom.int/', 
                        'IOM Missing Migrants Project - Americas Only', 'incidents', 'weekly', 1)
            """))
            session.commit()
            iom_source = session.execute(text("""
                SELECT id FROM data_sources WHERE name = 'IOM Missing Migrants'
            """)).fetchone()
        
        source_id = iom_source[0]
        print(f"   ✓ Using source_id: {source_id}")
        
        # Insert filtered data
        print(f"\n2. Inserting {len(df):,} filtered records...")
        
        loaded = 0
        errors = 0
        
        for idx, row in df.iterrows():
            try:
                session.execute(text("""
                    INSERT INTO smuggling_incidents (
                        incident_type, incident_date, incident_year, incident_month,
                        latitude, longitude, location_description, country,
                        number_dead, number_missing, number_survivors,
                        cause_of_death, migrant_origin_countries,
                        source_id, source_quality, is_verified
                    ) VALUES (
                        :incident_type, :incident_date, :incident_year, :incident_month,
                        :latitude, :longitude, :location_description, :country,
                        :number_dead, :number_missing, :number_survivors,
                        :cause_of_death, :migrant_origin_countries,
                        :source_id, :source_quality, :is_verified
                    )
                """), {
                    'incident_type': 'migration_incident',
                    'incident_date': row.get('incident_date'),
                    'incident_year': int(row['incident_year']) if pd.notna(row.get('incident_year')) else None,
                    'incident_month': int(row['incident_month']) if pd.notna(row.get('incident_month')) else None,
                    'latitude': float(row['latitude']) if pd.notna(row.get('latitude')) else None,
                    'longitude': float(row['longitude']) if pd.notna(row.get('longitude')) else None,
                    'location_description': str(row.get('location_description', ''))[:500],
                    'country': str(row.get('Region of Incident', ''))[:50],
                    'number_dead': int(row.get('number_dead', 0)),
                    'number_missing': int(row.get('number_missing', 0)),
                    'number_survivors': int(row.get('number_survivors', 0)),
                    'cause_of_death': str(row.get('cause_of_death', ''))[:200],
                    'migrant_origin_countries': str(row.get('origin_region', ''))[:200],
                    'source_id': source_id,
                    'source_quality': str(row.get('source_quality', 'unverified'))[:20],
                    'is_verified': False
                })
                
                loaded += 1
                
                if loaded % 100 == 0:
                    session.commit()
                    print(f"   Progress: {loaded:,}/{len(df):,} records...", end='\r')
                    
            except Exception as e:
                errors += 1
                if errors <= 3:
                    print(f"\n   ⚠️  Error on row {idx}: {e}")
        
        session.commit()
        
        print(f"\n   ✓ Loaded {loaded:,} records")
        if errors > 0:
            print(f"   ⚠️  {errors} errors")
        
        # Verify
        count = session.execute(text("""
            SELECT COUNT(*) FROM smuggling_incidents WHERE source_id = :source_id
        """), {'source_id': source_id}).scalar()
        
        print(f"\n3. Database now contains {count:,} IOM records (Americas only)")
        
        session.close()
        
        print("\n" + "=" * 70)
        print("✓ DATABASE UPDATE COMPLETE!")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False
    
    return True


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Filter IOM data for Americas regions')
    parser.add_argument(
        '--input',
        default='data/processed/iom_processed.csv',
        help='Input CSV file path'
    )
    parser.add_argument(
        '--update-db',
        action='store_true',
        help='Also update the database with filtered data'
    )
    
    args = parser.parse_args()
    
    # Filter the data
    df_americas = filter_americas_regions(args.input)
    
    if df_americas is not None and args.update_db:
        print("\n")
        response = input("Update database with filtered data? (yes/no): ")
        if response.lower() in ['yes', 'y']:
            update_database_with_filtered_data(df_americas)
        else:
            print("\nSkipping database update.")
            print("Filtered data saved to: data/processed/iom_americas_filtered.csv")
            print("\nTo update database later, run:")
            print("  python filter_iom_americas.py --update-db")
    
    print("\n✓ Done!")