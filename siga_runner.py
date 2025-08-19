# -*- coding: utf-8 -*-
import os
import logging
from dotenv import load_dotenv

from api_siga import ApiSigaClient
from api_siga.services import SigaServices
# Import mínimo y seguro a nivel de módulo: solo algo que sabemos que existe
from api_siga.utils import guardar_json

import requests
from requests_toolbelt.multipart_encoder import MultipartEncoder
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
    Opción 2 (JSON-only):
    - Consultar reporte 1003 -> guardar_json(output/reporte_1003.json)
    - Generar archivo modificado para Moodle -> generar_csv_con_informacionj("output/reporte_1003.json")
      (esta utilidad crea también el .json modificado)
    - Comparar contra 'Prueba de nivelacion Padre.json' -> comparar_documentos_y_generar_faltantesj()
    - Verificar usuarios en Moodle -> verificar_usuarios_individualmentej()
    - Procesar lotes -> procesar_archivoj('output/usuarios_no_matriculados.json')
    - Matricular en Moodle -> MoodleManager().matricular_usuarios('output/resultado_lotes.json')
    """
    logger.info("Option2: START")
    _ensure_output_dir()

    services, access_token, token_autenticacion = _get_tokens()

    logger.info("Option2: consultando reporte 1003...")
    resultado = services.consultar_reporte_1003(access_token, token_autenticacion)
    guardar_json(resultado, "reporte_1003")  # -> output/reporte_1003.json

    # Imports locales (evitan romper el import del módulo si faltara algo en utils)
    from api_siga.utils import (
        MoodleManager,
        generar_csv_con_informacionj,
        comparar_documentos_y_generar_faltantesj,
        verificar_usuarios_individualmentej,
        procesar_archivoj,
    )

    logger.info("Option2: generando archivo modificado (JSON) desde 1003...")
    # Esta función debe leer 'output/reporte_1003.json' y escribir 'output/reporte_1003_modificado.json'
    generar_csv_con_informacionj("output/reporte_1003.json")

    logger.info("Option2: validaciones internas (comparar faltantes)...")
    comparar_documentos_y_generar_faltantesj()

    logger.info("Option2: verificación individual en Moodle...")
    verificar_usuarios_individualmentej()

    logger.info("Option2: procesando lotes (usuarios no matriculados -> lotes)...")
    procesar_archivoj("output/usuarios_no_matriculados.json", moodle_manager=None)

    logger.info("Option2: matriculando en Moodle desde resultado_lotes.json...")
    moodle_manager = MoodleManager()
    moodle_manager.matricular_usuarios("output/resultado_lotes.json")

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
    Opción 5 (JSON-only):
    - Consultar 1003 y 992 -> guardar_json(...)
    - (Opcional) Post-procesos: extraer_columnas_reporte_1003j + combinar_reportesj
      Si esas utilidades no existen en utils, no se cae el server; se loguea un warning.
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
    guardar_json(res_992, "reporte_992")  # -> output/reporte_992.json

    combined_output = None
    try:
        from api_siga.utils import (
            extraer_columnas_reporte_1003j,
            combinar_reportesj,
        )
        logger.info("Option5: post-procesos (extraer columnas y combinar JSON)...")
        extraer_columnas_reporte_1003j()
        combined_output = combinar_reportesj()
    except ImportError:
        logger.warning(
            "Option5: utilidades extraer_columnas_reporte_1003j/combinar_reportesj no están disponibles. "
            "Se omite el post-proceso."
        )

    logger.info("Option5: DONE ok")
    outputs = [
        "output/reporte_1003.json",
        "output/reporte_992.json",
    ]
    if combined_output:
        outputs.append(combined_output)

    return {"ok": True, "step": "option5", "outputs": outputs}
