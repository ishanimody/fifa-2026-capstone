
from flask import Blueprint, jsonify, request, current_app
from sqlalchemy import and_, func, text
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
        db = get_db()
        
        # Use text query as fallback if model import fails
        result = db.session.execute(text("""
            SELECT id, venue_name, city, state_province, country, 
                   latitude, longitude, capacity, host_matches, 
                   security_risk_level, region
            FROM worldcup_venues
        """))
        
        venues_data = []
        for row in result:
            venues_data.append({
                'id': row[0],
                'name': row[1],
                'city': row[2],
                'state_province': row[3],
                'country': row[4],
                'latitude': float(row[5]) if row[5] else None,
                'longitude': float(row[6]) if row[6] else None,
                'capacity': row[7],
                'host_matches': row[8],
                'security_risk_level': row[9],
                'region': row[10]
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
        db = get_db()
        
        # Get query parameters
        country = request.args.get('country')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        limit = int(request.args.get('limit', 1000))
        
        # Build SQL query
        sql = """
            SELECT id, incident_date, latitude, longitude, location_description,
                   country, region, number_dead, number_missing, number_survivors,
                   cause_of_death
            FROM smuggling_incidents
            WHERE latitude IS NOT NULL AND longitude IS NOT NULL
        """
        
        params = {}
        
        if country:
            sql += " AND country LIKE :country"
            params['country'] = f'%{country}%'
        
        if start_date:
            sql += " AND incident_date >= :start_date"
            params['start_date'] = start_date
        
        if end_date:
            sql += " AND incident_date <= :end_date"
            params['end_date'] = end_date
        
        sql += f" LIMIT :limit"
        params['limit'] = limit
        
        result = db.session.execute(text(sql), params)
        
        incidents_data = []
        for row in result:
            incidents_data.append({
                'id': row[0],
                'date': row[1].isoformat() if row[1] else None,
                'latitude': float(row[2]) if row[2] else None,
                'longitude': float(row[3]) if row[3] else None,
                'location': row[4],
                'country': row[5],
                'region': row[6],
                'dead': row[7] or 0,
                'missing': row[8] or 0,
                'survivors': row[9] or 0,
                'cause_of_death': row[10]
            })
        
        return jsonify({
            'success': True,
            'count': len(incidents_data),
            'incidents': incidents_data
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/statistics', methods=['GET'])
def get_statistics():
    """Get overall statistics"""
    try:
        db = get_db()
        
        # Get venue count
        venue_result = db.session.execute(text("SELECT COUNT(*) FROM worldcup_venues"))
        total_venues = venue_result.scalar()
        
        # Get incident statistics
        incident_result = db.session.execute(text("""
            SELECT COUNT(*) as total,
                   COALESCE(SUM(number_dead), 0) as dead,
                   COALESCE(SUM(number_missing), 0) as missing
            FROM smuggling_incidents
        """))
        inc_row = incident_result.fetchone()
        
        total_incidents = inc_row[0]
        total_dead = int(inc_row[1])
        total_missing = int(inc_row[2])
        
        # Get incidents by country
        country_result = db.session.execute(text("""
            SELECT country, COUNT(*) as count
            FROM smuggling_incidents
            WHERE country IS NOT NULL
            GROUP BY country
            ORDER BY count DESC
            LIMIT 10
        """))
        
        top_countries = [
            {'country': row[0], 'count': row[1]}
            for row in country_result
        ]
        
        return jsonify({
            'success': True,
            'statistics': {
                'total_venues': total_venues,
                'total_incidents': total_incidents,
                'total_dead': total_dead,
                'total_missing': total_missing,
                'total_casualties': total_dead + total_missing,
                'top_countries': top_countries
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/cbp-seizures', methods=['GET'])
def get_cbp_seizures():
    """Get CBP drug seizure data with optional filtering"""
    try:
        db = get_db()
        
        # Get query parameters
        drug_type = request.args.get('drug_type')
        year = request.args.get('year')
        office = request.args.get('office')
        limit = int(request.args.get('limit', 1000))
        
        # Build SQL query
        sql = """
            SELECT id, fiscal_year, month, latitude, longitude, city, state,
                   area_of_responsibility, drug_type, event_count, quantity_lbs, component
            FROM cbp_drug_seizures
            WHERE latitude IS NOT NULL AND longitude IS NOT NULL
        """
        
        params = {}
        
        if drug_type:
            sql += " AND drug_type LIKE :drug_type"
            params['drug_type'] = f'%{drug_type}%'
        
        if year:
            sql += " AND fiscal_year = :year"
            params['year'] = int(year)
        
        if office:
            sql += " AND area_of_responsibility LIKE :office"
            params['office'] = f'%{office}%'
        
        sql += f" LIMIT :limit"
        params['limit'] = limit
        
        result = db.session.execute(text(sql), params)
        
        seizures_data = []
        for row in result:
            seizures_data.append({
                'id': row[0],
                'year': row[1],
                'month': row[2],
                'latitude': float(row[3]) if row[3] else None,
                'longitude': float(row[4]) if row[4] else None,
                'city': row[5],
                'state': row[6],
                'office': row[7],
                'drug_type': row[8],
                'event_count': row[9] or 0,
                'quantity_lbs': float(row[10]) if row[10] else 0.0,
                'component': row[11]
            })
        
        return jsonify({
            'success': True,
            'count': len(seizures_data),
            'seizures': seizures_data
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/cbp-statistics', methods=['GET'])
def get_cbp_statistics():
    """Get CBP drug seizure statistics - FIXED VERSION"""
    try:
        db = get_db()
        
        # Get total records
        total_result = db.session.execute(text("SELECT COUNT(*) FROM cbp_drug_seizures"))
        total_seizures = total_result.scalar() or 0
        
        # Get sum of events and quantity
        stats_result = db.session.execute(text("""
            SELECT COALESCE(SUM(event_count), 0) as total_events,
                   COALESCE(SUM(quantity_lbs), 0) as total_quantity
            FROM cbp_drug_seizures
        """))
        stats_row = stats_result.fetchone()
        total_events = int(stats_row[0])
        total_quantity = float(stats_row[1])
        
        # Get top drug types
        drugs_result = db.session.execute(text("""
            SELECT drug_type,
                   SUM(event_count) as events,
                   SUM(quantity_lbs) as quantity
            FROM cbp_drug_seizures
            WHERE drug_type IS NOT NULL
            GROUP BY drug_type
            ORDER BY SUM(event_count) DESC
            LIMIT 10
        """))
        
        top_drugs = [
            {
                'drug_type': row[0],
                'events': int(row[1]),
                'quantity_lbs': round(float(row[2]), 2)
            }
            for row in drugs_result
        ]
        
        # Get top field offices
        offices_result = db.session.execute(text("""
            SELECT area_of_responsibility,
                   SUM(event_count) as events
            FROM cbp_drug_seizures
            WHERE area_of_responsibility IS NOT NULL
            GROUP BY area_of_responsibility
            ORDER BY SUM(event_count) DESC
            LIMIT 10
        """))
        
        top_offices = [
            {'office': row[0], 'events': int(row[1])}
            for row in offices_result
        ]
        
        return jsonify({
            'success': True,
            'statistics': {
                'total_records': total_seizures,
                'total_events': total_events,
                'total_quantity_lbs': round(total_quantity, 2),
                'top_drugs': top_drugs,
                'top_offices': top_offices
            }
        })
        
    except Exception as e:
        print(f"ERROR in /api/cbp-statistics: {str(e)}")  # Debug print
        import traceback
        traceback.print_exc()  # Print full traceback
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