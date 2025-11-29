from app.models import db, User
from services.telegram_service import TelegramService
from services.usgs_service import USGSService
from services.weather_service import WeatherService

telegram = TelegramService()
usgs = USGSService()
weather = WeatherService()


def handle_start(chat_id, message):
    user_info = message.get('from', {})
    first_name = user_info.get('first_name', '')
    last_name = user_info.get('last_name', '')
    nome_completo = (first_name + ' ' + last_name).strip()
    
    user = User.query.filter_by(telegram_chat_id=str(chat_id)).first()
    
    if user:
        msg = f"""
<b>Bem-vindo de volta, {user.name}</b>

Você está cadastrado e receberá alertas de:
• Terremotos (magnitude 5.0+)
• Condições meteorológicas extremas

<b>Comandos disponíveis:</b>
/terremoto - Último evento sísmico
/clima - Condições atuais em {user.city}
/status - Ver seu cadastro
/cancelar - Desativar alertas
/ajuda - Lista de comandos
        """
        telegram.send_message(chat_id, msg)
    else:
        msg = f"""
<b>Bem-vindo ao SismoClima</b>

Olá, {nome_completo}

Para receber alertas automáticos, envie:

<code>/cadastrar Seu Nome Completo, Sua Cidade</code>

<b>Exemplo:</b>
<code>/cadastrar Sidraque Agostinho, Recife</code>
        """
        telegram.send_message(chat_id, msg)


def handle_command(chat_id, text):
    comando = text.split()[0].lower()
    
    if comando == '/cadastrar':
        handle_cadastrar(chat_id, text)
    elif comando == '/terremoto':
        handle_terremoto(chat_id)
    elif comando == '/clima':
        handle_clima(chat_id, text)
    elif comando == '/status':
        handle_status(chat_id)
    elif comando == '/cancelar':
        handle_cancelar(chat_id)
    elif comando == '/ajuda':
        handle_ajuda(chat_id)
    else:
        msg = "Comando não reconhecido. Use /ajuda para ver comandos disponíveis."
        telegram.send_message(chat_id, msg)


def handle_cadastrar(chat_id, text):
    try:
        _, dados = text.split(' ', 1)
        
        if ',' not in dados:
            raise ValueError("Formato incorreto")
        
        nome, cidade = dados.split(',', 1)
        nome = nome.strip()
        cidade = cidade.strip()
        
        if not nome or not cidade:
            raise ValueError("Nome ou cidade vazio")
        
        existing = User.query.filter_by(telegram_chat_id=str(chat_id)).first()
        
        if existing:
            msg = f"""
Você já está cadastrado como <b>{existing.name}</b>

Para atualizar:
/cancelar - Remover cadastro atual
/cadastrar - Cadastrar novamente
            """
            telegram.send_message(chat_id, msg)
            return
        
        user = User(
            name=nome,
            phone=str(chat_id),
            city=cidade,
            telegram_chat_id=str(chat_id),
            confirmed=True,
            active=True
        )
        
        db.session.add(user)
        db.session.commit()
        
        msg = f"""
✓ <b>Cadastro confirmado</b>

<b>Nome:</b> {nome}
<b>Cidade:</b> {cidade}

Você receberá alertas automáticos de:
• Terremotos (magnitude 5.0+)
• Condições meteorológicas extremas

<b>Comandos úteis:</b>
/terremoto - Último terremoto
/clima - Clima atual
/status - Ver cadastro
        """
        telegram.send_message(chat_id, msg)
        
    except ValueError:
        msg = """
<b>Formato incorreto</b>

Use este formato:
<code>/cadastrar Seu Nome Completo, Sua Cidade</code>

<b>Exemplo:</b>
<code>/cadastrar Sidraque Agostinho, Recife</code>
        """
        telegram.send_message(chat_id, msg)
    
    except Exception as e:
        msg = f"Erro ao cadastrar: {str(e)}\n\nTente novamente ou contate o suporte."
        telegram.send_message(chat_id, msg)


def handle_terremoto(chat_id):
    earthquakes = usgs.get_recent_earthquakes(hours=24)
    
    if earthquakes:
        latest = earthquakes[0]
        msg = usgs.format_earthquake_message(latest)
    else:
        msg = "<b>Nenhum terremoto significativo</b>\n\nNão houve terremotos com magnitude maior que 5.0 nas últimas 24 horas."
    
    telegram.send_message(chat_id, msg)


def handle_clima(chat_id, text):
    parts = text.split(' ', 1)
    
    if len(parts) > 1:
        cidade = parts[1].strip()
    else:
        user = User.query.filter_by(telegram_chat_id=str(chat_id)).first()
        
        if not user:
            msg = "Você não está cadastrado.\n\nUse: /cadastrar Seu Nome, Sua Cidade"
            telegram.send_message(chat_id, msg)
            return
        
        cidade = user.city
    
    w = weather.get_current_weather(cidade)
    
    if w:
        msg = weather.format_weather_message(w)
    else:
        msg = f"Não foi possível obter clima para: {cidade}\n\nVerifique o nome da cidade."
    
    telegram.send_message(chat_id, msg)


def handle_status(chat_id):
    user = User.query.filter_by(telegram_chat_id=str(chat_id)).first()
    
    if not user:
        msg = """
<b>Você não está cadastrado</b>

Para se cadastrar:
<code>/cadastrar Seu Nome, Sua Cidade</code>
        """
    else:
        status = "● Ativo" if user.active else "○ Inativo"
        
        msg = f"""
<b>Seu Cadastro</b>

<b>Nome:</b> {user.name}
<b>Cidade:</b> {user.city}
<b>Status:</b> {status}
<b>Cadastrado em:</b> {user.created_at.strftime('%d/%m/%Y')}

<b>Alertas ativos:</b>
• Terremotos (magnitude 5.0+)
• Clima extremo em {user.city}
        """
    
    telegram.send_message(chat_id, msg)


def handle_cancelar(chat_id):
    user = User.query.filter_by(telegram_chat_id=str(chat_id)).first()
    
    if not user:
        msg = "Você não está cadastrado."
        telegram.send_message(chat_id, msg)
        return
    
    if not user.active:
        msg = "Seus alertas já estão desativados.\n\nPara reativar, use: /reativar"
        telegram.send_message(chat_id, msg)
        return
    
    user.active = False
    db.session.commit()
    
    msg = """
✓ <b>Alertas desativados</b>

Você não receberá mais alertas automáticos.

Para reativar a qualquer momento: /reativar
    """
    telegram.send_message(chat_id, msg)


def handle_ajuda(chat_id):
    msg = """
<b>COMANDOS DISPONÍVEIS</b>

<b>Cadastro</b>
/cadastrar Nome, Cidade - Cadastrar no sistema
/status - Ver seu cadastro
/cancelar - Desativar alertas
/reativar - Reativar alertas

<b>Consultas</b>
/terremoto - Último terremoto registrado
/clima [cidade] - Condições atuais
/ajuda - Esta mensagem

<b>Exemplos</b>
<code>/clima Recife</code>
<code>/cadastrar Sidraque, Jaboatão</code>
    """
    telegram.send_message(chat_id, msg)