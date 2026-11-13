# api de hospitais

from flask import (
    Blueprint,
    render_template,
    request,
    session,
    redirect,
    flash,
    url_for
)

import requests

from datetime import datetime
from datetime import date
import re
from sqlalchemy.exc import IntegrityError

from services.geolocalizacao import obter_localizacao

from models import (
    db,
    Usuario,
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

        flash("Não conseguimos localizar sua região pelo IP; os resultados serão de São Paulo.", "info")

        latitude = -23.55052
        longitude = -46.633308

    url = (
        f"https://nominatim.openstreetmap.org/search?"
        f"q=hospital"
        f"&format=jsonv2"
        f"&limit=20"
        f"&viewbox="
        f"{longitude-0.1},{latitude+0.1},"
        f"{longitude+0.1},{latitude-0.1}"
        f"&bounded=1"
    )

    headers = {

        "User-Agent":"OwlConvenial/1.0"

    }

    try:
        resposta = requests.get(url, headers=headers, timeout=10)
        resposta.raise_for_status()
        hospitais = resposta.json()
        if not isinstance(hospitais, list):
            hospitais = []
    except (requests.RequestException, ValueError):
        hospitais = []
        flash("A busca de hospitais está temporariamente indisponível. Tente novamente.", "warning")

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
        hoje=date.today(),

        nome=session["usuario_nome"]

    )


@hospital_bp.route("/agendamento")
def tela_agendamento():

    if "usuario_id" not in session:

        return redirect("/login")

    hospital = request.args.get("hospital", "").strip()[:300]
    if not hospital:
        flash("Escolha um hospital para continuar.", "warning")
        return redirect(url_for("hospital.hospitais"))

    return render_template(

        "agendamento.html",

        hospital=hospital,
        hoje=date.today().isoformat(),
        especialidade=request.args.get("especialidade", ""),
        data=request.args.get("data", ""),
        hora=request.args.get("hora", "")

    )


@hospital_bp.route(

    "/agendar",

    methods=["POST"]

)
def agendar():

    if "usuario_id" not in session:

        return redirect("/login")

    hospital = request.form.get("hospital", "").strip()
    especialidade = request.form.get("especialidade", "").strip()
    data = request.form.get("data", "")
    hora = request.form.get("hora", "")
    especialidades = {"Clínico Geral", "Cardiologia", "Dermatologia", "Endocrinologia", "Gastroenterologia", "Ginecologia", "Neurologia", "Nutrição", "Oftalmologia", "Ortopedia", "Otorrinolaringologia", "Pediatria", "Pneumologia", "Psiquiatria", "Psicologia", "Reumatologia", "Urologia"}
    try:
        data_consulta = datetime.strptime(data, "%Y-%m-%d").date()
    except ValueError:
        data_consulta = None
    horario_valido = bool(re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", hora))
    horario_passado = bool(data_consulta == date.today() and horario_valido and hora <= datetime.now().strftime("%H:%M"))
    if not hospital or len(hospital) > 300 or especialidade not in especialidades or not data_consulta or data_consulta < date.today() or not horario_valido or horario_passado:
        flash("Confira hospital, especialidade, data futura e horário válido.", "danger")
        return redirect(url_for("hospital.tela_agendamento", hospital=hospital, especialidade=especialidade, data=data, hora=hora))

    novo_agendamento = Agendamento(

        usuario_id=session["usuario_id"],

        hospital=hospital,

        especialidade=especialidade,

        data_consulta=data_consulta,

        horario=hora

    )

    db.session.add(

        novo_agendamento

    )

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        flash("Esse horário já foi reservado. Escolha outro horário.", "warning")
        return redirect(url_for("hospital.tela_agendamento", hospital=hospital, especialidade=especialidade, data=data, hora=hora))

    return render_template(

        "agendado.html",

        nome=session["usuario_nome"],

        hospital=hospital,

        especialidade=especialidade,

        data=data,

        hora=hora

    )


@hospital_bp.route("/agendamento/<int:agendamento_id>/cancelar", methods=["POST"])
def cancelar_agendamento(agendamento_id):
    if "usuario_id" not in session:
        return redirect(url_for("auth.login"))
    consulta = Agendamento.query.filter_by(id=agendamento_id, usuario_id=session["usuario_id"]).first_or_404()
    passou = consulta.data_consulta < date.today() or (
        consulta.data_consulta == date.today() and consulta.horario <= datetime.now().strftime("%H:%M")
    )
    if passou:
        flash("Consultas passadas não podem ser canceladas.", "warning")
    else:
        db.session.delete(consulta)
        db.session.commit()
        flash("Agendamento cancelado.", "success")
    return redirect(url_for("hospital.paciente"))


# ==========================================
# ÁREA DO PACIENTE
# ==========================================

@hospital_bp.route("/paciente")
def paciente():

    if "usuario_id" not in session:

        return redirect("/login")

    paciente = db.session.get(Usuario,
        session["usuario_id"]
    )
    if not paciente:
        session.clear()
        flash("Sua sessão expirou. Entre novamente para continuar.", "info")
        return redirect(url_for("auth.login"))

    consultas = Agendamento.query.filter_by(

        usuario_id=session["usuario_id"]

    ).order_by(

        Agendamento.data_consulta.asc()

    ).all()

    return render_template(

        "areapaciente.html",

        paciente=paciente,

        consultas=consultas,
        hoje=date.today(),
        hora_atual=datetime.now().strftime("%H:%M")

    )
