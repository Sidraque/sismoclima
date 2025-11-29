# -*- coding: utf-8 -*-
"""
Run - SismoClima COMPLETO
Sistema Web + Bot Telegram + Scheduler
"""

import threading
import time
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
last_update_id = 0


def telegram_bot_loop():
    """Loop do bot Telegram em background"""
    global last_update_id
    
    print("🤖 Bot Telegram iniciado!")
    
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
                    
                    # Processar mensagem
                    if 'message' in update:
                        with app.app_context():
                            message = update['message']
                            chat_id = message['chat']['id']
                            text = message.get('text', '')
                            
                            print(f"📩 Telegram [{chat_id}]: {text}")
                            
                            if text.startswith('/start'):
                                handle_start(chat_id, message)
                                print("✅ Resposta enviada!")
                            elif text.startswith('/'):
                                handle_command(chat_id, text)
                                print("✅ Resposta enviada!")
            
            time.sleep(2)  # Verificar a cada 2 segundos
            
        except Exception as e:
            print(f"⚠️ Erro no bot: {e}")
            time.sleep(5)


if __name__ == '__main__':
    # Configurar para aceitar ngrok
    app.config['SERVER_NAME'] = None
    
    # Iniciar scheduler em background
    print("📅 Iniciando scheduler...")
    scheduler.start_background()
    
    # Iniciar bot Telegram em background
    print("🤖 Iniciando bot Telegram...")
    bot_thread = threading.Thread(target=telegram_bot_loop, daemon=True)
    bot_thread.start()
    
    # Iniciar aplicacao Flask
    print("\n" + "="*60)
    print("🚀 SISMOCLIMA ONLINE!")
    print("="*60)
    print("📍 Site Local: http://localhost:5000")
    print("📍 Site Rede: http://192.168.0.76:5000")
    print("🤖 Bot: @sismoclima_bot")
    print("📊 Status: Monitorando terremotos e clima")
    print("⏹️  Para parar: CTRL + C")
    print("="*60 + "\n")
    
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)