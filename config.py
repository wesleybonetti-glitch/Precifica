import os


class Config:
    # Suas configurações originais (mantidas)
    SECRET_KEY = os.getenv('SECRET_KEY', 'default_secret_key')
    SESSION_COOKIE_SECURE = False
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'sqlite:///precificaja_local.db' if os.getenv('FLASK_ENV') == 'development' else
        'mysql+pymysql://admin:bruno2013@database-1.c1kkuuacawg4.us-east-1.rds.amazonaws.com:3306/precificaja'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # --- CORREÇÃO: Impede que a conexão com o banco de dados expire durante processos longos ---
    SQLALCHEMY_POOL_RECYCLE = 280
    # -----------------------------------------------------------------------------------------

    # Suas configurações de e-mail (mantidas)
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = 'precificaja@gmail.com'
    MAIL_PASSWORD = 'jgsb rixl fyxn podb'
    MAIL_DEFAULT_SENDER = 'precificaja@gmail.com'

    # A linha da GEMINI_API_KEY foi removida daqui para ser controlada pelo app.py
