import hmac
import secrets

from flask import Flask, abort, render_template, request, session
from sqlalchemy import inspect, text

from config import Config
from models import db
from routes.auth import auth_bp
from routes.doacoes import doacao_bp
from routes.hospitais import hospital_bp
from services.email_service import mail

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)
mail.init_app(app)

app.register_blueprint(auth_bp)
app.register_blueprint(hospital_bp)
app.register_blueprint(doacao_bp)


@app.context_processor
def dados_da_sessao():
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_urlsafe(32)
    return {
        "usuario_logado": bool(session.get("usuario_id")),
        "usuario_nome_logado": session.get("usuario_nome"),
        "csrf_token": session["csrf_token"],
    }


@app.before_request
def proteger_requisicoes_post():
    if request.method == "POST" and request.endpoint != "doacoes.webhook":
        enviado = request.form.get("csrf_token", "")
        esperado = session.get("csrf_token", "")
        if not esperado or not hmac.compare_digest(enviado, esperado):
            abort(400, description="Formulário expirado. Atualize a página e tente novamente.")


@app.route("/")
def index():
    return render_template("paginainicial.html")


@app.route("/sobrenos")
def sobrenos():
    return render_template("sobrenos.html")


@app.errorhandler(400)
def requisicao_invalida(error):
    mensagem = getattr(error, "description", "Não foi possível processar o formulário.")
    return render_template("erro.html", titulo="Formulário expirado", mensagem=mensagem), 400


@app.errorhandler(404)
def nao_encontrado(_error):
    return render_template(
        "erro.html",
        titulo="Página não encontrada",
        mensagem="O endereço pode estar desatualizado ou a página não existe.",
    ), 404


with app.app_context():
    db.create_all()
    # Compatibilidade com bancos locais criados antes do campo de telefone.
    if "telefone" not in {column["name"] for column in inspect(db.engine).get_columns("usuarios")}:
        with db.engine.begin() as connection:
            connection.execute(text("ALTER TABLE usuarios ADD COLUMN telefone VARCHAR(20)"))
            connection.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uq_usuarios_telefone ON usuarios (telefone)"))
    colunas_usuario = {column["name"] for column in inspect(db.engine).get_columns("usuarios")}
    with db.engine.begin() as connection:
        if "login_code_hash" not in colunas_usuario:
            connection.execute(text("ALTER TABLE usuarios ADD COLUMN login_code_hash VARCHAR(64)"))
        if "login_code_expires_at" not in colunas_usuario:
            connection.execute(text("ALTER TABLE usuarios ADD COLUMN login_code_expires_at TIMESTAMP"))
        if "login_code_sent_at" not in colunas_usuario:
            connection.execute(text("ALTER TABLE usuarios ADD COLUMN login_code_sent_at TIMESTAMP"))
        if "login_code_attempts" not in colunas_usuario:
            connection.execute(text("ALTER TABLE usuarios ADD COLUMN login_code_attempts INTEGER NOT NULL DEFAULT 0"))
        if "email_verification_code_hash" not in colunas_usuario:
            connection.execute(text("ALTER TABLE usuarios ADD COLUMN email_verification_code_hash VARCHAR(64)"))
        if "email_verification_code_expires_at" not in colunas_usuario:
            connection.execute(text("ALTER TABLE usuarios ADD COLUMN email_verification_code_expires_at TIMESTAMP"))
        if "email_verification_code_sent_at" not in colunas_usuario:
            connection.execute(text("ALTER TABLE usuarios ADD COLUMN email_verification_code_sent_at TIMESTAMP"))
        if "email_verification_code_attempts" not in colunas_usuario:
            connection.execute(text("ALTER TABLE usuarios ADD COLUMN email_verification_code_attempts INTEGER NOT NULL DEFAULT 0"))


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=app.config["DEBUG"])
