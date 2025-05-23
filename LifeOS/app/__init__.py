# Package initialization
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import Config

db = SQLAlchemy()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize app with config
    config_class.init_app(app)
    
    # Ensure database directory exists (only for file-based database)
    if 'DB_PATH' in app.config and app.config['DB_PATH'] != ':memory:':
        db_dir = os.path.dirname(app.config['DB_PATH'])
        if not os.path.exists(db_dir):
            os.makedirs(db_dir)
            print(f"Created database directory: {db_dir}")
    
    # Initialize extensions
    db.init_app(app)
    
    # Register blueprints
    from app.routes import routes
    app.register_blueprint(routes)
    
    return app

app = create_app()
