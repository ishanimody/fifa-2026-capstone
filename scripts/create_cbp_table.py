"""
Create CBP Drug Seizures Table in PostgreSQL

Place in: scripts/create_cbp_table.py
"""

import sys
sys.path.append('src')

from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()

def create_cbp_table():
    """Create CBP drug seizures table in PostgreSQL"""
    
    engine = create_engine(os.getenv('DATABASE_URL'))
    
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS cbp_drug_seizures (
        id SERIAL PRIMARY KEY,
        fiscal_year INTEGER,
        month VARCHAR(10),
        month_number INTEGER,
        component VARCHAR(200),
        region VARCHAR(200),
        land_filter VARCHAR(100),
        area_of_responsibility VARCHAR(200),
        drug_type VARCHAR(100),
        event_count INTEGER,
        quantity_lbs FLOAT,
        latitude FLOAT,
        longitude FLOAT,
        city VARCHAR(100),
        state VARCHAR(100),
        data_source VARCHAR(200),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE INDEX IF NOT EXISTS idx_cbp_fiscal_year ON cbp_drug_seizures(fiscal_year);
    CREATE INDEX IF NOT EXISTS idx_cbp_drug_type ON cbp_drug_seizures(drug_type);
    CREATE INDEX IF NOT EXISTS idx_cbp_location ON cbp_drug_seizures(latitude, longitude);
    CREATE INDEX IF NOT EXISTS idx_cbp_area ON cbp_drug_seizures(area_of_responsibility);
    """
    
    try:
        with engine.connect() as conn:
            conn.execute(text(create_table_sql))
            conn.commit()
            
        print("=" * 60)
        print("✓ CBP Drug Seizures Table Created Successfully!")
        print("=" * 60)
        print("\nTable: cbp_drug_seizures")
        print("Indexes created on:")
        print("  - fiscal_year")
        print("  - drug_type")
        print("  - latitude, longitude")
        print("  - area_of_responsibility")
        print("=" * 60)
        
    except Exception as e:
        print(f"✗ Error creating table: {e}")

if __name__ == "__main__":
    create_cbp_table()