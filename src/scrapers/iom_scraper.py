"""
IOM Missing Migrants Project Data Scraper
Downloads and processes data from IOM Missing Migrants database
URL: https://missingmigrants.iom.int/

Place this file in: src/scrapers/iom_scraper.py
"""

import requests
import pandas as pd
from datetime import datetime
import time
import os
from typing import Optional, Dict
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class IOMMigrantsScraper:
    """Scraper for IOM Missing Migrants Project data"""
    
    def __init__(self, data_dir='data/raw'):
        """
        Initialize the scraper
        
        Args:
            data_dir: Directory to save downloaded data
        """
        self.base_url = "https://missingmigrants.iom.int"
        self.download_url = f"{self.base_url}/downloads"
        self.data_dir = data_dir
        
        # Create data directory if it doesn't exist
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Headers to mimic browser request
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def download_csv_data(self, save_filename=None) -> Optional[str]:
        """
        Download CSV data from IOM Missing Migrants
        
        Args:
            save_filename: Custom filename (optional)
            
        Returns:
            Path to downloaded file or None if failed
        """
        # IOM provides CSV download - try multiple possible URLs
        csv_urls = [
            "https://missingmigrants.iom.int/data/export",
            "https://missingmigrants.iom.int/sites/g/files/tmzbdl601/files/data_export/missing_migrants_global_figures_allincidents_2014_onwards.csv",
            "https://gmdac.iom.int/sites/g/files/tmzbdl601/files/Missing_Migrants_Global_Figures.csv"
        ]
        
        csv_url = csv_urls[0]  # Try first URL
        
        if save_filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            save_filename = f'iom_missing_migrants_{timestamp}.csv'
        
        filepath = os.path.join(self.data_dir, save_filename)
        
        try:
            logger.info(f"Downloading data from {csv_url}...")
            response = requests.get(csv_url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            # Save to file
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"✓ Data downloaded successfully: {filepath}")
            logger.info(f"  File size: {len(response.content) / 1024:.2f} KB")
            
            return filepath
            
        except requests.exceptions.RequestException as e:
            logger.error(f"✗ Error downloading data: {e}")
            return None
    
    def parse_csv_data(self, filepath: str) -> Optional[pd.DataFrame]:
        """
        Parse downloaded CSV file
        
        Args:
            filepath: Path to CSV file
            
        Returns:
            DataFrame with parsed data or None if failed
        """
        try:
            logger.info(f"Parsing CSV file: {filepath}")
            
            # Read CSV with proper encoding
            df = pd.read_csv(filepath, encoding='utf-8-sig')
            
            logger.info(f"✓ Loaded {len(df)} records")
            logger.info(f"  Columns: {list(df.columns)[:5]}...")  # Show first 5 columns
            
            return df
            
        except Exception as e:
            logger.error(f"✗ Error parsing CSV: {e}")
            return None
        
    def use_manual_file(self, filepath: str):
        """
        Use a manually downloaded CSV file
        
        Args:
            filepath: Path to manually downloaded CSV file
            
        Returns:
            Processed DataFrame
        """
        logger.info("=" * 60)
        logger.info("USING MANUALLY DOWNLOADED FILE")
        logger.info("=" * 60)
        
        if not os.path.exists(filepath):
            logger.error(f"File not found: {filepath}")
            logger.info("\nPlease download the data manually:")
            logger.info("1. Go to: https://missingmigrants.iom.int/downloads")
            logger.info("2. Click 'Download Data'")
            logger.info(f"3. Save to: {filepath}")
            return None
        
        # Parse the file
        df = self.parse_csv_data(filepath)
        if df is None:
            return None
        
        # Clean and transform
        df = self.clean_and_transform(df)
        
        # Generate summary
        stats = self.get_summary_statistics(df)
        logger.info("\nSummary Statistics:")
        logger.info(f"  Total incidents: {stats.get('total_incidents', 0)}")
        if 'casualties' in stats:
            logger.info(f"  Total dead: {stats['casualties']['total_dead']}")
            logger.info(f"  Total missing: {stats['casualties']['total_missing']}")
        
        # Save processed data
        self.save_processed_data(df)
        
        logger.info("=" * 60)
        logger.info("✓ Processing completed successfully!")
        logger.info("=" * 60)
        
        return df
    
    def clean_and_transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean and transform raw data
        
        Args:
            df: Raw DataFrame
            
        Returns:
            Cleaned DataFrame
        """
        logger.info("Cleaning and transforming data...")
        
        df_clean = df.copy()
        
        # Common column name mappings (IOM uses these column names)
        column_mapping = {
            'Main ID': 'incident_id',
            'Incident Date': 'incident_date',
            'Reported Date': 'reported_date',
            'Number Dead': 'number_dead',
            'Minimum Estimated Number of Missing': 'number_missing',
            'Total Dead and Missing': 'total_dead_missing',
            'Number of Survivors': 'number_survivors',
            'Number of Females': 'number_females',
            'Number of Males': 'number_males',
            'Number of Children': 'number_children',
            'Cause of Death': 'cause_of_death',
            'Region of Origin': 'origin_region',
            'Migration Route': 'migration_route',
            'Location Description': 'location_description',
            'Coordinates': 'coordinates',
            'Source': 'source',
            'Information Source Quality': 'source_quality'
        }
        
        # Rename columns if they exist
        existing_columns = {k: v for k, v in column_mapping.items() if k in df_clean.columns}
        df_clean = df_clean.rename(columns=existing_columns)
        
        # Parse dates
        if 'incident_date' in df_clean.columns:
            df_clean['incident_date'] = pd.to_datetime(df_clean['incident_date'], errors='coerce')
            df_clean['incident_year'] = df_clean['incident_date'].dt.year
            df_clean['incident_month'] = df_clean['incident_date'].dt.month
        
        # Parse coordinates (usually in format "lat, lon")
        if 'coordinates' in df_clean.columns:
            coords = df_clean['coordinates'].str.split(',', expand=True)
            if coords.shape[1] >= 2:
                df_clean['latitude'] = pd.to_numeric(coords[0], errors='coerce')
                df_clean['longitude'] = pd.to_numeric(coords[1], errors='coerce')
        
        # Convert numeric columns
        numeric_cols = ['number_dead', 'number_missing', 'total_dead_missing', 
                       'number_survivors', 'number_females', 'number_males', 'number_children']
        for col in numeric_cols:
            if col in df_clean.columns:
                df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce').fillna(0).astype(int)
        
        # Remove rows with no date
        if 'incident_date' in df_clean.columns:
            df_clean = df_clean[df_clean['incident_date'].notna()]
        
        # Remove rows with no location data
        if 'latitude' in df_clean.columns and 'longitude' in df_clean.columns:
            df_clean = df_clean[
                (df_clean['latitude'].notna()) & 
                (df_clean['longitude'].notna())
            ]
        
        logger.info(f"✓ Cleaned data: {len(df_clean)} records remain")
        
        return df_clean
    
    def filter_region(self, df: pd.DataFrame, region='Americas') -> pd.DataFrame:
        """
        Filter data by region
        
        Args:
            df: DataFrame to filter
            region: Region name (e.g., 'Americas', 'Mediterranean')
            
        Returns:
            Filtered DataFrame
        """
        if 'migration_route' not in df.columns and 'Region' not in df.columns:
            logger.warning("No region column found, returning full dataset")
            return df
        
        region_col = 'migration_route' if 'migration_route' in df.columns else 'Region'
        
        filtered = df[df[region_col].str.contains(region, case=False, na=False)]
        logger.info(f"Filtered to {region}: {len(filtered)} records")
        
        return filtered
    
    def filter_date_range(self, df: pd.DataFrame, start_date=None, end_date=None) -> pd.DataFrame:
        """
        Filter data by date range
        
        Args:
            df: DataFrame to filter
            start_date: Start date (datetime or string)
            end_date: End date (datetime or string)
            
        Returns:
            Filtered DataFrame
        """
        if 'incident_date' not in df.columns:
            logger.warning("No date column found")
            return df
        
        df_filtered = df.copy()
        
        if start_date:
            start_date = pd.to_datetime(start_date)
            df_filtered = df_filtered[df_filtered['incident_date'] >= start_date]
            logger.info(f"Filtered from {start_date}: {len(df_filtered)} records")
        
        if end_date:
            end_date = pd.to_datetime(end_date)
            df_filtered = df_filtered[df_filtered['incident_date'] <= end_date]
            logger.info(f"Filtered until {end_date}: {len(df_filtered)} records")
        
        return df_filtered
    
    def get_summary_statistics(self, df: pd.DataFrame) -> Dict:
        """
        Generate summary statistics
        
        Args:
            df: DataFrame to analyze
            
        Returns:
            Dictionary with summary stats
        """
        if df.empty:
            return {}
        
        stats = {
            'total_incidents': len(df),
            'date_range': {
                'earliest': str(df['incident_date'].min()) if 'incident_date' in df.columns else None,
                'latest': str(df['incident_date'].max()) if 'incident_date' in df.columns else None
            },
            'casualties': {
                'total_dead': int(df['number_dead'].sum()) if 'number_dead' in df.columns else 0,
                'total_missing': int(df['number_missing'].sum()) if 'number_missing' in df.columns else 0,
                'total_survivors': int(df['number_survivors'].sum()) if 'number_survivors' in df.columns else 0
            }
        }
        
        return stats
    
    def save_processed_data(self, df: pd.DataFrame, filename='iom_processed.csv'):
        """Save processed data to CSV"""
        processed_dir = 'data/processed'
        os.makedirs(processed_dir, exist_ok=True)
        
        filepath = os.path.join(processed_dir, filename)
        df.to_csv(filepath, index=False)
        
        logger.info(f"✓ Processed data saved: {filepath}")
        return filepath
    
    def run_full_pipeline(self, region=None, start_date=None, end_date=None):
        """
        Run complete scraping and processing pipeline
        
        Args:
            region: Optional region filter
            start_date: Optional start date
            end_date: Optional end date
            
        Returns:
            Processed DataFrame
        """
        logger.info("=" * 60)
        logger.info("IOM MISSING MIGRANTS DATA SCRAPER")
        logger.info("=" * 60)
        
        # Step 1: Download
        filepath = self.download_csv_data()
        if not filepath:
            logger.error("Download failed, aborting")
            return None
        
        # Step 2: Parse
        df = self.parse_csv_data(filepath)
        if df is None:
            logger.error("Parsing failed, aborting")
            return None
        
        # Step 3: Clean and transform
        df = self.clean_and_transform(df)
        
        # Step 4: Apply filters if specified
        if region:
            df = self.filter_region(df, region)
        
        if start_date or end_date:
            df = self.filter_date_range(df, start_date, end_date)
        
        # Step 5: Generate summary
        stats = self.get_summary_statistics(df)
        logger.info("\nSummary Statistics:")
        logger.info(f"  Total incidents: {stats['total_incidents']}")
        logger.info(f"  Date range: {stats['date_range']['earliest']} to {stats['date_range']['latest']}")
        logger.info(f"  Total dead: {stats['casualties']['total_dead']}")
        logger.info(f"  Total missing: {stats['casualties']['total_missing']}")
        logger.info(f"  Total survivors: {stats['casualties']['total_survivors']}")
        
        # Step 6: Save processed data
        self.save_processed_data(df)
        
        logger.info("=" * 60)
        logger.info("✓ Pipeline completed successfully!")
        logger.info("=" * 60)
        
        return df


# Example usage
if __name__ == "__main__":
    # Create scraper instance
    scraper = IOMMigrantsScraper()
    
    # Run the full pipeline
    # Filter for Americas region and recent data (2023-2024)
    df = scraper.run_full_pipeline(
        region='Americas',
        start_date='2023-01-01',
        end_date='2024-12-31'
    )
    
    if df is not None:
        print(f"\n✓ Successfully scraped {len(df)} incidents")
        print("\nFirst few records:")
        print(df.head())