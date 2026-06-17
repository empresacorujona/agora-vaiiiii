import requests

def obter_localizacao(ip):

    try:

        resposta = requests.get(
            f"http://ip-api.com/json/{ip}",
            timeout=5
        )

        dados = resposta.json()

        return {
            "latitude": dados["lat"],
            "longitude": dados["lon"],
            "cidade": dados["city"]
        }

    except Exception:
        return None