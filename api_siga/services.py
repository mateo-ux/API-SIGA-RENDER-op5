import json
from datetime import datetime
from pathlib import Path



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

    def consultar_reporte_992(self, token, token_autenticacion, cod_periodo_academico, solo_pendientes_matricula=False):
        endpoint = "talentotech2/informacion_reporte_992"
        headers = {'token': token, 'token_autenticacion': token_autenticacion}
        body = {
            "cod_periodo_academico": cod_periodo_academico,
            "solo_pendientes_matricula": solo_pendientes_matricula
        }
        return self.client.post(endpoint, json_data=body, extra_headers=headers)

    def consultar_reporte_992_completo(
        self,
        token: str,
        token_autenticacion: str,
        cod_periodos: list,
        solo_pendientes_matricula: bool = False,
        outfile_path: str | None = None
    ):
        """
        Consolida EXACTAMENTE 6 periodos del reporte 992 en un solo JSON.
        Reescribe 'cod_periodo_academico' con el formato requerido (ej: 2025-5).
        Retorna (ruta_archivo, lista_registros).
        """
        # Validar longitud
        if not isinstance(cod_periodos, (list, tuple)) or len(cod_periodos) != 6:
            raise ValueError("Debes enviar exactamente 6 cod_periodo_academico en 'cod_periodos'.")

        # Mapeo solicitado
        mapping = {
            "2025012710": "2025-5",
            "2025011112": "2025-1",
            "2024101510": "2024-4",
            "2024100708": "2024-3",
            "2024091608": "2024-2",
            "2024090208": "2024-1",
        }

        consolidadas = []

        for cod in cod_periodos:
            cod_str = str(cod)

            # Llamada al servicio base
            resp = self.consultar_reporte_992(
                token=token,
                token_autenticacion=token_autenticacion,
                cod_periodo_academico=cod_str,
                solo_pendientes_matricula=solo_pendientes_matricula
            )

            # Normalizar payload -> lista de dicts
            payload = resp
            if isinstance(resp, dict):
                payload = (
                    resp.get("data")
                    or resp.get("resultado")
                    or resp.get("items")
                    or resp.get("registros")
                    or resp
                )

            if isinstance(payload, dict):
                payload = [payload]
            elif not isinstance(payload, list):
                payload = []

            # Reescribir el campo con el valor mapeado
            periodo_mapeado = mapping.get(cod_str, cod_str)
            for item in payload:
                if isinstance(item, dict):
                    item["cod_periodo_academico"] = periodo_mapeado

            consolidadas.extend(payload)

        # Escribir archivo
        if outfile_path is None:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            outfile_path = f"reporte_992_completo_{ts}.json"

        outfile = Path(outfile_path)
        outfile.parent.mkdir(parents=True, exist_ok=True)
        with outfile.open("w", encoding="utf-8") as f:
            json.dump(consolidadas, f, ensure_ascii=False, indent=2)

        return str(outfile), consolidadas
