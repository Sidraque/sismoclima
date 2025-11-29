import requests
from config.settings import Config

class WeatherService:
    BASE_URL = "https://api.openweathermap.org/data/2.5/weather"
    ALERTS_URL = "https://api.openweathermap.org/data/2.5/onecall"
    
    def __init__(self):
        self.api_key = Config.OPENWEATHER_API_KEY
    
    def get_current_weather(self, city):
        params = {
            'q': city,
            'appid': self.api_key,
            'units': 'metric',
            'lang': 'pt_br'
        }
        
        try:
            response = requests.get(self.BASE_URL, params=params, timeout=10)
            response.raise_for_status()
            return self._parse_weather(response.json())
        except requests.exceptions.RequestException as e:
            return None
    
    def get_weather_alerts(self, lat, lon):
        params = {
            'lat': lat,
            'lon': lon,
            'appid': self.api_key,
            'exclude': 'minutely,hourly,daily',
            'lang': 'pt_br'
        }
        
        try:
            response = requests.get(self.ALERTS_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            return data.get('alerts', [])
        except requests.exceptions.RequestException as e:
            print(f"Erro ao consultar alertas: {e}")
            return []
    
    def _parse_weather(self, data):
        """Processa dados meteorológicos"""
        return {
            'city': data.get('name'),
            'temperature': data['main'].get('temp'),
            'feels_like': data['main'].get('feels_like'),
            'humidity': data['main'].get('humidity'),
            'pressure': data['main'].get('pressure'),
            'description': data['weather'][0].get('description'),
            'wind_speed': data['wind'].get('speed'),
            'icon': data['weather'][0].get('icon')
        }
    
    def has_severe_conditions(self, weather):
        severe_keywords = ['tempestade', 'tornado', 'furacão', 'tufão', 'ciclone']
        description = weather.get('description', '').lower()
        
        return any(keyword in description for keyword in severe_keywords)
    
    def format_weather_message(self, weather):
        msg = f"🌤 *CLIMA ATUAL* 🌤\n\n"
        msg += f"📍 Cidade: {weather['city']}\n"
        msg += f"🌡 Temperatura: {weather['temperature']}°C\n"
        msg += f"🤔 Sensação: {weather['feels_like']}°C\n"
        msg += f"💧 Umidade: {weather['humidity']}%\n"
        msg += f"🌪 Vento: {weather['wind_speed']} m/s\n"
        msg += f"☁️ Condição: {weather['description'].capitalize()}"
        return msg