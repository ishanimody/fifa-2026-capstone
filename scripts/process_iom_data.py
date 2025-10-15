"""
Process manually downloaded IOM data
"""
import sys
sys.path.append('src')

from scrapers.iom_scraper import IOMMigrantsScraper

# Create scraper instance
scraper = IOMMigrantsScraper()

print("Processing IOM Missing Migrants data...")

# Use the manually downloaded file
filepath = 'data/raw/iom_missing_migrants_manual.csv'

df = scraper.use_manual_file(filepath)

if df is not None:
    print(f"\n✅ Successfully processed {len(df)} incidents!")
    
    # Show available columns
    print("\n" + "="*60)
    print("AVAILABLE COLUMNS:")
    print("="*60)
    print(df.columns.tolist())
    
    # Show some statistics
    print("\n" + "="*60)
    print("SAMPLE DATA (first 10 rows):")
    print("="*60)
    
    # Display columns that exist
    display_cols = []
    for col in ['incident_date', 'latitude', 'longitude', 'number_missing', 'number_dead', 'incident_id']:
        if col in df.columns:
            display_cols.append(col)
    
    if display_cols:
        print(df[display_cols].head(10))
    else:
        print(df.head(10))
    
    # Filter for Americas region (relevant to World Cup)
    if 'migration_route' in df.columns:
        americas_df = scraper.filter_region(df, 'Americas')
        print(f"\n📍 Incidents in Americas region: {len(americas_df)}")
        
        # Save Americas-specific data
        scraper.save_processed_data(americas_df, 'iom_americas.csv')
        print(f"✅ Americas data saved to: data/processed/iom_americas.csv")
    
    print(f"\n✅ Full processed data saved to: data/processed/iom_processed.csv")
else:
    print("\n❌ Processing failed!")