from datetime import datetime
from services.usgs_service import USGSService
from services.weather_service import WeatherService
from services.telegram_service import TelegramService
from app.models import User, AlertLog, db
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EventMonitor:
    def __init__(self):
        self.usgs = USGSService()
        self.weather = WeatherService()
        self.telegram = TelegramService()
        
        self.last_earthquake_id = None
        self.alerted_weather_events = set()
        
        logger.info("🔍 EventMonitor inicializado")
    
    def check_earthquakes(self):
        try:
            logger.info("🌍 Verificando terremotos...")
            
            earthquakes = self.usgs.get_recent_earthquakes(hours=1)
            
            if not earthquakes:
                logger.info("✅ Nenhum terremoto significativo detectado")
                return
            
            latest = earthquakes[0]
            earthquake_id = self._generate_earthquake_id(latest)
            
            if earthquake_id == self.last_earthquake_id:
                logger.info(f"⏭️ Terremoto ja alertado: {earthquake_id}")
                return
            
            logger.warning(f"🚨 NOVO TERREMOTO: Magnitude {latest['magnitude']}")
            
            self.last_earthquake_id = earthquake_id
            self._send_earthquake_alerts(latest)
            
        except Exception as e:
            logger.error(f"❌ Erro ao verificar terremotos: {e}")
    
    def check_weather(self):
        try:
            logger.info("☁️ Verificando clima...")
            
            users = User.query.filter_by(active=True, confirmed=True).filter(User.telegram_chat_id.isnot(None)).all()
            
            if not users:
                logger.info("ℹ️ Nenhum usuario ativo com Telegram")
                return
            
            logger.info(f"👥 Verificando clima para {len(users)} usuarios")
            
            cities = {}
            for user in users:
                if user.city not in cities:
                    cities[user.city] = []
                cities[user.city].append(user)
            
            for city, city_users in cities.items():
                try:
                    weather = self.weather.get_current_weather(city)
                    
                    if not weather:
                        logger.warning(f"⚠️ Clima nao obtido para: {city}")
                        continue
                    
                    if self.weather.has_severe_conditions(weather):
                        event_id = f"{city}_{datetime.utcnow().strftime('%Y%m%d')}"
                        
                        if event_id not in self.alerted_weather_events:
                            logger.warning(f"⚠️ CONDICAO SEVERA: {city}")
                            self._send_weather_alerts(city_users, weather)
                            self.alerted_weather_events.add(event_id)
                        else:
                            logger.info(f"⏭️ Alerta ja enviado hoje para: {city}")
                    else:
                        logger.info(f"✅ Condicoes normais em: {city}")
                
                except Exception as e:
                    logger.error(f"❌ Erro ao verificar {city}: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"❌ Erro ao verificar clima: {e}")
    
    def _generate_earthquake_id(self, earthquake):
        timestamp = earthquake['time'].strftime('%Y%m%d%H%M')
        magnitude = str(earthquake['magnitude']).replace('.', '')
        return f"{timestamp}_{magnitude}"
    
    def _send_earthquake_alerts(self, earthquake):
        users = User.query.filter_by(active=True, confirmed=True).filter(User.telegram_chat_id.isnot(None)).all()
        
        if not users:
            logger.info("ℹ️ Nenhum usuario para alertar")
            return
        
        message = self.usgs.format_earthquake_message(earthquake)
        
        success_count = 0
        fail_count = 0
        
        for user in users:
            try:
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
                    logger.info(f"✅ Enviado para: {user.name}")
                else:
                    fail_count += 1
                    logger.warning(f"⚠️ Falha para: {user.name}")
            
            except Exception as e:
                fail_count += 1
                logger.error(f"❌ Erro para {user.name}: {e}")
        
        try:
            db.session.commit()
        except Exception as e:
            logger.error(f"❌ Erro ao salvar logs: {e}")
            db.session.rollback()
        
        logger.info(f"📊 Resumo: {success_count} enviados, {fail_count} falhas")
    
    def _send_weather_alerts(self, users, weather):
        message = "🚨 ALERTA METEOROLOGICO 🚨\n\n"
        message += self.weather.format_weather_message(weather)
        message += "\n\n⚠️ Tome precaucoes necessarias!"
        
        success_count = 0
        fail_count = 0
        
        for user in users:
            try:
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
                else:
                    fail_count += 1
            
            except Exception as e:
                fail_count += 1
                logger.error(f"❌ Erro para {user.name}: {e}")
        
        try:
            db.session.commit()
        except Exception as e:
            logger.error(f"❌ Erro ao salvar logs: {e}")
            db.session.rollback()
        
        logger.info(f"📊 Alerta clima: {success_count} enviados, {fail_count} falhas")
    
    def get_status(self):
        return {
            'last_earthquake_id': self.last_earthquake_id,
            'alerted_weather_events': len(self.alerted_weather_events),
            'timestamp': datetime.utcnow()
        }