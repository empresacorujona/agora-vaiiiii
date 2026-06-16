# routes/auth.py

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session
)

from models import db, Usuario

from bcrypt import (
    hashpw,
    gensalt,
    checkpw
)

auth_bp = Blueprint(
    "auth",
    __name__
)


@auth_bp.route("/cadastro", methods=["GET", "POST"])
def cadastro():

    if request.method == "POST":

        nome = request.form["nome"]
        email = request.form["email"]
        senha = request.form["senha"]

        usuario_existente = Usuario.query.filter_by(
            email=email
        ).first()

        if usuario_existente:
            return "Este e-mail já está cadastrado."

        senha_hash = hashpw(
            senha.encode(),
            gensalt()
        )

        usuario = Usuario(
            nome=nome,
            email=email,
            senha=senha_hash.decode()
        )

        db.session.add(usuario)
        db.session.commit()

        return redirect("/login")

    return render_template(
        "cadastro.html"
    )


@auth_bp.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        senha = request.form["senha"]

        usuario = Usuario.query.filter_by(
            email=email
        ).first()

        if usuario:

            if checkpw(
                senha.encode(),
                usuario.senha.encode()
            ):

                session["usuario_id"] = usuario.id
                session["usuario_nome"] = usuario.nome
                session["usuario_email"] = usuario.email

                return redirect("/hospitais")

        return "E-mail ou senha inválidos."

    return render_template("login.html")


@auth_bp.route("/logout")
def logout():

    session.clear()

    return redirect("/login")