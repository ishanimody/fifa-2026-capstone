# 🌍 World Cup 2026 - Human Smuggling Intelligence Platform

A geospatial intelligence platform for analyzing human smuggling patterns and risks associated with the 2026 FIFA World Cup across USA, Canada, and Mexico.

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-2.3+-green.svg)](https://flask.palletsprojects.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-14+-blue.svg)](https://www.postgresql.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---


## 🎯 Overview

This platform was developed as a Capstone project for Q2 IMPACT to support USNORTHCOM's Human Security and Resilience team in analyzing smuggling risks during the 2026 FIFA World Cup. The system provides real-time geospatial visualization and analysis of human smuggling incidents across North America.

### Problem Statement

Law enforcement agencies lack efficient access to real-time, localized intelligence on:
- Human smuggling routes and corridors
- Activity patterns near high-profile events
- Cross-border coordination data
- Risk assessment for major venues

### Solution

An interactive geospatial platform that:
- Visualizes 20,100+ smuggling incidents
- Maps 16 World Cup venues with risk assessments
- Provides heat map analysis of incident density
- Enables temporal and spatial filtering
- Offers RESTful API for data access

---

## ✨ Features

### 🗺️ Interactive Mapping
- **Multiple Layers**: Venues, incidents, heat maps, routes, border crossings
- **Real-time Data**: 20,100+ incidents from IOM Missing Migrants database
- **Clustering**: Automatic grouping of nearby incidents for performance
- **Heat Maps**: Density visualization of smuggling activity

### 🔍 Advanced Filtering
- **Temporal**: Filter incidents by date range (2014-2024)
- **Geographic**: Filter by country and region
- **Type**: Filter by incident characteristics
- **Layer Toggles**: Show/hide different data layers

### 📊 Geospatial Analysis
- **Distance Calculations**: Find incidents within radius of venues
- **Hotspot Detection**: Identify high-density smuggling areas
- **Risk Assessment**: Calculate venue security risk scores
- **Temporal Trends**: Analyze patterns over time

### 🔌 RESTful API
- 8+ endpoints for data access
- JSON responses
- Filtering and pagination support
- Real-time statistics

### 📱 Responsive Design
- Works on desktop, tablet, and mobile
- Touch-friendly interface
- Adaptive layout

---

## 🛠️ Technology Stack

### Backend
- **Python 3.9+** - Core programming language
- **Flask 2.3+** - Web framework
- **PostgreSQL 14+** - Database
- **PostGIS 3.3+** - Geospatial extension
- **SQLAlchemy 2.0+** - ORM

### Frontend
- **HTML5/CSS3/JavaScript** - Core web technologies
- **Leaflet.js** - Interactive mapping
- **Leaflet.markercluster** - Marker clustering
- **Leaflet.heat** - Heat map visualization

### Data Processing
- **Pandas** - Data manipulation
- **GeoPandas** - Geospatial data processing
- **Beautiful Soup** - Web scraping
- **Requests** - HTTP library

### Tools & Services
- **Git/GitHub** - Version control
- **VS Code** - IDE
- **pgAdmin** - Database management

---

## 📦 Installation

### Prerequisites

- Python 3.9 or higher
- PostgreSQL 14 or higher with PostGIS
- pip (Python package manager)
- Git

### Step 1: Clone the Repository

```bash
git clone https://github.com/yourusername/worldcup-intelligence.git
cd worldcup-intelligence
```

### Step 2: Create Virtual Environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Set Up PostgreSQL

```sql
-- Connect to PostgreSQL
psql -U postgres

-- Create database
CREATE DATABASE worldcup_intelligence;

-- Create user
CREATE USER wcuser WITH PASSWORD 'your_password';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE worldcup_intelligence TO wcuser;

-- Connect to database
\c worldcup_intelligence

-- Enable PostGIS
CREATE EXTENSION postgis;
```

### Step 5: Configure Environment

Create `.env` file in project root:

```env
DATABASE_URL=postgresql://wcuser:your_password@localhost:5432/worldcup_intelligence
FLASK_APP=src/app.py
FLASK_ENV=development
SECRET_KEY=your-secret-key-here
DEBUG=True
```

### Step 6: Initialize Database

```bash
python scripts/setup_database_postgresql.py
```

### Step 7: Load Data

```bash
# Load World Cup venues
python scripts/load_venues_postgresql.py

# Load IOM incident data
python scripts/load_iom_data_fixed.py
```

### Step 8: Run Application

```bash
python src/app.py
```

Open browser to: `http://127.0.0.1:5000`

---

## 🚀 Usage

### Accessing the Platform

1. **Home Page**: `http://127.0.0.1:5000/`
2. **Interactive Map**: `http://127.0.0.1:5000/map`
3. **API Health Check**: `http://127.0.0.1:5000/api/health`

### Using the Map

1. **Zoom/Pan**: Click and drag to pan, scroll to zoom
2. **Click Markers**: Click venue or incident markers for details
3. **Toggle Layers**: Use checkboxes in sidebar to show/hide layers
4. **Apply Filters**: Select filters and click "Apply Filters"
5. **Search Location**: Type location in search box and press Enter
6. **Reset**: Click "Reset" to clear all filters

### Running Analysis

```bash
# Generate geospatial analysis report
python scripts/run_analysis.py

# Run specific scraper
python src/scrapers/iom_scraper.py

# Run scheduler (automated updates)
python scripts/scheduler.py --mode schedule
```

---

## 📁 Project Structure

```
worldcup-smuggling-intelligence/
├── data/
│   ├── raw/              # Raw downloaded data
│   ├── processed/        # Cleaned data
│   └── geojson/          # GeoJSON files
├── docs/                 # Documentation
├── reports/              # Analysis reports
├── scripts/              # Standalone scripts
│   ├── setup_database_postgresql.py
│   ├── load_venues_postgresql.py
│   ├── load_iom_data_fixed.py
│   ├── run_analysis.py
│   └── scheduler.py
├── src/
│   ├── models/           # Database models
│   │   └── models.py
│   ├── routes/           # API routes
│   │   └── api_routes.py
│   ├── scrapers/         # Data scrapers
│   │   ├── iom_scraper.py
│   │   └── cbp_scraper.py
│   ├── utils/            # Utility functions
│   │   └── geo_analysis.py
│   └── app.py            # Main Flask application
├── static/               # Static files (CSS, JS, images)
├── templates/            # HTML templates
│   ├── index.html
│   └── map.html
├── tests/                # Unit tests
├── .env                  # Environment variables
├── .gitignore
├── requirements.txt      # Python dependencies
└── README.md
```

---

## 🔌 API Documentation

### Base URL
```
http://127.0.0.1:5000/api
```

### Endpoints

#### Get Statistics
```http
GET /api/statistics
```
Returns overall platform statistics.

#### Get Venues
```http
GET /api/venues
```
Returns all World Cup venues.

#### Get Incidents
```http
GET /api/incidents?country=Libya&limit=1000
```
Returns smuggling incidents with optional filtering.

**Parameters:**
- `country` (optional): Filter by country
- `limit` (optional): Maximum results (default: 1000)
- `start_date` (optional): Filter from date
- `end_date` (optional): Filter to date

#### Get Heat Map Data
```http
GET /api/heatmap?grid_size=1.0
```
Returns heat map data for visualization.

#### Get Nearby Incidents
```http
GET /api/venue/{venue_id}/nearby?radius=50
```
Returns incidents near a specific venue.

#### Get Risk Assessment
```http
GET /api/risk-assessment
```
Returns risk assessment for all venues.

See full API documentation in `docs/API_DOCUMENTATION.md`

---

## 📊 Data Sources

### Primary Sources

1. **IOM Missing Migrants Project**
   - URL: https://missingmigrants.iom.int/
   - Data: 20,100+ global migration incidents
   - Update: Weekly
   - Format: CSV download

2. **World Cup 2026 Venues**
   - 16 official venues (USA, Canada, Mexico)
   - Geocoded coordinates
   - Capacity and security risk data

### Secondary Sources

3. **CBP Statistics** - US border data
4. **UNODC** - UN trafficking data
5. **OpenStreetMap** - Base mapping

---



## 🧪 Testing

Run tests:

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_scrapers.py

# Run with coverage
pytest --cov=src tests/
```



## 📄 License

This project was developed for educational purposes as part of a Capstone project.

---

## 🙏 Acknowledgments

- **Q2 IMPACT** - Project sponsor and requirements
- **USNORTHCOM** - Use case and domain expertise
- **IOM Missing Migrants Project** - Primary data source
- **OpenStreetMap Contributors** - Mapping data
- **Leaflet.js Community** - Mapping library

