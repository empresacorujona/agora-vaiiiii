from datetime import datetime
# 1. Corrigido: Incluída a importação do render_template no topo
from flask import Flask, redirect, request, render_template, session

from config import Config
# 2. Centralizado: O db deve vir de models para manter a consistência
from models import Agendamento, db
from routes.auth import auth_bp
from routes.hospitais import hospital_bp

app = Flask(__name__)
app.config.from_object(Config)

# Inicializa o banco de dados
db.init_app(app)

# Registro de Blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(hospital_bp)


# Rota Inicial
@app.route("/")
def index():
    return render_template("paginainicial.html")


# Rota de Agendamento (Movida para antes do app.run)
@app.route("/agendar", methods=["POST"])
def agendar():
    usuario_id = session.get("usuario_id")

    if not usuario_id:
        return redirect("/login")

    data = request.form["data"]
    hora = request.form["hora"]

    # Converte a string da data para objeto date do Python
    data_formatada = datetime.strptime(data, "%Y-%m-%d").date()

    novo_agendamento = Agendamento(
        usuario_id=usuario_id, data_consulta=data_formatada, horario=hora
    )

    # 3. Corrigido: Utiliza o db importado de models que foi inicializado no app
    db.session.add(novo_agendamento)
    db.session.commit()

    return render_template(
        "agendado.html", nome=session.get("usuario_nome"), data=data, hora=hora
    )


# Criação das tabelas dentro do contexto do app
with app.app_context():
    db.create_all()

@app.route("/sobrenos")
def sobrenos():

    return render_template(

        "sobrenos.html"

    )

# Inicialização do Servidor (Sempre no final do arquivo)
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)