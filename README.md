# SismoClima

Sistema de alertas automáticos de terremotos e clima extremo via Telegram.

## Instalação

```bash
git clone https://github.com/sidraque/sismoclima.git
cd sismoclima
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Configuração

Crie `.env` na raiz:

```env
OPENWEATHER_API_KEY=sua_chave
TELEGRAM_BOT_TOKEN=seu_token
FLASK_SECRET_KEY=chave_secreta
```

**Obter APIs:**
- OpenWeather: https://openweathermap.org/api
- Telegram Bot: Envie `/newbot` para @BotFather

## Execução

```bash
python run.py
```

Acesse: http://localhost:5000

## Uso

1. Cadastre-se no site
2. Abra o bot no Telegram
3. Envie `/cadastrar Nome, Cidade`
4. Receba alertas automaticamente

## Comandos do Bot

```
/cadastrar Nome, Cidade  - Cadastrar
/terremoto              - Último terremoto
/clima [cidade]         - Condições atuais
/status                 - Ver cadastro
/cancelar               - Desativar alertas
```

## Stack

Python · Flask · SQLAlchemy · Telegram Bot API · USGS · OpenWeather

## Licença

MIT