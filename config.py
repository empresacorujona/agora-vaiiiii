import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY")
    if not SECRET_KEY:
        if os.getenv("FLASK_DEBUG", "false").lower() == "true":
            SECRET_KEY = "dev-only-change-this-secret"
        else:
            raise RuntimeError("Defina SECRET_KEY no ambiente antes de iniciar o app.")
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL", "sqlite:///owlconvenial.db"
    ).replace("postgres://", "postgresql://", 1)
    # Use the bundled psycopg2 binary driver. This avoids requiring libpq
    # or the optional C/binary modules used by psycopg 3.
    if SQLALCHEMY_DATABASE_URI.startswith("postgresql+psycopg://"):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace(
            "postgresql+psycopg://", "postgresql+psycopg2://", 1
        )
    elif SQLALCHEMY_DATABASE_URI.startswith("postgresql://"):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace(
            "postgresql://", "postgresql+psycopg2://", 1
        )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.getenv("MAIL_PORT", "587"))
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "true").lower() == "true"
    MAIL_USE_SSL = os.getenv("MAIL_USE_SSL", "false").lower() == "true"
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER", MAIL_USERNAME or "")

    APP_BASE_URL = os.getenv("APP_BASE_URL", "http://localhost:5000").rstrip("/")
    EMAIL_VERIFICATION_MAX_AGE = int(os.getenv("EMAIL_VERIFICATION_MAX_AGE", "86400"))

    MERCADOPAGO_ACCESS_TOKEN = os.getenv("MERCADOPAGO_ACCESS_TOKEN")
    MERCADOPAGO_WEBHOOK_SECRET = os.getenv("MERCADOPAGO_WEBHOOK_SECRET")
    MERCADOPAGO_API_URL = "https://api.mercadopago.com"

    DEBUG = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = APP_BASE_URL.startswith("https://")
