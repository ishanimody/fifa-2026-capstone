"""
PostgreSQL Database Setup Script
Creates database tables with PostGIS support

Place in: scripts/setup_database_postgresql.py
"""

import sys
import os
sys.path.append('src')

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from models.models import Base, DataSource
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def setup_postgresql():
    """Set up PostgreSQL database with PostGIS"""
    
    print("=" * 60)
    print("POSTGRESQL + POSTGIS SETUP")
    print("=" * 60)
    
    # Get database URL from environment
    db_url = os.getenv('DATABASE_URL', 'postgresql://wcuser:password@localhost:5432/worldcup_intelligence')
    
    print(f"\nDatabase URL: {db_url}")
    
    try:
        # Create engine
        print("\n1. Connecting to PostgreSQL...")
        engine = create_engine(db_url, echo=False)
        
        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version();"))
            version = result.fetchone()[0]
            print(f"   ✓ Connected! PostgreSQL {version.split(',')[0]}")
            
            # Check PostGIS
            try:
                result = conn.execute(text("SELECT PostGIS_version();"))
                postgis_version = result.fetchone()[0]
                print(f"   ✓ PostGIS installed: {postgis_version}")
            except Exception as e:
                print(f"   ⚠ PostGIS not found: {e}")
                print("   Installing PostGIS extension...")
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))
                conn.commit()
                print("   ✓ PostGIS extension created")
        
        # Create all tables
        print("\n2. Creating database tables...")
        Base.metadata.create_all(engine)
        
        print("   ✓ Tables created:")
        for table in Base.metadata.sorted_tables:
            print(f"     - {table.name}")
        
        # Create session
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Add initial data sources
        print("\n3. Adding initial data sources...")
        
        data_sources = [
            {
                'name': 'IOM Missing Migrants',
                'url': 'https://missingmigrants.iom.int/',
                'description': 'IOM Missing Migrants Project - Global database of migrant deaths',
                'data_type': 'incidents',
                'update_frequency': 'weekly',
                'is_active': True
            },
            {
                'name': 'CBP Statistics',
                'url': 'https://www.cbp.gov/newsroom/stats',
                'description': 'US Customs and Border Protection statistics',
                'data_type': 'statistics',
                'update_frequency': 'monthly',
                'is_active': True
            },
            {
                'name': 'UNODC',
                'url': 'https://www.unodc.org',
                'description': 'UN Office on Drugs and Crime - Human Trafficking Data',
                'data_type': 'statistics',
                'update_frequency': 'annual',
                'is_active': True
            }
        ]
        
        for source_data in data_sources:
            existing = session.query(DataSource).filter_by(name=source_data['name']).first()
            if not existing:
                source = DataSource(**source_data)
                session.add(source)
                print(f"   ✓ Added: {source_data['name']}")
            else:
                print(f"   - Already exists: {source_data['name']}")
        
        session.commit()
        
        # Create spatial indexes
        print("\n4. Creating spatial indexes...")
        with engine.connect() as conn:
            # Index for venues using lat/lon
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_venues_lat_lon 
                ON worldcup_venues (latitude, longitude);
            """))
            
            # Index for incidents using lat/lon
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_incidents_lat_lon 
                ON smuggling_incidents (latitude, longitude);
            """))
            
            conn.commit()
            print("   ✓ Spatial indexes created")
        
        # Show summary
        print("\n5. Database Summary:")
        print(f"   - Data Sources: {session.query(DataSource).count()}")
        print(f"   - Tables: {len(Base.metadata.tables)}")
        
        session.close()
        
        print("\n" + "=" * 60)
        print("✓ POSTGRESQL SETUP COMPLETE!")
        print("=" * 60)
        print(f"\nDatabase: {db_url.split('@')[1]}")  # Hide password
        print("\nNext steps:")
        print("1. Run: python scripts/load_venues_postgresql.py")
        print("2. Run: python scripts/load_iom_data.py")
        print("=" * 60)
        
        return engine
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        print("\nTroubleshooting:")
        print("1. Check if PostgreSQL is running")
        print("2. Verify DATABASE_URL in .env file")
        print("3. Ensure database 'worldcup_intelligence' exists")
        print("4. Check if PostGIS is installed")
        return None


if __name__ == "__main__":
    setup_postgresql()