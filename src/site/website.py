import os
from flask import Blueprint, render_template, request, jsonify, send_from_directory
from dotenv import load_dotenv, set_key
import requests

# Load environment variables from .env file
load_dotenv()

# It's good practice to have a central place for the .env file path
# Assuming .env is in the project root
DOTENV_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')

site_bp = Blueprint(
    'site',
    __name__,
    template_folder='templates',
    static_folder='static'
)

HC_API_BASE = "https://ai.hackclub.com/proxy/v1"

# --- Page Routes ---

@site_bp.route('/')
def index():
    return render_template('index.html')

@site_bp.route('/settings')
def settings():
    return render_template('settings.html')

@site_bp.route('/favicon.ico')
def favicon():
    return send_from_directory(
        os.path.join(site_bp.root_path, 'static'),
        'favicon.ico',
        mimetype='image/vnd.microsoft.icon'
    )

# --- API Routes ---

@site_bp.route('/api/models')
def get_models():
    try:
        response = requests.get(f"{HC_API_BASE}/models")
        response.raise_for_status()
        models_data = response.json()
        return jsonify(models=models_data.get('data', []))
    except requests.exceptions.RequestException as e:
        print(f"Error fetching models: {e}")
        return jsonify(error="Could not fetch models from Hack Club API."), 500

@site_bp.route('/api/stats')
def get_stats():
    # Reload the .env file to get the latest key
    load_dotenv(dotenv_path=DOTENV_PATH, override=True)
    
    api_key = os.getenv("HC_API_KEY")
    if not api_key:
        return jsonify(error="API key not configured."), 400

    headers = {"Authorization": f"Bearer {api_key}"}
    try:
        response = requests.get(f"{HC_API_BASE}/stats", headers=headers)
        response.raise_for_status()
        stats = response.json()
        return jsonify(stats)
    except requests.exceptions.RequestException as e:
        if e.response and e.response.status_code == 401:
            return jsonify(error="Invalid API key."), 401
        print(f"Error fetching stats: {e}")
        return jsonify(error="Could not fetch stats from Hack Club API."), 500

@site_bp.route('/api/config', methods=['GET', 'POST'])
def manage_config():
    if request.method == 'GET':
        api_key = os.getenv("HC_API_KEY", "")
        model = os.getenv("HC_MODEL", "")
        return jsonify(API_KEY=api_key, MODEL=model)

    if request.method == 'POST':
        data = request.get_json()
        api_key = data.get('api_key')
        model = data.get('model')

        if not api_key or not model:
            return jsonify(success=False, error="API key and model are required."), 400

        try:
            # Verify model is valid
            models_response = requests.get(f"{HC_API_BASE}/models")
            models_response.raise_for_status()
            valid_models = [m['id'] for m in models_response.json().get('data', [])]
            if model not in valid_models:
                return jsonify(success=False, error="Invalid model selected."), 400

            # Save to .env file
            set_key(DOTENV_PATH, "HC_API_KEY", api_key)
            set_key(DOTENV_PATH, "HC_MODEL", model)
            
            return jsonify(success=True, message="Settings saved successfully.")
        except Exception as e:
            print(f"Error saving config: {e}")
            return jsonify(success=False, error="Failed to save settings."), 500


