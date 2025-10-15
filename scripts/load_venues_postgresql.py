"""
Load World Cup 2026 Venues into PostgreSQL Database

Place in: scripts/load_venues_postgresql.py
"""

import sys
import os
sys.path.append('src')

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.models import WorldCupVenue
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


# World Cup 2026 Venues with coordinates
venues_data = [
    {'venue_id': 1, 'venue_name': 'MetLife Stadium', 'city': 'East Rutherford', 'state_province': 'New Jersey', 'country': 'USA', 'latitude': 40.8128, 'longitude': -74.0742, 'capacity': 82500, 'host_matches': 8, 'security_risk_level': 'Medium', 'region': 'US Northeast'},
    {'venue_id': 2, 'venue_name': 'Mercedes-Benz Stadium', 'city': 'Atlanta', 'state_province': 'Georgia', 'country': 'USA', 'latitude': 33.7555, 'longitude': -84.4008, 'capacity': 71000, 'host_matches': 8, 'security_risk_level': 'Medium', 'region': 'US South'},
    {'venue_id': 3, 'venue_name': 'Hard Rock Stadium', 'city': 'Miami Gardens', 'state_province': 'Florida', 'country': 'USA', 'latitude': 25.9580, 'longitude': -80.2389, 'capacity': 65326, 'host_matches': 7, 'security_risk_level': 'High', 'region': 'US Southeast'},
    {'venue_id': 4, 'venue_name': 'Arrowhead Stadium', 'city': 'Kansas City', 'state_province': 'Missouri', 'country': 'USA', 'latitude': 39.0489, 'longitude': -94.4839, 'capacity': 76416, 'host_matches': 6, 'security_risk_level': 'Low', 'region': 'US Midwest'},
    {'venue_id': 5, 'venue_name': 'AT&T Stadium', 'city': 'Arlington', 'state_province': 'Texas', 'country': 'USA', 'latitude': 32.7473, 'longitude': -97.0945, 'capacity': 80000, 'host_matches': 9, 'security_risk_level': 'High', 'region': 'US Southwest'},
    {'venue_id': 6, 'venue_name': 'NRG Stadium', 'city': 'Houston', 'state_province': 'Texas', 'country': 'USA', 'latitude': 29.6847, 'longitude': -95.4107, 'capacity': 72220, 'host_matches': 7, 'security_risk_level': 'High', 'region': 'US Southwest'},
    {'venue_id': 7, 'venue_name': 'Levi\'s Stadium', 'city': 'Santa Clara', 'state_province': 'California', 'country': 'USA', 'latitude': 37.4035, 'longitude': -121.9699, 'capacity': 68500, 'host_matches': 6, 'security_risk_level': 'Low', 'region': 'US West Coast'},
    {'venue_id': 8, 'venue_name': 'SoFi Stadium', 'city': 'Inglewood', 'state_province': 'California', 'country': 'USA', 'latitude': 33.9535, 'longitude': -118.3392, 'capacity': 70240, 'host_matches': 8, 'security_risk_level': 'High', 'region': 'US West Coast'},
    {'venue_id': 9, 'venue_name': 'Lincoln Financial Field', 'city': 'Philadelphia', 'state_province': 'Pennsylvania', 'country': 'USA', 'latitude': 39.9008, 'longitude': -75.1675, 'capacity': 67594, 'host_matches': 6, 'security_risk_level': 'Medium', 'region': 'US Northeast'},
    {'venue_id': 10, 'venue_name': 'Lumen Field', 'city': 'Seattle', 'state_province': 'Washington', 'country': 'USA', 'latitude': 47.5952, 'longitude': -122.3316, 'capacity': 68740, 'host_matches': 6, 'security_risk_level': 'Low', 'region': 'US West Coast'},
    {'venue_id': 11, 'venue_name': 'Gillette Stadium', 'city': 'Foxborough', 'state_province': 'Massachusetts', 'country': 'USA', 'latitude': 42.0909, 'longitude': -71.2643, 'capacity': 65878, 'host_matches': 7, 'security_risk_level': 'Low', 'region': 'US Northeast'},
    {'venue_id': 12, 'venue_name': 'BMO Field', 'city': 'Toronto', 'state_province': 'Ontario', 'country': 'Canada', 'latitude': 43.6332, 'longitude': -79.4189, 'capacity': 30000, 'host_matches': 6, 'security_risk_level': 'Medium', 'region': 'Canada East'},
    {'venue_id': 13, 'venue_name': 'BC Place', 'city': 'Vancouver', 'state_province': 'British Columbia', 'country': 'Canada', 'latitude': 49.2768, 'longitude': -123.1120, 'capacity': 54500, 'host_matches': 7, 'security_risk_level': 'Low', 'region': 'Canada West'},
    {'venue_id': 14, 'venue_name': 'Estadio Azteca', 'city': 'Mexico City', 'state_province': 'CDMX', 'country': 'Mexico', 'latitude': 19.3030, 'longitude': -99.1506, 'capacity': 87523, 'host_matches': 5, 'security_risk_level': 'High', 'region': 'Mexico'},
    {'venue_id': 15, 'venue_name': 'Estadio BBVA', 'city': 'Monterrey', 'state_province': 'Nuevo León', 'country': 'Mexico', 'latitude': 25.7380, 'longitude': -100.2443, 'capacity': 53500, 'host_matches': 4, 'security_risk_level': 'High', 'region': 'Mexico'},
    {'venue_id': 16, 'venue_name': 'Estadio Akron', 'city': 'Guadalajara', 'state_province': 'Jalisco', 'country': 'Mexico', 'latitude': 20.6770, 'longitude': -103.4615, 'capacity': 46232, 'host_matches': 4, 'security_risk_level': 'Medium', 'region': 'Mexico'}
]


def load_venues(db_url=None):
    """Load World Cup venues into database"""
    
    # Use DATABASE_URL from .env if not provided
    if db_url is None:
        db_url = os.getenv('DATABASE_URL', 'sqlite:///worldcup_intelligence.db')
    
    print("=" * 60)
    print("LOADING WORLD CUP 2026 VENUES INTO DATABASE")
    print("=" * 60)
    
    print(f"\nDatabase: {db_url.split('@')[1] if '@' in db_url else db_url}")
    
    # Create database connection
    engine = create_engine(db_url, echo=False)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    print(f"\n1. Loading {len(venues_data)} World Cup venues...")
    
    loaded_count = 0
    updated_count = 0
    
    for venue_data in venues_data:
        # Remove venue_id from data (we use 'id' instead)
        venue_dict = venue_data.copy()
        venue_dict.pop('venue_id', None)
        
        # Check if venue already exists
        existing = session.query(WorldCupVenue).filter_by(
            venue_name=venue_dict['venue_name']
        ).first()
        
        if existing:
            # Update existing venue
            for key, value in venue_dict.items():
                if hasattr(existing, key):
                    setattr(existing, key, value)
            existing.updated_at = datetime.utcnow()
            updated_count += 1
            print(f"   ✓ Updated: {venue_dict['venue_name']}")
        else:
            # Create new venue
            venue = WorldCupVenue(**venue_dict)
            session.add(venue)
            loaded_count += 1
            print(f"   ✓ Added: {venue_dict['venue_name']}")
    
    session.commit()
    
    # Show summary
    print("\n2. Database Summary:")
    total_venues = session.query(WorldCupVenue).count()
    print(f"   - Total venues in database: {total_venues}")
    print(f"   - New venues added: {loaded_count}")
    print(f"   - Venues updated: {updated_count}")
    
    # Show venues by country
    print("\n3. Venues by Country:")
    for country in ['USA', 'Canada', 'Mexico']:
        count = session.query(WorldCupVenue).filter_by(country=country).count()
        print(f"   - {country}: {count} venues")
    
    session.close()
    
    print("\n" + "=" * 60)
    print("✓ VENUES LOADED SUCCESSFULLY!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Run: python scripts/load_iom_data.py (to load incident data)")
    print("2. Start building visualizations!")
    print("=" * 60)


if __name__ == "__main__":
    load_venues()