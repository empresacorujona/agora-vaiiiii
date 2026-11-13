from datetime import date, datetime, timedelta
import hashlib
import hmac
import secrets
import time
import re

from bcrypt import checkpw, gensalt, hashpw
from flask import Blueprint, current_app, flash, redirect, render_template, request, session, url_for
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError

from models import Usuario, db
from services.email_service import enviar_codigo_login, enviar_codigo_verificacao, validar_token_verificacao

auth_bp = Blueprint("auth", __name__)


def _hash_codigo(usuario_id, codigo):
    mensagem = f"{usuario_id}:{codigo}".encode("utf-8")
    return hmac.new(current_app.config["SECRET_KEY"].encode("utf-8"), mensagem, hashlib.sha256).hexdigest()


def _enviar_codigo(usuario, reset_attempts=True):
    codigo = f"{secrets.randbelow(1_000_000):06d}"
    enviar_codigo_login(usuario.email, codigo)
    usuario.login_code_hash = _hash_codigo(usuario.id, codigo)
    usuario.login_code_expires_at = datetime.utcnow() + timedelta(minutes=10)
    usuario.login_code_sent_at = datetime.utcnow()
    if reset_attempts:
        usuario.login_code_attempts = 0
    db.session.commit()


def _hash_codigo_verificacao(usuario_id, codigo):
    mensagem = f"email:{usuario_id}:{codigo}".encode("utf-8")
    return hmac.new(current_app.config["SECRET_KEY"].encode("utf-8"), mensagem, hashlib.sha256).hexdigest()


def _enviar_codigo_confirmacao(usuario, reset_attempts=True):
    codigo = f"{secrets.randbelow(1_000_000):06d}"
    enviar_codigo_verificacao(usuario.email, codigo)
    usuario.email_verification_code_hash = _hash_codigo_verificacao(usuario.id, codigo)
    usuario.email_verification_code_expires_at = datetime.utcnow() + timedelta(minutes=10)
    usuario.email_verification_code_sent_at = datetime.utcnow()
    if reset_attempts:
        usuario.email_verification_code_attempts = 0
    db.session.commit()


def _iniciar_confirmacao_email(usuario):
    session["email_verificacao_pendente"] = usuario.email
    agora = datetime.utcnow()
    codigo_recente = (
        usuario.email_verification_code_hash
        and usuario.email_verification_code_expires_at
        and usuario.email_verification_code_expires_at >= agora
        and usuario.email_verification_code_sent_at
        and agora - usuario.email_verification_code_sent_at < timedelta(minutes=1)
    )
    if codigo_recente:
        session["email_codigo_enviado_em"] = time.time()
        flash("Um código recente já foi enviado. Confira seu e-mail.", "info")
        return
    try:
        _enviar_codigo_confirmacao(usuario)
        session["email_codigo_enviado_em"] = time.time()
        flash("Enviamos um código de 6 dígitos para seu e-mail. Ele expira em 10 minutos.", "info")
    except Exception:
        session.pop("email_codigo_enviado_em", None)
        current_app.logger.exception("Falha ao enviar código de confirmação de e-mail")
        flash("Não foi possível enviar o código. Confira o SMTP e peça um novo código.", "warning")


@auth_bp.route("/cadastro", methods=["GET", "POST"])
def cadastro():
    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        email = request.form.get("email", "").strip().lower()
        telefone = re.sub(r"\D", "", request.form.get("telefone", ""))
        cpf = re.sub(r"\D", "", request.form.get("cpf", ""))
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
        if len(nome) > 150 or len(cpf) != 11 or (email and (len(email) > 200 or not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email))):
            flash("Confira o nome, o CPF com 11 dígitos e o formato do e-mail.", "danger")
            return render_template("cadastro.html")
        if len(senha.encode("utf-8")) > 72:
            flash("A senha deve ter no máximo 72 bytes. Use menos caracteres ou uma senha mais simples.", "danger")
            return render_template("cadastro.html")
        if telefone and not (10 <= len(telefone) <= 13):
            flash("Informe um número de telefone válido.", "danger")
            return render_template("cadastro.html")
        if data_nascimento >= date.today():
            flash("A data de nascimento deve ser anterior a hoje.", "danger")
            return render_template("cadastro.html")

        filtros = [Usuario.cpf == cpf]
        if email:
            filtros.append(Usuario.email == email)
        if telefone:
            filtros.append(Usuario.telefone == telefone)
        existing = Usuario.query.filter(or_(*filtros)).first()
        if existing:
            flash("Este e-mail ou CPF já está cadastrado. Se falta confirmar o e-mail, solicite outro código.", "warning")
            return render_template("cadastro.html")

        usuario = Usuario(
            nome=nome,
            email=email or None,
            telefone=telefone or None,
            cpf=cpf,
            genero=genero,
            data_nascimento=data_nascimento,
            senha=hashpw(senha.encode("utf-8"), gensalt()).decode("utf-8"),
            email_verificado=not bool(email),
        )
        db.session.add(usuario)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash("Este e-mail ou CPF já está cadastrado.", "warning")
            return render_template("cadastro.html")

        if email:
            session.clear()
            _iniciar_confirmacao_email(usuario)
            flash("Conta criada. Confirme seu e-mail com o código para liberar o acesso.", "info")
            return redirect(url_for("auth.verificar_email_codigo"))
        else:
            # Cadastro só com telefone não pode ser validado até existir provedor SMS.
            session.clear()
            session["usuario_id"] = usuario.id
            session["usuario_nome"] = usuario.nome
            session["usuario_email"] = usuario.email
            flash("Conta criada. O telefone ainda não foi verificado por SMS.", "warning")
        return redirect(url_for("index"))

    return render_template("cadastro.html")


@auth_bp.route("/verificar-email-codigo", methods=["GET", "POST"])
def verificar_email_codigo():
    email = session.get("email_verificacao_pendente")
    if not email:
        flash("Informe seu e-mail para solicitar um código de confirmação.", "info")
        return redirect(url_for("auth.reenviar_verificacao"))
    usuario = Usuario.query.filter_by(email=email).first()
    if not usuario:
        session.pop("email_verificacao_pendente", None)
        flash("Não encontramos uma conta para esse e-mail.", "warning")
        return redirect(url_for("auth.cadastro"))
    if usuario.email_verificado:
        session.pop("email_verificacao_pendente", None)
        flash("E-mail já confirmado. Você pode entrar.", "success")
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        if request.form.get("acao") == "reenviar":
            ultimo_envio = session.get("email_codigo_enviado_em", 0)
            if time.time() - ultimo_envio < 60:
                flash("Aguarde um minuto antes de pedir outro código.", "warning")
                return redirect(url_for("auth.verificar_email_codigo"))
            try:
                _enviar_codigo_confirmacao(usuario, reset_attempts=False)
                session["email_codigo_enviado_em"] = time.time()
                flash("Enviamos outro código para seu e-mail.", "success")
            except Exception:
                current_app.logger.exception("Falha ao reenviar código de confirmação")
                flash("Não foi possível reenviar o código. Tente novamente mais tarde.", "danger")
            return redirect(url_for("auth.verificar_email_codigo"))

        codigo = request.form.get("codigo", "").strip()
        if usuario.email_verification_code_attempts >= 5:
            usuario.email_verification_code_hash = None
            usuario.email_verification_code_expires_at = None
            db.session.commit()
            session.pop("email_verificacao_pendente", None)
            flash("Limite de tentativas atingido. Solicite outro código.", "warning")
            return redirect(url_for("auth.reenviar_verificacao"))

        usuario.email_verification_code_attempts += 1
        valido = (
            bool(usuario.email_verification_code_hash)
            and bool(usuario.email_verification_code_expires_at)
            and usuario.email_verification_code_expires_at >= datetime.utcnow()
            and len(codigo) == 6
            and codigo.isdigit()
            and hmac.compare_digest(
                usuario.email_verification_code_hash,
                _hash_codigo_verificacao(usuario.id, codigo),
            )
        )
        if not valido:
            db.session.commit()
            flash("Código inválido ou expirado. Confira o e-mail ou peça outro código.", "danger")
            return render_template("verificar_email_codigo.html", email=usuario.email)

        usuario.email_verificado = True
        usuario.email_verification_code_hash = None
        usuario.email_verification_code_expires_at = None
        usuario.email_verification_code_attempts = 0
        db.session.commit()
        session.clear()
        session["usuario_id"] = usuario.id
        session["usuario_nome"] = usuario.nome
        session["usuario_email"] = usuario.email
        flash("E-mail confirmado e conta ativada. Bem-vindo(a)!", "success")
        return redirect(url_for("index"))

    return render_template("verificar_email_codigo.html", email=usuario.email)


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
            _iniciar_confirmacao_email(usuario)
            return redirect(url_for("auth.verificar_email_codigo"))
        else:
            flash("Se houver uma conta pendente para esse e-mail, enviaremos um código.", "info")
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

        senha_bytes = senha.encode("utf-8")
        senha_correta = bool(usuario and len(senha_bytes) <= 72 and checkpw(senha_bytes, usuario.senha.encode("utf-8")))
        if senha_correta:
            if not usuario.email_verificado:
                _iniciar_confirmacao_email(usuario)
                flash("Confirme seu e-mail com o código enviado para continuar.", "info")
                return redirect(url_for("auth.verificar_email_codigo"))
            if usuario.email:
                agora = datetime.utcnow()
                codigo_ainda_valido = (
                    usuario.login_code_hash
                    and usuario.login_code_expires_at
                    and usuario.login_code_expires_at >= agora
                    and usuario.login_code_sent_at
                    and agora - usuario.login_code_sent_at < timedelta(minutes=1)
                )
                if codigo_ainda_valido:
                    session.clear()
                    session["login_pendente_id"] = usuario.id
                    session["codigo_enviado_em"] = time.time()
                    flash("Um código recente já foi enviado. Confira seu e-mail antes de pedir outro.", "info")
                    return redirect(url_for("auth.verificar_codigo"))
                try:
                    _enviar_codigo(usuario)
                except Exception:
                    current_app.logger.exception("Falha ao enviar código de login")
                    usuario.login_code_hash = None
                    usuario.login_code_expires_at = None
                    db.session.commit()
                    flash("Não foi possível enviar o código. Confira a configuração de e-mail e tente novamente.", "danger")
                    return render_template("login.html")
                session.clear()
                session["login_pendente_id"] = usuario.id
                session["codigo_enviado_em"] = time.time()
                flash("Enviamos um código de 6 dígitos para seu e-mail. Ele expira em 10 minutos.", "info")
                return redirect(url_for("auth.verificar_codigo"))
            session.clear()
            session["usuario_id"] = usuario.id
            session["usuario_nome"] = usuario.nome
            session["usuario_email"] = usuario.email
            flash(f"Bem-vindo(a), {usuario.nome}!", "success")
            return redirect(url_for("index"))

        flash("E-mail ou senha inválidos.", "danger")
        return render_template("login.html")
    return render_template("login.html")


@auth_bp.route("/verificar-codigo", methods=["GET", "POST"])
def verificar_codigo():
    usuario_id = session.get("login_pendente_id")
    if not usuario_id:
        flash("Entre com sua senha para solicitar um código de acesso.", "info")
        return redirect(url_for("auth.login"))
    usuario = db.session.get(Usuario, usuario_id)
    if not usuario or not usuario.email:
        session.clear()
        flash("Não encontramos um e-mail para esta conta. Entre novamente.", "warning")
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        if request.form.get("acao") == "reenviar":
            ultimo_envio = session.get("codigo_enviado_em", 0)
            if time.time() - ultimo_envio < 60:
                flash("Aguarde um minuto antes de pedir outro código.", "warning")
                return redirect(url_for("auth.verificar_codigo"))
            try:
                _enviar_codigo(usuario, reset_attempts=False)
                session["codigo_enviado_em"] = time.time()
                flash("Enviamos um novo código para seu e-mail.", "success")
            except Exception:
                current_app.logger.exception("Falha ao reenviar código de login")
                flash("Não foi possível reenviar o código. Tente novamente mais tarde.", "danger")
            return redirect(url_for("auth.verificar_codigo"))

        codigo = request.form.get("codigo", "").strip()
        if usuario.login_code_attempts >= 5:
            usuario.login_code_hash = None
            usuario.login_code_expires_at = None
            db.session.commit()
            session.pop("login_pendente_id", None)
            flash("Limite de tentativas atingido. Entre novamente para solicitar outro código.", "warning")
            return redirect(url_for("auth.login"))

        usuario.login_code_attempts += 1
        valido = (
            bool(usuario.login_code_hash)
            and bool(usuario.login_code_expires_at)
            and usuario.login_code_expires_at >= datetime.utcnow()
            and len(codigo) == 6
            and codigo.isdigit()
            and hmac.compare_digest(usuario.login_code_hash, _hash_codigo(usuario.id, codigo))
        )
        if not valido:
            db.session.commit()
            flash("Código inválido ou expirado. Confira o e-mail ou solicite outro código.", "danger")
            return render_template("verificar_codigo.html", email=usuario.email)

        usuario.login_code_hash = None
        usuario.login_code_expires_at = None
        usuario.login_code_attempts = 0
        db.session.commit()
        session.clear()
        session["usuario_id"] = usuario.id
        session["usuario_nome"] = usuario.nome
        session["usuario_email"] = usuario.email
        flash(f"Bem-vindo(a), {usuario.nome}!", "success")
        return redirect(url_for("index"))

    return render_template("verificar_codigo.html", email=usuario.email)


@auth_bp.route("/logout", methods=["GET", "POST"])
def logout():
    session.clear()
    flash("Você saiu da sua conta.", "info")
    return redirect(url_for("index"))
