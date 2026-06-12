# services/geolocalizacao.py

import requests

def obter_localizacao(ip):

    url = f"https://ipapi.co/{ip}/json"

    dados = requests.get(url).json()

    return {
        "cidade": dados.get("city"),
        "latitude": dados.get("latitude"),
        "longitude": dados.get("longitude")
    }