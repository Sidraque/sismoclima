# -*- coding: utf-8 -*-
"""
Run - SismoClima COMPLETO
Sistema Web + Bot Telegram + Scheduler
"""

import threading
import time
import os
from app import create_app
from automation.scheduler import MonitorScheduler
from services.telegram_service import TelegramService
from automation.telegram_commands import handle_start, handle_command

# Criar aplicacao Flask
app = create_app()

# Criar scheduler
scheduler = MonitorScheduler(app=app)

# Telegram
telegram = TelegramService()

# Arquivo para salvar ultimo update
UPDATE_FILE = 'last_update.txt'


def load_last_update_id():
    """Carrega o ultimo update_id salvo"""
    if os.path.exists(UPDATE_FILE):
        try:
            with open(UPDATE_FILE, 'r') as f:
                return int(f.read().strip())
        except:
            return 0
    return 0


def save_last_update_id(update_id):
    """Salva o ultimo update_id processado"""
    with open(UPDATE_FILE, 'w') as f:
        f.write(str(update_id))


def telegram_bot_loop():
    """Loop do bot Telegram em background"""
    # Carregar ultimo update processado
    last_update_id = load_last_update_id()
    
    print(f"Bot Telegram iniciado (ultimo update: {last_update_id})")
    
    while True:
        try:
            updates = telegram.get_updates()
            
            if updates and updates.get('ok'):
                for update in updates.get('result', []):
                    update_id = update.get('update_id')
                    
                    # Ignorar updates ja processados
                    if update_id <= last_update_id:
                        continue
                    
                    last_update_id = update_id
                    
                    # Salvar imediatamente
                    save_last_update_id(last_update_id)
                    
                    # Processar mensagem
                    if 'message' in update:
                        with app.app_context():
                            message = update['message']
                            chat_id = message['chat']['id']
                            text = message.get('text', '')
                            
                            print(f"[{chat_id}] {text}")
                            
                            if text.startswith('/start'):
                                handle_start(chat_id, message)
                            elif text.startswith('/'):
                                handle_command(chat_id, text)
            
            time.sleep(2)
            
        except Exception as e:
            print(f"Erro no bot: {e}")
            time.sleep(5)


if __name__ == '__main__':
    # Configurar para aceitar ngrok
    app.config['SERVER_NAME'] = None
    
    # Iniciar scheduler em background
    print("Iniciando scheduler...")
    scheduler.start_background()
    
    # Iniciar bot Telegram em background
    print("Iniciando bot Telegram...")
    bot_thread = threading.Thread(target=telegram_bot_loop, daemon=True)
    bot_thread.start()
    
    # Iniciar aplicacao Flask
    print("\n" + "="*60)
    print("SISMOCLIMA ONLINE")
    print("="*60)
    print("Site: http://localhost:5000")
    print("Rede: http://192.168.0.76:5000")
    print("Bot: Telegram")
    print("Status: Monitorando (1 min)")
    print("="*60 + "\n")
    
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)