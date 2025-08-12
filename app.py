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
    periodo_992: int = Query(..., description="Ej: 2025011112"),
    background_tasks: BackgroundTasks = None,
    x_api_key: str | None = Header(default=None),
):
    """Dispara Opción 5 en background. Responde rápido para evitar timeouts."""
    _check_key(x_api_key)

    def task():
        LAST["opt5_started"] = datetime.now(timezone.utc).isoformat()
        LAST["opt5_error"] = None
        try:
            run_option5(periodo_992=periodo_992)
        except Exception as e:
            LAST["opt5_error"] = str(e)
            logger.exception("Option5: ERROR")
        finally:
            LAST["opt5_finished"] = datetime.now(timezone.utc).isoformat()

    background_tasks.add_task(task)
    return PlainTextResponse("ACCEPTED", status_code=202)
