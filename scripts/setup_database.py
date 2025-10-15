"""
Database Setup Script
Creates database tables and initializes the database

Run this script to set up your database:
python scripts/setup_database.py

Place in: scripts/setup_database.py
"""

import sys
import os
sys.path.append('src')

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.models import Base, DataSource, WorldCupVenue, SmugglingIncident
from datetime import datetime

def create_database(db_url='sqlite:///worldcup_intelligence.db'):
    """
    Create database and all tables
    
    Args:
        db_url: Database connection string
    """
    print("=" * 60)
    print("DATABASE SETUP - WORLD CUP 2026 INTELLIGENCE PLATFORM")
    print("=" * 60)
    
    # Create engine
    print(f"\n1. Creating database connection...")
    print(f"   Database: {db_url}")
    engine = create_engine(db_url, echo=False)
    
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
        # Check if source already exists
        existing = session.query(DataSource).filter_by(name=source_data['name']).first()
        if not existing:
            source = DataSource(**source_data)
            session.add(source)
            print(f"   ✓ Added: {source_data['name']}")
        else:
            print(f"   - Already exists: {source_data['name']}")
    
    session.commit()
    
    # Show summary
    print("\n4. Database Summary:")
    print(f"   - Data Sources: {session.query(DataSource).count()}")
    print(f"   - World Cup Venues: {session.query(WorldCupVenue).count()}")
    print(f"   - Smuggling Incidents: {session.query(SmugglingIncident).count()}")
    
    session.close()
    
    print("\n" + "=" * 60)
    print("✓ DATABASE SETUP COMPLETE!")
    print("=" * 60)
    print(f"\nDatabase location: {db_url}")
    print("\nNext steps:")
    print("1. Run: python scripts/load_venues.py (to load World Cup venues)")
    print("2. Run: python scripts/load_iom_data.py (to load IOM incidents)")
    print("=" * 60)
    
    return engine


def verify_database(db_url='sqlite:///worldcup_intelligence.db'):
    """Verify database setup"""
    engine = create_engine(db_url, echo=False)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    print("\nVerifying database...")
    print(f"✓ Data sources: {session.query(DataSource).count()}")
    print(f"✓ Tables created: {len(Base.metadata.tables)}")
    
    session.close()


if __name__ == "__main__":
    # Create database with SQLite (easier for development)
    db_url = 'sqlite:///worldcup_intelligence.db'
    
    # Or use PostgreSQL (uncomment below and configure):
    # db_url = 'postgresql://wcuser:password@localhost:5432/worldcup_intelligence'
    
    engine = create_database(db_url)
    verify_database(db_url)