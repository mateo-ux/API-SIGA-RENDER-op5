import requests

class ApiSigaClient:
    def __init__(self, base_url, client_id, secreto):
        self.base_url = base_url.rstrip("/")
        self.client_id = client_id
        self.secreto = secreto
        self.access_token = None

    def generar_token(self):
        """Obtiene el token de autenticación"""
        url = f"{self.base_url}/obtener_token"
        data = {
            'client_id': self.client_id,
            'secreto': self.secreto
        }

        try:
            response = requests.post(url, data=data)
            response.raise_for_status()
            resultado = response.json()
            self.access_token = resultado.get("access_token")
            if not self.access_token:
                raise ValueError("No se recibió access_token en la respuesta.")
            print(f"✅ Token generado: {self.access_token}")
            return self.access_token

        except requests.RequestException as e:
            print(f"❌ Error al solicitar token: {e}")
            return None
        except ValueError as ve:
            print(f"❌ Error en la respuesta de token: {ve}")
            return None

    def get(self, endpoint, params=None):
        """Realiza solicitudes GET autenticadas"""
        if not self.access_token:
            raise ValueError("Debe generar un token antes de hacer solicitudes.")

        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = {'Authorization': f'Bearer {self.access_token}'}

        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()

        except requests.RequestException as e:
            print(f"❌ Error en GET {endpoint}: {e}")
            return None

    def post(self, endpoint, json_data=None, extra_headers=None):
        """Realiza solicitudes POST autenticadas (reportes)"""
        if not self.access_token:
            raise ValueError("Debe generar un token antes de hacer solicitudes.")

        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }

        if extra_headers:
            headers.update(extra_headers)

        try:
            response = requests.post(url, headers=headers, json=json_data)
            response.raise_for_status()
            return response.json()

        except requests.RequestException as e:
            print(f"❌ Error en POST {endpoint}: {e}")
            return None
