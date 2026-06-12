# app.py

from flask import Flask

from config import Config

from models import db

from routes.auth import auth_bp

from routes.hospitais import hospital_bp

app = Flask(__name__)

app.config.from_object(
    Config
)

db.init_app(app)

app.register_blueprint(
    auth_bp
)

app.register_blueprint(
    hospital_bp
)

with app.app_context():
    db.create_all()

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )