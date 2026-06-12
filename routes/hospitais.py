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