import sys
sys.path.append('src')

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.models import SmugglingIncident, DataSource

engine = create_engine('sqlite:///worldcup_intelligence.db')
Session = sessionmaker(bind=engine)
session = Session()

print("Database Contents:")
print(f"Total incidents: {session.query(SmugglingIncident).count()}")
print(f"Data sources: {session.query(DataSource).count()}")

# Show sample incidents
print("\nSample incidents:")
incidents = session.query(SmugglingIncident).limit(5).all()
for inc in incidents:
    print(f"- {inc.incident_date}: {inc.location_description} ({inc.number_dead} dead, {inc.number_missing} missing)")

session.close()