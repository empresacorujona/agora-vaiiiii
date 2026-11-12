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

    cpf = db.Column(
    db.String(14),
    unique=True,
    nullable=False
    )

    genero = db.Column(
    db.String(30),
    nullable=False
    )

    data_nascimento = db.Column(
    db.Date,
    nullable=False
    )

    email = db.Column(
        db.String(200),
        unique=True,
        nullable=True
    )

    telefone = db.Column(db.String(20), unique=True, nullable=True)

    senha = db.Column(
        db.String(255),
        nullable=False
    )

    email_verificado = db.Column(
        db.Boolean,
        default=False
    )

    agendamentos = db.relationship(
        "Agendamento",
        backref="usuario",
        lazy=True
    )

    doacoes = db.relationship("Doacao", backref="usuario", lazy=True)


class Agendamento(db.Model):

    __tablename__ = "agendamentos"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    usuario_id = db.Column(
        db.Integer,
        db.ForeignKey("usuarios.id"),
        nullable=False
    )

    hospital = db.Column(
        db.String(300),
        nullable=False
    )

    data_consulta = db.Column(
        db.Date,
        nullable=False
    )

    horario = db.Column(
        db.String(10),
        nullable=False
    )

    especialidade = db.Column(
    db.String(100),
    nullable=False
)
    def __repr__(self):

        return f"<Agendamento {self.hospital}>"


class Doacao(db.Model):
    __tablename__ = "doacoes"

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    valor_centavos = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(30), nullable=False, default="pending")
    mercado_pago_preference_id = db.Column(db.String(100), unique=True)
    mercado_pago_payment_id = db.Column(db.String(100), unique=True)
    criado_em = db.Column(db.DateTime, nullable=False, default=db.func.now())

    def __repr__(self):
        return f"<Doacao {self.id} {self.status}>"
