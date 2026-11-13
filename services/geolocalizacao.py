import requests

def obter_localizacao(ip):

    try:

        resposta = requests.get(
            f"https://ipapi.co/{ip}/json/",
            timeout=5
        )
        resposta.raise_for_status()
        dados = resposta.json()
        if dados.get("error") or not dados.get("latitude") or not dados.get("longitude"):
            return None

        return {
            "latitude": dados["latitude"],
            "longitude": dados["longitude"],
            "cidade": dados.get("city") or "localização aproximada"
        }

    except Exception:
        return None
