# routes/auth.py
### o fazedor de rotas
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for
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

##comunicação de abas por back e bd
@auth_bp.route("/cadastro", methods=["GET", "POST"])
def cadastro():

    if request.method == "POST":

        nome = request.form["nome"]
        email = request.form["email"]
        senha = request.form["senha"]

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
## atualização retirando de cadastro pra loguin
        return redirect("/hospitais")

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

                return redirect("/hospitais")

    return render_template("login.html")