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
            
    def send_status_update(self):
        if self.app:
            with self.app.app_context():
                self._do_send_status()
        else:
            self._do_send_status()
    
    def _do_send_status(self):
        from app.models import User, db
        
        now = datetime.now()
        timestamp = now.strftime('%H:%M:%S')
                
        users = User.query.filter_by(active=True, confirmed=True).filter(User.telegram_chat_id.isnot(None)).all()
        
        if not users:
            return
        
        earthquakes = self.usgs.get_recent_earthquakes(hours=24)
        
        msg = f"<b>Status do Sistema</b>\n"
        msg += f"Horario: {now.strftime('%d/%m/%Y %H:%M:%S')}\n\n"
        
        if earthquakes:
            latest = earthquakes[0]
            msg += f"<b>Ultimo Terremoto:</b>\n"
            msg += f"• Magnitude: {latest['magnitude']}\n"
            msg += f"• Local: {latest['location']}\n"
            msg += f"• Quando: {latest['time'].strftime('%d/%m %H:%M')}\n\n"
        else:
            msg += "<b>Ultimo Terremoto:</b>\n"
            msg += "• Nenhum evento nas ultimas 24h\n\n"
        
        msg += f"<b>Monitoramento:</b>\n"
        msg += f"• Sistema: Online\n"
        msg += f"• Usuarios ativos: {len(users)}\n"
        msg += f"• Proxima verificacao: 1 minuto"
        
        # Enviar para todos
        success_count = 0
        for user in users:
            if self.telegram.send_message(user.telegram_chat_id, msg):
                success_count += 1
        
        print(f"Status enviado para {success_count}/{len(users)} usuarios")
    
    def check_earthquakes(self):
        if self.app:
            with self.app.app_context():
                self._do_check_earthquakes()
        else:
            self._do_check_earthquakes()
    
    def _do_check_earthquakes(self):
        from app.models import User, AlertLog, db
        
        earthquakes = self.usgs.get_recent_earthquakes(hours=1)
        
        if earthquakes:
            latest = earthquakes[0]
            earthquake_id = f"{latest['time'].strftime('%Y%m%d%H%M')}_{latest['magnitude']}"
            
            if earthquake_id != self.last_earthquake_id:
                self.last_earthquake_id = earthquake_id
                self._send_earthquake_alerts(latest, User, AlertLog, db)
            else:
                return
        else:
            return
        
    def check_weather(self):
        if self.app:
            with self.app.app_context():
                self._do_check_weather()
        else:
            self._do_check_weather()
    
    def _do_check_weather(self):
        from app.models import User, AlertLog, db
                
        users = User.query.filter_by(active=True, confirmed=True).filter(User.telegram_chat_id.isnot(None)).all()
        
        if not users:
            return
        
        cities = {}
        for user in users:
            if user.city not in cities:
                cities[user.city] = []
            cities[user.city].append(user)
        
        for city, city_users in cities.items():
            weather = self.weather.get_current_weather(city)
            
            if weather and self.weather.has_severe_conditions(weather):
                self._send_weather_alerts(city_users, weather, AlertLog, db)
            else:
                return
    
    def _send_earthquake_alerts(self, earthquake, User, AlertLog, db):
        users = User.query.filter_by(active=True, confirmed=True).filter(User.telegram_chat_id.isnot(None)).all()
        message = "ALERTA SISMICO\n\n" + self.usgs.format_earthquake_message(earthquake)
        
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
        schedule.every(1).minutes.do(self.send_status_update)
        
        schedule.every(1).minutes.do(self.check_earthquakes)
        schedule.every(1).minutes.do(self.check_weather)
        
        print("Scheduler ativo:")
        print("• Status automatico: 1 minuto")
        print("• Verificacao terremotos: 1 minuto")
        print("• Verificacao clima: 1 minuto")
        
        while True:
            schedule.run_pending()
            time.sleep(1)
    
    def start_background(self):
        thread = threading.Thread(target=self.start, daemon=True)
        thread.start()
        print("Scheduler em background")