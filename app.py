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

# Rota da página inicial
@app.route("/")
def index():
    return render_template("paginainicial.html")

with app.app_context():
    db.create_all()

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )

from flask import session, redirect, request, render_template
from datetime import datetime
from models import Agendamento
from config import db

@app.route("/agendar", methods=["POST"])
def agendar():

    usuario_id = session.get("usuario_id")

    if not usuario_id:
        return redirect("/login")

    data = request.form["data"]
    hora = request.form["hora"]

    novo_agendamento = Agendamento(
        usuario_id=usuario_id,
        data_consulta=datetime.strptime(
            data,
            "%Y-%m-%d"
        ).date(),
        horario=hora
    )

    db.session.add(novo_agendamento)
    db.session.commit()

    return render_template(
        "agendado.html",
        nome=session["usuario_nome"],
        data=data,
        hora=hora
    )

with app.app_context():
    db.create_all()