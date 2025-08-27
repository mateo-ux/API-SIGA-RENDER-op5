# -*- coding: utf-8 -*-
import os
import logging
from dotenv import load_dotenv

from api_siga import ApiSigaClient
from api_siga.services import SigaServices
from api_siga.utils import (
    MoodleManager,
    guardar_json,
    generar_csv_con_informacionj,
    comparar_documentos_y_generar_faltantesj,
    verificar_usuarios_individualmentej,
    procesar_archivoj,
    extraer_columnas_reporte_1003,
    combinar_reportes,
)

import requests
from requests_toolbelt.multipart.encoder import MultipartEncoder  # <- IMPORT CORRECTO
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger("siga")


def _ensure_output_dir() -> None:
    os.makedirs("output", exist_ok=True)


def _session_with_retries() -> requests.Session:
    s = requests.Session()
    retries = Retry(
        total=5,
        connect=5,
        read=5,
        backoff_factor=1.0,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=frozenset(["GET", "POST"]),
        raise_on_status=False,
    )
    s.mount("http://", HTTPAdapter(max_retries=retries))
    s.mount("https://", HTTPAdapter(max_retries=retries))
    return s


def _get_tokens():
    load_dotenv()
    _ensure_output_dir()

    BASE_URL = os.getenv("BASE_URL")
    CLIENT_ID = os.getenv("CLIENT_ID")
    SECRETO = os.getenv("SECRETO")
    USERNAME = os.getenv("USERNAME_PRUEBA")
    PASSWORD = os.getenv("PASSWORD_PRUEBA")

    if not all([BASE_URL, CLIENT_ID, SECRETO, USERNAME, PASSWORD]):
        raise RuntimeError(
            "Faltan variables de entorno requeridas: "
            "BASE_URL, CLIENT_ID, SECRETO, USERNAME_PRUEBA, PASSWORD_PRUEBA"
        )

    logger.info("Auth: generando access_token…")
    cliente = ApiSigaClient(BASE_URL, CLIENT_ID, SECRETO)
    access_token = cliente.generar_token()
    if not access_token:
        raise RuntimeError("No se pudo obtener el token de acceso.")

    logger.info("Auth: autenticando en SIGA…")
    url_autenticar = f"{BASE_URL}/talentotech2/autenticar"
    headers = {"auth_token": access_token}
    data = MultipartEncoder(fields={"username": USERNAME, "password": PASSWORD})
    headers["Content-Type"] = data.content_type

    session = _session_with_retries()
    resp = session.post(url_autenticar, headers=headers, data=data, timeout=120)
    resp.raise_for_status()
    auth_response = resp.json()
    if auth_response.get("RESPUESTA") != "1":
        raise RuntimeError(f"Error al autenticar: {auth_response}")

    token_autenticacion = auth_response.get("TOKEN")
    services = SigaServices(cliente)
    logger.info("Auth OK")
    return services, access_token, token_autenticacion


def run_option2() -> dict:
    """
    Flujo JSON:
    1) Consulta 1003 -> guarda output/reporte_1003.json
    2) Genera output/reporte_1003_modificado.json (formato Moodle)
    3) Compara con 'Padre' -> genera faltantes JSON
    4) Verificación individual -> genera usuarios_no_matriculados.json
    5) Asigna lotes -> resultado_lotes.json
    6) Matricula en Moodle desde resultado_lotes.json
    """
    logger.info("Option2: START")
    _ensure_output_dir()

    services, access_token, token_autenticacion = _get_tokens()

    logger.info("Option2: consultando reporte 1003…")
    res_1003 = services.consultar_reporte_1003(access_token, token_autenticacion)
    guardar_json(res_1003, "reporte_1003")  # -> output/reporte_1003.json

    logger.info("Option2: generando estructura Moodle (JSON)…")
    generar_csv_con_informacionj("output/reporte_1003.json")  # crea *_modificado.json

    logger.info("Option2: comparando y generando faltantes (JSON)…")
    comparar_documentos_y_generar_faltantesj()

    logger.info("Option2: verificación individual (JSON)…")
    verificar_usuarios_individualmentej()

    logger.info("Option2: asignando lotes (JSON)…")
    procesar_archivoj("output/usuarios_no_matriculados.json", moodle_manager=None)

    logger.info("Option2: matriculando en Moodle (JSON)…")
    mm = MoodleManager()
    # La versión JSON mantiene el mismo nombre si así la dejaste:
    mm.matricular_usuarios("output/resultado_lotes.json")

    logger.info("Option2: DONE")
    return {
        "ok": True,
        "step": "option2",
        "outputs": [
            "output/reporte_1003.json",
            "output/reporte_1003_modificado.json",
            "output/usuarios_faltantes_nivelacion.json",
            "output/verificacion_individual_moodle.json",
            "output/usuarios_no_matriculados.json",
            "output/resultado_lotes.json",
            "output/resultado_lotes_descartados.json",
        ],
    }
