
from flask import Flask, render_template, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__, 
           template_folder='../templates',
           static_folder='../static')

# Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
    'DATABASE_URL', 
    'postgresql://postgres:Q2%40impact@localhost:5432/worldcup_intelligence'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-for-sprint-4')

# Import and initialize extensions
from extensions import db
db.init_app(app)
CORS(app)  # Enable CORS for API access

# Create application context and tables
with app.app_context():
    # Import models (after db is initialized)
    from models.models import*
    
    # Create tables if they don't exist
    #db.create_all()

# Import and register API blueprint
from routes.api_routes import api_bp
app.register_blueprint(api_bp)

# Main routes
@app.route('/')
def index():
    """Main landing page"""
    return render_template('index.html')

@app.route('/map')
def map_view():
    """Interactive map page"""
    return render_template('map.html')

@app.route('/dashboard')
def dashboard():
    """Dashboard page"""
    return render_template('dashboard.html')

@app.route('/analysis')
def analysis():
    """Analysis page"""
    return render_template('analysis.html')

# Error handlers
@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 World Cup 2026 Intelligence Platform")
    print("Sprint 4 - Interactive Map Development")
    print("=" * 60)
    print(f"Database: {app.config['SQLALCHEMY_DATABASE_URI'].split('@')[1] if '@' in app.config['SQLALCHEMY_DATABASE_URI'] else 'SQLite'}")
    print("Server starting on http://127.0.0.1:5000")
    print("=" * 60)
    print("\nAvailable routes:")
    print("  - http://127.0.0.1:5000/          (Home)")
    print("  - http://127.0.0.1:5000/map       (Interactive Map)")
    print("  - http://127.0.0.1:5000/dashboard (Dashboard)")
    print("\nAPI Endpoints:")
    print("  - http://127.0.0.1:5000/api/venues")
    print("  - http://127.0.0.1:5000/api/incidents")
    print("  - http://127.0.0.1:5000/api/statistics")
    print("  - http://127.0.0.1:5000/api/heatmap")
    print("  - http://127.0.0.1:5000/api/cbp-statistics")
    print("  - http://127.0.0.1:5000/api/nibrs/statistics")
    print("\nPress CTRL+C to stop the server")
    print("=" * 60 + "\n")
    
    app.run(debug=True, host='127.0.0.1', port=5000)