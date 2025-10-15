"""
Run Geospatial Analysis and Generate Reports

Place in: scripts/run_analysis.py
"""

import sys
sys.path.append('src')

from utils.geo_analysis import GeospatialAnalyzer
import json
import pandas as pd
from datetime import datetime
import os


def main():
    """Run complete geospatial analysis"""
    
    print("=" * 80)
    print("WORLD CUP 2026 - GEOSPATIAL INTELLIGENCE ANALYSIS")
    print("=" * 80)
    
    analyzer = GeospatialAnalyzer()
    
    # 1. Summary Report
    print("\n📊 GENERATING SUMMARY REPORT...")
    summary = analyzer.generate_summary_report()
    
    print(f"\n{'='*80}")
    print("OVERVIEW")
    print(f"{'='*80}")
    print(f"Total World Cup Venues: {summary['overview']['total_venues']}")
    print(f"Total Incidents Analyzed: {summary['overview']['total_incidents']:,}")
    print(f"Total Casualties (Dead + Missing): {summary['overview']['total_casualties']:,}")
    print(f"  - Dead: {summary['overview']['total_dead']:,}")
    print(f"  - Missing: {summary['overview']['total_missing']:,}")
    print(f"Date Range: {summary['overview']['date_range']['earliest']} to {summary['overview']['date_range']['latest']}")
    
    # 2. Hotspot Analysis
    print(f"\n{'='*80}")
    print("TOP 10 SMUGGLING HOTSPOTS")
    print(f"{'='*80}")
    
    for idx, hotspot in enumerate(summary['hotspots'][:10], 1):
        print(f"\n{idx}. Location: ({hotspot['latitude']:.2f}, {hotspot['longitude']:.2f})")
        print(f"   Incidents: {hotspot['incident_count']}")
        print(f"   Casualties: {hotspot['total_casualties']} (Dead: {hotspot['total_dead']}, Missing: {hotspot['total_missing']})")
    
    # 3. Venue Risk Assessment
    print(f"\n{'='*80}")
    print("VENUE RISK ASSESSMENT")
    print(f"{'='*80}")
    
    risk_summary = summary['venue_risk_summary']
    print(f"\nRisk Distribution:")
    print(f"  🔴 High Risk: {risk_summary['High']} venues")
    print(f"  🟡 Medium Risk: {risk_summary['Medium']} venues")
    print(f"  🟢 Low Risk: {risk_summary['Low']} venues")
    
    print(f"\n{'='*80}")
    print("HIGH RISK VENUES (Detailed Analysis)")
    print(f"{'='*80}")
    
    if summary['high_risk_venues']:
        for venue in summary['high_risk_venues']:
            print(f"\n🏟️  {venue['venue_name']}")
            print(f"   Location: {venue['city']}, {venue['country']}")
            print(f"   Current Risk Level: {venue['current_risk_level']}")
            print(f"   Calculated Risk Score: {venue['calculated_risk_score']}/100")
            print(f"   Incidents within 100km: {venue['incidents_within_100km']}")
            print(f"   Total Casualties Nearby: {venue['total_casualties_nearby']}")
            if venue['closest_incident_km']:
                print(f"   Closest Incident: {venue['closest_incident_km']:.1f} km away")
    else:
        print("\n✓ No high-risk venues identified")
    
    # 4. Detailed Venue Analysis
    print(f"\n{'='*80}")
    print("ANALYZING ALL VENUES (50km radius)")
    print(f"{'='*80}")
    
    venue_analysis = analyzer.analyze_all_venues(radius_km=50)
    
    # Create summary table
    venue_data = []
    for venue_name, data in venue_analysis.items():
        venue_data.append({
            'Venue': venue_name,
            'City': data['city'],
            'Country': data['country'],
            'Risk Level': data['security_risk_level'],
            'Incidents (50km)': data['incidents_within_radius'],
            'Casualties': data['total_casualties'],
            'Closest (km)': data['closest_incident_km'] if data['closest_incident_km'] else 'N/A'
        })
    
    df_venues = pd.DataFrame(venue_data)
    df_venues = df_venues.sort_values('Incidents (50km)', ascending=False)
    
    print("\n" + df_venues.to_string(index=False))
    
    # 5. Temporal Analysis
    print(f"\n{'='*80}")
    print("TEMPORAL TREND ANALYSIS")
    print(f"{'='*80}")
    
    temporal = analyzer.temporal_analysis()
    
    print(f"\nTotal Incidents Analyzed: {temporal['total_incidents']:,}")
    print(f"Date Range: {temporal['date_range']['start']} to {temporal['date_range']['end']}")
    
    # Show recent trends (last 12 months if available)
    recent_trends = temporal['monthly_trends'][-12:]
    print(f"\nRecent Monthly Trends (Last {len(recent_trends)} months):")
    for trend in recent_trends:
        print(f"  {trend['year']}-{trend['month']:02d}: {trend['incident_count']} incidents, "
              f"{trend['total_dead']} dead, {trend['total_missing']} missing")
    
    # 6. Save Reports
    print(f"\n{'='*80}")
    print("SAVING REPORTS")
    print(f"{'='*80}")
    
    # Create reports directory
    os.makedirs('reports', exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Save summary as JSON
    summary_file = f'reports/summary_report_{timestamp}.json'
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2, default=str)
    print(f"✓ Summary report saved: {summary_file}")
    
    # Save venue analysis as CSV
    venue_file = f'reports/venue_analysis_{timestamp}.csv'
    df_venues.to_csv(venue_file, index=False)
    print(f"✓ Venue analysis saved: {venue_file}")
    
    # Save temporal trends as CSV
    temporal_file = f'reports/temporal_trends_{timestamp}.csv'
    df_temporal = pd.DataFrame(temporal['monthly_trends'])
    df_temporal.to_csv(temporal_file, index=False)
    print(f"✓ Temporal trends saved: {temporal_file}")
    
    # Save hotspots as CSV
    hotspot_file = f'reports/hotspots_{timestamp}.csv'
    df_hotspots = pd.DataFrame(summary['hotspots'])
    df_hotspots.to_csv(hotspot_file, index=False)
    print(f"✓ Hotspots saved: {hotspot_file}")
    
    print(f"\n{'='*80}")
    print("✓ ANALYSIS COMPLETE!")
    print(f"{'='*80}")
    print(f"\nReports saved to: reports/")
    print(f"\nKey Findings:")
    print(f"  • {summary['overview']['total_incidents']:,} incidents analyzed")
    print(f"  • {len(summary['hotspots'])} smuggling hotspots identified")
    print(f"  • {risk_summary['High']} high-risk venues require enhanced security")
    print(f"  • Data spans from {temporal['date_range']['start'].year} to {temporal['date_range']['end'].year}")
    
    analyzer.close()
    
    return summary


if __name__ == "__main__":
    main()