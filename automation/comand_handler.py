from services.usgs_service import USGSService
from services.weather_service import WeatherService
from services.whatsapp_service import WhatsAppService
from app.models import User

class CommandHandler:
    def __init__(self):
        self.usgs = USGSService()
        self.weather = WeatherService()
        self.whatsapp = WhatsAppService()
        
        self.commands = {
            '/terremoto': self.handle_earthquake,
            '/clima': self.handle_weather,
            '/cancelar': self.handle_cancel,
            '/ajuda': self.handle_help
        }
    
    def process_message(self, phone, message):
        message = message.strip().lower()
        
        user = User.query.filter_by(phone=phone, confirmed=True).first()
        if not user:
            return "Você não está cadastrado. Acesse nosso site para se cadastrar."
        
        parts = message.split(' ', 1)
        command = parts[0]
        args = parts[1] if len(parts) > 1 else None
        
        handler = self.commands.get(command)
        if handler:
            return handler(user, args)
        else:
            return self.handle_help(user, None)
    
    def handle_earthquake(self, user, args):
        earthquakes = self.usgs.get_recent_earthquakes(hours=24)
        if earthquakes:
            return self.usgs.format_earthquake_message(earthquakes[0])
        return "Nenhum terremoto significativo nas últimas 24 horas."
    
    def handle_weather(self, user, args):
        city = args if args else user.city
        weather = self.weather.get_current_weather(city)
        
        if weather:
            return self.weather.format_weather_message(weather)
        return f"Não foi possível obter informações para: {city}"
    
    def handle_cancel(self, user, args):
        user.active = False
        from app import db
        db.session.commit()
        return "✅ Alertas desativados. Para reativar, acesse nosso site."
    
    def handle_help(self, user, args):
        help_text = "📱 *COMANDOS DISPONÍVEIS*\n\n"
        help_text += "/terremoto - Último terremoto registrado\n"
        help_text += "/clima [cidade] - Condições atuais\n"
        help_text += "/cancelar - Desativar alertas\n"
        help_text += "/ajuda - Esta mensagem"
        return help_text