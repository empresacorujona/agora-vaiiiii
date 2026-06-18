# api de hospitais

from flask import (
    Blueprint,
    render_template,
    request,
    session,
    redirect
)

import requests
from datetime import datetime

from services.geolocalizacao import obter_localizacao

from models import (
    db,
    Agendamento
)

hospital_bp = Blueprint(
    "hospital",
    __name__
)


@hospital_bp.route("/hospitais")
def hospitais():

    if "usuario_id" not in session:
        return redirect("/login")

    ip = request.remote_addr

    localizacao = obter_localizacao(ip)

    if localizacao:
        latitude = localizacao["latitude"]
        longitude = localizacao["longitude"]
    else:
        latitude = -23.55052
        longitude = -46.633308

    url = (
        f"https://nominatim.openstreetmap.org/search?"
        f"q=hospital&format=jsonv2"
        f"&limit=20"
        f"&viewbox="
        f"{longitude-0.1},{latitude+0.1},"
        f"{longitude+0.1},{latitude-0.1}"
        f"&bounded=1"
    )

    headers = {
        "User-Agent": "ConvenioMedico/1.0"
    }

    resposta = requests.get(
        url,
        headers=headers,
        timeout=30
    )

    hospitais = resposta.json()

    consultas = Agendamento.query.filter_by(
        usuario_id=session["usuario_id"]
    ).order_by(
        Agendamento.data_consulta.asc()
    ).all()

    return render_template(
        "hospitais.html",
        hospitais=hospitais,
        cidade=localizacao["cidade"] if localizacao else "São Paulo",
        consultas=consultas,
        nome=session["usuario_nome"]
    )


@hospital_bp.route("/agendamento")
def tela_agendamento():

    if "usuario_id" not in session:
        return redirect("/login")

    return render_template(
        "agendamento.html"
    )


@hospital_bp.route(
    "/agendar",
    methods=["POST"]
)
def agendar():

    if "usuario_id" not in session:
        return redirect("/login")

    data = request.form["data"]
    hora = request.form["hora"]
    hospital = request.form["hospital"]

    novo_agendamento = Agendamento(
    usuario_id=session["usuario_id"],
    data_consulta=datetime.strptime(
        data,
        "%Y-%m-%d"
    ).date(),
    horario=hora,
    hospital=hospital
    )

    db.session.add(novo_agendamento)
    db.session.commit()

    return render_template(
        "agendado.html",
        nome=session["usuario_nome"],
        data=data,
        hora=hora
    )