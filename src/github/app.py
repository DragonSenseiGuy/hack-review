from flask import Flask
from dotenv import load_dotenv
import logging
import os

from ..extensions import db, login_manager, migrate
from ..models import User

def create_app():
    load_dotenv()
    app = Flask(__name__)

    app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'a-very-secret-key')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///../instance/site.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    logging.basicConfig(level=logging.INFO)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db, render_as_batch=True)
    login_manager.login_view = 'site.login'


    # Blueprints
    from .webhook import webhook as webhook_blueprint
    app.register_blueprint(webhook_blueprint)

    from ..site.website import site as site_blueprint
    app.register_blueprint(site_blueprint)

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(port=3000, debug=True)
