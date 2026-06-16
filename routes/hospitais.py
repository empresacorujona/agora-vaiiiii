##api de hospitais
from flask import Blueprint, render_template
import requests

hospital_bp = Blueprint("hospital", __name__)

@hospital_bp.route("/hospitais")
def hospitais():

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

    return render_template(
        "dashboard.html",
        hospitais=hospitais
    )

from flask import render_template

@hospital_bp.route("/agendamento")
def tela_agendamento():

    return render_template(
        "agendamento.html"
    )

from flask import (
    request,
    session,
    render_template
)

from models import (
    db,
    Agendamento
)

from datetime import datetime

@hospital_bp.route(
    "/agendar",
    methods=["POST"]
)
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
        nome=session["usuario_nome"],
        data=data,
        hora=hora
    )