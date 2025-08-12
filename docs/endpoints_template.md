# API SIGA - TalentoTech2
## Documentación de Endpoints (ambiente pruebas y producción)

---

## 🔐 Autenticación

### 1. generarToken
POST `/obtener_token`
- Params (form-data):
    - client_id
    - secreto
- Response: access_token, token_type, expires_in, scope, refresh_token, etc.

### 2. autenticar
POST `/autenticar`
- Headers:
    - auth_token
- Params (form-data):
    - username
    - password
- Response: RESPUESTA, ERROR, TOKEN, EXPIRA_EN, USU_LOGIN

---

## 📋 Reportes

### 3. obtenerInformacionReporte1003
POST `/informacion_reporte_1003`
- Headers:
    - token
    - token_autenticacion
- Body (json):
    - soloactivos: true/false

### 4. obtenerInformacionReporte992
POST `/informacion_reporte_992`
- Headers:
    - token
    - token_autenticacion
- Body (json):
    - cod_periodo_academico (opcional)
    - solo_pendientes_matricula (opcional)

### 5. obtenerInformacionReporte622
POST `/informacion_reporte_622`
- Headers:
    - token
    - token_autenticacion
- Body (json):
    - periodo (obligatorio)
    - soloactivos (obligatorio)
    - solo_matriculados (obligatorio)

### 6. obtenerInformacionReporte775
POST `/informacion_reporte_775`
- Headers:
    - token
    - token_autenticacion
- Body (json):
    - periodo (obligatorio)
    - soloactivos (obligatorio)

### 7. obtenerInformacionReporte997
POST `/informacion_reporte_997`
- Headers:
    - token
    - token_autenticacion
- Body (json):
    - ano_periodo (obligatorio)
    - soloactivos (opcional)

---

> Esta plantilla se irá completando conforme avancen las pruebas reales.
