# config.py
## banco de dados 
class Config:
    SECRET_KEY = "senha_super_secreta"

    SQLALCHEMY_DATABASE_URI = (
    "postgresql+psycopg2://postgres:123456@localhost:5436/convenio_db"
)

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = 'seuemail@gmail.com'
    MAIL_PASSWORD = 'senha_app_google'