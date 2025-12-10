"""
API Routes for World Cup 2026 Intelligence Platform
Includes: Venues, Incidents, CBP Drug Seizures, NIBRS Crime Data
"""

from flask import Blueprint, jsonify, request
from src.extensions import db
from sqlalchemy import func, desc
from datetime import datetime
from math import radians, cos, sin, asin, sqrt

# Import with CORRECT model names from your models.py
from models.models import WorldCupVenue, SmugglingIncident, CBPDrugSeizure, NIBRSCrimeData

# Create aliases for cleaner code
Venue = WorldCupVenue
Incident = SmugglingIncident

api_bp = Blueprint('api', __name__, url_prefix='/api')


# ============================================================================
# VENUES
# ============================================================================

@api_bp.route('/venues', methods=['GET'])
def get_venues():
    """Get all World Cup 2026 venues"""
    try:
        venues = db.session.query(Venue).all()
        
        venues_data = []
        for venue in venues:
            venues_data.append({
                'id': venue.id,
                'name': venue.venue_name,
                'city': venue.city,
                'country': venue.country,
                'capacity': venue.capacity,
                'latitude': float(venue.latitude) if venue.latitude else None,
                'longitude': float(venue.longitude) if venue.longitude else None
            })
        
        return jsonify({
            'success': True,
            'venues': venues_data,
            'count': len(venues_data)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================================
# INCIDENTS (IOM Missing Migrants / Smuggling Incidents)
# ============================================================================

@api_bp.route('/incidents', methods=['GET'])
def get_incidents():
    """Get migration/smuggling incidents with optional filters"""
    try:
        # Get query parameters
        country = request.args.get('country')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        incident_type = request.args.get('type')
        limit = request.args.get('limit', default=1000, type=int)
        
        # Build query
        query = db.session.query(Incident)
        
        # Apply filters
        if country:
            query = query.filter(Incident.country == country)
        
        if start_date:
            try:
                start_dt = datetime.strptime(start_date, '%Y-%m-%d')
                query = query.filter(Incident.incident_date >= start_dt)
            except ValueError:
                pass
        
        if end_date:
            try:
                end_dt = datetime.strptime(end_date, '%Y-%m-%d')
                query = query.filter(Incident.incident_date <= end_dt)
            except ValueError:
                pass
        
        if incident_type:
            query = query.filter(Incident.incident_type == incident_type)
        
        # Apply limit
        query = query.limit(limit)
        
        # Execute query
        incidents = query.all()
        
        # Format results
        incidents_data = []
        for incident in incidents:
            incidents_data.append({
                'id': incident.id,
                'date': incident.incident_date.isoformat() if incident.incident_date else None,
                'country': incident.country,
                'region': incident.region,
                'latitude': float(incident.latitude) if incident.latitude else None,
                'longitude': float(incident.longitude) if incident.longitude else None,
                'total_dead': incident.number_dead or 0,
                'total_missing': incident.number_missing or 0,
                'incident_type': incident.incident_type,
                'description': incident.location_description
            })
        
        return jsonify({
            'success': True,
            'incidents': incidents_data,
            'count': len(incidents_data),
            'filters': {
                'country': country,
                'start_date': start_date,
                'end_date': end_date,
                'type': incident_type,
                'limit': limit
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================================
# STATISTICS
# ============================================================================

@api_bp.route('/statistics', methods=['GET'])
def get_statistics():
    """Get overall platform statistics"""
    try:
        # Count venues
        total_venues = db.session.query(Venue).count()
        
        # Count incidents
        total_incidents = db.session.query(Incident).count()
        
        # Sum casualties
        casualties = db.session.query(
            func.coalesce(func.sum(Incident.number_dead), 0) + 
            func.coalesce(func.sum(Incident.number_missing), 0)
        ).scalar() or 0
        
        return jsonify({
            'success': True,
            'statistics': {
                'total_venues': total_venues,
                'total_incidents': total_incidents,
                'total_casualties': int(casualties)
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================================
# CBP DRUG SEIZURES
# ============================================================================

@api_bp.route('/cbp-seizures', methods=['GET'])
def get_cbp_seizures():
    """Get CBP drug seizure data with optional filters"""
    try:
        # Query parameters
        drug_type = request.args.get('drug_type')
        year = request.args.get('year', type=int)   # UI uses "year", DB uses fiscal_year
        state = request.args.get('state')
        limit = request.args.get('limit', default=10000, type=int)

        # Base query – only rows with coordinates
        query = db.session.query(CBPDrugSeizure).filter(
            CBPDrugSeizure.latitude.isnot(None),
            CBPDrugSeizure.longitude.isnot(None)
        )

        # Filters
        if drug_type:
            query = query.filter(CBPDrugSeizure.drug_type == drug_type)

        if year:
            # map "year" param → fiscal_year column
            query = query.filter(CBPDrugSeizure.fiscal_year == year)

        if state:
            query = query.filter(CBPDrugSeizure.state == state.upper())

        # Order and limit
        query = query.order_by(desc(CBPDrugSeizure.event_count)).limit(limit)

        seizures = query.all()

        seizures_data = []
        for s in seizures:
            seizures_data.append({
                'id': s.id,
                'year': s.fiscal_year,                     # ✅ correct field
                'month': s.month,
                'drug_type': s.drug_type,
                'office': s.area_of_responsibility,        # ✅ correct field
                'city': s.city,
                'state': s.state,
                'latitude': float(s.latitude) if s.latitude is not None else None,
                'longitude': float(s.longitude) if s.longitude is not None else None,
                'event_count': s.event_count or 0,
                'quantity_lbs': float(s.quantity_lbs or 0),
            })

        return jsonify({
            'success': True,
            'seizures': seizures_data,
            'count': len(seizures_data),
            'filters': {
                'drug_type': drug_type,
                'year': year,
                'state': state,
                'limit': limit,
            },
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
        }), 500


# ============================================================================
# NIBRS CRIME DATA
# ============================================================================

@api_bp.route('/nibrs/statistics', methods=['GET'])
def get_nibrs_statistics():
    """
    Get overall NIBRS crime statistics
    
    Query Parameters:
        - year: Filter by year (e.g., 2024)
        - state: Filter by state (e.g., TEXAS)
    
    Returns:
        JSON with total_records, total_offenses, violent_crimes, property_crimes, homicides
    """
    try:
        year = request.args.get('year', type=int)
        state = request.args.get('state', type=str)
        
        # Base query
        query = db.session.query(NIBRSCrimeData)
        
        # Apply filters
        if year:
            query = query.filter(NIBRSCrimeData.year == year)
        if state:
            query = query.filter(NIBRSCrimeData.state == state.upper())
        
        # Get all results
        results = query.all()
        
        # Calculate totals
        total_records = len(results)
        total_offenses = sum(r.total_offenses or 0 for r in results)
        total_violent = sum(r.crimes_against_persons or 0 for r in results)
        total_property = sum(r.crimes_against_property or 0 for r in results)
        total_homicides = sum(r.murder_nonnegligent_manslaughter or 0 for r in results)
        total_drug_crimes = sum(r.drug_narcotic_offenses or 0 for r in results)
        total_human_trafficking = sum(r.human_trafficking_offenses or 0 for r in results)
        
        return jsonify({
            'success': True,
            'statistics': {
                'total_records': total_records,
                'total_offenses': total_offenses,
                'violent_crimes': total_violent,
                'property_crimes': total_property,
                'homicides': total_homicides,
                'drug_crimes': total_drug_crimes,
                'human_trafficking': total_human_trafficking
            },
            'filters': {
                'year': year,
                'state': state
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/nibrs/geojson', methods=['GET'])
def get_nibrs_geojson():
    """
    Get NIBRS crime data in GeoJSON format for map visualization
    
    Query Parameters:
        - year: Filter by year (default: 2024)
        - min_risk: Minimum risk score (default: 50)
        - limit: Maximum records to return (default: 1000)
        - crime_type: Filter by crime type (violent, property, drug, human_trafficking, all)
        - state: Filter by state
    
    Returns:
        GeoJSON FeatureCollection with crime locations
    """
    try:
        # Get parameters
        year = request.args.get('year', type=int)
        start_year = request.args.get('start_year', type=int)
        end_year = request.args.get('end_year', type=int)
        min_risk = request.args.get('min_risk', default=50, type=float)
        limit = request.args.get('limit', default=1000, type=int)
        crime_type = request.args.get('crime_type', default='all', type=str)
        state = request.args.get('state', type=str)
        
        # Build query
        query = db.session.query(NIBRSCrimeData).filter(
            NIBRSCrimeData.latitude.isnot(None),
            NIBRSCrimeData.longitude.isnot(None),
            NIBRSCrimeData.overall_risk_score >= min_risk
        )
        
        # Apply year filter
        if year:
            query = query.filter(NIBRSCrimeData.year == year)
        
        # Apply state filter
        if year:
            query = query.filter(NIBRSCrimeData.year == year)
        elif start_year or end_year:
            if start_year:
                query = query.filter(NIBRSCrimeData.year >= start_year)
            if end_year:
                query = query.filter(NIBRSCrimeData.year <= end_year)
        
        # Apply crime type filter
        if crime_type == 'violent':
            query = query.filter(NIBRSCrimeData.crimes_against_persons > 0)
        elif crime_type == 'property':
            query = query.filter(NIBRSCrimeData.crimes_against_property > 0)
        elif crime_type == 'drug':
            query = query.filter(NIBRSCrimeData.drug_narcotic_offenses > 0)
        elif crime_type == 'human_trafficking':
            query = query.filter(NIBRSCrimeData.human_trafficking_offenses > 0)
        
        # Order by risk score and limit
        results = query.order_by(
            NIBRSCrimeData.overall_risk_score.desc()
        ).limit(limit).all()
        
        # Build GeoJSON
        features = []
        for record in results:
            features.append({
                'type': 'Feature',
                'geometry': {
                    'type': 'Point',
                    'coordinates': [float(record.longitude), float(record.latitude)]
                },
                'properties': {
                    'agency_name': record.agency_name,
                    'city': record.city,
                    'state': record.state,
                    'year': record.year,
                    'risk_score': float(record.overall_risk_score or 0),
                    'total_offenses': record.total_offenses or 0,
                    'violent_crimes': record.crimes_against_persons or 0,
                    'property_crimes': record.crimes_against_property or 0,
                    'homicides': record.murder_nonnegligent_manslaughter or 0,
                    'human_trafficking': record.human_trafficking_offenses or 0,
                    'drug_crimes': record.drug_narcotic_offenses or 0
                }
            })
        
        return jsonify({
            'success': True,
            'type': 'FeatureCollection',
            'features': features,
            'filters': {
                'year': year,
                'min_risk': min_risk,
                'crime_type': crime_type,
                'state': state,
                'limit': limit
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'features': []
        }), 500


@api_bp.route('/nibrs/by-state', methods=['GET'])
def get_nibrs_by_state():
    """
    Get crime statistics aggregated by state
    
    Query Parameters:
        - year: Filter by year (optional)
    
    Returns:
        Array of state statistics with totals and averages
    """
    try:
        year = request.args.get('year', type=int)
        
        # Build query
        query = db.session.query(
            NIBRSCrimeData.state,
            func.sum(NIBRSCrimeData.total_offenses).label('total_offenses'),
            func.sum(NIBRSCrimeData.crimes_against_persons).label('violent_crimes'),
            func.sum(NIBRSCrimeData.murder_nonnegligent_manslaughter).label('homicides'),
            func.sum(NIBRSCrimeData.drug_narcotic_offenses).label('drug_crimes'),
            func.sum(NIBRSCrimeData.human_trafficking_offenses).label('human_trafficking'),
            func.avg(NIBRSCrimeData.overall_risk_score).label('avg_risk_score'),
            func.count(NIBRSCrimeData.id).label('agency_count')
        ).group_by(NIBRSCrimeData.state)
        
        if year:
            query = query.filter(NIBRSCrimeData.year == year)
        
        results = query.all()
        
        # Format results
        state_data = []
        for row in results:
            state_data.append({
                'state': row.state,
                'total_offenses': int(row.total_offenses or 0),
                'violent_crimes': int(row.violent_crimes or 0),
                'homicides': int(row.homicides or 0),
                'drug_crimes': int(row.drug_crimes or 0),
                'human_trafficking': int(row.human_trafficking or 0),
                'avg_risk_score': float(row.avg_risk_score or 0),
                'agency_count': int(row.agency_count)
            })
        
        # Sort by total offenses
        state_data.sort(key=lambda x: x['total_offenses'], reverse=True)
        
        return jsonify({
            'success': True,
            'data': state_data,
            'count': len(state_data),
            'year': year
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/nibrs/high-risk-areas', methods=['GET'])
def get_high_risk_areas():
    """
    Get agencies with highest risk scores
    
    Query Parameters:
        - limit: Number of results (default: 20)
        - year: Filter by year (optional)
        - min_risk: Minimum risk score (default: 50)
    
    Returns:
        Array of high-risk agencies sorted by risk score
    """
    try:
        limit = request.args.get('limit', default=20, type=int)
        year = request.args.get('year', type=int)
        min_risk = request.args.get('min_risk', default=50, type=float)
        
        # Build query
        query = db.session.query(NIBRSCrimeData).filter(
            NIBRSCrimeData.overall_risk_score >= min_risk
        )
        
        if year:
            query = query.filter(NIBRSCrimeData.year == year)
        
        results = query.order_by(
            NIBRSCrimeData.overall_risk_score.desc()
        ).limit(limit).all()
        
        # Format results
        high_risk_areas = []
        for record in results:
            high_risk_areas.append({
                'agency_name': record.agency_name,
                'city': record.city,
                'state': record.state,
                'year': record.year,
                'risk_score': round(record.overall_risk_score or 0, 2),
                'total_offenses': record.total_offenses or 0,
                'violent_crimes': record.crimes_against_persons or 0,
                'homicides': record.murder_nonnegligent_manslaughter or 0,
                'human_trafficking': record.human_trafficking_offenses or 0,
                'drug_crimes': record.drug_narcotic_offenses or 0,
                'latitude': record.latitude,
                'longitude': record.longitude
            })
        
        return jsonify({
            'success': True,
            'data': high_risk_areas,
            'count': len(high_risk_areas),
            'filters': {
                'min_risk': min_risk,
                'year': year,
                'limit': limit
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================================
# HEALTH CHECK
# ============================================================================

@api_bp.route('/health', methods=['GET'])
def health_check():
    """API health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'message': 'World Cup 2026 Intelligence Platform API is running',
        'models': {
            'WorldCupVenue': True,
            'SmugglingIncident': True,
            'CBPDrugSeizure': True,
            'NIBRSCrimeData': True
        },
        'endpoints': {
            'venues': '/api/venues',
            'incidents': '/api/incidents',
            'statistics': '/api/statistics',
            'cbp_seizures': '/api/cbp-seizures',
            'cbp_statistics': '/api/cbp-statistics',
            'nibrs_statistics': '/api/nibrs/statistics',
            'nibrs_geojson': '/api/nibrs/geojson',
            'nibrs_by_state': '/api/nibrs/by-state',
            'nibrs_high_risk': '/api/nibrs/high-risk-areas'
        }
    })

def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate distance in miles between two lat/lon points"""
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    return c * 3956  # Earth radius in miles

@api_bp.route('/nibrs/near-venues', methods=['GET'])
def get_nibrs_near_venues():
    """Get NIBRS data within distance of World Cup venues"""
    try:
        max_distance = request.args.get('distance', default=100, type=float)
        min_risk = request.args.get('min_risk', default=0, type=float)
        limit = request.args.get('limit', default=5000, type=int)
        crime_type = request.args.get('crime_type', default='all', type=str)
        start_year = request.args.get('start_year', type=int)
        end_year = request.args.get('end_year', type=int)
        
        # Get all venues
        venues = db.session.query(Venue).filter(
            Venue.latitude.isnot(None),
            Venue.longitude.isnot(None)
        ).all()
        
        if not venues:
            return jsonify({'success': False, 'error': 'No venues found', 'features': []}), 404
        
        # Build NIBRS query
        query = db.session.query(NIBRSCrimeData).filter(
            NIBRSCrimeData.latitude.isnot(None),
            NIBRSCrimeData.longitude.isnot(None),
            NIBRSCrimeData.overall_risk_score >= min_risk
        )
        
        # Apply year filters
        if start_year:
            query = query.filter(NIBRSCrimeData.year >= start_year)
        if end_year:
            query = query.filter(NIBRSCrimeData.year <= end_year)
        
        # Apply crime type filter
        if crime_type == 'violent':
            query = query.filter(NIBRSCrimeData.crimes_against_persons > 0)
        elif crime_type == 'property':
            query = query.filter(NIBRSCrimeData.crimes_against_property > 0)
        elif crime_type == 'drug':
            query = query.filter(NIBRSCrimeData.drug_narcotic_offenses > 0)
        elif crime_type == 'human_trafficking':
            query = query.filter(NIBRSCrimeData.human_trafficking_offenses > 0)
        
        all_records = query.order_by(NIBRSCrimeData.overall_risk_score.desc()).limit(limit * 3).all()
        
        # Filter by distance
        filtered_records = []
        for record in all_records:
            record_lat = float(record.latitude)
            record_lon = float(record.longitude)
            
            for venue in venues:
                distance = haversine_distance(
                    record_lat, record_lon,
                    float(venue.latitude), float(venue.longitude)
                )
                
                if distance <= max_distance:
                    filtered_records.append({
                        'record': record,
                        'nearest_venue': venue.venue_name,
                        'distance_miles': round(distance, 1)
                    })
                    break
            
            if len(filtered_records) >= limit:
                break
        
        # Build GeoJSON
        features = []
        for item in filtered_records:
            record = item['record']
            features.append({
                'type': 'Feature',
                'geometry': {
                    'type': 'Point',
                    'coordinates': [float(record.longitude), float(record.latitude)]
                },
                'properties': {
                    'agency_name': record.agency_name,
                    'city': record.city,
                    'state': record.state,
                    'year': record.year,
                    'risk_score': float(record.overall_risk_score or 0),
                    'total_offenses': record.total_offenses or 0,
                    'violent_crimes': record.crimes_against_persons or 0,
                    'property_crimes': record.crimes_against_property or 0,
                    'homicides': record.murder_nonnegligent_manslaughter or 0,
                    'human_trafficking': record.human_trafficking_offenses or 0,
                    'drug_crimes': record.drug_narcotic_offenses or 0,
                    'nearest_venue': item['nearest_venue'],
                    'distance_to_venue': item['distance_miles']
                }
            })
        
        return jsonify({
            'success': True,
            'type': 'FeatureCollection',
            'features': features,
            'metadata': {  # ← Make sure this exists
                'total_records': len(features),
                'max_distance_miles': max_distance,
                'venues_count': len(venues)
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e), 'features': []}), 500