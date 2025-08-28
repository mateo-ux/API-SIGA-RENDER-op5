# app.py
# -*- coding: utf-8 -*-
import os, json, logging
from datetime import datetime, timezone
from fastapi import FastAPI, Header, HTTPException, Query, BackgroundTasks
from fastapi.responses import PlainTextResponse, JSONResponse
from dotenv import load_dotenv
from siga_runner import run_option2, run_option5

load_dotenv()
API_KEY = os.getenv("SECRET_KEY")  # usa SECRET_KEY en Render
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("siga-app")

app = FastAPI(title="SIGA Runner", version="1.0")

LAST = {
    "opt2_started": None, "opt2_finished": None, "opt2_error": None,
    "opt5_started": None, "opt5_finished": None, "opt5_error": None,
}

def _check_key(x_api_key: str | None):
    if API_KEY and x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/status")
def status():
    return LAST

@app.post("/run/option2")
def run_opt2(background_tasks: BackgroundTasks, x_api_key: str | None = Header(default=None)):
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
    periodo_992: str = Query(..., description="Uno o varios períodos separados por coma"),
    solo_pendientes_matricula: bool = Query(False),
    background_tasks: BackgroundTasks = None,
    x_api_key: str | None = Header(default=None),
):
    _check_key(x_api_key)
    codigos = [c.strip() for c in str(periodo_992).split(",") if c.strip()]
    if not codigos:
        raise HTTPException(status_code=422, detail="periodo_992 vacío")

    def task():
        LAST["opt5_started"] = datetime.now(timezone.utc).isoformat()
        LAST["opt5_error"] = None
        try:
            run_option5(codigos=codigos, solo_pendientes_matricula=solo_pendientes_matricula)
        except Exception as e:
            LAST["opt5_error"] = str(e)
            logger.exception("Option5: ERROR")
        finally:
            LAST["opt5_finished"] = datetime.now(timezone.utc).isoformat()
    background_tasks.add_task(task)

    return JSONResponse(
        {"status": "ACCEPTED", "queued": True,
         "periodos": codigos, "solo_pendientes_matricula": solo_pendientes_matricula},
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
            data = json.load(f)
        payload = data.get("reporte_1003_combinado", data if isinstance(data, list) else [])
        return {"reporte_1003_combinado": payload}
    except Exception as e:
        logger.exception("No se pudo leer el combinado")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
