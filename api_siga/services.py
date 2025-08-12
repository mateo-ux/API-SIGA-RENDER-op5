class SigaServices:
    def __init__(self, client):
        self.client = client

    def consultar_reporte_622(self, token, token_autenticacion, periodo, soloactivos=True, solo_matriculados=True):
        endpoint = "talentotech2/informacion_reporte_622"
        headers = {
            'token': token,
            'token_autenticacion': token_autenticacion
        }
        body = {
            "periodo": periodo,
            "soloactivos": soloactivos,
            "solo_matriculados": solo_matriculados
        }
        return self.client.post(endpoint, json_data=body, extra_headers=headers)

    def consultar_reporte_1003(self, token, token_autenticacion, soloactivos=True):
        endpoint = "talentotech2/informacion_reporte_1003"
        headers = {
            'token': token,
            'token_autenticacion': token_autenticacion
        }
        body = {
            "soloactivos": soloactivos
        }
        return self.client.post(endpoint, json_data=body, extra_headers=headers)

    def consultar_reporte_775(self, token, token_autenticacion, periodo, soloactivos=True):
        endpoint = "talentotech2/informacion_reporte_775"
        headers = {
            'token': token,
            'token_autenticacion': token_autenticacion
        }
        body = {
            "periodo": periodo,
            "soloactivos": soloactivos
        }
        return self.client.post(endpoint, json_data=body, extra_headers=headers)

    def consultar_reporte_997(self, token, token_autenticacion, ano_periodo, soloactivos=False):
        endpoint = "talentotech2/informacion_reporte_997"
        headers = {
            'token': token,
            'token_autenticacion': token_autenticacion
        }
        body = {
            "ano_periodo": ano_periodo,
            "soloactivos": soloactivos
        }
        return self.client.post(endpoint, json_data=body, extra_headers=headers)

    def consultar_reporte_992(self, token, token_autenticacion, cod_periodo_academico, solo_pendientes_matricula=False):
        endpoint = "talentotech2/informacion_reporte_992"
        headers = {
            'token': token,
            'token_autenticacion': token_autenticacion
        }
        body = {
            "cod_periodo_academico": cod_periodo_academico,
            "solo_pendientes_matricula": solo_pendientes_matricula
        }
        return self.client.post(endpoint, json_data=body, extra_headers=headers)
