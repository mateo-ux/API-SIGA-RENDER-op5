from fastapi import FastAPI, Header, HTTPException, Query
from fastapi.responses import JSONResponse, PlainTextResponse
import os
from siga_runner import run_option2, run_option5

API_KEY = os.getenv("SECRET_KEY")

def _check_key(x_api_key: str | None):
    if API_KEY and x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

@app.post("/run/option2")
def run_opt2(
    verbose: int = Query(0, description="1 para detalle, 0 para mínimo"),
    x_api_key: str | None = Header(default=None),
):
    _check_key(x_api_key)
    result = run_option2(verbose=bool(verbose))
    if verbose:
        return JSONResponse(result)
    # Respuesta mínima
    return PlainTextResponse("OK", status_code=200)

@app.post("/run/option5")
def run_opt5(
    periodo_992: int = Query(..., description="Ej: 2025011112"),
    verbose: int = Query(0, description="1 para detalle, 0 para mínimo"),
    x_api_key: str | None = Header(default=None),
):
    _check_key(x_api_key)
    result = run_option5(periodo_992=periodo_992, verbose=bool(verbose))
    if verbose:
        return JSONResponse(result)
    return PlainTextResponse("OK", status_code=200)
