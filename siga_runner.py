# -*- coding: utf-8 -*-
import os
import logging
from dotenv import load_dotenv

# Importa tus clientes/servicios/utilidades existentes
from api_siga import ApiSigaClient
from api_siga.services import SigaServices
from api_siga.utils import (
    MoodleManager,
    combinar_reportes,
    comparar_documentos_y_generar_faltantes,
    extraer_columnas_reporte_1003,
    generar_csv_con_informacion,
    guardar_excel,
    procesar_archivo,
    verificar_usuarios_individualmente,
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
    """
    Crea una sesión de requests con reintentos y backoff exponencial
    para hacer las llamadas más tolerantes a fallos temporales.
    """
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
    Carga variables de entorno, genera access_token y TOKEN de autenticación SIGA.
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
    Opción 2:
    - Consultar reporte 1003
    - Generar CSV de Moodle (desde 1003)
    - Validaciones internas + verificación individual
    - Procesar archivo de lotes
    - Matricular en Moodle
    """
    logger.info("Option2: START")
    _ensure_output_dir()

    services, access_token, token_autenticacion = _get_tokens()

    logger.info("Option2: consultando reporte 1003...")
    resultado = services.consultar_reporte_1003(access_token, token_autenticacion)
    guardar_excel(resultado, "reporte_1003")

    logger.info("Option2: generando CSV desde 1003...")
    generar_csv_con_informacion("output/reporte_1003.xlsx")

    logger.info("Option2: validaciones internas...")
    comparar_documentos_y_generar_faltantes()
    verificar_usuarios_individualmente()

    logger.info("Option2: procesando lotes...")
    procesar_archivo("output/usuarios_no_matriculados.csv", moodle_manager=None)

    logger.info("Option2: matriculando en Moodle...")
    moodle_manager = MoodleManager()
    moodle_manager.matricular_usuarios("output/resultado_lotes.csv")

    logger.info("Option2: DONE ok")
    return {
        "ok": True,
        "step": "option2",
        "outputs": [
            "output/reporte_1003.xlsx",
            "output/usuarios_no_matriculados.csv",
            "output/resultado_lotes.csv",
        ],
    }


def run_option5(periodo_992: int) -> dict:
    """
    Opción 5:
    - Consultar reporte 1003
    - Consultar reporte 992 (cod_periodo_academico=periodo_992)
    - Post-procesos: extraer columnas (1003) + combinar reportes
    """
    logger.info(f"Option5: START (periodo_992={periodo_992})")
    _ensure_output_dir()

    services, access_token, token_autenticacion = _get_tokens()

    logger.info("Option5: consultando 1003...")
    res_1003 = services.consultar_reporte_1003(access_token, token_autenticacion)
    guardar_excel(res_1003, "reporte_1003")

    logger.info("Option5: consultando 992...")
    res_992 = services.consultar_reporte_992(
        access_token, token_autenticacion, cod_periodo_academico=periodo_992
    )
    guardar_excel(res_992, "reporte_992")

    logger.info("Option5: post-procesos (extraer columnas y combinar)...")
    extraer_columnas_reporte_1003()
    combinar_reportes()

    logger.info("Option5: DONE ok")
    return {
        "ok": True,
        "step": "option5",
        "outputs": [
            "output/reporte_1003.xlsx",
            "output/reporte_992.xlsx",
            # Si tus utilidades generan un archivo combinado, agrégalo aquí.
        ],
    }
