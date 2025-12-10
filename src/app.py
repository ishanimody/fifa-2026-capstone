from flask import Flask, render_template, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv
from src.extensions import db
from src.models.models import *
from src.routes.api_routes import api_bp

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__, 
           template_folder='../templates',
           static_folder='../static')

# Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
    'DATABASE_URL', 
    'postgresql://postgres:Glenwood%4027573@db.rzlwlqgtozuscpifzzre.supabase.co:5432/postgres?sslmode=require'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-for-sprint-4')

# Import and initialize extensions
db.init_app(app)
CORS(app)  # Enable CORS for API access

# register API blueprint
app.register_blueprint(api_bp)

@app.route("/test-db")
def test_db():
    try:
        count = db.session.query(WorldCupVenue).count()
        return f"DB connected, {count} venues found"
    except Exception as e:
        return f"DB connection failed: {e}"


@app.route("/")
def home():
    return render_template("map.html") 


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

