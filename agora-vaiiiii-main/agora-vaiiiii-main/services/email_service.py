# services/email_service.py

from flask_mail import Mail, Message

mail = Mail()

def enviar_email(email, token):

    msg = Message(
        "Verificação de Conta",
        recipients=[email]
    )

    msg.body = f"""
    Clique no link:

    http://localhost:5000/verificar/{token}
    """

    mail.send(msg)