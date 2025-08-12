# -*- coding: utf-8 -*-
import os
from fastapi import FastAPI, Header, HTTPException, Query
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from siga_runner import run_option2, run_option5

# Cargar variables de entorno
load_dotenv()
API_KEY = os.getenv("SECRET_KEY")

# Crear la instancia de la aplicación FastAPI
app = FastAPI(title="SIGA Runner", version="1.0")

def _check_key(x_api_key: str | None):
    """Verifica el API Key si está configurado."""
    if API_KEY and x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

@app.get("/health")
def health():
    """Verifica si el servicio está activo."""
    return {"status": "ok"}

@app.post("/run/option2")
def run_opt2(x_api_key: str | None = Header(default=None)):
    """Ejecuta la Opción 2 (matrícula automática)."""
    _check_key(x_api_key)
    result = run_option2()
    return JSONResponse(result)

@app.post("/run/option5")
def run_opt5(
    periodo_992: int = Query(..., description="Ej: 2025011112"),
    x_api_key: str | None = Header(default=None),
):
    """Ejecuta la Opción 5 (procesar reportes 1003 y 992)."""
    _check_key(x_api_key)
    result = run_option5(periodo_992=periodo_992)
    return JSONResponse(result)
