# -*- coding: utf-8 -*-
import os
from fastapi import FastAPI, Header, HTTPException, Query
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from siga_runner import run_option2, run_option5

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
def run_opt2(x_api_key: str | None = Header(default=None)):
    _check_key(x_api_key)
    result = run_option2()
    return JSONResponse(result)

@app.post("/run/option5")
def run_opt5(
    periodo_992: int = Query(..., description="Ej: 2025011112"),
    x_api_key: str | None = Header(default=None),
):
    _check_key(x_api_key)
    result = run_option5(periodo_992=periodo_992)
    return JSONResponse(result)