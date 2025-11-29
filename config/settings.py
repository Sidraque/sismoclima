import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Flask
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///sismoclima.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    OPENWEATHER_API_KEY = os.getenv('OPENWEATHER_API_KEY')
    
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    
    EARTHQUAKE_CHECK_INTERVAL = int(os.getenv('EARTHQUAKE_CHECK_INTERVAL', 30))
    WEATHER_CHECK_INTERVAL = int(os.getenv('WEATHER_CHECK_INTERVAL', 60))
    EARTHQUAKE_MIN_MAGNITUDE = float(os.getenv('EARTHQUAKE_MIN_MAGNITUDE', 5.0))
    
    ADMIN_PHONE = os.getenv('ADMIN_PHONE')