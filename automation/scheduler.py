import schedule
import time
import threading
from datetime import datetime
from services.usgs_service import USGSService
from services.weather_service import WeatherService
from services.telegram_service import TelegramService
from config.settings import Config


class MonitorScheduler:
    def __init__(self, app=None):
        self.usgs = USGSService()
        self.weather = WeatherService()
        self.telegram = TelegramService()
        self.last_earthquake_id = None
        self.app = app
        
        print("Scheduler inicializado")
    
    def check_earthquakes(self):
        if self.app:
            with self.app.app_context():
                self._do_check_earthquakes()
        else:
            self._do_check_earthquakes()
    
    def _do_check_earthquakes(self):
        from app.models import User, AlertLog, db
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Verificando terremotos...")
        earthquakes = self.usgs.get_recent_earthquakes(hours=1)
        
        if earthquakes:
            latest = earthquakes[0]
            earthquake_id = f"{latest['time'].strftime('%Y%m%d%H%M')}_{latest['magnitude']}"
            
            if earthquake_id != self.last_earthquake_id:
                self.last_earthquake_id = earthquake_id
                print(f"NOVO TERREMOTO: Magnitude {latest['magnitude']}")
                self._send_earthquake_alerts(latest, User, AlertLog, db)
            else:
                print("Terremoto ja alertado")
        else:
            print("Nenhum terremoto significativo")
    
    def check_weather(self):
        if self.app:
            with self.app.app_context():
                self._do_check_weather()
        else:
            self._do_check_weather()
    
    def _do_check_weather(self):
        from app.models import User, AlertLog, db
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Verificando clima...")
        
        users = User.query.filter_by(active=True, confirmed=True).filter(User.telegram_chat_id.isnot(None)).all()
        
        if not users:
            print("Nenhum usuario ativo")
            return
        
        cities = {}
        for user in users:
            if user.city not in cities:
                cities[user.city] = []
            cities[user.city].append(user)
        
        for city, city_users in cities.items():
            weather = self.weather.get_current_weather(city)
            
            if weather and self.weather.has_severe_conditions(weather):
                print(f"CONDICAO SEVERA: {city}")
                self._send_weather_alerts(city_users, weather, AlertLog, db)
            else:
                print(f"Clima normal em: {city}")
    
    def _send_earthquake_alerts(self, earthquake, User, AlertLog, db):
        users = User.query.filter_by(active=True, confirmed=True).filter(User.telegram_chat_id.isnot(None)).all()
        message = self.usgs.format_earthquake_message(earthquake)
        
        success_count = 0
        for user in users:
            sent = self.telegram.send_alert(user.telegram_chat_id, message)
            
            alert_log = AlertLog(
                user_id=user.id,
                alert_type='earthquake',
                message=message,
                success=sent
            )
            db.session.add(alert_log)
            
            if sent:
                success_count += 1
        
        db.session.commit()
        print(f"Alertas enviados: {success_count}/{len(users)}")
    
    def _send_weather_alerts(self, users, weather, AlertLog, db):
        message = "ALERTA METEOROLOGICO\n\n"
        message += self.weather.format_weather_message(weather)
        
        success_count = 0
        for user in users:
            sent = self.telegram.send_alert(user.telegram_chat_id, message)
            
            alert_log = AlertLog(
                user_id=user.id,
                alert_type='weather',
                message=message,
                success=sent
            )
            db.session.add(alert_log)
            
            if sent:
                success_count += 1
        
        db.session.commit()
        print(f"Alertas clima: {success_count}/{len(users)}")
    
    def start(self):
        # Agendar verificacoes a cada 1 minuto
        schedule.every(1).minutes.do(self.check_earthquakes)
        schedule.every(1).minutes.do(self.check_weather)
        
        print("Scheduler ativo - Verificacoes a cada 1 minuto")
        
        while True:
            schedule.run_pending()
            time.sleep(1)
    
    def start_background(self):
        thread = threading.Thread(target=self.start, daemon=True)
        thread.start()
        print("Scheduler em background")