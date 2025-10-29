"""
Complete IOM Data Setup for World Cup 2026 Project
This script will guide you through getting and filtering IOM data

Run this from the scripts directory:
    python setup_iom_americas.py
"""

import os
import sys
import pandas as pd
from datetime import datetime

def check_file_exists(filepath):
    """Check if a file exists"""
    return os.path.exists(filepath)

def main():
    print("""
    ╔════════════════════════════════════════════════════════════════════╗
    ║                                                                    ║
    ║           IOM DATA SETUP - World Cup 2026 Project                 ║
    ║                      Americas Regions Only                         ║
    ║                                                                    ║
    ╚════════════════════════════════════════════════════════════════════╝
    """)
    
    # Step 1: Check for raw IOM file
    print("Step 1: Checking for IOM data file...\n")
    
    possible_files = [
        'data/raw/iom_missing_migrants_manual.csv',
        'data/raw/iom_missing_migrants.csv',
        'data/iom_missing_migrants.csv',
        '../data/raw/iom_missing_migrants_manual.csv',
    ]
    
    raw_file = None
    for filepath in possible_files:
        if check_file_exists(filepath):
            raw_file = filepath
            print(f"✓ Found IOM data: {filepath}")
            break
    
    if not raw_file:
        print("❌ No IOM data file found!\n")
        print("=" * 70)
        print("DOWNLOAD INSTRUCTIONS")
        print("=" * 70)
        print("\n📥 Please download the IOM data manually:\n")
        print("1. Open your browser and go to:")
        print("   https://missingmigrants.iom.int/downloads\n")
        print("2. Click the 'Download Data' button")
        print("   (It will download a CSV file)\n")
        print("3. Save the file to one of these locations:")
        for fp in possible_files[:2]:
            print(f"   - {fp}")
        print("\n4. Then run this script again:")
        print("   python setup_iom_americas.py\n")
        print("=" * 70)
        return False
    
    # Step 2: Process the raw file
    print(f"\nStep 2: Processing IOM data...\n")
    
    try:
        # Read the raw CSV
        print(f"Reading: {raw_file}")
        df_raw = pd.read_csv(raw_file, encoding='utf-8-sig')
        print(f"✓ Loaded {len(df_raw):,} records")
        
        # Show columns
        print(f"\nColumns found: {len(df_raw.columns)}")
        print(f"  {', '.join(df_raw.columns[:5])}...")
        
        # Clean and process
        print("\nProcessing data...")
        
        # Column mapping
        column_mapping = {
            'Main ID': 'incident_id',
            'Incident Date': 'incident_date',
            'Reported Date': 'reported_date',
            'Number Dead': 'number_dead',
            'Minimum Estimated Number of Missing': 'number_missing',
            'Total Dead and Missing': 'total_dead_missing',
            'Number of Survivors': 'number_survivors',
            'Cause of Death': 'cause_of_death',
            'Region of Origin': 'origin_region',
            'Migration Route': 'migration_route',
            'Location Description': 'location_description',
            'Region of Incident': 'region_of_incident',
            'Coordinates': 'coordinates',
            'Information Source Quality': 'source_quality'
        }
        
        # Rename columns
        existing_cols = {k: v for k, v in column_mapping.items() if k in df_raw.columns}
        df = df_raw.rename(columns=existing_cols)
        
        # Parse dates
        if 'incident_date' in df.columns:
            df['incident_date'] = pd.to_datetime(df['incident_date'], errors='coerce')
            df['incident_year'] = df['incident_date'].dt.year
            df['incident_month'] = df['incident_date'].dt.month
        
        # Parse coordinates
        if 'coordinates' in df.columns:
            coords = df['coordinates'].str.split(',', expand=True)
            if coords.shape[1] >= 2:
                df['latitude'] = pd.to_numeric(coords[0], errors='coerce')
                df['longitude'] = pd.to_numeric(coords[1], errors='coerce')
        
        # Convert numeric columns
        for col in ['number_dead', 'number_missing', 'number_survivors']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
        
        print(f"✓ Processed {len(df):,} records")
        
        # Step 3: Filter for Americas
        print(f"\nStep 3: Filtering for Americas regions...\n")
        
        # Find region column
        region_col = None
        for col in ['region_of_incident', 'Region of Incident', 'migration_route', 'Migration Route']:
            if col in df.columns:
                region_col = col
                break
        
        if region_col:
            print(f"Using region column: {region_col}")
            
            # Show unique regions
            unique_regions = df[region_col].dropna().unique()
            print(f"\nRegions in data ({len(unique_regions)}):")
            for region in sorted(unique_regions)[:10]:
                count = len(df[df[region_col] == region])
                print(f"  - {region}: {count:,} records")
            if len(unique_regions) > 10:
                print(f"  ... and {len(unique_regions) - 10} more")
            
            # Filter for Americas
            americas_keywords = [
                'north america', 'central america', 'south america', 'caribbean',
                'us-mexico', 'mexico', 'united states', 'canada', 'guatemala',
                'honduras', 'el salvador', 'nicaragua', 'costa rica', 'panama',
                'colombia', 'venezuela', 'ecuador', 'peru', 'brazil', 'chile',
                'argentina', 'cuba', 'haiti', 'dominican republic', 'jamaica',
            ]
            
            df_americas = df[df[region_col].apply(
                lambda x: any(kw in str(x).lower() for kw in americas_keywords) 
                if pd.notna(x) else False
            )]
        else:
            print("⚠️  No region column found, filtering by coordinates...")
            # Filter by coordinates for Americas
            df_americas = df[
                (df['latitude'].between(-60, 80)) & 
                (df['longitude'].between(-170, -30))
            ]
        
        print(f"\n📊 Filtering Results:")
        print(f"  Original records: {len(df):,}")
        print(f"  Americas records: {len(df_americas):,}")
        print(f"  Removed: {len(df) - len(df_americas):,}")
        print(f"  Kept: {(len(df_americas)/len(df)*100):.1f}%")
        
        # Statistics
        print(f"\n📈 Americas Data Statistics:")
        if 'number_dead' in df_americas.columns:
            print(f"  Total dead: {int(df_americas['number_dead'].sum()):,}")
        if 'number_missing' in df_americas.columns:
            print(f"  Total missing: {int(df_americas['number_missing'].sum()):,}")
        if 'number_survivors' in df_americas.columns:
            print(f"  Total survivors: {int(df_americas['number_survivors'].sum()):,}")
        
        # Step 4: Save processed data
        print(f"\nStep 4: Saving processed data...\n")
        
        # Create directories
        os.makedirs('data/processed', exist_ok=True)
        
        # Save full processed data
        full_output = 'data/processed/iom_processed.csv'
        df.to_csv(full_output, index=False)
        print(f"✓ Full data saved: {full_output}")
        
        # Save Americas-only data
        americas_output = 'data/processed/iom_americas_filtered.csv'
        df_americas.to_csv(americas_output, index=False)
        print(f"✓ Americas data saved: {americas_output}")
        
        # Save with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_output = f'data/processed/iom_americas_{timestamp}.csv'
        df_americas.to_csv(backup_output, index=False)
        print(f"✓ Backup saved: {backup_output}")
        
        print("\n" + "=" * 70)
        print("✅ SUCCESS! IOM DATA IS READY!")
        print("=" * 70)
        
        print(f"\n📁 Files created:")
        print(f"  1. {full_output} ({len(df):,} records - all regions)")
        print(f"  2. {americas_output} ({len(df_americas):,} records - Americas only)")
        print(f"  3. {backup_output} (timestamped backup)")
        
        print(f"\n🎯 Next Steps:")
        print(f"  1. Load data into database:")
        print(f"     python scripts/load_iom_data.py")
        print(f"\n  2. Or use Americas-only data:")
        print(f"     Modify load_iom_data.py to use: {americas_output}")
        print(f"\n  3. Start Flask and view your map!")
        print(f"     python src/app.py")
        
        print("\n" + "=" * 70)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error processing data: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    try:
        success = main()
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