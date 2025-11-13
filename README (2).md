# **World Cup 2026 Intelligence Platform**

**A Geospatial Security Analytics System for Multi-Country Event Planning**

The World Cup 2026 Intelligence Platform is a comprehensive data analytics and visualization system designed to support security planning and risk assessment for the FIFA World Cup 2026, which will be hosted across the United States, Canada, and Mexico. By integrating multiple data sources including drug seizure statistics, migration incident data, and venue locations, this platform provides actionable intelligence for cross-border security coordination.

<p align="center">
  <img src="docs/images/map_overview.png" width="850" alt="Platform Overview">
</p>

## **Overview**

The 2026 FIFA World Cup presents unique security challenges as the first World Cup to be hosted across three countries simultaneously. With 16 host cities and millions of expected visitors crossing international borders, understanding regional security patterns, migration routes, and drug trafficking corridors is critical for effective planning.

This platform synthesizes data from:
- **U.S. Customs and Border Protection (CBP)** - Drug seizure statistics by field office and region
- **International Organization for Migration (IOM)** - Missing migrants incident data
- **FIFA World Cup 2026** - Official venue locations and capacities

## **Purpose & Use Cases**

The platform serves multiple stakeholder groups:

### **Security Planners**
- Identify high-risk regions near World Cup venues
- Understand drug trafficking patterns by border sector
- Assess migration route proximity to event locations
- Coordinate multi-agency response strategies

### **Policy Analysts**
- Analyze temporal trends in border incidents
- Compare regional security metrics
- Evaluate resource allocation needs
- Generate data-driven policy recommendations

### **Researchers & Academics**
- Access cleaned, geocoded datasets
- Perform geospatial analysis
- Study cross-border security dynamics
- Develop predictive models

## **Key Features**

### 📊 **Interactive Dashboard**
Real-time statistics display showing:
- Total drug seizures by type and region
- Migration incident casualties and trends
- Venue-specific risk assessments
- Temporal pattern analysis

### 🗺️ **Geospatial Map Visualization**
Multi-layer interactive map featuring:
- All 16 World Cup 2026 venue locations
- CBP field office drug seizure heatmaps
- IOM migration incident markers
- Proximity-based risk scoring
- Custom radius analysis (50km, 100km, 200km)

### 📈 **Data Analytics Engine**
Comprehensive analysis capabilities:
- Hotspot detection using spatial clustering
- Temporal trend analysis (2014-2025)
- Venue risk scoring algorithms
- Distance-based impact assessments

### 🔄 **Automated Data Pipeline**
Robust ETL processes including:
- Automated data scraping and updates
- Geocoding and coordinate validation
- Data quality checks and logging
- Database synchronization

## **Architecture**

### **Technology Stack**

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Backend** | Flask 3.0 | Web framework and API server |
| **Database** | PostgreSQL 15+ | Geospatial data storage |
| **ORM** | SQLAlchemy 2.0 | Database abstraction layer |
| **Frontend** | Leaflet.js 1.9 | Interactive mapping |
| **UI Framework** | Bootstrap 5 | Responsive design |
| **Visualization** | Chart.js 4.0 | Statistical charts |
| **Geospatial** | PostGIS | Spatial queries and analysis |

### **System Architecture**

```
┌─────────────────────────────────────────────────────────┐
│                   Flask Application                      │
├─────────────────────────────────────────────────────────┤
│  Routes Layer    │  /                (Landing Page)      │
│                  │  /map             (Interactive Map)   │
│                  │  /dashboard       (Analytics)         │
│                  │  /api/*           (REST Endpoints)    │
├─────────────────────────────────────────────────────────┤
│  Business Logic  │  Geospatial Analysis                 │
│                  │  Risk Scoring Algorithms             │
│                  │  Statistical Computations            │
├─────────────────────────────────────────────────────────┤
│  Data Layer      │  SQLAlchemy ORM Models               │
│                  │  Database Connection Pool            │
├─────────────────────────────────────────────────────────┤
│  Storage         │  PostgreSQL + PostGIS                │
│                  │  - worldcup_venues                   │
│                  │  - cbp_drug_seizures                 │
│                  │  - smuggling_incidents (IOM)         │
│                  │  - data_sources                      │
└─────────────────────────────────────────────────────────┘
```

## **Data Sources & Processing**

### **1. CBP Drug Seizure Data**

**Source:** U.S. Customs and Border Protection Statistical Reports  
**Coverage:** Fiscal Years 2014-2025  
**Records:** ~50,000+ seizure events  
**Granularity:** Monthly, by field office and drug type

**Processing Pipeline:**
1. Download CSV files from CBP public data portal
2. Parse and validate fiscal year formats
3. Geocode field office locations (23 offices)
4. Load into `cbp_drug_seizures` table
5. Generate aggregated statistics

**Sample Data Structure:**
```python
{
  'fiscal_year': 2024,
  'month': 'October',
  'area_of_responsibility': 'EL PASO FIELD OFFICE',
  'drug_type': 'Cocaine',
  'event_count': 247,
  'quantity_lbs': 1834.5,
  'latitude': 31.7619,
  'longitude': -106.4850
}
```

### **2. IOM Missing Migrants Data**

**Source:** IOM Missing Migrants Project  
**Coverage:** Global, filtered for Americas (2014-2025)  
**Records:** ~8,000+ incidents  
**Scope:** North America, Central America, Caribbean

**Processing Pipeline:**
1. Download global CSV from IOM portal
2. Filter for Americas regions
3. Parse coordinates and casualty counts
4. Validate data quality
5. Load into `smuggling_incidents` table

**Sample Data Structure:**
```python
{
  'incident_date': '2024-06-15',
  'latitude': 32.5321,
  'longitude': -116.9325,
  'region_of_incident': 'US-Mexico Border',
  'number_dead': 3,
  'number_missing': 2,
  'cause_of_death': 'Environmental/Accidental'
}
```

### **3. World Cup 2026 Venues**

**Source:** FIFA Official Venue List  
**Coverage:** All 16 host cities  
**Countries:** USA (11), Canada (2), Mexico (3)

**Venue Data:**
```python
venues = [
  {
    'venue_name': 'MetLife Stadium',
    'city': 'East Rutherford',
    'state_province': 'New Jersey',
    'country': 'USA',
    'capacity': 82500,
    'host_matches': 8,
    'latitude': 40.8128,
    'longitude': -74.0742
  },
  # ... 15 more venues
]
```

## **Key Statistics (Current Dataset)**

| Metric | Value |
|--------|-------|
| **CBP Drug Seizures** | 50,000+ events |
| **IOM Incidents (Americas)** | 8,000+ incidents |
| **Total Casualties Tracked** | 20,000+ persons |
| **World Cup Venues** | 16 stadiums |
| **Geographic Coverage** | 3 countries |
| **Temporal Range** | 2014-2025 (11 years) |
| **Database Size** | ~150 MB |

## **API Endpoints**

### **Core Data Endpoints**

```bash
GET /api/venues
# Returns all World Cup venue locations with coordinates

GET /api/incidents?radius=100&venue_id=1
# Returns migration incidents within radius (km) of venue

GET /api/cbp-statistics
# Returns aggregated CBP drug seizure statistics

GET /api/statistics
# Returns comprehensive platform statistics
```

### **Geospatial Analysis Endpoints**

```bash
GET /api/heatmap?layer=cbp
# Returns heatmap data for CBP seizures

GET /api/venue-analysis?venue_id=1&radius=50
# Returns risk analysis for specific venue

GET /api/temporal-trends?start_year=2020&end_year=2024
# Returns temporal trend analysis
```

## **Installation & Setup**

See [PROCESS.md](PROCESS.md) for detailed setup instructions including:
- Python environment configuration
- PostgreSQL database installation
- Data restoration from backup
- Environment variable configuration
- Running the application

## **Project Structure**

```
worldcup-2026-intelligence/
├── data/
│   ├── raw/                      # Raw downloaded data
│   ├── processed/                # Cleaned datasets
│   └── geojson/                  # GeoJSON exports
├── scripts/
│   ├── setup_database_postgresql.py    # DB initialization
│   ├── load_cbp_drug_data.py          # CBP data loader
│   ├── load_iom_data.py               # IOM data loader
│   ├── load_venues_postgresql.py      # Venue data loader
│   ├── add_geocoding_to_cbp.py        # Geocoding utility
│   └── run_analysis.py                # Analysis runner
├── src/
│   ├── app.py                    # Flask application
│   ├── models/
│   │   └── models.py            # SQLAlchemy models
│   ├── routes/
│   │   └── api_routes.py        # API endpoints
│   ├── scrapers/
│   │   ├── cbp_scraper.py       # CBP data scraper
│   │   └── iom_scraper.py       # IOM data scraper
│   └── utils/
│       └── geo_analysis.py      # Geospatial utilities
├── templates/
│   ├── index.html               # Landing page
│   ├── map.html                 # Interactive map
│   └── dashboard.html           # Analytics dashboard
├── static/
│   ├── css/                     # Stylesheets
│   └── js/                      # JavaScript modules
├── backup.sql                   # PostgreSQL database backup
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment template
├── README.md                    # This file
└── PROCESS.md                   # Setup instructions
```

## **Development Roadmap**

### **✅ Completed (Sprint 1-4)**
- [x] Database schema design and implementation
- [x] Data scraping and ETL pipelines
- [x] Geocoding and coordinate validation
- [x] Flask API development
- [x] Interactive map with Leaflet.js
- [x] Basic statistical dashboard
- [x] CBP and IOM data integration

### **🚧 In Progress (Sprint 5)**
- [ ] Advanced risk scoring algorithms
- [ ] Predictive modeling for incident patterns
- [ ] Enhanced temporal visualizations
- [ ] User authentication system
- [ ] Export functionality (PDF reports)

### **📋 Planned (Future Sprints)**
- [ ] Real-time data updates via scheduled tasks
- [ ] Machine learning for hotspot prediction
- [ ] Multi-language support (English/Spanish/French)
- [ ] Mobile-responsive design improvements
- [ ] Integration with additional data sources (crime statistics, weather data)
- [ ] Collaborative annotation system for security analysts

## **Use Case Examples**

### **Example 1: Venue Risk Assessment**

**Scenario:** Security team needs to assess risk for AT&T Stadium (Arlington, TX)

**Steps:**
1. Navigate to map interface
2. Select AT&T Stadium from venue list
3. Set analysis radius to 100km
4. View incidents within radius
5. Generate risk score report

**Output:**
```
AT&T Stadium Risk Assessment (100km radius)
- Drug Seizures (nearby): 4,250 events
- Migration Incidents: 78 incidents
- Total Casualties: 245 persons
- Risk Score: 72/100 (High)
- Recommendation: Enhanced security protocols required
```

### **Example 2: Regional Comparison**

**Scenario:** Compare security patterns between US Southwest and Northeast venues

**Analysis:**
- Southwest venues (TX, AZ): Average risk score 68/100
- Northeast venues (NY, MA, PA): Average risk score 34/100
- Conclusion: Southwest venues require 2x security resource allocation

### **Example 3: Temporal Pattern Analysis**

**Scenario:** Identify seasonal trends in border incidents

**Findings:**
- Peak incident months: May-August (summer)
- Lowest incident months: December-February (winter)
- Implication: World Cup timing (June-July) aligns with peak risk period

## **Contributing**

This is an academic capstone project. While not open for public contributions during the project period, the methodology and code will be made available for educational purposes after project completion.

## **Ethical Considerations**

This platform handles sensitive data related to human casualties and law enforcement activities. Key ethical guidelines:

1. **Data Privacy:** No personally identifiable information (PII) is stored
2. **Humanitarian Focus:** Migration data is used to understand humanitarian patterns, not for enforcement
3. **Transparent Methodology:** All algorithms and scoring methods are documented
4. **Responsible Use:** Platform is designed for security planning, not surveillance
5. **Academic Purpose:** This is a research and educational project


## **Data Source Credits**

- **CBP Data:** U.S. Customs and Border Protection (Public Domain)
- **IOM Data:** International Organization for Migration Missing Migrants Project (Creative Commons)
- **Venue Data:** FIFA (Fair Use - Educational/Research)
- **Basemap:** OpenStreetMap Contributors (ODbL License)

## **License**

