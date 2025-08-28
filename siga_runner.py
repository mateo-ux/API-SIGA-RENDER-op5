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
# siga_runner.py
# -*- coding: utf-8 -*-
import os, json, logging
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

from api_siga import ApiSigaClient
from api_siga.services import SigaServices
from api_siga.utils import (
    guardar_json,
    extraer_columnas_reporte_1003,
    combinar_reportes,
)

logger = logging.getLogger("siga-runner-op5")
logger.setLevel(logging.INFO)
OUTPUT_DIR = "output"

def _ensure_output_dir() -> None:
    os.makedirs(OUTPUT_DIR, exist_ok=True)

def _get_tokens():
    load_dotenv()
    _ensure_output_dir()

    BASE_URL  = os.getenv("BASE_URL")
    CLIENT_ID = os.getenv("CLIENT_ID")
    SECRETO   = os.getenv("SECRETO")
    USERNAME  = os.getenv("USERNAME_PRUEBA")
    PASSWORD  = os.getenv("PASSWORD_PRUEBA")
    if not all([BASE_URL, CLIENT_ID, SECRETO, USERNAME, PASSWORD]):
        raise RuntimeError("Faltan variables de entorno: BASE_URL, CLIENT_ID, SECRETO, USERNAME_PRUEBA, PASSWORD_PRUEBA")

    from requests_toolbelt.multipart.encoder import MultipartEncoder
    import requests

    cliente = ApiSigaClient(BASE_URL, CLIENT_ID, SECRETO)
    access_token = cliente.generar_token()
    if not access_token:
        raise RuntimeError("No se pudo obtener el token de acceso.")

    url_aut = f"{BASE_URL}/talentotech2/autenticar"
    headers = {"auth_token": access_token}
    data = MultipartEncoder(fields={"username": USERNAME, "password": PASSWORD})
    headers["Content-Type"] = data.content_type

    resp = requests.post(url_aut, headers=headers, data=data, timeout=120)
    resp.raise_for_status()
    j = resp.json()
    if j.get("RESPUESTA") != "1":
        raise RuntimeError(f"Error al autenticar: {j}")

    token_autenticacion = j.get("TOKEN")
    services = SigaServices(cliente)
    return services, access_token, token_autenticacion

def run_option5(
    codigos: Optional[List[str]] = None,
    solo_pendientes_matricula: bool = False,
    outfile_path: str = os.path.join(OUTPUT_DIR, "reporte_1003_combinado.json"),
) -> Dict[str, Any]:
    """
    1) 1003 -> output/reporte_1003.json
    2) (opcional) extraer_columnas_reporte_1003()
    3) 992 completo con periodos 'codigos'
    4) combinar_reportes() -> output/reporte_1003_combinado.json
    5) return {'reporte_1003_combinado': [...]}
    """
    _ensure_output_dir()
    if not codigos:
        codigos = ["2025012710","2025011112","2024101510","2024100708","2024091608","2024090208"]

    services, access_token, token_autenticacion = _get_tokens()

    # 1003
    res_1003 = services.consultar_reporte_1003(access_token, token_autenticacion)
    guardar_json(res_1003, "reporte_1003")
    try:
        extraer_columnas_reporte_1003()
    except Exception as e:
        logger.warning(f"extraer_columnas_reporte_1003() no crítico: {e}")

    # 992 completo
    _ = services.consultar_reporte_992_completo(
        token=access_token,
        token_autenticacion=token_autenticacion,
        cod_periodos=codigos,
        solo_pendientes_matricula=solo_pendientes_matricula,
        outfile_path=os.path.join(OUTPUT_DIR, "reporte_992_completo.json"),
    )

    # combinar
    combinar_reportes()

    # preparar respuesta
        # preparar respuesta
    payload = []
    try:
        if os.path.exists(outfile_path):
            with open(outfile_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            if isinstance(data, dict):
                # Caso 1: ya viene con la clave "reporte_1003_combinado"
                if "reporte_1003_combinado" in data and isinstance(data["reporte_1003_combinado"], list):
                    payload = data["reporte_1003_combinado"]
                # Caso 2: viene como {"data": [...]}
                elif "data" in data and isinstance(data["data"], list):
                    payload = data["data"]
                else:
                    # Caso 3: dict arbitrario -> intentar convertir valores a lista
                    try:
                        vals = list(data.values())
                        # Si son todo dicts o elementos "fila", úsalo
                        payload = vals if isinstance(vals, list) else []
                    except Exception:
                        payload = []
            elif isinstance(data, list):
                # Caso 4: el archivo es directamente una lista
                payload = data
            else:
                payload = []
        else:
            logger.warning("Option5: no se encontró reporte_1003_combinado.json")
    except Exception as e:
        logger.error(f"Option5: no se pudo leer combinado: {e}")
        payload = []

    logger.info(f"Option5: DONE. Registros combinados: {len(payload)}")
    return {"ok": True, "step": "option5", "reporte_1003_combinado": payload}
