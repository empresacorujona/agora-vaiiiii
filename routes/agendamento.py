from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    session
)

from models import (
    db,
    Agendamento
)

from datetime import datetime

agendamento_bp = Blueprint(
    "agendamento",
    __name__
)

@agendamento_bp.route("/agendar", methods=["POST"])
def agendar():

    data = request.form["data"]
    hora = request.form["hora"]

    novo_agendamento = Agendamento(
        usuario_id=session["usuario_id"],
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
        data=data,
        hora=hora,
        nome=session["usuario_nome"]
    )