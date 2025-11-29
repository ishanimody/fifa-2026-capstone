from flask import Blueprint, jsonify, request, current_app
from sqlalchemy import and_, func, text
from datetime import datetime
from sqlalchemy import text, func
from extensions import db
from models.models import WorldCupVenue, SmugglingIncident, DataSource
from flask import Blueprint, jsonify, request
from sqlalchemy import text, func
from models.models import db, NIBRSCrimeData, WorldCupVenue

# Note: NIBRSCrimeData will be imported when needed (after you add it to models.py)
# Uncomment this line after adding NIBRSCrimeData to models.py:
# from models.models import NIBRSCrimeData

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
"""
NIBRS Crime Data API Endpoints

ADD THESE ENDPOINTS TO: src/routes/api_routes.py

These endpoints serve FBI NIBRS crime statistics for the World Cup security analysis.
"""




# ADD THESE ROUTES TO YOUR EXISTING api_bp Blueprint in api_routes.py

@api_bp.route('/api/nibrs/statistics', methods=['GET'])
def get_nibrs_statistics():
    """
    Get overall NIBRS crime statistics
    
    Query Parameters:
        - year: Filter by year (e.g., 2024)
        - state: Filter by state (e.g., TEXAS)
        - limit: Number of results (default: 100)
    """
    try:
        year = request.args.get('year', type=int)
        state = request.args.get('state', type=str)
        limit = request.args.get('limit', default=100, type=int)
        
        # Base query
        query = db.session.query(NIBRSCrimeData)
        
        # Apply filters
        if year:
            query = query.filter(NIBRSCrimeData.year == year)
        if state:
            query = query.filter(NIBRSCrimeData.state == state.upper())
        
        # Get results
        results = query.limit(limit).all()
        
        # Calculate totals
        total_offenses = sum(r.total_offenses or 0 for r in results)
        total_violent = sum(r.crimes_against_persons or 0 for r in results)
        total_property = sum(r.crimes_against_property or 0 for r in results)
        total_homicides = sum(r.murder_nonnegligent_manslaughter or 0 for r in results)
        
        return jsonify({
            'success': True,
            'statistics': {
                'total_records': len(results),
                'total_offenses': total_offenses,
                'violent_crimes': total_violent,
                'property_crimes': total_property,
                'homicides': total_homicides,
            },
            'filters': {
                'year': year,
                'state': state,
                'limit': limit
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/api/nibrs/by-state', methods=['GET'])
def get_nibrs_by_state():
    """
    Get crime statistics aggregated by state
    
    Query Parameters:
        - year: Filter by year (default: latest year)
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
                'avg_risk_score': float(row.avg_risk_score or 0),
                'agency_count': int(row.agency_count)
            })
        
        # Sort by total offenses
        state_data.sort(key=lambda x: x['total_offenses'], reverse=True)
        
        return jsonify({
            'success': True,
            'data': state_data,
            'year': year
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/api/nibrs/high-risk-areas', methods=['GET'])
def get_high_risk_areas():
    """
    Get agencies with highest risk scores
    
    Query Parameters:
        - limit: Number of results (default: 20)
        - year: Filter by year
        - min_risk: Minimum risk score (default: 50)
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


@api_bp.route('/api/nibrs/venue-crime-analysis', methods=['GET'])
def analyze_venue_crime():
    """
    Analyze crime statistics near World Cup venues
    
    Query Parameters:
        - venue_id: Specific venue ID (optional)
        - radius_km: Search radius in km (default: 50)
        - year: Filter by year (default: latest)
    """
    try:
        venue_id = request.args.get('venue_id', type=int)
        radius_km = request.args.get('radius_km', default=50, type=float)
        year = request.args.get('year', default=2024, type=int)
        
        # Get venues
        if venue_id:
            venues = db.session.query(WorldCupVenue).filter_by(id=venue_id).all()
        else:
            venues = db.session.query(WorldCupVenue).all()
        
        venue_analysis = []
        
        for venue in venues:
            if not venue.latitude or not venue.longitude:
                continue
            
            # Find crime data near venue
            # Using simplified distance calculation (approximate)
            # For production, use PostGIS ST_Distance
            
            lat_range = radius_km / 111.0  # roughly 111 km per degree latitude
            lon_range = radius_km / (111.0 * abs(venue.latitude))
            
            nearby_crimes = db.session.query(NIBRSCrimeData).filter(
                NIBRSCrimeData.year == year,
                NIBRSCrimeData.latitude.isnot(None),
                NIBRSCrimeData.longitude.isnot(None),
                NIBRSCrimeData.latitude.between(
                    venue.latitude - lat_range,
                    venue.latitude + lat_range
                ),
                NIBRSCrimeData.longitude.between(
                    venue.longitude - lon_range,
                    venue.longitude + lon_range
                )
            ).all()
            
            # Calculate statistics
            total_offenses = sum(c.total_offenses or 0 for c in nearby_crimes)
            violent_crimes = sum(c.crimes_against_persons or 0 for c in nearby_crimes)
            homicides = sum(c.murder_nonnegligent_manslaughter or 0 for c in nearby_crimes)
            drug_crimes = sum(c.drug_narcotic_offenses or 0 for c in nearby_crimes)
            human_trafficking = sum(c.human_trafficking_offenses or 0 for c in nearby_crimes)
            
            avg_risk = sum(c.overall_risk_score or 0 for c in nearby_crimes) / len(nearby_crimes) if nearby_crimes else 0
            
            venue_analysis.append({
                'venue_id': venue.id,
                'venue_name': venue.venue_name,
                'city': venue.city,
                'state_province': venue.state_province,
                'country': venue.country,
                'latitude': venue.latitude,
                'longitude': venue.longitude,
                'crime_statistics': {
                    'agencies_nearby': len(nearby_crimes),
                    'total_offenses': total_offenses,
                    'violent_crimes': violent_crimes,
                    'homicides': homicides,
                    'drug_crimes': drug_crimes,
                    'human_trafficking': human_trafficking,
                    'avg_risk_score': round(avg_risk, 2)
                },
                'analysis': {
                    'radius_km': radius_km,
                    'year': year
                }
            })
        
        # Sort by total offenses
        venue_analysis.sort(key=lambda x: x['crime_statistics']['total_offenses'], reverse=True)
        
        return jsonify({
            'success': True,
            'data': venue_analysis,
            'total_venues': len(venue_analysis),
            'parameters': {
                'radius_km': radius_km,
                'year': year
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/api/nibrs/crime-trends', methods=['GET'])
def get_crime_trends():
    """
    Get crime trends over time (2020-2024)
    
    Query Parameters:
        - state: Filter by state (optional)
        - crime_type: Specific crime category (optional)
    """
    try:
        state = request.args.get('state', type=str)
        
        # Build query for yearly trends
        query = db.session.query(
            NIBRSCrimeData.year,
            func.sum(NIBRSCrimeData.total_offenses).label('total_offenses'),
            func.sum(NIBRSCrimeData.crimes_against_persons).label('violent_crimes'),
            func.sum(NIBRSCrimeData.murder_nonnegligent_manslaughter).label('homicides'),
            func.sum(NIBRSCrimeData.drug_narcotic_offenses).label('drug_crimes'),
            func.sum(NIBRSCrimeData.human_trafficking_offenses).label('human_trafficking')
        ).group_by(NIBRSCrimeData.year).order_by(NIBRSCrimeData.year)
        
        if state:
            query = query.filter(NIBRSCrimeData.state == state.upper())
        
        results = query.all()
        
        # Format trends
        trends = []
        for row in results:
            trends.append({
                'year': row.year,
                'total_offenses': int(row.total_offenses or 0),
                'violent_crimes': int(row.violent_crimes or 0),
                'homicides': int(row.homicides or 0),
                'drug_crimes': int(row.drug_crimes or 0),
                'human_trafficking': int(row.human_trafficking or 0)
            })
        
        return jsonify({
            'success': True,
            'data': trends,
            'state': state
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/api/nibrs/geojson', methods=['GET'])
def get_nibrs_geojson():
    """
    Get NIBRS data in GeoJSON format for mapping
    
    Query Parameters:
        - year: Filter by year (default: 2024)
        - min_risk: Minimum risk score (default: 60)
        - limit: Max features (default: 500)
    """
    try:
        year = request.args.get('year', default=2024, type=int)
        min_risk = request.args.get('min_risk', default=60, type=float)
        limit = request.args.get('limit', default=500, type=int)
        
        # Query high-risk agencies with coordinates
        results = db.session.query(NIBRSCrimeData).filter(
            NIBRSCrimeData.year == year,
            NIBRSCrimeData.overall_risk_score >= min_risk,
            NIBRSCrimeData.latitude.isnot(None),
            NIBRSCrimeData.longitude.isnot(None)
        ).order_by(
            NIBRSCrimeData.overall_risk_score.desc()
        ).limit(limit).all()
        
        # Build GeoJSON
        features = []
        for record in results:
            feature = {
                'type': 'Feature',
                'geometry': {
                    'type': 'Point',
                    'coordinates': [record.longitude, record.latitude]
                },
                'properties': {
                    'agency_name': record.agency_name,
                    'city': record.city,
                    'state': record.state,
                    'year': record.year,
                    'risk_score': round(record.overall_risk_score or 0, 2),
                    'total_offenses': record.total_offenses or 0,
                    'violent_crimes': record.crimes_against_persons or 0,
                    'homicides': record.murder_nonnegligent_manslaughter or 0,
                    'drug_crimes': record.drug_narcotic_offenses or 0,
                    'human_trafficking': record.human_trafficking_offenses or 0
                }
            }
            features.append(feature)
        
        geojson = {
            'type': 'FeatureCollection',
            'features': features,
            'metadata': {
                'year': year,
                'min_risk': min_risk,
                'count': len(features)
            }
        }
        
        return jsonify(geojson)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# At the END of src/routes/api_routes.py, add these 4 endpoints:

# ============================================================================
# NIBRS CRIME DATA API ENDPOINTS - ADD TO api_routes.py
# ============================================================================
# Add this code at the END of your src/routes/api_routes.py file

from sqlalchemy import func, and_, or_

@api_bp.route('/nibrs/geojson', methods=['GET'])
def get_nibrs_geojson():
    """
    Get NIBRS crime data in GeoJSON format for map visualization
    
    Query Parameters:
        - year: Filter by year (default: 2024)
        - min_risk: Minimum risk score (default: 50)
        - limit: Maximum records to return (default: 1000)
        - crime_type: Filter by crime type (violent, property, drug, all)
        - state: Filter by state
    
    Returns:
        GeoJSON FeatureCollection with crime locations
    """
    try:
        from models.models import NIBRSCrimeData
        
        # Get parameters
        year = request.args.get('year', default=2024, type=int)
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
        if state:
            query = query.filter(NIBRSCrimeData.state == state.upper())
        
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
    """Get crime statistics aggregated by state"""
    try:
        from models.models import NIBRSCrimeData
        
        year = request.args.get('year', type=int)
        
        # Build query
        query = db.session.query(
            NIBRSCrimeData.state,
            func.sum(NIBRSCrimeData.total_offenses).label('total_offenses'),
            func.sum(NIBRSCrimeData.crimes_against_persons).label('violent_crimes'),
            func.sum(NIBRSCrimeData.murder_nonnegligent_manslaughter).label('homicides'),
            func.sum(NIBRSCrimeData.drug_narcotic_offenses).label('drug_crimes'),
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
                'avg_risk_score': float(row.avg_risk_score or 0),
                'agency_count': int(row.agency_count)
            })
        
        # Sort by total offenses
        state_data.sort(key=lambda x: x['total_offenses'], reverse=True)
        
        return jsonify({
            'success': True,
            'data': state_data,
            'year': year
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/nibrs/high-risk-areas', methods=['GET'])
def get_high_risk_areas():
    """Get agencies with highest risk scores"""
    try:
        from models.models import NIBRSCrimeData
        
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

# Health check endpoint
@api_bp.route('/health', methods=['GET'])
def health_check():
    """API health check"""
    return jsonify({
        'success': True,
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat()
    })

