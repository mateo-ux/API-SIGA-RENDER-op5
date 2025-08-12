# Arquitectura API SIGA - Talentotech2

## 📝 Diagrama de flujo general

         +--------------------+
         |    Python Script   |
         |   (main.py)        |
         +--------------------+
                     |
                     v
         +--------------------+
         | ApiSigaClient      |
         | (client.py)        |
         +--------------------+
                     |
                     v
          +----------------------+
          | Servicio API SIGA    |
          | (https://siga...)    |
          +----------------------+
                     |
                     v
        +----------------------------------+
        | Flujo de llamadas API REST       |
        +----------------------------------+

1. Autenticación general
------------------------
    main.py
        |
        v
    cliente.generar_token()
        |
        v
    POST → /obtener_token
        |
        v
    Devuelve access_token

2. Autenticación usuario API
----------------------------
    main.py
        |
        v
    cliente.post("autenticar", username, password, auth_token)
        |
        v
    POST → /autenticar
        |
        v
    Devuelve TOKEN sesión

3. Consumo de servicios de reportes
-----------------------------------
    main.py
        |
        v
    services.consultar_reporte_XXX(token, token_autenticacion)
        |
        v
    POST → /informacion_reporte_1003
                   /informacion_reporte_992
                   /informacion_reporte_622
                   /informacion_reporte_775
                   /informacion_reporte_997
        |
        v
    Devuelve información académica (JSON)

## 🎯 Componentes del sistema

- `main.py` → Orquestador de las pruebas.
- `api_siga/client.py` → Encargado de autenticación y peticiones HTTP.
- `api_siga/services.py` → Lógica de negocio para reportes.
- `api_siga/utils.py` → Funciones auxiliares (impresión, validaciones).
- `.env` → Contiene todas las credenciales.
- `.gitignore` → Evita exponer información sensible.
- `docs/` → Carpeta para documentación interna.

## ✅ Estado del sistema

| Componente | Estado |
|------------|--------|
| generarToken | Implementado y probado |
| autenticar | Pendiente credenciales |
| Reportes | Pendientes habilitación Datasae |
| Seguridad | Correcta (uso de .env + .gitignore) |
| Código | Modular y escalable |

---

## 🏁 Notas finales

El sistema se encuentra en etapa de pruebas a la espera de habilitación completa de servicios y entrega de usuario API de pruebas por parte de Datasae.

