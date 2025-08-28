# -*- coding: utf-8 -*-
import os
import logging
from datetime import datetime, timezone
from fastapi import FastAPI, Header, HTTPException, Query, BackgroundTasks
from fastapi.responses import PlainTextResponse, JSONResponse
from dotenv import load_dotenv
from siga_runner import OUTPUT_DIR, _ensure_output_dir, run_option2, run_option5
from utils import combinar_reportes, extraer_columnas_reporte_1003, guardar_json

# Cargar variables de entorno
load_dotenv()
API_KEY = os.getenv("SECRET_KEY")

# Logging básico
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("siga-app")

# FastAPI
app = FastAPI(title="SIGA Runner", version="1.0")

# Memoria simple para estado de últimas corridas
LAST = {
    "opt2_started": None,
    "opt2_finished": None,
    "opt2_error": None,
    "opt5_started": None,
    "opt5_finished": None,
    "opt5_error": None,
}

def _check_key(x_api_key: str | None):
    """Verifica el API Key si está configurado."""
    if API_KEY and x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

@app.get("/health")
def health():
    """Endpoint simple para healthcheck."""
    return {"status": "ok"}

@app.get("/status")
def status():
    """Últimos timestamps de ejecución y error (si hubo)."""
    return LAST

@app.post("/run/option2")
def run_opt2(background_tasks: BackgroundTasks, x_api_key: str | None = Header(default=None)):
    """Dispara Opción 2 en background. Responde rápido para evitar timeouts."""
    _check_key(x_api_key)

    def task():
        LAST["opt2_started"] = datetime.now(timezone.utc).isoformat()
        LAST["opt2_error"] = None
        try:
            run_option2()
        except Exception as e:
            LAST["opt2_error"] = str(e)
            logger.exception("Option2: ERROR")
        finally:
            LAST["opt2_finished"] = datetime.now(timezone.utc).isoformat()

    background_tasks.add_task(task)
    return PlainTextResponse("ACCEPTED", status_code=202)

# ... imports arriba ...
from typing import List, Dict, Any, Optional

def run_option5(
    codigos: Optional[List[str]] = None,
    solo_pendientes_matricula: bool = False,   # <- NUEVO
    outfile_path: str = os.path.join(OUTPUT_DIR, "reporte_1003_combinado.json"),
) -> Dict[str, Any]:
    logger.info("Option5: START")
    _ensure_output_dir()

    if not codigos:
        codigos = ["2025012710", "2025011112", "2024101510", "2024100708", "2024091608", "2024090208"]

    services, access_token, token_autenticacion = _get_tokens()

    logger.info("Option5: consultando reporte 1003…")
    res_1003 = services.consultar_reporte_1003(access_token, token_autenticacion)
    guardar_json(res_1003, "reporte_1003")

    try:
        extraer_columnas_reporte_1003()
    except Exception as e:
        logger.warning(f"extraer_columnas_reporte_1003() no crítico: {e}")

    logger.info("Option5: consultando reporte 992 completo…")
    _ = services.consultar_reporte_992_completo(
        token=access_token,
        token_autenticacion=token_autenticacion,
        cod_periodos=codigos,
        solo_pendientes_matricula=solo_pendientes_matricula,   # <- USAR EL PARAMETRO
        outfile_path=os.path.join(OUTPUT_DIR, "reporte_992_completo.json"),
    )

    logger.info("Option5: combinando reportes (1003 + 992)…")
    combinar_reportes()

    payload = []
    if os.path.exists(outfile_path):
        import json
        with open(outfile_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        payload = data.get("reporte_1003_combinado", data if isinstance(data, list) else [])
    logger.info(f"Option5: DONE. Registros combinados: {len(payload)}")
    return {"ok": True, "step": "option5", "reporte_1003_combinado": payload}

@app.get("/reporte_1003_combinado")
def get_reporte_1003_combinado(x_api_key: str | None = Header(default=None)):
    _check_key(x_api_key)
    path = os.path.join("output", "reporte_1003_combinado.json")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Aún no hay reporte combinado")
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = f.read()
        return JSONResponse(content={"reporte_1003_combinado": json.loads(data)})
    except Exception as e:
        logger.exception("No se pudo leer el combinado")
        raise HTTPException(status_code=500, detail=str(e))
