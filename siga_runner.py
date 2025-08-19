# -*- coding: utf-8 -*-
import os
import logging
from dotenv import load_dotenv

from api_siga import ApiSigaClient
from api_siga.services import SigaServices
from api_siga.utils import (
    MoodleManager,
    combinar_reportesj,
    comparar_documentos_y_generar_faltantesj,
    extraer_columnas_reporte_1003j,
    generar_csv_con_informacionj,   # ahora genera JSON (modificado) desde reporte_1003.json
    guardar_json,
    procesar_archivoj,              # procesa JSON de no matriculados y genera resultado_lotes.json
    verificar_usuarios_individualmentej,
)

import requests
from requests_toolbelt.multipart.encoder import MultipartEncoder
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger("siga")


def _ensure_output_dir() -> None:
    """Garantiza que exista el directorio de salida."""
    os.makedirs("output", exist_ok=True)


def _session_with_retries() -> requests.Session:
    """Sesión requests con reintentos/backoff para mayor resiliencia."""
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
    """
    Carga variables, genera access_token y TOKEN de autenticación SIGA.
    Retorna (services, access_token, token_autenticacion).
    """
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

    logger.info("Auth: generando access_token...")
    cliente = ApiSigaClient(BASE_URL, CLIENT_ID, SECRETO)
    access_token = cliente.generar_token()
    if not access_token:
        raise RuntimeError("No se pudo obtener el token de acceso.")

    logger.info("Auth: autenticando usuario SIGA...")
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
    logger.info("Auth: OK")
    return services, access_token, token_autenticacion


def run_option2() -> dict:
    """
    Opción 2 (todo en JSON):
    - Consultar reporte 1003 -> guardar_json('output/reporte_1003.json')
    - Generar JSON modificado para Moodle (desde 1003) -> output/reporte_1003_modificado.json
    - Comparar con nivelación padre.json -> output/usuarios_faltantes_nivelacion.json
    - Verificación individual en Moodle -> output/verificacion_individual_moodle.json
    - Separar no matriculados -> output/usuarios_no_matriculados.json
    - Procesar lotes -> output/resultado_lotes.json (+ descartados)
    - Matricular en Moodle usando JSON -> MoodleManager.matricular_usuarios_json('output/resultado_lotes.json')
    """
    logger.info("Option2: START")
    _ensure_output_dir()

    services, access_token, token_autenticacion = _get_tokens()

    logger.info("Option2: consultando reporte 1003...")
    resultado = services.consultar_reporte_1003(access_token, token_autenticacion)
    guardar_json(resultado, "reporte_1003")  # -> output/reporte_1003.json

    logger.info("Option2: generando JSON modificado desde 1003...")
    # Esta util ya debería leer 'output/reporte_1003.json' y producir 'output/reporte_1003_modificado.json'
    generar_csv_con_informacionj("output/reporte_1003.json")

    logger.info("Option2: validaciones internas (comparar faltantes + verificación individual)...")
    comparar_documentos_y_generar_faltantesj()  # produce usuarios_faltantes_nivelacion.json
    verificar_usuarios_individualmentej()       # produce verificacion_individual_moodle.json + usuarios_no_matriculados.json

    logger.info("Option2: procesando lotes (JSON)...")
    # Lee 'output/usuarios_no_matriculados.json' y genera resultado_lotes.json (+descartados)
    procesar_archivoj("output/usuarios_no_matriculados.json", moodle_manager=None)

    logger.info("Option2: matriculando en Moodle (JSON)...")
    moodle_manager = MoodleManager()
    # Importante: usar el método JSON que definiste en tu clase
    moodle_manager.matricular_usuarios_json("output/resultado_lotes.json")

    logger.info("Option2: DONE ok")
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


def run_option5(periodo_992: int) -> dict:
    """
    Opción 5 (todo en JSON):
    - Consultar reporte 1003 -> guardar_json('output/reporte_1003.json')
    - Consultar reporte 992  -> guardar_json('output/reporte_992.json')
    - Post-procesos JSON: extraer columnas (1003) + combinar reportes (1003 + 992)
    """
    logger.info(f"Option5: START (periodo_992={periodo_992})")
    _ensure_output_dir()

    services, access_token, token_autenticacion = _get_tokens()

    logger.info("Option5: consultando 1003...")
    res_1003 = services.consultar_reporte_1003(access_token, token_autenticacion)
    guardar_json(res_1003, "reporte_1003")  # -> output/reporte_1003.json

    logger.info("Option5: consultando 992...")
    res_992 = services.consultar_reporte_992(
        access_token, token_autenticacion, cod_periodo_academico=periodo_992
    )
    guardar_json(res_992, "reporte_992")     # -> output/reporte_992.json

    logger.info("Option5: post-procesos (extraer columnas y combinar en JSON)...")
    extraer_columnas_reporte_1003j()         # debería producir output/reporte_1003_filtrado.json
    combinar_reportesj()                     # debería producir output/reporte_1003_combinado.json

    logger.info("Option5: DONE ok")
    return {
        "ok": True,
        "step": "option5",
        "outputs": [
            "output/reporte_1003.json",
            "output/reporte_992.json",
            "output/reporte_1003_filtrado.json",
            "output/reporte_1003_combinado.json",
        ],
    }
