from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app.models import db, User
from services.telegram_service import TelegramService
from services.usgs_service import USGSService
from services.weather_service import WeatherService

bp = Blueprint('main', __name__)
telegram = TelegramService()
usgs = USGSService()
weather = WeatherService()

@bp.route('/')
def index():
    return render_template('index.html')

@bp.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        name = request.form.get('name')
        phone = request.form.get('phone')
        city = request.form.get('city')
        
        phone = phone.replace(' ', '').replace('-', '').replace('(', '').replace(')', '').replace('+', '')
        
        if not phone.startswith('55'):
            phone = '55' + phone
        
        existing_user = User.query.filter_by(phone=phone).first()
        if existing_user:
            flash('Telefone ja cadastrado!', 'error')
            return redirect(url_for('main.cadastro'))
        
        user = User(name=name, phone=phone, city=city)
        
        db.session.add(user)
        db.session.commit()
        
        flash('Cadastro iniciado!', 'success')
        return redirect(url_for('main.instrucoes_telegram', user_id=user.id))
    
    return render_template('cadastro.html')

@bp.route('/instrucoes-telegram/<int:user_id>')
def instrucoes_telegram(user_id):
    user = User.query.get_or_404(user_id)
    
    bot_info = telegram.get_bot_info()
    bot_username = bot_info.get('result', {}).get('username', 'sismoclima_bot') if bot_info else 'sismoclima_bot'
    
    return render_template('instrucoes_telegram.html', user=user, bot_username=bot_username)

@bp.route('/api/earthquake/latest')
def latest_earthquake():
    earthquakes = usgs.get_recent_earthquakes(hours=24)
    if earthquakes:
        return jsonify(earthquakes[0])
    return jsonify({'message': 'Nenhum terremoto recente'}), 404

@bp.route('/api/weather/<city>')
def get_weather(city):
    w = weather.get_current_weather(city)
    if w:
        return jsonify(w)
    return jsonify({'message': 'Cidade nao encontrada'}), 404

@bp.route('/api/telegram/webhook', methods=['POST'])
def telegram_webhook():
    data = request.json
    
    if 'message' in data:
        message = data['message']
        chat_id = message['chat']['id']
        text = message.get('text', '')
        
        if text.startswith('/start'):
            from automation.telegram_commands import handle_start
            handle_start(chat_id, message)
        
        elif text.startswith('/'):
            from automation.telegram_commands import handle_command
            handle_command(chat_id, text)
    
    return jsonify({'ok': True})