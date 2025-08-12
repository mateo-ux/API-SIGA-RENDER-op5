# -*- coding: utf-8 -*-
import os
from dotenv import load_dotenv
from api_siga import ApiSigaClient
from api_siga.services import SigaServices
from api_siga.utils import (
    MoodleManager, combinar_reportes, comparar_documentos_y_generar_faltantes,
    extraer_columnas_reporte_1003, generar_csv_con_informacion, guardar_excel,
    procesar_archivo, verificar_usuarios_individualmente
)

import requests
from requests_toolbelt.multipart.encoder import MultipartEncoder


def _get_tokens():
    load_dotenv()
    BASE_URL   = os.getenv("BASE_URL")
    CLIENT_ID  = os.getenv("CLIENT_ID")
    SECRETO    = os.getenv("SECRETO")
    USERNAME   = os.getenv("USERNAME_PRUEBA")
    PASSWORD   = os.getenv("PASSWORD_PRUEBA")

    if not all([BASE_URL, CLIENT_ID, SECRETO, USERNAME, PASSWORD]):
        raise RuntimeError("Faltan variables de entorno requeridas en .env")

    cliente = ApiSigaClient(BASE_URL, CLIENT_ID, SECRETO)
    access_token = cliente.generar_token()
    if not access_token:
        raise RuntimeError("No se pudo obtener el token de acceso.")

    url_autenticar = f"{BASE_URL}/talentotech2/autenticar"
    headers = {"auth_token": access_token}
    data = MultipartEncoder(fields={"username": USERNAME, "password": PASSWORD})
    headers["Content-Type"] = data.content_type

    resp = requests.post(url_autenticar, headers=headers, data=data)
    resp.raise_for_status()
    auth_response = resp.json()
    if auth_response.get("RESPUESTA") != "1":
        raise RuntimeError(f"Error al autenticar: {auth_response}")

    token_autenticacion = auth_response.get("TOKEN")
    services = SigaServices(cliente)
    return services, access_token, token_autenticacion


def run_option2() -> dict:
    services, access_token, token_autenticacion = _get_tokens()

    resultado = services.consultar_reporte_1003(access_token, token_autenticacion)
    guardar_excel(resultado, "reporte_1003")

    generar_csv_con_informacion("output/reporte_1003.xlsx")

    comparar_documentos_y_generar_faltantes()
    verificar_usuarios_individualmente()

    procesar_archivo("output/usuarios_no_matriculados.csv", moodle_manager=None)

    moodle_manager = MoodleManager()
    moodle_manager.matricular_usuarios("output/resultado_lotes.csv")

    return {"ok": True, "step": "option2", "outputs": [
        "output/reporte_1003.xlsx",
        "output/usuarios_no_matriculados.csv",
        "output/resultado_lotes.csv"
    ]}


def run_option5(periodo_992: int) -> dict:
    services, access_token, token_autenticacion = _get_tokens()

    res_1003 = services.consultar_reporte_1003(access_token, token_autenticacion)
    guardar_excel(res_1003, "reporte_1003")

    res_992 = services.consultar_reporte_992(access_token, token_autenticacion,
                                             cod_periodo_academico=periodo_992)
    guardar_excel(res_992, "reporte_992")

    extraer_columnas_reporte_1003()
    combinar_reportes()

    return {"ok": True, "step": "option5", "outputs": [
        "output/reporte_1003.xlsx",
        "output/reporte_992.xlsx"
    ]}