from datetime import date, datetime

from bcrypt import checkpw, gensalt, hashpw
from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
import re

from models import Usuario, db
from services.email_service import enviar_email_verificacao, validar_token_verificacao

auth_bp = Blueprint("auth", __name__)


def _enviar_confirmacao(email):
    try:
        enviar_email_verificacao(email)
        flash("Enviamos um link de confirmação para seu e-mail. Confira também o spam.", "success")
    except Exception:
        # The account remains available for a resend once SMTP is configured.
        flash("Conta criada, mas não foi possível enviar o e-mail. Configure o SMTP e solicite novo link.", "warning")


@auth_bp.route("/cadastro", methods=["GET", "POST"])
def cadastro():
    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        email = request.form.get("email", "").strip().lower()
        telefone = re.sub(r"\D", "", request.form.get("telefone", ""))
        cpf = request.form.get("cpf", "").strip()
        genero = request.form.get("genero", "").strip()
        senha = request.form.get("senha", "")
        try:
            data_nascimento = datetime.strptime(request.form.get("data_nascimento", ""), "%Y-%m-%d").date()
        except ValueError:
            flash("Informe uma data de nascimento válida.", "danger")
            return render_template("cadastro.html")

        if not all((nome, cpf, genero, senha)) or not (email or telefone) or len(senha) < 8:
            flash("Preencha os campos obrigatórios e informe e-mail ou telefone. A senha deve ter pelo menos 8 caracteres.", "danger")
            return render_template("cadastro.html")
        if telefone and not (10 <= len(telefone) <= 13):
            flash("Informe um número de telefone válido.", "danger")
            return render_template("cadastro.html")
        if data_nascimento >= date.today():
            flash("A data de nascimento deve ser anterior a hoje.", "danger")
            return render_template("cadastro.html")

        existing = Usuario.query.filter(
            or_(Usuario.email == email, Usuario.cpf == cpf, Usuario.telefone == telefone)
        ).first()
        if existing:
            flash("Este e-mail ou CPF já está cadastrado. Se falta confirmar o e-mail, solicite outro link.", "warning")
            return render_template("cadastro.html")

        usuario = Usuario(
            nome=nome,
            email=email,
            telefone=telefone or None,
            cpf=cpf,
            genero=genero,
            data_nascimento=data_nascimento,
            senha=hashpw(senha.encode("utf-8"), gensalt()).decode("utf-8"),
            email_verificado=True,
        )
        db.session.add(usuario)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash("Este e-mail ou CPF já está cadastrado.", "warning")
            return render_template("cadastro.html")

        session.clear()
        session["usuario_id"] = usuario.id
        session["usuario_nome"] = usuario.nome
        session["usuario_email"] = usuario.email
        flash(f"Conta criada com sucesso. Bem-vindo(a), {usuario.nome}!", "success")
        return redirect(url_for("index"))

    return render_template("cadastro.html")


@auth_bp.route("/verificar-email/<token>")
def verificar_email(token):
    email = validar_token_verificacao(token)
    if not email:
        flash("O link é inválido ou expirou. Solicite um novo link de confirmação.", "danger")
        return redirect(url_for("auth.reenviar_verificacao"))

    usuario = Usuario.query.filter_by(email=email).first()
    if not usuario:
        flash("Não encontramos uma conta para esse link.", "danger")
        return redirect(url_for("auth.cadastro"))
    if not usuario.email_verificado:
        usuario.email_verificado = True
        db.session.commit()
    flash("E-mail confirmado! Agora você já pode entrar.", "success")
    return redirect(url_for("auth.login"))


@auth_bp.route("/reenviar-verificacao", methods=["GET", "POST"])
def reenviar_verificacao():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        usuario = Usuario.query.filter_by(email=email).first()
        # Use the same response for known and unknown accounts.
        if usuario and not usuario.email_verificado:
            _enviar_confirmacao(usuario.email)
        else:
            flash("Se houver uma conta pendente para esse e-mail, enviaremos um novo link.", "info")
        return redirect(url_for("auth.login"))
    return render_template("reenviar_verificacao.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        identificador = request.form.get("identificador", "").strip()
        email = identificador.lower()
        telefone = re.sub(r"\D", "", identificador)
        senha = request.form.get("senha", "")
        usuario = Usuario.query.filter(or_(Usuario.email == email, Usuario.telefone == telefone)).first()

        if usuario and checkpw(senha.encode("utf-8"), usuario.senha.encode("utf-8")):
            if not usuario.email_verificado:
                flash("Confirme seu e-mail antes de entrar. Você pode solicitar outro link abaixo.", "warning")
                return redirect(url_for("auth.reenviar_verificacao"))
            session.clear()
            session["usuario_id"] = usuario.id
            session["usuario_nome"] = usuario.nome
            session["usuario_email"] = usuario.email
            flash(f"Bem-vindo(a), {usuario.nome}!", "success")
            return redirect(url_for("index"))

        flash("E-mail ou senha inválidos.", "danger")
        return render_template("login.html")
    return render_template("login.html")


@auth_bp.route("/logout", methods=["GET", "POST"])
def logout():
    session.clear()
    flash("Você saiu da sua conta.", "info")
    return redirect(url_for("index"))
