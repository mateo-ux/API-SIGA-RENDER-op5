# -*- coding: utf-8 -*-
"""
op5_service.py
- Lógica reusable para la Opción 5 (similar a run_option2).
- Expone un FastAPI con /reporte_1003_combinado para Render.
"""
import os
import json
import logging
from typing import List, Dict, Any, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException

from api_siga import ApiSigaClient
from api_siga.services import SigaServices
from api_siga.utils import (
    guardar_json,
    extraer_columnas_reporte_1003,
    combinar_reportes,  # <-- genera el "reporte_1003_combinado.json" final
)

# ------------------ Config & Logger ------------------
logger = logging.getLogger("siga-op5")
logger.setLevel(logging.INFO)

OUTPUT_DIR = "output"
API_TOKEN = os.getenv("API_TOKEN", "")  # opcional, para proteger el endpoint

# ------------------ Helpers compartidos ------------------
def _ensure_output_dir() -> None:
    os.makedirs(OUTPUT_DIR, exist_ok=True)

def _get_tokens():
    """Igual a tu opción 2: carga .env, genera token y autentica en SIGA."""
    load_dotenv()
    _ensure_output_dir()

    BASE_URL  = os.getenv("BASE_URL")
    CLIENT_ID = os.getenv("CLIENT_ID")
    SECRETO   = os.getenv("SECRETO")
    USERNAME  = os.getenv("USERNAME_PRUEBA")
    PASSWORD  = os.getenv("PASSWORD_PRUEBA")

    if not all([BASE_URL, CLIENT_ID, SECRETO, USERNAME, PASSWORD]):
        raise RuntimeError(
            "Faltan variables de entorno requeridas: "
            "BASE_URL, CLIENT_ID, SECRETO, USERNAME_PRUEBA, PASSWORD_PRUEBA"
        )

    from requests_toolbelt.multipart.encoder import MultipartEncoder
    import requests

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

    resp = requests.post(url_autenticar, headers=headers, data=data, timeout=120)
    resp.raise_for_status()
    auth_response = resp.json()
    if auth_response.get("RESPUESTA") != "1":
        raise RuntimeError(f"Error al autenticar: {auth_response}")

    token_autenticacion = auth_response.get("TOKEN")
    services = SigaServices(cliente)
    logger.info("Auth OK (op5)")
    return services, access_token, token_autenticacion

# ------------------ Núcleo Opción 5 ------------------
def run_option5(
    codigos: Optional[List[str]] = None,
    outfile_path: str = os.path.join(OUTPUT_DIR, "reporte_1003_combinado.json"),
) -> Dict[str, Any]:
    """
    Flujo combinado (similar a tu opción 5 actual):
    1) Consulta 1003 -> output/reporte_1003.json
    2) extraer_columnas_reporte_1003()  (si lo requieres como en tu main)
    3) Consulta 992 completo con periodos
    4) combinar_reportes() -> genera output/reporte_1003_combinado.json
    5) Devuelve dict {'ok': True, 'reporte_1003_combinado': [...]}
    """
    logger.info("Option5: START")
    _ensure_output_dir()

    # Periodos por defecto (los que muestras en tu main.py)
    if not codigos:
        codigos = ["2025012710", "2025011112", "2024101510", "2024100708", "2024091608", "2024090208"]

    # 1) Tokens
    services, access_token, token_autenticacion = _get_tokens()

    # 2) 1003
    logger.info("Option5: consultando reporte 1003…")
    res_1003 = services.consultar_reporte_1003(access_token, token_autenticacion)
    guardar_json(res_1003, "reporte_1003")  # -> output/reporte_1003.json

    # (Opcional) si necesitas dejar el 1003 "limpio" como en tu main
    try:
        extraer_columnas_reporte_1003()
    except Exception as e:
        logger.warning(f"extraer_columnas_reporte_1003() falló (continuo igual). Detalle: {e}")

    # 3) 992 completo
    logger.info("Option5: consultando reporte 992 completo…")
    _ = services.consultar_reporte_992_completo(
        token=access_token,
        token_autenticacion=token_autenticacion,
        cod_periodos=codigos,
        solo_pendientes_matricula=False,
        outfile_path=os.path.join(OUTPUT_DIR, "reporte_992_completo.json"),
    )

    # 4) Combinar 1003 + 992
    logger.info("Option5: combinando reportes (1003 + 992)…")
    combinar_reportes()  # Debe generar output/reporte_1003_combinado.json

    # 5) Cargar y responder
    if os.path.exists(outfile_path):
        with open(outfile_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        logger.info("Option5: DONE (archivo combinado encontrado).")
        # Si tu combinar_reportes deja una llave distinta, ajusta aquí:
        if isinstance(data, dict) and "reporte_1003_combinado" in data:
            payload = data["reporte_1003_combinado"]
        else:
            # Asumimos que es una lista directa
            payload = data
    else:
        logger.warning("Option5: archivo combinado no encontrado; devolviendo vacío.")
        payload = []

    return {"ok": True, "step": "option5", "reporte_1003_combinado": payload}

# ------------------ FastAPI para Render ------------------
app = FastAPI(title="API SIGA - Opción 5")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/reporte_1003_combinado")
def get_reporte_1003_combinado(authorization: Optional[str] = Header(default=None)):
    if API_TOKEN:
        if not authorization or authorization != f"Bearer {API_TOKEN}":
            raise HTTPException(status_code=401, detail="Unauthorized")
    result = run_option5()
    # Entregar exactamente con la llave esperada por tu Apps Script
    return {"reporte_1003_combinado": result.get("reporte_1003_combinado", [])}
