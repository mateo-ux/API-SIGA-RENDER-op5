# -*- coding: utf-8 -*-
import os
from fastapi import FastAPI, Header, HTTPException, Query
from fastapi.responses import JSONResponse, PlainTextResponse
from dotenv import load_dotenv
from siga_runner import run_option2, run_option5

# Cargar variables de entorno
load_dotenv()
API_KEY = os.getenv("SECRET_KEY")

# Crear instancia de la aplicación
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
def run_opt2(
    verbose: int = Query(0, description="1 para respuesta detallada, 0 para mínima"),
    x_api_key: str | None = Header(default=None)
):
    """Ejecuta la Opción 2 (matrícula automática)."""
    _check_key(x_api_key)
    result = run_option2()
    if verbose:
        return JSONResponse(result)
    return PlainTextResponse("OK", status_code=200)

@app.post("/run/option5")
def run_opt5(
    periodo_992: int = Query(..., description="Ej: 2025011112"),
    verbose: int = Query(0, description="1 para respuesta detallada, 0 para mínima"),
    x_api_key: str | None = Header(default=None)
):
    """Ejecuta la Opción 5 (procesar reportes 1003 y 992)."""
    _check_key(x_api_key)
    result = run_option5(periodo_992=periodo_992)
    if verbose:
        return JSONResponse(result)
    return PlainTextResponse("OK", status_code=200)
