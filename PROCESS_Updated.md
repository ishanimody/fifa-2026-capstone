# **Setup & Deployment Process**

Complete step-by-step guide for setting up the World Cup 2026 Intelligence Platform on your local machine.

## **Table of Contents**

1. [Prerequisites](#prerequisites)
2. [Quick Start (Using Backup Database)](#quick-start-using-backup-database)
3. [Manual Setup (From Scratch)](#manual-setup-from-scratch)
4. [Running the Application](#running-the-application)
5. [Data Loading & Updates](#data-loading--updates)
6. [Troubleshooting](#troubleshooting)
7. [Development Workflow](#development-workflow)

---

## **Prerequisites**

### **System Requirements**

- **Operating System:** Windows 10+, macOS 10.15+, or Linux (Ubuntu 20.04+)
- **Python:** 3.9 or higher
- **PostgreSQL:** 15.0 or higher (project uses PostgreSQL 18)
- **RAM:** 4GB minimum, 8GB recommended
- **Disk Space:** 2GB for application + data

### **Required Software**

Install the following before proceeding:

1. **Python 3.9+**
   ```bash
   # Check version
   python --version  # or python3 --version
   ```

2. **PostgreSQL 15+**
   - **Windows:** Download from https://www.postgresql.org/download/windows/
   - **macOS:** `brew install postgresql@15` or higher
   - **Linux:** `sudo apt-get install postgresql postgresql-contrib`
   - **Note:** Project database is running on PostgreSQL 18

3. **PostGIS Extension**
   - **Windows:** Included in PostgreSQL installer (select PostGIS during installation)
   - **macOS:** `brew install postgis`
   - **Linux:** `sudo apt-get install postgis postgresql-XX-postgis-3` (replace XX with your version)

4. **Git** (for cloning repository)
   ```bash
   git --version
   ```

---

## **Quick Start (Using Backup Database)**

This is the **RECOMMENDED** method for teammates. It uses the pre-populated database backup.

**📋 BEFORE YOU BEGIN:**
- **Contact Ishani** to receive your database credentials (username and password)
- You will need these credentials for Steps 5 and 6
- The database `worldcup_intelligence` and user accounts are already set up
- You just need to restore the data using `backup.sql`

**Credentials Checklist - What You Should Receive:**
```
✅ PostgreSQL Username (e.g., employee, meghana, sangram, sara, wcuser)
✅ PostgreSQL Password
✅ Database Name: worldcup_intelligence (same for everyone)
✅ Access to backup.sql file (should be in project root after cloning)
```

**Important:** The `backup.sql` file contains all the database structure and data (approximately 50-150 MB). Ishani will ensure this file is included in the repository or shared separately. If you don't see it after cloning, contact Ishani.

**Keep your credentials secure and do not share them publicly!**

### **Step 1: Clone the Repository**

```bash
# Clone the repository
git clone <repository-url>
cd worldcup-2026-intelligence

# Verify you're in the correct directory
ls -la  # Should see: data/, scripts/, src/, templates/, backup.sql
```

### **Step 2: Create Python Virtual Environment**

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows (Command Prompt):
.venv\Scripts\activate

# On Windows (PowerShell):
.venv\Scripts\Activate.ps1

# On macOS/Linux:
source .venv/bin/activate

### **Step 3: Install Python Dependencies**

```bash
# Upgrade pip first
pip install --upgrade pip

# Install all required packages
pip install -r requirements.txt

# Verify critical packages
pip list | grep -E "Flask|SQLAlchemy|psycopg2"
```

**Expected output:**
```
Flask                3.0.0
Flask-CORS           4.0.0
Flask-SQLAlchemy     3.1.1
psycopg2-binary      2.9.9
SQLAlchemy           2.0.23
```

### **Step 4: PostgreSQL Setup & Database Credentials**

#### **4.1: Start PostgreSQL Service**

```bash
# Check if PostgreSQL is running

# Windows:
# Open Services app (services.msc) and look for "postgresql-x64-18"
# Or use Command Prompt:
pg_ctl status

# macOS:
brew services list | grep postgresql
# Start if not running:
brew services start postgresql@15

# Linux:
sudo systemctl status postgresql
# Start if not running:
sudo systemctl start postgresql
```

#### **4.2: Get Your Database Credentials**

**IMPORTANT:** The database and user accounts have already been set up by the project lead. You will receive your credentials directly from Ishanis.

**Your credentials will include:**
- **Database Name:** `worldcup_intelligence` (already created)
- **Username:** Your assigned username (e.g., `employee`, `meghana`, `sangram`, `sara`, or `wcuser`)
- **Password:** Your assigned password
- **Host:** `localhost`
- **Port:** `5432` (default PostgreSQL port)

**Save these credentials securely!** You'll need them for database restoration and connecting the application.

**Note:** Do NOT try to create the database or user - they already exist. The `backup.sql` file contains all the necessary database structure and data.

### **Step 5: Restore Database from Backup**

The `backup.sql` file contains the complete database with all tables and data pre-populated. You'll restore it using the credentials provided to you.

**Before proceeding:**
1. Ensure you have received your database credentials from Ishani
2. Verify you have the `backup.sql` file in your project root directory

```bash
# Navigate to the project root directory (where backup.sql is located)
cd /path/to/worldcup-2026-intelligence

# Verify backup.sql exists
ls -lh backup.sql
# Should show a file size of approximately 50-150 MB
```

#### **5.1: Restore Using Your Credentials**

Replace `YOUR_USERNAME` below with your assigned username (e.g., `employee`, `meghana`, `sangram`, `sara`, or `wcuser`):

```bash
# Method 1: Direct restore (you'll be prompted for your password)
psql -U YOUR_USERNAME -d worldcup_intelligence -h localhost -f backup.sql

# Example if your username is "employee":
psql -U employee -d worldcup_intelligence -h localhost -f backup.sql

# When prompted, enter YOUR assigned password
#password for employee user is Employee@q2
```

**Alternative methods if the above doesn't work:**

```bash
# Method 2: Using piped input
# Windows (Command Prompt):
type backup.sql | psql -U YOUR_USERNAME -d worldcup_intelligence -h localhost

# Windows (PowerShell):
Get-Content backup.sql | psql -U YOUR_USERNAME -d worldcup_intelligence -h localhost

# macOS/Linux:
cat backup.sql | psql -U YOUR_USERNAME -d worldcup_intelligence -h localhost
```

**Method 3: Set password as environment variable (less secure but convenient for development)**

```bash
# Windows (Command Prompt):
set PGPASSWORD=your_assigned_password
psql -U YOUR_USERNAME -d worldcup_intelligence -h localhost -f backup.sql

# Windows (PowerShell):
$env:PGPASSWORD="your_assigned_password"
psql -U YOUR_USERNAME -d worldcup_intelligence -h localhost -f backup.sql

# macOS/Linux:
export PGPASSWORD=your_assigned_password
psql -U YOUR_USERNAME -d worldcup_intelligence -h localhost -f backup.sql

# Remember to unset after use:
# Windows CMD: set PGPASSWORD=
# Windows PS: Remove-Item Env:\PGPASSWORD
# macOS/Linux: unset PGPASSWORD
```

**What you should see during restoration:**

```
SET
SET
SET
...
CREATE TABLE
CREATE TABLE
CREATE TABLE
CREATE INDEX
...
COPY 16        ← World Cup venues loaded
COPY 8234      ← IOM migration incidents loaded  
COPY 52847     ← CBP drug seizures loaded
COPY 3         ← Data sources loaded
...
CREATE INDEX
CREATE INDEX
ALTER TABLE
```

**Restoration typically takes 1-3 minutes depending on your machine.**

#### **5.2: Troubleshooting Restoration Issues**

**Error: "password authentication failed for user"**
```bash
# Double-check you're using the correct credentials provided by Ishani
# Verify database connection:
psql -U YOUR_USERNAME -d worldcup_intelligence -h localhost -c "SELECT version();"
```

**Error: "permission denied"**
```bash
# Contact Ishani - your user may need additional permissions
# The user account should already have the necessary privileges
```

**Error: "database does not exist"**
```bash
# The database should already exist
# Verify with:
psql -U postgres -h localhost -c "\l" | grep worldcup_intelligence

# If missing, contact Ishani
```

#### **5.3: Verify Database Restoration**

After successful restoration, verify the data was loaded correctly:

```bash
# Connect to database using YOUR assigned credentials
psql -U YOUR_USERNAME -d worldcup_intelligence -h localhost

# In psql, check tables:
\dt

# Expected output:
#  Schema |         Name          | Type  |   Owner    
# --------+-----------------------+-------+------------
#  public | cbp_drug_seizures     | table | postgres
#  public | data_sources          | table | postgres
#  public | smuggling_incidents   | table | postgres
#  public | worldcup_venues       | table | postgres

# Check record counts:
SELECT 'CBP Seizures' as table_name, COUNT(*) as records FROM cbp_drug_seizures
UNION ALL
SELECT 'IOM Incidents', COUNT(*) FROM smuggling_incidents
UNION ALL
SELECT 'Venues', COUNT(*) FROM worldcup_venues
UNION ALL
SELECT 'Data Sources', COUNT(*) FROM data_sources;

# Expected output (approximately):
#   table_name    | records 
# ----------------+---------
#  CBP Seizures   |   52847
#  IOM Incidents  |    8234
#  Venues         |      16
#  Data Sources   |       3

# ✅ If you see these counts, restoration was successful!

# Check a sample of venue data:
SELECT venue_name, city, country FROM worldcup_venues LIMIT 5;

# Exit psql:
\q
```

**Expected venue sample:**
```
       venue_name       |      city       | country 
------------------------+-----------------+---------
 MetLife Stadium        | East Rutherford | USA
 Mercedes-Benz Stadium  | Atlanta         | USA
 Hard Rock Stadium      | Miami Gardens   | USA
 Arrowhead Stadium      | Kansas City     | USA
 AT&T Stadium           | Arlington       | USA
```

### **Step 6: Configure Environment Variables**

Create a `.env` file in the project root with your database credentials:

```bash
# Copy the example file if it exists
cp .env.example .env

# Or create manually
# On Windows:
notepad .env

# On macOS/Linux:
nano .env
```

**Add the following content to `.env` (replace with YOUR assigned credentials):**

```bash
# Database Configuration
# IMPORTANT: Replace YOUR_USERNAME and YOUR_PASSWORD with credentials from Ishani
DATABASE_URL=postgresql://YOUR_USERNAME:YOUR_PASSWORD@localhost:5432/worldcup_intelligence


# Flask Configuration
SECRET_KEY=your-secret-key-here-change-in-production-xyz123
FLASK_ENV=development
FLASK_DEBUG=True

# API Keys (optional - for future data updates)
# CBP_API_KEY=your-key-here
# IOM_API_KEY=your-key-here
```

**Real-world example:**
```bash


# Example:Your DATABASE_URL would be:
DATABASE_URL=postgresql://meghana:secure_pass_2026@localhost:5432/worldcup_intelligence
```

**Important Notes:**
- ⚠️ **Never commit `.env` file to version control!** (It's already in `.gitignore`)
- ⚠️ **Keep your password secure** - don't share it or post it publicly
- ✅ The `.env` file stays local to your machine only
- ✅ Each teammate will have their own `.env` with their assigned credentials

### **Step 7: Verify Setup**

Run the verification script:

```bash
# Activate virtual environment if not already active
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\activate     # Windows

# Run verification
python scripts/verify_cbp_data.py
```

**Expected output:**
```
======================================================================
CBP DATA VERIFICATION
======================================================================

✓ Table exists
📊 Total records: 52,847
📈 Total events: 1,245,678
⚖️ Total quantity: 45,234,567.89 lbs
📍 Records with coordinates: 52,847 (100.0%)

======================================================================
✅ VERIFICATION COMPLETE - DATA IS READY!
======================================================================
```

### **Step 8: Run the Application**

```bash
# Start Flask server
python src/app.py
```

**Expected output:**
```
============================================================
🚀 World Cup 2026 Intelligence Platform
Sprint 4 - Interactive Map Development
============================================================
Database: localhost:5432/worldcup_intelligence
Server starting on http://127.0.0.1:5000
============================================================

Available routes:
  - http://127.0.0.1:5000/          (Home)
  - http://127.0.0.1:5000/map       (Interactive Map)
  - http://127.0.0.1:5000/dashboard (Dashboard)

API Endpoints:
  - http://127.0.0.1:5000/api/venues
  - http://127.0.0.1:5000/api/incidents
  - http://127.0.0.1:5000/api/statistics
  - http://127.0.0.1:5000/api/heatmap

Press CTRL+C to stop the server
============================================================

 * Running on http://127.0.0.1:5000
```

### **Step 9: Access the Application**

Open your browser and navigate to:

- **Home Page:** http://127.0.0.1:5000/
- **Interactive Map:** http://127.0.0.1:5000/map
- **Dashboard:** http://127.0.0.1:5000/dashboard

**Test the API:**
```bash
# In a new terminal:
curl http://127.0.0.1:5000/api/statistics
```

---

## **Manual Setup (From Scratch)**

If you need to build the database from scratch without using `backup.sql`:

### **Step 1-3:** Follow Steps 1-3 from Quick Start

### **Step 4:** Database Setup (same as Quick Start)

### **Step 5:** Initialize Empty Database

```bash
# Run database setup script
python scripts/setup_database_postgresql.py
```

### **Step 6:** Load World Cup Venues

```bash
python scripts/load_venues_postgresql.py
```

### **Step 7:** Load CBP Drug Seizure Data

```bash
# First, ensure you have CBP CSV files in data/cbp/ directory
ls data/cbp/

# Load all CSV files
python scripts/load_cbp_drug_data.py data/cbp/*.csv

# Add geocoding (coordinates) to CBP data
python scripts/add_geocoding_to_cbp.py
```

### **Step 8:** Load IOM Missing Migrants Data

```bash
# Option A: Use processed file (if available)
python scripts/load_iom_data.py --file data/processed/iom_americas_filtered.csv

# Option B: Process from raw file
python scripts/setup_iom_americas.py
python scripts/load_iom_data.py
```

### **Step 9:** Verify Data Loading

```bash
# Check CBP data
python scripts/check_cbp_data_postgresql.py

# Query database
python scripts/query_database.py
```

### **Step 10:** Run Application

# Start Flask server
python src/app.py

---

## **Running the Application**

### **Development Mode**

```bash
# Activate virtual environment
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\activate     # Windows

# Run with auto-reload
python src/app.py

```

### **Production Mode** (when deploying)

```bash
# Install production server
pip install gunicorn  # Linux/macOS
pip install waitress  # Windows

# Run with Gunicorn (Linux/macOS)
gunicorn -w 4 -b 127.0.0.1:5000 src.app:app

# Run with Waitress (Windows)
waitress-serve --host=127.0.0.1 --port=5000 src.app:app
```

### **Running on a Different Port**

```bash
# Edit src/app.py, change last line to:
app.run(debug=True, host='127.0.0.1', port=8080)

# Or set environment variable
export FLASK_RUN_PORT=8080
flask run
```

---

## **Alternative: Using GUI Database Tools**

If you prefer a graphical interface instead of command-line tools, you can use:

### **pgAdmin (Recommended)**

pgAdmin comes bundled with PostgreSQL installation.

1. **Open pgAdmin** (usually installed with PostgreSQL)

2. **Create Server Connection:**
   - Right-click "Servers" → "Register" → "Server"
   - **General Tab:**
     - Name: `World Cup 2026 Intelligence`
   - **Connection Tab:**
     - Host: `localhost`
     - Port: `5432`
     - Database: `worldcup_intelligence`
     - Username: `YOUR_USERNAME` (from Ishani)
     - Password: `YOUR_PASSWORD` (from Ishani)
     - Save password: ✓ (check this box)

3. **Restore Database:**
   - Right-click on `worldcup_intelligence` database
   - Select "Restore..."
   - Format: Custom or tar
   - Filename: Browse to your `backup.sql` file
   - Click "Restore"


## **Data Loading & Updates**

### **Update CBP Data**

```bash
# Download latest data from CBP
# Place new CSV files in data/cbp/

# Load new data
python scripts/load_cbp_drug_data.py data/cbp/new_data.csv

# Refresh geocoding
python scripts/add_geocoding_to_cbp.py
```

### **Update IOM Data**

```bash
# Download from https://missingmigrants.iom.int/downloads
# Save to data/raw/iom_missing_migrants_manual.csv

# Process and filter for Americas
python scripts/setup_iom_americas.py

# Load into database
python scripts/load_iom_data.py
```

### **Run Geospatial Analysis**

```bash
# Generate analysis reports
python scripts/run_analysis.py

# Reports will be saved to reports/ directory
ls reports/
```

### **Automated Scheduling** (optional)

```bash
# Test automated data collection
python scripts/scheduler.py --mode test

# Run scheduler (continuous)
python scripts/scheduler.py --mode schedule
```

---

## **Troubleshooting**

### **Issue: PostgreSQL Connection Failed**

**Error:** `could not connect to server: Connection refused`

**Solutions:**
```bash
# 1. Check if PostgreSQL is running
sudo systemctl status postgresql  # Linux
brew services list | grep postgresql  # macOS

# 2. Check port
sudo netstat -tulpn | grep 5432  # Linux
lsof -i :5432  # macOS

# 3. Check pg_hba.conf authentication
# Location:
# Windows: C:\Program Files\PostgreSQL\15\data\pg_hba.conf
# macOS: /opt/homebrew/var/postgresql@15/pg_hba.conf
# Linux: /etc/postgresql/15/main/pg_hba.conf

# Add this line if not present:
# host    all             all             127.0.0.1/32            md5

# 4. Restart PostgreSQL
sudo systemctl restart postgresql  # Linux
brew services restart postgresql@15  # macOS
```

### **Issue: backup.sql File Not Found**

**Error:** `No such file or directory: backup.sql`

**Solution:**
```bash
# 1. Verify you're in the correct directory
pwd  # Should show: /path/to/worldcup-2026-intelligence

# 2. List files in current directory
ls -la | grep backup.sql  # macOS/Linux
dir | findstr backup.sql   # Windows

# 3. If file is missing:
# - Contact Ishani to get the backup.sql file
# - File should be approximately 50-150 MB
# - Place it in the project root directory (same level as README.md)

# 4. If file is in a different location, specify full path:
psql -U YOUR_USERNAME -d worldcup_intelligence -h localhost -f /full/path/to/backup.sql
```

### **Issue: backup.sql Restore Failed**

**Error:** `permission denied for schema public` or `must be owner of table`

**Solution:**
```bash
# Your user account should already have the necessary permissions
# If you encounter this error, contact Ishani

# You can verify your permissions:
psql -U YOUR_USERNAME -d worldcup_intelligence -h localhost -c "\du"

# This shows all users and their roles
# Your username should appear in the list
```

**Error:** `relation "tablename" already exists`

This means the tables are already there from a previous restore attempt.

**Solution:**
```bash
# Option 1: Drop and recreate the database (CAUTION: destroys existing data)
# Contact Ishani if you need to do this - they have postgres superuser access

# Option 2: Skip the error and continue
# If only some tables exist, you can manually delete them:
psql -U YOUR_USERNAME -d worldcup_intelligence -h localhost

# In psql:
DROP TABLE IF EXISTS cbp_drug_seizures CASCADE;
DROP TABLE IF EXISTS smuggling_incidents CASCADE;
DROP TABLE IF EXISTS worldcup_venues CASCADE;
DROP TABLE IF EXISTS data_sources CASCADE;
\q

# Then try restoring again
psql -U YOUR_USERNAME -d worldcup_intelligence -h localhost -f backup.sql
```

**Error:** `password authentication failed`

**Solution:**
```bash
# 1. Verify you're using the correct credentials from Ishani
# 2. Check for typos in username/password
# 3. Try resetting PGPASSWORD and retry:

# Windows (Command Prompt):
set PGPASSWORD=
set PGPASSWORD=your_actual_password

# macOS/Linux:
unset PGPASSWORD
export PGPASSWORD=your_actual_password

# 4. If still failing, contact Ishani to verify your account is active
```

### **Issue: PostGIS Extension Missing**

**Error:** `ERROR: could not open extension control file`

**Solution:**
```bash
# Install PostGIS
# Ubuntu/Debian:
sudo apt-get install postgresql-15-postgis-3

# macOS:
brew install postgis

# Windows: Reinstall PostgreSQL with PostGIS selected

# Then enable in database:
sudo -u postgres psql
\c worldcup_intelligence
CREATE EXTENSION postgis;
```

### **Issue: Python Module Not Found**

**Error:** `ModuleNotFoundError: No module named 'flask'`

**Solution:**
```bash
# Ensure virtual environment is activated
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\activate     # Windows

# Reinstall dependencies
pip install -r requirements.txt

# Verify
pip list
```

### **Issue: Database Empty After Restore**

**Problem:** Tables exist but have no data

**Solution:**
```bash
# Check backup.sql file size
ls -lh backup.sql  # Should be > 50MB

# If file is corrupted or incomplete, request new backup

# Verify table schemas exist
psql -U wcuser -d worldcup_intelligence -c "\dt"

# Try manual table-by-table restore
psql -U wcuser -d worldcup_intelligence -c "COPY worldcup_venues FROM '/path/to/venues.csv' CSV HEADER;"
```

### **Issue: Port 5000 Already in Use**

**Error:** `OSError: [Errno 48] Address already in use`

**Solution:**
```bash
# Find process using port 5000
# macOS/Linux:
lsof -i :5000
kill -9 <PID>

# Windows:
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# Or use different port
python src/app.py  # Edit app.py to change port to 8080
```

### **Issue: Flask Debug Mode Not Working**

**Problem:** Changes not reflected automatically

**Solution:**
```bash
# Install watchdog for better file watching
pip install watchdog

# Set environment variables
export FLASK_ENV=development
export FLASK_DEBUG=1

# Run
flask run --debug
```

---

## **Development Workflow**

### **Daily Development Routine**

```bash
# 1. Pull latest changes
git pull origin main

# 2. Activate virtual environment
source .venv/bin/activate

# 3. Update dependencies if needed
pip install -r requirements.txt

# 4. Start PostgreSQL (if not already running)
# Check platform-specific commands above

# 5. Run application
python src/app.py

# 6. Make changes and test
# Server auto-reloads in debug mode

# 7. Run verification scripts
python scripts/verify_cbp_data.py
python scripts/check_cbp_data_postgresql.py
```

### **Making Database Changes**

```bash
# 1. Make changes to models.py
nano src/models/models.py

# 2. Create migration script (if using Alembic)
# Or manually update database:
psql -U wcuser -d worldcup_intelligence

# 3. Test changes
python src/app.py

# 4. Create new backup if needed
pg_dump -U wcuser -d worldcup_intelligence > backup_new.sql
```

### **Creating New Analysis Scripts**

```bash
# 1. Create new script in scripts/
touch scripts/my_analysis.py

# 2. Add to imports:
import sys
sys.path.append('src')
from models.models import *

# 3. Run
python scripts/my_analysis.py
```

### **Testing API Endpoints**

```bash
# Use curl or httpie
curl http://127.0.0.1:5000/api/statistics | jq

# Or use Python requests
python -c "import requests; print(requests.get('http://127.0.0.1:5000/api/venues').json())"

# Or use Postman/Insomnia for GUI testing
```

