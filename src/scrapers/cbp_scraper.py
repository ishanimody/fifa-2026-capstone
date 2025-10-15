"""
CBP (Customs and Border Protection) Statistics Scraper
Scrapes border encounter and enforcement data from CBP website

Place in: src/scrapers/cbp_scraper.py
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import time
import os
import re
from typing import Optional, Dict, List
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CBPScraper:
    """Scraper for CBP border statistics"""
    
    def __init__(self, data_dir='data/raw'):
        self.base_url = "https://www.cbp.gov"
        self.stats_url = f"{self.base_url}/newsroom/stats"
        self.data_dir = data_dir
        
        os.makedirs(self.data_dir, exist_ok=True)
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def get_nationwide_encounters(self) -> Optional[pd.DataFrame]:
        """
        Scrape nationwide encounters data from CBP stats page
        """
        try:
            logger.info("Fetching CBP nationwide encounters data...")
            
            # CBP provides downloadable data
            # Try to find the latest data link
            response = requests.get(self.stats_url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for Excel/CSV download links
            data_links = []
            for link in soup.find_all('a', href=True):
                href = link['href']
                if any(ext in href.lower() for ext in ['.xlsx', '.xls', '.csv']):
                    if 'nationwide' in href.lower() or 'encounter' in href.lower():
                        full_url = href if href.startswith('http') else f"{self.base_url}{href}"
                        data_links.append({
                            'url': full_url,
                            'text': link.get_text(strip=True)
                        })
            
            logger.info(f"Found {len(data_links)} potential data files")
            
            if data_links:
                # Download the first (most recent) file
                download_url = data_links[0]['url']
                logger.info(f"Downloading: {download_url}")
                
                response = requests.get(download_url, headers=self.headers, timeout=60)
                response.raise_for_status()
                
                # Save file
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f'cbp_encounters_{timestamp}.xlsx'
                filepath = os.path.join(self.data_dir, filename)
                
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                
                logger.info(f"✓ Downloaded: {filepath}")
                
                # Try to read the Excel file
                try:
                    df = pd.read_excel(filepath, sheet_name=0)
                    logger.info(f"✓ Loaded {len(df)} records from Excel")
                    return df
                except Exception as e:
                    logger.warning(f"Could not read Excel: {e}")
                    logger.info("File saved for manual processing")
                    return None
            else:
                logger.warning("No downloadable data files found")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching CBP data: {e}")
            return None
    
    def scrape_southwest_border_stats(self) -> Optional[Dict]:
        """
        Scrape Southwest Border statistics from CBP website
        This data is often in HTML tables
        """
        try:
            logger.info("Scraping Southwest Border statistics...")
            
            # Southwest border stats URL
            swb_url = f"{self.base_url}/newsroom/stats/southwest-land-border-encounters"
            
            response = requests.get(swb_url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find all tables on the page
            tables = soup.find_all('table')
            logger.info(f"Found {len(tables)} tables on page")
            
            all_data = []
            
            for idx, table in enumerate(tables):
                try:
                    # Convert HTML table to DataFrame
                    df = pd.read_html(str(table))[0]
                    
                    if not df.empty:
                        all_data.append({
                            'table_index': idx,
                            'data': df,
                            'rows': len(df),
                            'columns': list(df.columns)
                        })
                        logger.info(f"  Table {idx}: {len(df)} rows, columns: {list(df.columns)[:3]}...")
                except Exception as e:
                    logger.debug(f"  Could not parse table {idx}: {e}")
            
            if all_data:
                logger.info(f"✓ Successfully parsed {len(all_data)} tables")
                return {
                    'url': swb_url,
                    'tables': all_data,
                    'scraped_at': datetime.now().isoformat()
                }
            else:
                logger.warning("No tables could be parsed")
                return None
                
        except Exception as e:
            logger.error(f"Error scraping Southwest Border stats: {e}")
            return None
    
    def get_sector_data(self) -> Optional[List[Dict]]:
        """
        Get data by border sector (San Diego, El Paso, Rio Grande Valley, etc.)
        """
        sectors = [
            'san-diego', 'el-centro', 'yuma', 'tucson', 'el-paso',
            'big-bend', 'del-rio', 'laredo', 'rio-grande-valley'
        ]
        
        sector_data = []
        
        for sector in sectors:
            try:
                url = f"{self.base_url}/border-security/{sector}-sector"
                logger.info(f"Fetching {sector} sector data...")
                
                response = requests.get(url, headers=self.headers, timeout=30)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Extract any statistics or data
                    stats_text = soup.get_text()
                    
                    # Look for numbers (apprehensions, seizures, etc.)
                    numbers = re.findall(r'\d{1,3}(?:,\d{3})*(?:\.\d+)?', stats_text)
                    
                    sector_data.append({
                        'sector': sector,
                        'url': url,
                        'statistics_found': len(numbers),
                        'scraped_at': datetime.now().isoformat()
                    })
                    
                    logger.info(f"  ✓ {sector}: Found {len(numbers)} statistics")
                
                time.sleep(1)  # Be respectful of the server
                
            except Exception as e:
                logger.warning(f"  Error with {sector}: {e}")
        
        return sector_data if sector_data else None
    
    def create_sample_dataset(self) -> pd.DataFrame:
        """
        Create a sample dataset based on typical CBP data structure
        This is useful if live scraping fails
        """
        logger.info("Creating sample CBP dataset...")
        
        # Sample data structure based on CBP format
        sample_data = {
            'fiscal_year': [2023, 2023, 2023, 2024, 2024, 2024] * 3,
            'month': ['October', 'November', 'December', 'January', 'February', 'March'] * 3,
            'sector': ['Rio Grande Valley'] * 6 + ['El Paso'] * 6 + ['San Diego'] * 6,
            'encounters': [15234, 14567, 16789, 18234, 17890, 19456, 
                          8234, 7890, 9123, 10234, 9567, 11234,
                          5678, 5234, 6123, 6789, 6234, 7123],
            'apprehensions': [14234, 13567, 15789, 17234, 16890, 18456,
                             7234, 6890, 8123, 9234, 8567, 10234,
                             4678, 4234, 5123, 5789, 5234, 6123],
            'inadmissibles': [1000, 1000, 1000, 1000, 1000, 1000,
                             1000, 1000, 1000, 1000, 1000, 1000,
                             1000, 1000, 1000, 1000, 1000, 1000]
        }
        
        df = pd.DataFrame(sample_data)
        
        # Save sample data
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filepath = os.path.join(self.data_dir, f'cbp_sample_{timestamp}.csv')
        df.to_csv(filepath, index=False)
        
        logger.info(f"✓ Sample dataset created: {filepath}")
        logger.info(f"  Records: {len(df)}")
        
        return df
    
    def save_to_csv(self, data: pd.DataFrame, filename: str = None) -> str:
        """Save data to CSV"""
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'cbp_processed_{timestamp}.csv'
        
        processed_dir = 'data/processed'
        os.makedirs(processed_dir, exist_ok=True)
        
        filepath = os.path.join(processed_dir, filename)
        data.to_csv(filepath, index=False)
        
        logger.info(f"✓ Data saved: {filepath}")
        return filepath
    
    def run_full_pipeline(self):
        """
        Run complete CBP scraping pipeline
        """
        logger.info("=" * 60)
        logger.info("CBP STATISTICS SCRAPER")
        logger.info("=" * 60)
        
        results = {
            'nationwide_encounters': None,
            'southwest_border': None,
            'sector_data': None,
            'sample_data': None
        }
        
        # Try to get nationwide encounters
        df_encounters = self.get_nationwide_encounters()
        if df_encounters is not None:
            results['nationwide_encounters'] = df_encounters
            self.save_to_csv(df_encounters, 'cbp_nationwide_encounters.csv')
        
        # Try Southwest Border stats
        swb_data = self.scrape_southwest_border_stats()
        if swb_data:
            results['southwest_border'] = swb_data
            # Save the first table if available
            if swb_data['tables']:
                first_table = swb_data['tables'][0]['data']
                self.save_to_csv(first_table, 'cbp_southwest_border.csv')
        
        # Get sector data
        sector_data = self.get_sector_data()
        if sector_data:
            results['sector_data'] = sector_data
            # Save sector summary
            df_sectors = pd.DataFrame(sector_data)
            self.save_to_csv(df_sectors, 'cbp_sectors.csv')
        
        # Create sample dataset as fallback
        sample_df = self.create_sample_dataset()
        results['sample_data'] = sample_df
        
        logger.info("\n" + "=" * 60)
        logger.info("SCRAPING SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Nationwide encounters: {'✓' if results['nationwide_encounters'] is not None else '✗'}")
        logger.info(f"Southwest Border stats: {'✓' if results['southwest_border'] is not None else '✗'}")
        logger.info(f"Sector data: {'✓' if results['sector_data'] is not None else '✗'}")
        logger.info(f"Sample data: ✓ (always created as fallback)")
        logger.info("=" * 60)
        
        return results


if __name__ == "__main__":
    scraper = CBPScraper()
    results = scraper.run_full_pipeline()
    
    print("\n✓ CBP Scraping Complete!")
    print("\nNote: CBP website structure changes frequently.")
    print("If live scraping fails, use the sample dataset for development.")
    print("Check data/processed/ folder for output files.")