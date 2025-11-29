from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
import random
import string

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), unique=True, nullable=False)
    city = db.Column(db.String(100), nullable=False)
    
    # Telegram
    telegram_chat_id = db.Column(db.String(50), unique=True, nullable=True)
    
    confirmation_code = db.Column(db.String(6))
    confirmed = db.Column(db.Boolean, default=False)
    
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def generate_confirmation_code(self):
        self.confirmation_code = ''.join(random.choices(string.digits, k=6))
        return self.confirmation_code
    
    def verify_code(self, code):
        if self.confirmation_code == code:
            self.confirmed = True
            return True
        return False
    
    def __repr__(self):
        return '<User %s>' % self.name


class AlertLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    alert_type = db.Column(db.String(20))  # 'earthquake' ou 'weather'
    message = db.Column(db.Text)
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    success = db.Column(db.Boolean, default=True)
    
    user = db.relationship('User', backref='alerts')
    
    def __repr__(self):
        return '<Alert %s - %s>' % (self.alert_type, self.sent_at)