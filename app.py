# -*- coding: utf-8 -*-
import os
import logging
from datetime import datetime, timezone
from fastapi import FastAPI, Header, HTTPException, Query, BackgroundTasks
from fastapi.responses import PlainTextResponse, JSONResponse
from dotenv import load_dotenv
from siga_runner import run_option2, run_option5

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

@app.post("/run/option5")
def run_opt5(
    periodo_992: str = Query(..., description="Uno o varios periodos separados por coma. Ej: 2025011112 o 2025012710,2025011112"),
    solo_pendientes_matricula: bool = Query(False),
    background_tasks: BackgroundTasks = None,
    x_api_key: str | None = Header(default=None),
):
    """Dispara Opción 5 en background. Acepta 1+ periodos en 'periodo_992'. Responde JSON 202."""
    _check_key(x_api_key)

    # Parseo flexible: "2025,2024" -> ["2025","2024"]
    codigos = [c.strip() for c in str(periodo_992).split(",") if c.strip()]
    if not codigos:
        raise HTTPException(status_code=422, detail="periodo_992 vacío")

    def task():
        LAST["opt5_started"] = datetime.now(timezone.utc).isoformat()
        LAST["opt5_error"] = None
        try:
            # run_option5 debe aceptar 'codigos' y 'solo_pendientes_matricula'
            run_option5(codigos=codigos, solo_pendientes_matricula=solo_pendientes_matricula)
        except Exception as e:
            LAST["opt5_error"] = str(e)
            logger.exception("Option5: ERROR")
        finally:
            LAST["opt5_finished"] = datetime.now(timezone.utc).isoformat()

    background_tasks.add_task(task)
    return JSONResponse(
        {
            "status": "ACCEPTED",
            "queued": True,
            "periodos": codigos,
            "solo_pendientes_matricula": solo_pendientes_matricula,
        },
        status_code=202,
    )
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
