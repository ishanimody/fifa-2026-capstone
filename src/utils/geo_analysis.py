"""
Geospatial Analysis Functions
Advanced spatial queries and analysis for smuggling intelligence

Place in: src/utils/geo_analysis.py
"""

import sys
sys.path.append('src')

from sqlalchemy import create_engine, func, and_, or_
from sqlalchemy.orm import sessionmaker
from models.models import WorldCupVenue, SmugglingIncident, DataSource
from datetime import datetime, timedelta
import pandas as pd
from typing import List, Dict, Tuple, Optional
import os
from dotenv import load_dotenv
import math

load_dotenv()


class GeospatialAnalyzer:
    """Geospatial analysis for smuggling intelligence"""
    
    def __init__(self, db_url=None):
        if db_url is None:
            db_url = os.getenv('DATABASE_URL', 'sqlite:///worldcup_intelligence.db')
        
        self.engine = create_engine(db_url, echo=False)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
    
    def calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate distance between two points using Haversine formula
        Returns distance in kilometers
        """
        # Convert to radians
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        # Radius of Earth in kilometers
        r = 6371
        
        return c * r
    
    def find_incidents_near_venue(self, venue_id: int, radius_km: float = 50) -> List[Dict]:
        """
        Find all incidents within specified radius of a venue
        
        Args:
            venue_id: ID of the World Cup venue
            radius_km: Search radius in kilometers (default 50km)
            
        Returns:
            List of incidents with distance information
        """
        venue = self.session.query(WorldCupVenue).get(venue_id)
        if not venue:
            return []
        
        # Get all incidents with coordinates
        incidents = self.session.query(SmugglingIncident).filter(
            and_(
                SmugglingIncident.latitude.isnot(None),
                SmugglingIncident.longitude.isnot(None)
            )
        ).all()
        
        # Calculate distances and filter
        nearby_incidents = []
        for incident in incidents:
            distance = self.calculate_distance(
                venue.latitude, venue.longitude,
                incident.latitude, incident.longitude
            )
            
            if distance <= radius_km:
                nearby_incidents.append({
                    'incident_id': incident.id,
                    'incident_date': incident.incident_date,
                    'location_description': incident.location_description,
                    'distance_km': round(distance, 2),
                    'number_dead': incident.number_dead,
                    'number_missing': incident.number_missing,
                    'latitude': incident.latitude,
                    'longitude': incident.longitude
                })
        
        # Sort by distance
        nearby_incidents.sort(key=lambda x: x['distance_km'])
        
        return nearby_incidents
    
    def analyze_all_venues(self, radius_km: float = 50) -> Dict:
        """
        Analyze incidents near all World Cup venues
        
        Args:
            radius_km: Search radius in kilometers
            
        Returns:
            Dictionary with analysis results for each venue
        """
        venues = self.session.query(WorldCupVenue).all()
        
        analysis_results = {}
        
        for venue in venues:
            incidents = self.find_incidents_near_venue(venue.id, radius_km)
            
            total_casualties = sum(
                (inc.get('number_dead', 0) + inc.get('number_missing', 0)) 
                for inc in incidents
            )
            
            analysis_results[venue.venue_name] = {
                'venue_id': venue.id,
                'city': venue.city,
                'country': venue.country,
                'security_risk_level': venue.security_risk_level,
                'incidents_within_radius': len(incidents),
                'total_casualties': total_casualties,
                'closest_incident_km': incidents[0]['distance_km'] if incidents else None,
                'incidents': incidents[:5]  # Top 5 closest
            }
        
        return analysis_results
    
    def generate_heat_map_data(self, grid_size: float = 1.0) -> List[Dict]:
        """
        Generate heat map data by aggregating incidents into grid cells
        
        Args:
            grid_size: Size of grid cells in degrees (default 1.0)
            
        Returns:
            List of grid cells with incident counts
        """
        incidents = self.session.query(SmugglingIncident).filter(
            and_(
                SmugglingIncident.latitude.isnot(None),
                SmugglingIncident.longitude.isnot(None)
            )
        ).all()
        
        # Group incidents into grid cells
        grid_data = {}
        
        for incident in incidents:
            # Round coordinates to grid
            grid_lat = round(incident.latitude / grid_size) * grid_size
            grid_lon = round(incident.longitude / grid_size) * grid_size
            grid_key = (grid_lat, grid_lon)
            
            if grid_key not in grid_data:
                grid_data[grid_key] = {
                    'latitude': grid_lat,
                    'longitude': grid_lon,
                    'incident_count': 0,
                    'total_dead': 0,
                    'total_missing': 0
                }
            
            grid_data[grid_key]['incident_count'] += 1
            grid_data[grid_key]['total_dead'] += incident.number_dead or 0
            grid_data[grid_key]['total_missing'] += incident.number_missing or 0
        
        # Convert to list and add intensity
        heat_map_data = []
        for cell in grid_data.values():
            cell['intensity'] = cell['incident_count']
            cell['total_casualties'] = cell['total_dead'] + cell['total_missing']
            heat_map_data.append(cell)
        
        # Sort by intensity
        heat_map_data.sort(key=lambda x: x['intensity'], reverse=True)
        
        return heat_map_data
    
    def identify_hotspots(self, min_incidents: int = 10) -> List[Dict]:
        """
        Identify smuggling hotspots (areas with high incident concentration)
        
        Args:
            min_incidents: Minimum incidents to qualify as hotspot
            
        Returns:
            List of hotspot locations
        """
        heat_data = self.generate_heat_map_data(grid_size=0.5)
        
        hotspots = [
            cell for cell in heat_data 
            if cell['incident_count'] >= min_incidents
        ]
        
        return hotspots
    
    def temporal_analysis(self, start_date=None, end_date=None) -> Dict:
        """
        Analyze incident trends over time
        
        Args:
            start_date: Start date for analysis
            end_date: End date for analysis
            
        Returns:
            Dictionary with temporal trends
        """
        query = self.session.query(SmugglingIncident).filter(
            SmugglingIncident.incident_date.isnot(None)
        )
        
        if start_date:
            query = query.filter(SmugglingIncident.incident_date >= start_date)
        if end_date:
            query = query.filter(SmugglingIncident.incident_date <= end_date)
        
        incidents = query.all()
        
        # Group by year and month
        temporal_data = {}
        
        for incident in incidents:
            year = incident.incident_year
            month = incident.incident_month
            
            if year and month:
                key = f"{year}-{month:02d}"
                
                if key not in temporal_data:
                    temporal_data[key] = {
                        'year': year,
                        'month': month,
                        'incident_count': 0,
                        'total_dead': 0,
                        'total_missing': 0
                    }
                
                temporal_data[key]['incident_count'] += 1
                temporal_data[key]['total_dead'] += incident.number_dead or 0
                temporal_data[key]['total_missing'] += incident.number_missing or 0
        
        # Convert to sorted list
        temporal_trends = sorted(temporal_data.values(), key=lambda x: (x['year'], x['month']))
        
        return {
            'total_incidents': len(incidents),
            'date_range': {
                'start': min([i.incident_date for i in incidents if i.incident_date]),
                'end': max([i.incident_date for i in incidents if i.incident_date])
            },
            'monthly_trends': temporal_trends
        }
    
    def risk_assessment(self) -> List[Dict]:
        """
        Assess risk levels for each World Cup venue based on nearby incidents
        
        Returns:
            List of venues with calculated risk scores
        """
        venue_analysis = self.analyze_all_venues(radius_km=100)
        
        risk_assessments = []
        
        for venue_name, data in venue_analysis.items():
            # Calculate risk score (0-100)
            incident_score = min(data['incidents_within_radius'] * 2, 50)
            casualty_score = min(data['total_casualties'] / 10, 30)
            
            # Adjust by existing risk level
            risk_multiplier = {
                'Low': 0.8,
                'Medium': 1.0,
                'High': 1.2
            }.get(data['security_risk_level'], 1.0)
            
            total_risk_score = (incident_score + casualty_score) * risk_multiplier
            
            # Categorize risk
            if total_risk_score < 30:
                calculated_risk = 'Low'
            elif total_risk_score < 60:
                calculated_risk = 'Medium'
            else:
                calculated_risk = 'High'
            
            risk_assessments.append({
                'venue_name': venue_name,
                'city': data['city'],
                'country': data['country'],
                'current_risk_level': data['security_risk_level'],
                'calculated_risk_score': round(total_risk_score, 2),
                'calculated_risk_level': calculated_risk,
                'incidents_within_100km': data['incidents_within_radius'],
                'total_casualties_nearby': data['total_casualties'],
                'closest_incident_km': data['closest_incident_km']
            })
        
        # Sort by risk score
        risk_assessments.sort(key=lambda x: x['calculated_risk_score'], reverse=True)
        
        return risk_assessments
    
    def generate_summary_report(self) -> Dict:
        """Generate comprehensive summary report"""
        
        total_venues = self.session.query(WorldCupVenue).count()
        total_incidents = self.session.query(SmugglingIncident).count()
        
        # Get date range
        incidents_with_dates = self.session.query(SmugglingIncident).filter(
            SmugglingIncident.incident_date.isnot(None)
        ).all()
        
        if incidents_with_dates:
            min_date = min([i.incident_date for i in incidents_with_dates])
            max_date = max([i.incident_date for i in incidents_with_dates])
        else:
            min_date = max_date = None
        
        # Calculate totals
        total_dead = self.session.query(
            func.sum(SmugglingIncident.number_dead)
        ).scalar() or 0
        
        total_missing = self.session.query(
            func.sum(SmugglingIncident.number_missing)
        ).scalar() or 0
        
        # Get hotspots
        hotspots = self.identify_hotspots(min_incidents=5)
        
        # Get risk assessments
        risk_data = self.risk_assessment()
        
        return {
            'overview': {
                'total_venues': total_venues,
                'total_incidents': total_incidents,
                'total_casualties': int(total_dead + total_missing),
                'total_dead': int(total_dead),
                'total_missing': int(total_missing),
                'date_range': {
                    'earliest': str(min_date) if min_date else None,
                    'latest': str(max_date) if max_date else None
                }
            },
            'hotspots': hotspots[:10],  # Top 10 hotspots
            'high_risk_venues': [v for v in risk_data if v['calculated_risk_level'] == 'High'],
            'venue_risk_summary': {
                'High': len([v for v in risk_data if v['calculated_risk_level'] == 'High']),
                'Medium': len([v for v in risk_data if v['calculated_risk_level'] == 'Medium']),
                'Low': len([v for v in risk_data if v['calculated_risk_level'] == 'Low'])
            }
        }
    
    def close(self):
        """Close database session"""
        self.session.close()


# Convenience functions
def analyze_venue_proximity(venue_id: int, radius_km: float = 50):
    """Quick function to analyze incidents near a venue"""
    analyzer = GeospatialAnalyzer()
    results = analyzer.find_incidents_near_venue(venue_id, radius_km)
    analyzer.close()
    return results


def get_summary_report():
    """Quick function to get summary report"""
    analyzer = GeospatialAnalyzer()
    report = analyzer.generate_summary_report()
    analyzer.close()
    return report


if __name__ == "__main__":
    # Example usage
    analyzer = GeospatialAnalyzer()
    
    print("=" * 60)
    print("GEOSPATIAL ANALYSIS REPORT")
    print("=" * 60)
    
    # Generate summary report
    report = analyzer.generate_summary_report()
    
    print("\nOVERVIEW:")
    print(f"  Total Venues: {report['overview']['total_venues']}")
    print(f"  Total Incidents: {report['overview']['total_incidents']}")
    print(f"  Total Casualties: {report['overview']['total_casualties']}")
    
    print("\nHOTSPOTS (Top 5):")
    for idx, hotspot in enumerate(report['hotspots'][:5], 1):
        print(f"  {idx}. ({hotspot['latitude']}, {hotspot['longitude']})")
        print(f"     Incidents: {hotspot['incident_count']}, Casualties: {hotspot['total_casualties']}")
    
    print("\nHIGH RISK VENUES:")
    for venue in report['high_risk_venues']:
        print(f"  - {venue['venue_name']} ({venue['city']}, {venue['country']})")
        print(f"    Risk Score: {venue['calculated_risk_score']}")
        print(f"    Incidents within 100km: {venue['incidents_within_100km']}")
    
    print("\n" + "=" * 60)
    
    analyzer.close()