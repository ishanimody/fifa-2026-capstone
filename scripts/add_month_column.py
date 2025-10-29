import sys
sys.path.append('src')

from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()

engine = create_engine(os.getenv('DATABASE_URL'))

try:
    with engine.connect() as conn:
        # Add month_number column if it doesn't exist
        conn.execute(text('''
            ALTER TABLE cbp_drug_seizures 
            ADD COLUMN IF NOT EXISTS month_number INTEGER
        '''))
        conn.commit()
        print('✓ Column month_number added successfully')
except Exception as e:
    print(f'Column might already exist or error: {e}')
    print('This is okay if the column already exists')

print('\nDone!')