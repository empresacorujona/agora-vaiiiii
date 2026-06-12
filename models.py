# models.py

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Usuario(db.Model):

    __tablename__ = "usuarios"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    nome = db.Column(
        db.String(150),
        nullable=False
    )

    email = db.Column(
        db.String(200),
        unique=True,
        nullable=False
    )

    senha = db.Column(
        db.String(255),
        nullable=False
    )

    email_verificado = db.Column(
        db.Boolean,
        default=False
    )