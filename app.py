from fastapi import FastAPI, Header, HTTPException, Query, BackgroundTasks
from fastapi.responses import JSONResponse, PlainTextResponse
from siga_runner import run_option2, run_option5
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("SECRET_KEY")
app = FastAPI(title="SIGA Runner", version="1.0")

def _check_key(x_api_key: str | None):
    if API_KEY and x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/run/option2")
def run_opt2(
    background_tasks: BackgroundTasks,
    x_api_key: str | None = Header(default=None),
    verbose: int = Query(0)
):
    _check_key(x_api_key)
    # dispara la tarea y responde rápido
    background_tasks.add_task(run_option2)
    # 202 = aceptado, en proceso
    return PlainTextResponse("ACCEPTED", status_code=202)

@app.post("/run/option5")
def run_opt5(
    periodo_992: int = Query(..., description="Ej: 2025011112"),
    x_api_key: str | None = Header(default=None),
    verbose: int = Query(0)
):
    _check_key(x_api_key)
    # también puedes hacerlo async si quieres:
    background_tasks = BackgroundTasks()
    background_tasks.add_task(run_option5, periodo_992=periodo_992)
    return PlainTextResponse("ACCEPTED", status_code=202)
