from flask import current_app, url_for
from flask_mail import Mail, Message
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

mail = Mail()


def _serializer():
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"], salt="email-confirmation")


def gerar_token_verificacao(email):
    return _serializer().dumps(email, salt="email-confirmation")


def validar_token_verificacao(token):
    try:
        return _serializer().loads(
            token,
            salt="email-confirmation",
            max_age=current_app.config["EMAIL_VERIFICATION_MAX_AGE"],
        )
    except (BadSignature, SignatureExpired):
        return None


def enviar_email_verificacao(email):
    if not current_app.config.get("MAIL_USERNAME") or not current_app.config.get("MAIL_PASSWORD"):
        raise RuntimeError("Configure MAIL_USERNAME e MAIL_PASSWORD para enviar e-mails.")

    token = gerar_token_verificacao(email)
    link = f"{current_app.config['APP_BASE_URL']}{url_for('auth.verificar_email', token=token)}"
    mensagem = Message(
        subject="Confirme seu e-mail | OwlConvenial",
        recipients=[email],
        body=(
            "Olá!\n\n"
            "Confirme seu e-mail para ativar sua conta OwlConvenial acessando o link abaixo.\n"
            f"{link}\n\n"
            f"Este link expira em {current_app.config['EMAIL_VERIFICATION_MAX_AGE'] // 3600} horas."
        ),
        html=(
            "<p>Olá!</p><p>Confirme seu e-mail para ativar sua conta OwlConvenial:</p>"
            f'<p><a href="{link}">Confirmar meu e-mail</a></p>'
            f"<p>O link expira em {current_app.config['EMAIL_VERIFICATION_MAX_AGE'] // 3600} horas.</p>"
        ),
    )
    mail.send(mensagem)


def enviar_codigo_login(email, codigo):
    if not current_app.config.get("MAIL_USERNAME") or not current_app.config.get("MAIL_PASSWORD"):
        raise RuntimeError("Configure MAIL_USERNAME e MAIL_PASSWORD para enviar e-mails.")
    mensagem = Message(
        subject="Seu código de acesso | OwlConvenial",
        recipients=[email],
        body=(
            "Olá!\n\n"
            f"Seu código para entrar no OwlConvenial é: {codigo}\n\n"
            "Ele expira em 10 minutos. Se você não solicitou este código, ignore esta mensagem."
        ),
        html=(
            "<p>Olá!</p><p>Seu código para entrar no OwlConvenial é:</p>"
            f"<p style='font-size:28px;font-weight:bold;letter-spacing:6px'>{codigo}</p>"
            "<p>Ele expira em 10 minutos. Se você não solicitou este código, ignore esta mensagem.</p>"
        ),
    )
    mail.send(mensagem)


def enviar_codigo_verificacao(email, codigo):
    if not current_app.config.get("MAIL_USERNAME") or not current_app.config.get("MAIL_PASSWORD"):
        raise RuntimeError("Configure MAIL_USERNAME e MAIL_PASSWORD para enviar e-mails.")
    mensagem = Message(
        subject="Código para confirmar seu e-mail | OwlConvenial",
        recipients=[email],
        body=(
            "Olá!\n\n"
            f"Seu código para confirmar o e-mail no OwlConvenial é: {codigo}\n\n"
            "Ele expira em 10 minutos. Se você não criou uma conta, ignore esta mensagem."
        ),
        html=(
            "<p>Olá!</p><p>Use este código para confirmar seu e-mail no OwlConvenial:</p>"
            f"<p style='font-size:28px;font-weight:bold;letter-spacing:6px'>{codigo}</p>"
            "<p>Ele expira em 10 minutos. Se você não criou uma conta, ignore esta mensagem.</p>"
        ),
    )
    mail.send(mensagem)
