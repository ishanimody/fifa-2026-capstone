
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, Date, DateTime, Float, JSON, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

# For now, we'll use a simple declarative base
# This will be connected to the db object in app.py
Base = declarative_base()


class DataSource(Base):
    """Track data sources and their update schedules"""
    __tablename__ = 'data_sources'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    url = Column(String(500))
    description = Column(Text)
    data_type = Column(String(50))  # 'incidents', 'statistics', 'routes'
    update_frequency = Column(String(50))  # 'daily', 'weekly', 'monthly'
    last_updated = Column(DateTime)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    incidents = relationship('SmugglingIncident', back_populates='source')
    
    def __repr__(self):
        return f'<DataSource {self.name}>'


class WorldCupVenue(Base):
    """World Cup 2026 venue locations"""
    __tablename__ = 'worldcup_venues'
    
    id = Column(Integer, primary_key=True)
    venue_name = Column(String(100), nullable=False)
    city = Column(String(100), nullable=False)
    state_province = Column(String(100))
    country = Column(String(50), nullable=False)
    
    # For now, store as separate lat/lon columns
    # We'll add PostGIS Geography type later when PostgreSQL is set up
    latitude = Column(Float)
    longitude = Column(Float)
    
    # Venue details
    capacity = Column(Integer)
    metro_population = Column(Integer)
    border_proximity_km = Column(Integer)
    host_matches = Column(Integer)
    security_risk_level = Column(String(20))  # 'Low', 'Medium', 'High'
    region = Column(String(50))
    
    # Metadata
    formatted_address = Column(String(500))
    google_place_id = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Venue {self.venue_name}, {self.city}>'


class SmugglingIncident(Base):
    """Individual smuggling incidents and migration events"""
    __tablename__ = 'smuggling_incidents'
    
    id = Column(Integer, primary_key=True)
    
    # Basic information
    incident_type = Column(String(50))  # 'border_crossing', 'interdiction', 'death', etc.
    incident_date = Column(Date, nullable=False)
    incident_year = Column(Integer, index=True)
    incident_month = Column(Integer)
    
    # Location data (using lat/lon for now)
    latitude = Column(Float)
    longitude = Column(Float)
    location_description = Column(String(500))
    city = Column(String(100))
    state_province = Column(String(100))
    country = Column(String(50), index=True)
    region = Column(String(100))
    
    # Incident details
    number_of_people = Column(Integer)
    number_dead = Column(Integer)
    number_missing = Column(Integer)
    number_survivors = Column(Integer)
    
    # Smuggling specifics
    smuggling_method = Column(String(100))  # 'vehicle', 'boat', 'foot', etc.
    route_description = Column(Text)
    cause_of_death = Column(String(200))
    
    # Demographics (when available)
    migrant_origin_countries = Column(Text)  # Comma-separated list
    age_groups = Column(String(200))
    gender_distribution = Column(String(100))
    
    # Source information
    source_id = Column(Integer, ForeignKey('data_sources.id'))
    source_url = Column(String(500))
    source_quality = Column(String(20))  # 'verified', 'unverified', 'estimated'
    
    # Metadata
    raw_data = Column(JSON)  # Store original data for reference
    notes = Column(Text)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    source = relationship('DataSource', back_populates='incidents')
    
    def __repr__(self):
        return f'<Incident {self.id}: {self.incident_type} on {self.incident_date}>'


class SmugglingRoute(Base):
    """Known smuggling corridors and routes"""
    __tablename__ = 'smuggling_routes'
    
    id = Column(Integer, primary_key=True)
    route_name = Column(String(200), nullable=False)
    route_description = Column(Text)
    
    # Store route as JSON array of coordinates for now
    # Format: [{"lat": x, "lon": y}, {"lat": x2, "lon": y2}, ...]
    route_coordinates = Column(JSON)
    
    # Route details
    origin_country = Column(String(50))
    destination_country = Column(String(50))
    transit_countries = Column(Text)  # Comma-separated
    
    # Activity metrics
    activity_level = Column(String(20))  # 'Low', 'Medium', 'High', 'Very High'
    estimated_annual_crossings = Column(Integer)
    primary_transport_method = Column(String(100))
    
    # Risk assessment
    danger_level = Column(String(20))
    known_criminal_organizations = Column(Text)
    
    # Source and metadata
    source_id = Column(Integer, ForeignKey('data_sources.id'))
    last_reported_activity = Column(Date)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Route {self.route_name}>'


class BorderCrossing(Base):
    """Official and unofficial border crossing points"""
    __tablename__ = 'border_crossings'
    
    id = Column(Integer, primary_key=True)
    crossing_name = Column(String(200), nullable=False)
    crossing_type = Column(String(50))  # 'official', 'unofficial', 'common_route'
    
    # Location
    latitude = Column(Float)
    longitude = Column(Float)
    border_between = Column(String(100))  # e.g., "USA-Mexico"
    state_province = Column(String(100))
    
    # Details
    crossing_status = Column(String(50))  # 'open', 'closed', 'restricted'
    daily_capacity = Column(Integer)
    surveillance_level = Column(String(20))  # 'Low', 'Medium', 'High'
    
    # Statistics (when available)
    average_daily_crossings = Column(Integer)
    apprehensions_last_month = Column(Integer)
    
    # Metadata
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<BorderCrossing {self.crossing_name}>'


class DataQualityLog(Base):
    """Track data quality and validation issues"""
    __tablename__ = 'data_quality_logs'
    
    id = Column(Integer, primary_key=True)
    source_id = Column(Integer, ForeignKey('data_sources.id'))
    
    # Quality metrics
    total_records_processed = Column(Integer)
    valid_records = Column(Integer)
    invalid_records = Column(Integer)
    duplicate_records = Column(Integer)
    
    # Issues found
    validation_errors = Column(JSON)  # Store error details
    
    # Processing info
    processing_date = Column(DateTime, default=datetime.utcnow)
    processing_duration_seconds = Column(Float)
    
    def __repr__(self):
        return f'<QualityLog {self.processing_date}>'
    
    """
CBP Drug Seizures Database Model
Add to: src/models/models.py (at the end, before helper functions)
"""

class CBPDrugSeizure(Base):
    """CBP Drug Seizures Data"""
    __tablename__ = 'cbp_drug_seizures'
    
    id = Column(Integer, primary_key=True)
    
    # Time information
    fiscal_year = Column(Integer, nullable=False, index=True)
    month = Column(String(20), nullable=False)
    month_number = Column(Integer)  # 1-12 for easy sorting
    
    # Organization
    component = Column(String(100))  # Office of Field Operations, Border Patrol, etc.
    region = Column(String(100))
    land_filter = Column(String(50))
    area_of_responsibility = Column(String(100), index=True)  # Field Office name
    
    # Drug information
    drug_type = Column(String(100), nullable=False, index=True)
    event_count = Column(Integer, default=0)
    quantity_lbs = Column(Float, default=0.0)
    
    # Geocoding (we'll add coordinates based on field office)
    latitude = Column(Float)
    longitude = Column(Float)
    city = Column(String(100))
    state = Column(String(50))
    
    # Metadata
    data_source = Column(String(200))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Unique constraint to prevent duplicates
    __table_args__ = (
        Index('idx_cbp_unique', 'fiscal_year', 'month', 'component', 'area_of_responsibility', 'drug_type', unique=True),
        Index('idx_cbp_location', 'latitude', 'longitude'),
        Index('idx_cbp_drug_type', 'drug_type'),
        Index('idx_cbp_year_month', 'fiscal_year', 'month_number'),
    )
    
    def __repr__(self):
        return f'<CBPSeizure {self.fiscal_year}-{self.month} {self.area_of_responsibility} {self.drug_type}>'


# Field Office Location Mapping
CBP_FIELD_OFFICE_LOCATIONS = {
    'ATLANTA FIELD OFFICE': {'city': 'Atlanta', 'state': 'GA', 'lat': 33.7490, 'lon': -84.3880},
    'BALTIMORE FIELD OFFICE': {'city': 'Baltimore', 'state': 'MD', 'lat': 39.2904, 'lon': -76.6122},
    'BOSTON FIELD OFFICE': {'city': 'Boston', 'state': 'MA', 'lat': 42.3601, 'lon': -71.0589},
    'BUFFALO FIELD OFFICE': {'city': 'Buffalo', 'state': 'NY', 'lat': 42.8864, 'lon': -78.8784},
    'CHICAGO FIELD OFFICE': {'city': 'Chicago', 'state': 'IL', 'lat': 41.8781, 'lon': -87.6298},
    'DETROIT FIELD OFFICE': {'city': 'Detroit', 'state': 'MI', 'lat': 42.3314, 'lon': -83.0458},
    'EL PASO FIELD OFFICE': {'city': 'El Paso', 'state': 'TX', 'lat': 31.7619, 'lon': -106.4850},
    'HOUSTON FIELD OFFICE': {'city': 'Houston', 'state': 'TX', 'lat': 29.7604, 'lon': -95.3698},
    'LAREDO FIELD OFFICE': {'city': 'Laredo', 'state': 'TX', 'lat': 27.5306, 'lon': -99.4803},
    'LOS ANGELES FIELD OFFICE': {'city': 'Los Angeles', 'state': 'CA', 'lat': 34.0522, 'lon': -118.2437},
    'MIAMI FIELD OFFICE': {'city': 'Miami', 'state': 'FL', 'lat': 25.7617, 'lon': -80.1918},
    'NEW ORLEANS FIELD OFFICE': {'city': 'New Orleans', 'state': 'LA', 'lat': 29.9511, 'lon': -90.0715},
    'NEW YORK FIELD OFFICE': {'city': 'New York', 'state': 'NY', 'lat': 40.7128, 'lon': -74.0060},
    'NOGALES FIELD OFFICE': {'city': 'Nogales', 'state': 'AZ', 'lat': 31.3404, 'lon': -110.9342},
    'PHILADELPHIA FIELD OFFICE': {'city': 'Philadelphia', 'state': 'PA', 'lat': 39.9526, 'lon': -75.1652},
    'PHOENIX FIELD OFFICE': {'city': 'Phoenix', 'state': 'AZ', 'lat': 33.4484, 'lon': -112.0740},
    'PORTLAND FIELD OFFICE': {'city': 'Portland', 'state': 'OR', 'lat': 45.5152, 'lon': -122.6784},
    'SAN DIEGO FIELD OFFICE': {'city': 'San Diego', 'state': 'CA', 'lat': 32.7157, 'lon': -117.1611},
    'SAN FRANCISCO FIELD OFFICE': {'city': 'San Francisco', 'state': 'CA', 'lat': 37.7749, 'lon': -122.4194},
    'SAN JUAN FIELD OFFICE': {'city': 'San Juan', 'state': 'PR', 'lat': 18.4655, 'lon': -66.1057},
    'SEATTLE FIELD OFFICE': {'city': 'Seattle', 'state': 'WA', 'lat': 47.6062, 'lon': -122.3321},
    'TUCSON FIELD OFFICE': {'city': 'Tucson', 'state': 'AZ', 'lat': 32.2226, 'lon': -110.9747},
    'WASHINGTON FIELD OFFICE': {'city': 'Washington', 'state': 'DC', 'lat': 38.9072, 'lon': -77.0369},
}


# Helper function to calculate distance between two points
def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Calculate distance between two points using Haversine formula
    Returns distance in kilometers
    """
    from math import radians, cos, sin, asin, sqrt
    
    # Convert to radians
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    
    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    
    # Radius of earth in kilometers
    r = 6371
    
    return c * r