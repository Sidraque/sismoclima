from flask import Flask
from config.settings import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    from app.models import db
    db.init_app(app)
    
    from app.routes import bp
    app.register_blueprint(bp)
    
    with app.app_context():
        db.create_all()
    
    return app