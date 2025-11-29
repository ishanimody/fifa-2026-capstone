"""
Quick script to check NIBRS data in database
Run from project root: python check_nibrs_data.py
"""

import os
import sys
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, 'src')

# Load environment
load_dotenv()

# Import Flask app to get database connection
from app import app
from extensions import db
from models.models import NIBRSCrimeData

print("=" * 60)
print("🔍 Checking NIBRS Data in Database")
print("=" * 60)

with app.app_context():
    # Query 1: Total count
    total_count = db.session.query(NIBRSCrimeData).count()
    print(f"\n✓ Total NIBRS records: {total_count:,}")
    
    if total_count == 0:
        print("\n❌ NO NIBRS DATA FOUND!")
        print("You need to load the data using load_nibrs_data.py")
        sys.exit(1)
    
    # Query 2: Count by year
    print("\n📅 Records by year:")
    from sqlalchemy import func
    year_counts = db.session.query(
        NIBRSCrimeData.year,
        func.count(NIBRSCrimeData.id).label('count')
    ).group_by(NIBRSCrimeData.year).order_by(NIBRSCrimeData.year).all()
    
    for year, count in year_counts:
        print(f"   {year}: {count:,} records")
    
    # Query 3: Records with coordinates
    with_coords = db.session.query(NIBRSCrimeData).filter(
        NIBRSCrimeData.latitude.isnot(None),
        NIBRSCrimeData.longitude.isnot(None)
    ).count()
    
    print(f"\n🗺️  Records with coordinates: {with_coords:,}")
    
    # Query 4: Sample record
    print("\n📝 Sample record:")
    sample = db.session.query(NIBRSCrimeData).filter(
        NIBRSCrimeData.latitude.isnot(None)
    ).first()
    
    if sample:
        print(f"   Agency: {sample.agency_name}")
        print(f"   City: {sample.city}, {sample.state}")
        print(f"   Year: {sample.year}")
        print(f"   Risk Score: {sample.overall_risk_score}")
        print(f"   Total Offenses: {sample.total_offenses}")
        print(f"   Coordinates: ({sample.latitude}, {sample.longitude})")
    
    # Query 5: 2024 data check
    count_2024 = db.session.query(NIBRSCrimeData).filter(
        NIBRSCrimeData.year == 2024
    ).count()
    
    print(f"\n🔍 2024 records: {count_2024:,}")
    
    if count_2024 == 0:
        print("\n⚠️  WARNING: No 2024 data found!")
        print("Your map.html is filtering for year=2024, which is why you see 0 crime records.")
        print("\nRECOMMENDATION: Remove the year filter from map.html")
    
    # Query 6: Risk score distribution
    print("\n📊 Risk Score Distribution:")
    high_risk = db.session.query(NIBRSCrimeData).filter(
        NIBRSCrimeData.overall_risk_score >= 80
    ).count()
    medium_high = db.session.query(NIBRSCrimeData).filter(
        NIBRSCrimeData.overall_risk_score >= 60,
        NIBRSCrimeData.overall_risk_score < 80
    ).count()
    medium = db.session.query(NIBRSCrimeData).filter(
        NIBRSCrimeData.overall_risk_score >= 40,
        NIBRSCrimeData.overall_risk_score < 60
    ).count()
    low = db.session.query(NIBRSCrimeData).filter(
        NIBRSCrimeData.overall_risk_score < 40
    ).count()
    
    print(f"   🔴 High Risk (≥80): {high_risk:,}")
    print(f"   🟠 Medium-High (60-79): {medium_high:,}")
    print(f"   🟡 Medium (40-59): {medium:,}")
    print(f"   🟢 Low (<40): {low:,}")
    
    # Recommendation
    print("\n" + "=" * 60)
    print("💡 RECOMMENDATIONS:")
    print("=" * 60)
    
    if count_2024 == 0:
        print("1. ❌ Remove 'year=2024' filter from map.html")
        print("   - Line 823: Change to '/api/nibrs/statistics'")
        print("   - Line 1240: Remove 'year: 2024,' line")
    else:
        print("1. ✅ You have 2024 data")
    
    if with_coords < total_count * 0.8:
        print(f"2. ⚠️  Only {with_coords/total_count*100:.1f}% of records have coordinates")
    else:
        print(f"2. ✅ {with_coords/total_count*100:.1f}% of records have coordinates")
    
    print("\n3. Current min_risk filter: 50")
    print(f"   - Records with risk ≥50: {high_risk + medium_high:,}")
    print(f"   - Recommendation: Lower to 30 to see more data")
    
    print("\n" + "=" * 60)

print("\n✅ Database check complete!")
