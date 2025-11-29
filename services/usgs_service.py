import requests
from datetime import datetime, timedelta
from config.settings import Config

class USGSService:
    BASE_URL = "https://earthquake.usgs.gov/fdsnws/event/1/query"
    
    def __init__(self):
        self.min_magnitude = Config.EARTHQUAKE_MIN_MAGNITUDE
    
    def get_recent_earthquakes(self, hours=24):
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)
        
        params = {
            'format': 'geojson',
            'starttime': start_time.strftime('%Y-%m-%dT%H:%M:%S'),
            'endtime': end_time.strftime('%Y-%m-%dT%H:%M:%S'),
            'minmagnitude': self.min_magnitude,
            'orderby': 'time'
        }
        
        try:
            response = requests.get(self.BASE_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            return self._parse_earthquakes(data)
        except requests.exceptions.RequestException as e:
            print(f"Erro ao consultar USGS: {e}")
            return []
    
    def _parse_earthquakes(self, data):
        earthquakes = []
        
        for feature in data.get('features', []):
            props = feature.get('properties', {})
            coords = feature.get('geometry', {}).get('coordinates', [])
            
            earthquake = {
                'magnitude': props.get('mag'),
                'location': props.get('place'),
                'time': datetime.fromtimestamp(props.get('time') / 1000),
                'latitude': coords[1] if len(coords) > 1 else None,
                'longitude': coords[0] if len(coords) > 0 else None,
                'depth': coords[2] if len(coords) > 2 else None,
                'url': props.get('url')
            }
            earthquakes.append(earthquake)
        
        return earthquakes
    
    def format_earthquake_message(self, earthquake):
        msg = f"🚨 *ALERTA SÍSMICO* 🚨\n\n"
        msg += f"📍 Local: {earthquake['location']}\n"
        msg += f"📊 Magnitude: {earthquake['magnitude']}\n"
        msg += f"🕐 Horário: {earthquake['time'].strftime('%d/%m/%Y %H:%M:%S')} UTC\n"
        msg += f"🌐 Coordenadas: {earthquake['latitude']}, {earthquake['longitude']}\n"
        msg += f"⬇️ Profundidade: {earthquake['depth']} km\n"
        msg += f"\nMais informações: {earthquake['url']}"
        return msg