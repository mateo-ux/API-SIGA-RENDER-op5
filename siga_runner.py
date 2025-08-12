# -*- coding: utf-8 -*-
import os
import io
import contextlib
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


@contextlib.contextmanager
def _maybe_silent(verbose: bool):
    """
    Si verbose=False, redirige stdout/err a un buffer para evitar respuestas enormes.
    """
    if verbose:
        yield
    else:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
            yield


def _get_tokens():
    """
    Carga variables de entorno, obtiene access_token y TOKEN de autenticación SIGA.
    Retorna (services, access_token, token_autenticacion).
    """
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


def run_option2(verbose: bool = False) -> dict:
    """
    Opción 2:
    - Consultar reporte 1003
    - Generar CSV de Moodle
    - Validaciones internas
    - Procesar lotes
    - Matricular en Moodle
    """
    with _maybe_silent(verbose):
        services, access_token, token_autenticacion = _get_tokens()

        # 1003
        resultado = services.consultar_reporte_1003(access_token, token_autenticacion)
        guardar_excel(resultado, "reporte_1003")

        # CSV de Moodle (a partir del 1003 generado)
        generar_csv_con_informacion("output/reporte_1003.xlsx")

        # Validaciones internas
        comparar_documentos_y_generar_faltantes()
        verificar_usuarios_individualmente()

        # Procesar archivo para lotes
        procesar_archivo("output/usuarios_no_matriculados.csv", moodle_manager=None)

        # Matricular en Moodle
        moodle_manager = MoodleManager()
        moodle_manager.matricular_usuarios("output/resultado_lotes.csv")

    return {
        "ok": True,
        "step": "option2",
        "outputs": [
            "output/reporte_1003.xlsx",
            "output/usuarios_no_matriculados.csv",
            "output/resultado_lotes.csv",
        ],
    }


def run_option5(periodo_992: int, verbose: bool = False) -> dict:
    """
    Opción 5:
    - Consultar 1003
    - Consultar 992 (cod_periodo_academico=periodo_992)
    - Extraer columnas del 1003
    - Combinar reportes
    """
    with _maybe_silent(verbose):
        services, access_token, token_autenticacion = _get_tokens()

        # 1003
        res_1003 = services.consultar_reporte_1003(access_token, token_autenticacion)
        guardar_excel(res_1003, "reporte_1003")

        # 992
        res_992 = services.consultar_reporte_992(
            access_token, token_autenticacion, cod_periodo_academico=periodo_992
        )
        guardar_excel(res_992, "reporte_992")

        # Post-procesos
        extraer_columnas_reporte_1003()
        combinar_reportes()

    return {
        "ok": True,
        "step": "option5",
        "outputs": [
            "output/reporte_1003.xlsx",
            "output/reporte_992.xlsx",
        ],
    }
