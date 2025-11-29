
import requests
from config.settings import Config

class TelegramService:
    def __init__(self):
        self.token = Config.TELEGRAM_BOT_TOKEN
        self.base_url = f"https://api.telegram.org/bot{self.token}"
    
    def send_message(self, chat_id, message):
        url = f"{self.base_url}/sendMessage"
        
        data = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'HTML'
        }
        
        try:
            response = requests.post(url, json=data, timeout=10)
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            print(f"Erro ao enviar Telegram: {e}")
            return False
    
    def send_alert(self, chat_id, alert_message):
        return self.send_message(chat_id, alert_message)
    
    def send_confirmation_code(self, chat_id, code):
        message = f"""
🔐 <b>SismoClima - Confirmacao</b>

Seu codigo de confirmacao: <code>{code}</code>

Insira este codigo no site para ativar os alertas.
        """
        return self.send_message(chat_id, message)
    
    def get_updates(self):
        url = f"{self.base_url}/getUpdates"
        
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Erro ao obter updates: {e}")
            return None
    
    def get_bot_info(self):
        url = f"{self.base_url}/getMe"
        
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Erro ao obter info do bot: {e}")
            return None
