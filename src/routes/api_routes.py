"""
Flask API Routes for Geospatial Data
Provides endpoints for the interactive map

Place in: src/routes/api_routes.py
"""

from flask import Blueprint, jsonify, request, current_app
from sqlalchemy import and_, func
from datetime import datetime

api_bp = Blueprint('api', __name__, url_prefix='/api')


def get_db():
    """Get database session from current app"""
    from flask_sqlalchemy import SQLAlchemy
    return current_app.extensions['sqlalchemy']


@api_bp.route('/venues', methods=['GET'])
def get_venues():
    """Get all World Cup venues"""
    try:
        from models.models import WorldCupVenue
        db = get_db()
        
        venues = db.session.query(WorldCupVenue).all()
        
        venues_data = []
        for venue in venues:
            venues_data.append({
                'id': venue.id,
                'name': venue.venue_name,
                'city': venue.city,
                'state_province': venue.state_province,
                'country': venue.country,
                'latitude': venue.latitude,
                'longitude': venue.longitude,
                'capacity': venue.capacity,
                'host_matches': venue.host_matches,
                'security_risk_level': venue.security_risk_level,
                'region': venue.region
            })
        
        return jsonify({
            'success': True,
            'count': len(venues_data),
            'venues': venues_data
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/incidents', methods=['GET'])
def get_incidents():
    """Get smuggling incidents with optional filtering"""
    try:
        from models.models import SmugglingIncident
        db = get_db()
        
        # Get query parameters
        country = request.args.get('country')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        limit = int(request.args.get('limit', 1000))
        
        # Build query
        query = db.session.query(SmugglingIncident).filter(
            and_(
                SmugglingIncident.latitude.isnot(None),
                SmugglingIncident.longitude.isnot(None)
            )
        )
        
        # Apply filters
        if country:
            query = query.filter(SmugglingIncident.country.like(f'%{country}%'))
        
        if start_date:
            query = query.filter(SmugglingIncident.incident_date >= start_date)
        
        if end_date:
            query = query.filter(SmugglingIncident.incident_date <= end_date)
        
        # Limit results
        incidents = query.limit(limit).all()
        
        incidents_data = []
        for incident in incidents:
            incidents_data.append({
                'id': incident.id,
                'date': incident.incident_date.isoformat() if incident.incident_date else None,
                'latitude': incident.latitude,
                'longitude': incident.longitude,
                'location': incident.location_description,
                'country': incident.country,
                'region': incident.region,
                'dead': incident.number_dead,
                'missing': incident.number_missing,
                'survivors': incident.number_survivors,
                'cause_of_death': incident.cause_of_death
            })
        
        return jsonify({
            'success': True,
            'count': len(incidents_data),
            'incidents': incidents_data
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/heatmap', methods=['GET'])
def get_heatmap_data():
    """Get heat map data for visualization"""
    
    try:
        from utils.geo_analysis import GeospatialAnalyzer
        analyzer = GeospatialAnalyzer()
        
        # Get grid size from query params (default 1.0 degrees)
        grid_size = float(request.args.get('grid_size', 1.0))
        
        heat_data = analyzer.generate_heat_map_data(grid_size=grid_size)
        analyzer.close()
        
        return jsonify({
            'success': True,
            'count': len(heat_data),
            'heat_map': heat_data
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/venue/<int:venue_id>/nearby', methods=['GET'])
def get_nearby_incidents(venue_id):
    """Get incidents near a specific venue"""
    
    try:
        from utils.geo_analysis import GeospatialAnalyzer
        analyzer = GeospatialAnalyzer()
        
        # Get radius from query params (default 50km)
        radius_km = float(request.args.get('radius', 50))
        
        incidents = analyzer.find_incidents_near_venue(venue_id, radius_km)
        analyzer.close()
        
        return jsonify({
            'success': True,
            'venue_id': venue_id,
            'radius_km': radius_km,
            'count': len(incidents),
            'incidents': incidents
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/statistics', methods=['GET'])
def get_statistics():
    """Get overall statistics"""
    try:
        from models.models import WorldCupVenue, SmugglingIncident
        db = get_db()
        
        total_venues = db.session.query(WorldCupVenue).count()
        total_incidents = db.session.query(SmugglingIncident).count()
        
        total_dead = db.session.query(
            func.sum(SmugglingIncident.number_dead)
        ).scalar() or 0
        
        total_missing = db.session.query(
            func.sum(SmugglingIncident.number_missing)
        ).scalar() or 0
        
        # Get incidents by country
        by_country = db.session.query(
            SmugglingIncident.country,
            func.count(SmugglingIncident.id).label('count')
        ).filter(
            SmugglingIncident.country.isnot(None)
        ).group_by(
            SmugglingIncident.country
        ).order_by(
            func.count(SmugglingIncident.id).desc()
        ).limit(10).all()
        
        return jsonify({
            'success': True,
            'statistics': {
                'total_venues': total_venues,
                'total_incidents': total_incidents,
                'total_dead': int(total_dead),
                'total_missing': int(total_missing),
                'total_casualties': int(total_dead + total_missing),
                'top_countries': [
                    {'country': country, 'count': count} 
                    for country, count in by_country
                ]
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/risk-assessment', methods=['GET'])
def get_risk_assessment():
    """Get risk assessment for all venues"""
    
    try:
        from utils.geo_analysis import GeospatialAnalyzer
        analyzer = GeospatialAnalyzer()
        risk_data = analyzer.risk_assessment()
        analyzer.close()
        
        return jsonify({
            'success': True,
            'count': len(risk_data),
            'risk_assessment': risk_data
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/hotspots', methods=['GET'])
def get_hotspots():
    """Get smuggling hotspots"""
    
    try:
        from utils.geo_analysis import GeospatialAnalyzer
        analyzer = GeospatialAnalyzer()
        
        min_incidents = int(request.args.get('min_incidents', 10))
        hotspots = analyzer.identify_hotspots(min_incidents=min_incidents)
        analyzer.close()
        
        return jsonify({
            'success': True,
            'count': len(hotspots),
            'hotspots': hotspots
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/temporal-trends', methods=['GET'])
def get_temporal_trends():
    """Get temporal trends"""
    
    try:
        from utils.geo_analysis import GeospatialAnalyzer
        analyzer = GeospatialAnalyzer()
        
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        trends = analyzer.temporal_analysis(start_date=start_date, end_date=end_date)
        analyzer.close()
        
        return jsonify({
            'success': True,
            'trends': trends
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/border-crossings', methods=['GET'])
def get_border_crossings():
    """Get border crossing points (sample data for now)"""
    try:
        # Sample border crossing data
        # In production, this would come from database
        border_crossings = [
            {'id': 1, 'name': 'San Ysidro', 'type': 'official', 'border': 'USA-Mexico', 'lat': 32.5423, 'lon': -117.0325, 'status': 'open'},
            {'id': 2, 'name': 'El Paso', 'type': 'official', 'border': 'USA-Mexico', 'lat': 31.7619, 'lon': -106.4850, 'status': 'open'},
            {'id': 3, 'name': 'Laredo', 'type': 'official', 'border': 'USA-Mexico', 'lat': 27.5036, 'lon': -99.5075, 'status': 'open'},
            {'id': 4, 'name': 'Brownsville', 'type': 'official', 'border': 'USA-Mexico', 'lat': 25.9017, 'lon': -97.4975, 'status': 'open'},
            {'id': 5, 'name': 'Nogales', 'type': 'official', 'border': 'USA-Mexico', 'lat': 31.3404, 'lon': -110.9342, 'status': 'open'},
            {'id': 6, 'name': 'Detroit-Windsor', 'type': 'official', 'border': 'USA-Canada', 'lat': 42.3178, 'lon': -83.1336, 'status': 'open'},
            {'id': 7, 'name': 'Blaine', 'type': 'official', 'border': 'USA-Canada', 'lat': 49.0016, 'lon': -122.7469, 'status': 'open'},
        ]
        
        return jsonify({
            'success': True,
            'count': len(border_crossings),
            'border_crossings': border_crossings
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# Health check endpoint
@api_bp.route('/health', methods=['GET'])
def health_check():
    """API health check"""
    return jsonify({
        'success': True,
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat()
    })