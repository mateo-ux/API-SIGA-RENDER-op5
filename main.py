import os
from dotenv import load_dotenv
from api_siga import ApiSigaClient
from api_siga.services import SigaServices
from api_siga.utils import (
    MoodleManager,
    extraer_columnas_reporte_1003,      # JSON
    generar_csv_con_informacionj,       # JSON
    comparar_documentos_y_generar_faltantesj,  # JSON
    verificar_usuarios_individualmentej,       # JSON
    procesar_archivoj,                  # JSON
    guardar_json,                       # JSON
    combinar_reportes,                  # <-- sin "j"
)








def main():
    # Menú
    
    while True:
        print("\n🔍 Reporte a consultar?")
        print("1. Reporte 622 - Información académica detallada")
        print("2. Reporte 1003 - Lista de estudiantes")
        print("3. Reporte 775 - Detalle matrícula")
        print("4. Reporte 997 - Inscripciones por año")
        print("5. Reporte 992 - Matriculados por periodo")
        print("0. Salir")

        opcion = input("Selecciona una opción: ").strip()

        if opcion == "0":
            break

        elif opcion == "1":
            resultado = services.consultar_reporte_622(access_token, token_autenticacion, periodo=2025011112)
            guardar_json(resultado, "reporte_622")

        elif opcion == "2":
            load_dotenv()
            BASE_URL = os.getenv("BASE_URL")
            CLIENT_ID = os.getenv("CLIENT_ID")
            SECRETO = os.getenv("SECRETO")
            USERNAME = os.getenv("USERNAME_PRUEBA")
            PASSWORD = os.getenv("PASSWORD_PRUEBA")

            cliente = ApiSigaClient(BASE_URL, CLIENT_ID, SECRETO)
            access_token = cliente.generar_token()

            if not access_token:
                print("❌ No se pudo obtener el token de acceso.")
                return

            # Autenticación (con MultipartEncoder ya funcionando)
            from requests_toolbelt.multipart.encoder import MultipartEncoder
            import requests

            url_autenticar = f"{BASE_URL}/talentotech2/autenticar"
            headers = {"auth_token": access_token}
            data = MultipartEncoder(fields={"username": USERNAME, "password": PASSWORD})
            headers["Content-Type"] = data.content_type

            try:
                response = requests.post(url_autenticar, headers=headers, data=data)
                response.raise_for_status()
                auth_response = response.json()
            except Exception as e:
                print("❌ Error al autenticar:", e)
                return

            if auth_response.get("RESPUESTA") != "1":
                print("❌ Error al autenticar:", auth_response)
                return

            token_autenticacion = auth_response.get("TOKEN")
            print("✅ Autenticación correcta.")

            services = SigaServices(cliente)
            # Flujo 100% JSON
            resultado = services.consultar_reporte_1003(access_token, token_autenticacion)
            guardar_json(resultado, "reporte_1003")

            generar_csv_con_informacionj("output/reporte_1003.json")
            comparar_documentos_y_generar_faltantesj()
            verificar_usuarios_individualmentej()

            # Procesa usuarios NO matriculados -> genera output/resultado_lotes.json
            procesar_archivoj('output/usuarios_no_matriculados.json', moodle_manager=None)

            # Matriculación en Moodle desde JSON
            moodle_manager = MoodleManager()
            moodle_manager.matricular_usuarios('output/resultado_lotes.json')
            

        elif opcion == "3":
            resultado = services.consultar_reporte_775(access_token, token_autenticacion, periodo=2025011112)
            guardar_json(resultado, "reporte_775")

        elif opcion == "4":
            resultado = services.consultar_reporte_997(access_token, token_autenticacion, ano_periodo=2025)
            guardar_json(resultado, "reporte_997")

        elif opcion == "5":
            load_dotenv()
            BASE_URL = os.getenv("BASE_URL")
            CLIENT_ID = os.getenv("CLIENT_ID")
            SECRETO = os.getenv("SECRETO")
            USERNAME = os.getenv("USERNAME_PRUEBA")
            PASSWORD = os.getenv("PASSWORD_PRUEBA")

            cliente = ApiSigaClient(BASE_URL, CLIENT_ID, SECRETO)
            access_token = cliente.generar_token()

            if not access_token:
                print("❌ No se pudo obtener el token de acceso.")
                return

            # Autenticación (con MultipartEncoder ya funcionando)
            from requests_toolbelt.multipart.encoder import MultipartEncoder
            import requests

            url_autenticar = f"{BASE_URL}/talentotech2/autenticar"
            headers = {"auth_token": access_token}
            data = MultipartEncoder(fields={"username": USERNAME, "password": PASSWORD})
            headers["Content-Type"] = data.content_type

            try:
                response = requests.post(url_autenticar, headers=headers, data=data)
                response.raise_for_status()
                auth_response = response.json()
            except Exception as e:
                print("❌ Error al autenticar:", e)
                return

            if auth_response.get("RESPUESTA") != "1":
                print("❌ Error al autenticar:", auth_response)
                return

            token_autenticacion = auth_response.get("TOKEN")
            print("✅ Autenticación correcta.")

            services = SigaServices(cliente)
            # Flujo combinado (JSON)
            resultado = services.consultar_reporte_1003(access_token, token_autenticacion)
            guardar_json(resultado, "reporte_1003")
            codigos = ["2025012710", "2025011112", "2024101510", "2024100708", "2024091608", "2024090208"]
            import inspect, sys
            print("Clase real:", services.__class__)
            print("Módulo de la clase:", services.__class__.__module__)
            print("Archivo del módulo:", inspect.getsourcefile(services.__class__))
            print("Tiene método consultar_reporte_992_completo?:", hasattr(services, "consultar_reporte_992_completo"))
            print("Métodos disponibles:", [m for m in dir(services) if m.startswith("consultar_reporte")])
            resultado = services.consultar_reporte_992_completo(
            token=access_token,
            token_autenticacion=token_autenticacion,
            cod_periodos=codigos,
            solo_pendientes_matricula=False,  # o True si lo necesitas
            outfile_path="output/reporte_992_completo.json"  # opcional; si no lo pasas, genera uno con timestamp
        )

            extraer_columnas_reporte_1003()
            combinar_reportes()  # <-- sin "j"

        else:
            print("❌ Opción inválida.")

if __name__ == "__main__":
    main()
