import requests

class ApiSigaClient:
    def __init__(self, base_url, client_id, secreto):
        self.base_url = base_url
        self.client_id = client_id
        self.secreto = secreto
        self.access_token = None

    def generar_token(self):
        url = f"{self.base_url}/obtener_token"
        data = {
            'client_id': self.client_id,
            'secreto': self.secreto
        }

        try:
            response = requests.post(url, data=data)
            response.raise_for_status()  # Lanza excepción si no es 200

            resultado = response.json()
            self.access_token = resultado.get("access_token")
            if not self.access_token:
                raise ValueError("No se recibió access_token en la respuesta.")

            print(f"✅ Token generado: {self.access_token}")
            return self.access_token

        except requests.RequestException as e:
            print(f"❌ Error en la solicitud: {e}")
        except ValueError as ve:
            print(f"❌ Error en la respuesta: {ve}")

if __name__ == "__main__":
    # Configura aquí tus valores
    BASE_URL = "http://talentotech2prueba.datasae.com/siga_new/web/app.php/api/rest"
    CLIENT_ID = "talentotech2_webservice"
    SECRETO = "LcU54XCSqzRU"

    # Crea instancia y genera token
    cliente = ApiSigaClient(BASE_URL, CLIENT_ID, SECRETO)
    cliente.generar_token()
