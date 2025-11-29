"""
World Cup Venue Crime Analysis Script

Analyzes FBI NIBRS crime data in relation to World Cup 2026 venues
to provide security risk assessments.

Place in: scripts/analyze_venue_crime.py

Usage:
    python scripts/analyze_venue_crime.py
"""

import sys
import os
sys.path.append('src')

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import pandas as pd
from datetime import datetime
import json
from dotenv import load_dotenv
from math import radians, cos, sin, asin, sqrt

load_dotenv()


def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Calculate distance between two points using Haversine formula
    Returns distance in kilometers
    """
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


def analyze_venue_crime(db_url=None, radius_km=50, year=2024):
    """
    Analyze crime statistics near World Cup venues
    
    Args:
        db_url: Database URL
        radius_km: Radius to search around each venue
        year: Year of crime data to analyze
    """
    
    print("=" * 80)
    print("WORLD CUP 2026 - VENUE CRIME SECURITY ANALYSIS")
    print("=" * 80)
    
    # Get database URL
    if db_url is None:
        db_url = os.getenv('DATABASE_URL', 'postgresql://wcuser:password@localhost:5432/worldcup_intelligence')
    
    print(f"\nDatabase: {db_url.split('@')[1] if '@' in db_url else db_url}")
    print(f"Analysis Parameters:")
    print(f"  - Search Radius: {radius_km} km")
    print(f"  - Year: {year}")
    
    # Connect to database
    print(f"\n1. Connecting to database...")
    
    try:
        engine = create_engine(db_url, echo=False)
        Session = sessionmaker(bind=engine)
        session = Session()
        print(f"   ✓ Connected")
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
        return False
    
    # Get venues
    print(f"\n2. Loading World Cup venues...")
    
    try:
        venues_query = """
            SELECT id, venue_name, city, state_province, country, 
                   latitude, longitude, capacity, host_matches
            FROM worldcup_venues
            ORDER BY country, city
        """
        venues_df = pd.read_sql(venues_query, engine)
        print(f"   ✓ Loaded {len(venues_df)} venues")
    except Exception as e:
        print(f"   ❌ Error loading venues: {e}")
        return False
    
    # Get crime data
    print(f"\n3. Loading NIBRS crime data for {year}...")
    
    try:
        crime_query = f"""
            SELECT agency_name, city, state, latitude, longitude,
                   total_offenses, crimes_against_persons, crimes_against_property,
                   murder_nonnegligent_manslaughter, aggravated_assault,
                   human_trafficking_offenses, drug_narcotic_offenses,
                   overall_risk_score
            FROM nibrs_crime_data
            WHERE year = {year}
              AND latitude IS NOT NULL
              AND longitude IS NOT NULL
            ORDER BY overall_risk_score DESC
        """
        crime_df = pd.read_sql(crime_query, engine)
        print(f"   ✓ Loaded {len(crime_df):,} crime records")
    except Exception as e:
        print(f"   ❌ Error loading crime data: {e}")
        print(f"   Make sure you've run: python scripts/load_nibrs_data.py")
        return False
    
    # Analyze each venue
    print(f"\n4. Analyzing crime within {radius_km}km of each venue...")
    print(f"   " + "-" * 76)
    
    venue_analysis = []
    
    for idx, venue in venues_df.iterrows():
        venue_lat = venue['latitude']
        venue_lon = venue['longitude']
        
        if pd.isna(venue_lat) or pd.isna(venue_lon):
            continue
        
        # Find nearby crime agencies
        nearby_crimes = []
        
        for _, crime in crime_df.iterrows():
            crime_lat = crime['latitude']
            crime_lon = crime['longitude']
            
            if pd.isna(crime_lat) or pd.isna(crime_lon):
                continue
            
            distance = calculate_distance(venue_lat, venue_lon, crime_lat, crime_lon)
            
            if distance <= radius_km:
                crime_data = crime.to_dict()
                crime_data['distance_km'] = distance
                nearby_crimes.append(crime_data)
        
        # Calculate statistics
        if nearby_crimes:
            total_offenses = sum(c['total_offenses'] or 0 for c in nearby_crimes)
            violent_crimes = sum(c['crimes_against_persons'] or 0 for c in nearby_crimes)
            homicides = sum(c['murder_nonnegligent_manslaughter'] or 0 for c in nearby_crimes)
            drug_crimes = sum(c['drug_narcotic_offenses'] or 0 for c in nearby_crimes)
            human_trafficking = sum(c['human_trafficking_offenses'] or 0 for c in nearby_crimes)
            avg_risk = sum(c['overall_risk_score'] or 0 for c in nearby_crimes) / len(nearby_crimes)
            
            # Sort by distance
            nearby_crimes.sort(key=lambda x: x['distance_km'])
            closest = nearby_crimes[0] if nearby_crimes else None
        else:
            total_offenses = 0
            violent_crimes = 0
            homicides = 0
            drug_crimes = 0
            human_trafficking = 0
            avg_risk = 0
            closest = None
        
        analysis = {
            'venue_id': int(venue['id']),
            'venue_name': venue['venue_name'],
            'city': venue['city'],
            'state_province': venue['state_province'],
            'country': venue['country'],
            'latitude': float(venue['latitude']),
            'longitude': float(venue['longitude']),
            'capacity': int(venue['capacity']) if pd.notna(venue['capacity']) else None,
            'host_matches': int(venue['host_matches']) if pd.notna(venue['host_matches']) else None,
            'crime_analysis': {
                'agencies_nearby': len(nearby_crimes),
                'total_offenses': int(total_offenses),
                'violent_crimes': int(violent_crimes),
                'homicides': int(homicides),
                'drug_crimes': int(drug_crimes),
                'human_trafficking': int(human_trafficking),
                'avg_risk_score': float(avg_risk),
                'radius_km': radius_km
            }
        }
        
        if closest:
            analysis['closest_high_crime_area'] = {
                'agency_name': closest['agency_name'],
                'city': closest['city'],
                'state': closest['state'],
                'distance_km': round(closest['distance_km'], 2),
                'risk_score': float(closest['overall_risk_score'] or 0),
                'total_offenses': int(closest['total_offenses'] or 0)
            }
        
        # Categorize risk
        if avg_risk >= 70 or homicides >= 50:
            analysis['risk_category'] = 'HIGH'
        elif avg_risk >= 50 or homicides >= 20:
            analysis['risk_category'] = 'MEDIUM-HIGH'
        elif avg_risk >= 30:
            analysis['risk_category'] = 'MEDIUM'
        else:
            analysis['risk_category'] = 'LOW-MEDIUM'
        
        venue_analysis.append(analysis)
        
        # Print summary
        risk_emoji = {
            'HIGH': '🔴',
            'MEDIUM-HIGH': '🟠',
            'MEDIUM': '🟡',
            'LOW-MEDIUM': '🟢'
        }
        
        print(f"\n   {risk_emoji[analysis['risk_category']]} {venue['venue_name']}")
        print(f"      {venue['city']}, {venue['country']}")
        print(f"      Risk Level: {analysis['risk_category']}")
        print(f"      Agencies nearby: {len(nearby_crimes)}")
        print(f"      Total offenses: {total_offenses:,}")
        print(f"      Violent crimes: {violent_crimes:,} | Homicides: {homicides}")
        if closest:
            print(f"      Closest high-crime: {closest['city']}, {closest['state']} ({closest['distance_km']:.1f} km)")
    
    # Sort by risk
    venue_analysis.sort(key=lambda x: x['crime_analysis']['avg_risk_score'], reverse=True)
    
    # Generate summary report
    print(f"\n" + "=" * 80)
    print("SECURITY RISK SUMMARY")
    print("=" * 80)
    
    risk_counts = {}
    for v in venue_analysis:
        risk_counts[v['risk_category']] = risk_counts.get(v['risk_category'], 0) + 1
    
    print(f"\nVenues by Risk Category:")
    for category in ['HIGH', 'MEDIUM-HIGH', 'MEDIUM', 'LOW-MEDIUM']:
        count = risk_counts.get(category, 0)
        if count > 0:
            print(f"  {category}: {count} venues")
    
    print(f"\nTop 5 Highest Risk Venues:")
    for i, venue in enumerate(venue_analysis[:5], 1):
        print(f"\n  {i}. {venue['venue_name']} ({venue['city']}, {venue['country']})")
        print(f"     Risk Category: {venue['risk_category']}")
        print(f"     Avg Risk Score: {venue['crime_analysis']['avg_risk_score']:.1f}/100")
        print(f"     Total Offenses: {venue['crime_analysis']['total_offenses']:,}")
        print(f"     Violent Crimes: {venue['crime_analysis']['violent_crimes']:,}")
        print(f"     Homicides: {venue['crime_analysis']['homicides']}")
    
    # Save results
    print(f"\n" + "=" * 80)
    print("SAVING RESULTS")
    print("=" * 80)
    
    # Create reports directory
    os.makedirs('reports', exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Save as JSON
    json_file = f'reports/venue_crime_analysis_{year}_{timestamp}.json'
    with open(json_file, 'w') as f:
        json.dump({
            'analysis_date': datetime.now().isoformat(),
            'parameters': {
                'radius_km': radius_km,
                'year': year
            },
            'venues': venue_analysis,
            'summary': {
                'total_venues': len(venue_analysis),
                'risk_distribution': risk_counts
            }
        }, f, indent=2)
    print(f"✓ JSON report: {json_file}")
    
    # Save as CSV
    csv_data = []
    for v in venue_analysis:
        row = {
            'venue_name': v['venue_name'],
            'city': v['city'],
            'country': v['country'],
            'risk_category': v['risk_category'],
            'agencies_nearby': v['crime_analysis']['agencies_nearby'],
            'total_offenses': v['crime_analysis']['total_offenses'],
            'violent_crimes': v['crime_analysis']['violent_crimes'],
            'homicides': v['crime_analysis']['homicides'],
            'drug_crimes': v['crime_analysis']['drug_crimes'],
            'human_trafficking': v['crime_analysis']['human_trafficking'],
            'avg_risk_score': round(v['crime_analysis']['avg_risk_score'], 2)
        }
        if 'closest_high_crime_area' in v:
            row['closest_crime_area'] = v['closest_high_crime_area']['city']
            row['closest_distance_km'] = v['closest_high_crime_area']['distance_km']
        csv_data.append(row)
    
    csv_file = f'reports/venue_crime_analysis_{year}_{timestamp}.csv'
    pd.DataFrame(csv_data).to_csv(csv_file, index=False)
    print(f"✓ CSV report: {csv_file}")
    
    session.close()
    
    print(f"\n" + "=" * 80)
    print("✅ ANALYSIS COMPLETE!")
    print("=" * 80)
    print(f"\nKey Findings:")
    print(f"  • Analyzed {len(venue_analysis)} World Cup venues")
    print(f"  • Used crime data from {len(crime_df):,} agencies")
    print(f"  • {risk_counts.get('HIGH', 0)} venues in HIGH risk category")
    print(f"  • {risk_counts.get('MEDIUM-HIGH', 0)} venues in MEDIUM-HIGH risk category")
    print(f"\nReports saved to: reports/")
    print(f"  - {json_file}")
    print(f"  - {csv_file}")
    print("=" * 80)
    
    return True


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Analyze crime statistics near World Cup venues'
    )
    parser.add_argument(
        '--radius',
        type=float,
        default=50,
        help='Search radius in kilometers (default: 50)'
    )
    parser.add_argument(
        '--year',
        type=int,
        default=2024,
        help='Year of crime data to analyze (default: 2024)'
    )
    parser.add_argument(
        '--db',
        help='Database URL (default: from .env)',
        default=None
    )
    
    args = parser.parse_args()
    
    try:
        success = analyze_venue_crime(
            db_url=args.db,
            radius_km=args.radius,
            year=args.year
        )
        if not success:
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)