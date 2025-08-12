import os
import requests
import pandas as pd
from dotenv import load_dotenv

import time

# Cargar las variables del archivo .env
load_dotenv()

def print_json_bonito(data):
    """Imprime un JSON con formato legible por consola"""
    import json
    print(json.dumps(data, indent=2, ensure_ascii=False))

def guardar_excel(data, nombre_reporte):
    """Guarda la respuesta JSON como archivo Excel en carpeta output/"""
    if not data or not isinstance(data, list):
        print("⚠️ No hay datos válidos para exportar.")
        return

    # Crear carpeta de salida si no existe
    os.makedirs("output", exist_ok=True)

    # Generar nombre del archivo
    filename = f"output/{nombre_reporte}.xlsx"

    # Eliminar el archivo si ya existe
    if os.path.exists(filename):
        os.remove(filename)  # Eliminar el archivo existente

    try:
        # Convertir los datos a un DataFrame de pandas
        df = pd.DataFrame(data)

        # Guardar el archivo Excel
        df.to_excel(filename, index=False)
        print(f"✅ Archivo guardado: {filename}")
    except Exception as e:
        print(f"❌ Error al guardar Excel: {e}")

def generar_csv_con_informacion(reporte_excel):
    # Cargar el archivo Excel generado previamente
    try:
        df = pd.read_excel(reporte_excel)

        # Verificar que las columnas necesarias existan en el archivo
        required_columns = ['documento_numero', 'nombres', 'apellidos', 'telefono_celular', 'correo_electronico', 
                            'departamento', 'municipio', 'modalidad_formacion', 'programa_interes', 'inscripcion_aprobada']
        
        if not all(col in df.columns for col in required_columns):
            print("⚠️ Algunas columnas necesarias están ausentes en el archivo Excel.")
            return

        # Filtrar solo los registros donde 'inscripcion_aprobada' sea 'APROBADO'
        df_aprobados = df[df['inscripcion_aprobada'] == 'APROBADO']

        if df_aprobados.empty:
            print("⚠️ No hay registros aprobados para exportar.")
            return

        # Mapear las columnas originales a las nuevas columnas del archivo CSV
        df_nuevo = pd.DataFrame({
            'idnumber': df_aprobados['documento_numero'],  # Mantenemos 'documento_numero'
            'username': df_aprobados['documento_numero'],  # Usamos 'documento_numero' también para 'username'
            'password': df_aprobados['documento_numero'],  # Usamos 'documento_numero' también para 'password'
            'firstname': df_aprobados['nombres'],  # 'nombres' se mapea como 'nombres'
            'lastname': df_aprobados['apellidos'],  # 'apellidos' se mapea como 'apellidos'
            'phone1': df_aprobados['telefono_celular'],  # 'telefono_celular' se mapea como 'telefono_celular'
            'email': df_aprobados['correo_electronico'],  # 'correo_electronico' se mapea como 'correo_electronico'
            'profile_field_departamento': df_aprobados['departamento'],  # 'departamento' se mapea como 'departamento'
            'profile_field_municipio': df_aprobados['municipio'],  # 'municipio' se mapea como 'municipio'
            'profile_field_modalidad': df_aprobados['modalidad_formacion'],  # 'modalidad_formacion' se mapea como 'modalidad_formacion'
            'group1': df_aprobados['programa_interes'].replace({
                'INTELIGENCIA ARTIFICIAL': 'Inteligencia Artificial',
                'ANÁLISIS DE DATOS': 'Analisis_datos',
                'PROGRAMACIÓN': 'Programacion',
                'CIBERSEGURIDAD': 'Ciberseguridad1',
                'ARQUITECTURA EN LA NUBE': 'Arquitectura_Nube',
                'BLOCKCHAIN': 'Blockchain'
            }),  # Mapeo del 'programa_interes' a los valores especificados
            'course1': 'Prueba de Inicio Talento Tech',  # Agregamos columna 'course1' con valor fijo
            'role1': 5  # Agregamos columna 'role1' con valor fijo
        })

        # Guardar el DataFrame en un archivo CSV
        archivo_csv = reporte_excel.replace('.xlsx', '_modificado.csv')
        df_nuevo.to_csv(archivo_csv, index=False, sep=';', encoding='utf-8-sig')  # Usamos ';' como delimitador para evitar comas

        print(f"✅ Archivo CSV generado correctamente: {archivo_csv}")

    except Exception as e:
        print(f"❌ Error al generar el archivo CSV: {e}")


def comparar_documentos_y_generar_faltantes():
    try:
        # Cargar ambos archivos
        df_usuarios = pd.read_csv('output/reporte_1003_modificado.csv', sep=';')
        df_nivelacion = pd.read_csv('Prueba de nivelacion Padre.csv', sep=';')
        
        # Verificar que las columnas necesarias existan
        if 'idnumber' not in df_usuarios.columns:
            print("❌ El archivo usuarios_a_verificar no tiene la columna 'documento_numero'")
            return
            
        if 'username' not in df_nivelacion.columns:
            print("❌ El archivo Prueba de nivelacion Padre no tiene la columna 'username'")
            return
        
        # Convertir a string para evitar problemas de tipo de dato
        documentos_usuarios = set(df_usuarios['idnumber'].astype(str))
        documentos_nivelacion = set(df_nivelacion['username'].astype(str))
        
        # Encontrar documentos que están en usuarios_a_verificar pero no en nivelación
        documentos_faltantes = documentos_usuarios - documentos_nivelacion
        
        if not documentos_faltantes:
            print("✅ Todos los usuarios están en el archivo de nivelación")
            return
            
        # Filtrar los registros originales que corresponden a los documentos faltantes
        df_faltantes = df_usuarios[df_usuarios['idnumber'].astype(str).isin(documentos_faltantes)]
        
        if df_faltantes.empty:
            print("⚠️ No se encontraron registros faltantes")
            return
            
        # Guardar el resultado en un nuevo archivo
        output_path = 'output/usuarios_faltantes_nivelacion.csv'
        df_faltantes.to_csv(output_path, sep=';', index=False, encoding='utf-8-sig')
        print(f"✅ Archivo generado con usuarios faltantes: {output_path}")
        print(f"📝 Total de usuarios faltantes: {len(df_faltantes)}")
        
    except FileNotFoundError as e:
        print(f"❌ Error: Archivo no encontrado - {e}")
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
def verificar_usuarios_individualmente():
    """Verifica usuarios uno por uno evitando cargar todos los registros"""
    try:
        # 1. Cargar archivo con usuarios a verificar
        faltantes_path = 'output/usuarios_faltantes_nivelacion.csv'
        df_faltantes = pd.read_csv(faltantes_path, sep=';', dtype={'idnumber': str})
        
        # 2. Configuración Moodle
        load_dotenv()
        MOODLE_URL = os.getenv("MOODLE_URL")
        MOODLE_TOKEN = os.getenv("MOODLE_TOKEN")
        COURSE_ID = os.getenv("PRUEBA_INICIO_COURSE_ID")  # Ahora puede ser 5
        
        # 3. Preparar archivo de resultados
        resultados_path = 'output/verificacion_individual_moodle.csv'
        df_resultados = pd.DataFrame(columns=[
            'idnumber', 'en_moodle', 'fecha_verificacion'
        ])
        
        # 4. Verificar cada usuario
        total_usuarios = len(df_faltantes)
        print(f"\n🔍 Verificando {total_usuarios} usuarios individualmente...")
        
        for i, row in df_faltantes.iterrows():
            documento = str(row['idnumber'])
            
            # Función para verificar un solo usuario
            def usuario_en_moodle(documento):
                params = {
                    'wstoken': MOODLE_TOKEN,
                    'wsfunction': 'core_user_get_users_by_field',
                    'field': 'username',
                    'values[0]': documento,
                    'moodlewsrestformat': 'json'
                }
                
                try:
                    response = requests.get(
                        MOODLE_URL,
                        params=params,
                        timeout=15
                    )
                    users = response.json()
                    return len(users) > 0
                except:
                    return False
            
            # Verificar y guardar resultado
            en_moodle = usuario_en_moodle(documento)
            df_resultados.loc[i] = [
                documento,
                en_moodle,
                pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
            ]
            
            # Mostrar progreso
            if (i+1) % 10 == 0 or (i+1) == total_usuarios:
                print(f"Progreso: {i+1}/{total_usuarios} | Último documento: {documento}")
        
        # 5. Generar reportes
        df_resultados['en_moodle'] = df_resultados['en_moodle'].astype(bool)

        # Usuarios MATRICULADOS
        df_matriculados = df_faltantes[
            df_faltantes['idnumber'].isin(
                df_resultados[df_resultados['en_moodle']]['idnumber']
            )
        ]
        
        # Usuarios NO MATRICULADOS
        df_no_matriculados = df_faltantes[
            df_faltantes['idnumber'].isin(
                df_resultados[~df_resultados['en_moodle']]['idnumber']
            )
        ]
        
        if not df_no_matriculados.empty:
            no_matriculados_path = 'output/usuarios_no_matriculados.csv'
            df_no_matriculados.to_csv(no_matriculados_path, sep=';', index=False, encoding='utf-8-sig')
            print(f"✅ {len(df_no_matriculados)} usuarios NO matriculados guardados en {no_matriculados_path}")
        
        # Guardar registro completo
        df_resultados.to_csv(resultados_path, sep=';', index=False, encoding='utf-8-sig')
        print(f"\n📊 Reporte completo guardado en {resultados_path}")
        
        # 6. Agregar usuarios matriculados al archivo "Prueba de nivelacion Padre.csv"
        if not df_matriculados.empty:
            padre_path = 'Prueba de nivelacion Padre.csv'
            # Cargar si ya existe, si no, crear nuevo
            if os.path.exists(padre_path):
                df_padre = pd.read_csv(padre_path, sep=';', dtype=str)
            else:
                df_padre = pd.DataFrame(columns=['username'])

            nuevos = df_matriculados[['idnumber']].rename(columns={'idnumber': 'username'})
            df_actualizado = pd.concat([df_padre, nuevos]).drop_duplicates(subset='username')

            df_actualizado.to_csv(padre_path, sep=';', index=False, encoding='utf-8-sig')
            print(f"📁 {len(nuevos)} usuarios agregados a {padre_path}")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")


import os
import pandas as pd

def asignar_lote(df):
    # Contadores de filas
    total_validas = 0
    total_invalidas = 0
    total_virtual = 0
    total_presencial = 0
    total_departamento_validos = 0

    # Normalizar a mayúsculas sostenidas
    df['profile_field_modalidad'] = df['profile_field_modalidad'].apply(lambda x: x.upper() if isinstance(x, str) else '')
    
    # Filtrar por departamentos
    departamentos = ['ANTIOQUIA', 'CALDAS', 'CHOCÓ', 'QUINDÍO', 'RISARALDA']

    # Normalizar columna 'profile_field_departamento' a mayúsculas también
    df['profile_field_departamento'] = df['profile_field_departamento'].apply(lambda x: x.upper() if isinstance(x, str) else '')
    
    # Crear una columna de Lote
    df['profile_field_lote'] = None

    count_lote_1 = 0
    count_lote_2 = 0

    valid_rows = []
    invalid_rows = []

    for index, row in df.iterrows():
        modalidad = row['profile_field_modalidad']
        profile_field_departamento = row['profile_field_departamento']

        if modalidad in ['VIRTUAL', 'PRESENCIAL']:
            if modalidad == 'VIRTUAL':
                total_virtual += 1
            else:
                total_presencial += 1

            if profile_field_departamento in departamentos:
                total_departamento_validos += 1

                if count_lote_1 <= count_lote_2:
                    df.at[index, 'profile_field_lote'] = 'Lote 1'
                    count_lote_1 += 1
                else:
                    df.at[index, 'profile_field_lote'] = 'Lote 2'
                    count_lote_2 += 1

                valid_rows.append(index)
                total_validas += 1
            else:
                invalid_rows.append(index)
                total_invalidas += 1
        else:
            invalid_rows.append(index)
            total_invalidas += 1

    df_valid = df.loc[valid_rows].copy()
    df_invalid = df.loc[invalid_rows].copy()

    print(f"Total filas procesadas: {len(df)}")
    print(f"Filas válidas: {total_validas}")
    print(f"Filas inválidas: {total_invalidas}")
    print(f"Total Virtual: {total_virtual}")
    print(f"Total Presencial: {total_presencial}")
    print(f"Filas con departamentos válidos: {total_departamento_validos}")

    return df_valid, df_invalid

def procesar_archivo(ruta_archivo, moodle_manager=None):
    try:
        df = pd.read_csv(ruta_archivo, sep=';', encoding='utf-8-sig')

        print("Columnas del archivo cargado:")
        print(df.columns)

        if 'profile_field_modalidad' not in df.columns or 'profile_field_departamento' not in df.columns:
            print("❌ El archivo no contiene las columnas requeridas: 'profile_field_modalidad' y 'profile_field_departamento'.")
            return

        df_valid, df_invalid = asignar_lote(df)

        output_dir = 'output'
        os.makedirs(output_dir, exist_ok=True)

        # Guardar archivos CSV
        df_valid.to_csv(f'{output_dir}/resultado_lotes.csv', index=False, sep=';', encoding='utf-8-sig')
        print("✅ Archivo de filas válidas guardado como 'output/resultado_lotes.csv'.")

        if not df_invalid.empty:
            df_invalid.to_csv(f'{output_dir}/resultado_lotes_descartados.csv', index=False, sep=';', encoding='utf-8-sig')
            print("⚠️ Archivo de filas inválidas guardado como 'output/resultado_lotes_descartados.csv'.")

            # Registrar rechazados en Google Sheets si se proporciona moodle_manager
            if moodle_manager:
                print("\nRegistrando usuarios rechazados en Matriculados Fallidos...")
                for _, row in df_invalid.iterrows():
                    motivo = "Rechazado - "
                    modalidad = row.get('profile_field_modalidad', '')
                    departamento = row.get('profile_field_departamento', '')
                    
                    if modalidad not in ['VIRTUAL', 'PRESENCIAL']:
                        motivo += f"Modalidad inválida: {modalidad}"
                    elif departamento not in ['ANTIOQUIA', 'CALDAS', 'CHOCÓ', 'QUINDÍO', 'RISARALDA']:
                        motivo += f"Departamento no permitido: {departamento}"
                    else:
                        motivo += "Razón desconocida"
                    
                    # Convertir la fila a formato compatible con registrar_resultado
                    user_data = {
                        'username': row.get('username', ''),
                        'firstname': row.get('firstname', ''),
                        'lastname': row.get('lastname', ''),
                        'email': row.get('email', ''),
                        'phone1': row.get('phone1', ''),
                        'idnumber': row.get('idnumber', ''),
                        'group1': row.get('group1', ''),
                        'password': 'No aplica'  # Campo requerido pero no usado para rechazados
                    }
                    
                    moodle_manager.registrar_resultado(
                        row=user_data,
                        tipo="fallido",
                        motivo=motivo,
                        grupo=row.get('group1', '')
                    )

    except Exception as e:
        print(f"❌ Error al procesar el archivo: {e}")

# Ejemplo de uso
ruta_archivo = 'output/usuarios_no_matriculados.csv'
import csv
import os
import requests
import json
from dotenv import load_dotenv
from urllib.parse import urljoin
from datetime import datetime
import time

class MoodleManager:
    def __init__(self):
        load_dotenv()
        self.MOODLE_URL = os.getenv('MOODLE_URL').rstrip('/') + '/'
        self.MOODLE_TOKEN = os.getenv('MOODLE_TOKEN')
        self.session = requests.Session()
        self.headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        
        # Configuración de Google Sheets via Apps Script
        self.APPS_SCRIPT_URL = os.getenv('APPS_SCRIPT_WEBAPP_URL')
        self.SHEET_ID = os.getenv('GOOGLE_SHEET_ID')
        self.MAX_RETRIES = 3  # Número máximo de reintentos
        self.ARCHIVO_EXITOSOS = 'Prueba de nivelacion Padre.csv'
        
        if not all([self.MOODLE_URL, self.MOODLE_TOKEN, self.APPS_SCRIPT_URL, self.SHEET_ID]):
            raise ValueError("Faltan configuraciones en el archivo .env")

    def matricular_usuarios(self, csv_file_path):
        try:
            with open(csv_file_path, mode='r', encoding='utf-8-sig') as csvfile:
                csv_reader = csv.DictReader(csvfile, delimiter=';')
                usuarios = list(csv_reader)
                print(f"\nTotal de usuarios a procesar: {len(usuarios)}")
                
                # Inicializar archivo de exitosos si no existe
                if not os.path.exists(self.ARCHIVO_EXITOSOS):
                    with open(self.ARCHIVO_EXITOSOS, mode='w', encoding='utf-8', newline='') as f:
                        writer = csv.writer(f)
                        writer.writerow(['username'])
                
                for i, row in enumerate(usuarios, 1):
                    try:
                        username = row['username']
                        print(f"\n[{i}/{len(usuarios)}] Procesando usuario: {username}")
                        
                        # Verificar si el usuario ya existe
                        if self.usuario_existe(username):
                            print("⏩ Usuario ya existe, omitiendo...")
                            self.registrar_resultado(row, "fallido", "Usuario ya existente")
                            continue
                            
                        # Crear nuevo usuario
                        try:
                            user_id = self.crear_usuario(row)
                            if not user_id:
                                continue  # El error ya se registró en crear_usuario
                                
                            # Matricular en curso principal (ID=5)
                            if not self.matricular_en_curso(user_id, 5, 5):
                                self.registrar_resultado(row, "fallido", "Error en matriculación")
                                continue
                                
                            # Asignar a grupo/subgrupo si está especificado
                            grupo = row.get('group1', '').strip()
                            if grupo and not self.asignar_a_grupo(user_id, 5, grupo):
                                self.registrar_resultado(row, "fallido", "Error al asignar grupo")
                                continue
                            
                            # Registrar éxito en Google Sheets
                            if not self.registrar_resultado(row, "exitoso", "Matriculación exitosa", grupo):
                                print("⚠️ No se pudo registrar el éxito en Google Sheets, pero el usuario fue creado")
                            
                            # Registrar username en archivo CSV de exitosos
                            self.registrar_exitoso_csv(username)
                            
                        except Exception as e:
                            error_msg = str(e)
                            print(f"⚠️ Error al crear usuario: {error_msg}")
                            self.registrar_resultado(row, "fallido", error_msg)
                            continue
                    
                    except Exception as e:
                        error_msg = f"Error inesperado: {str(e)}"
                        print(f"⚠️ {error_msg}")
                        self.registrar_resultado(row, "fallido", error_msg)
                        continue
        
        except Exception as e:
            print(f"🚨 Error crítico: {str(e)}")
            raise
        finally:
            print("\n✅ Proceso completado. Revisa los registros en Google Sheets y en el archivo CSV")

    def registrar_exitoso_csv(self, username):
        """Registrar username en archivo CSV de exitosos"""
        try:
            # Verificar si el username ya existe en el archivo
            with open(self.ARCHIVO_EXITOSOS, mode='r', encoding='utf-8') as f:
                reader = csv.reader(f)
                if any(row and row[0] == username for row in reader):
                    print(f"⏩ Usuario {username} ya registrado en archivo CSV")
                    return True
            
            # Agregar nuevo username
            with open(self.ARCHIVO_EXITOSOS, mode='a', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([username])
                print(f"📝 Registrado {username} en archivo CSV de exitosos")
            return True
        except Exception as e:
            print(f"⚠️ Error al registrar en archivo CSV: {str(e)}")
            return False

    def registrar_resultado(self, row, tipo, motivo, grupo=""):
        """Registrar resultado en Google Sheets con las columnas especificadas"""
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        datos = {
            "sheet_id": self.SHEET_ID,
            "tipo": tipo,
            "datos": {
                "Cédula": row.get('username', ''),
                "Nombre Completo": f"{row.get('firstname', '')} {row.get('lastname', '')}",
                "Email": row.get('email', ''),
                "Examen": grupo or row.get('group1', ''),
                "Celular": row.get('phone1', ''),
                "Fecha": fecha,
                "Observaciones": motivo
            }
        }
        
        print(f"Enviando datos a Google Sheets: {json.dumps(datos, indent=2)}")  # Debug
        
        for attempt in range(self.MAX_RETRIES):
            try:
                response = requests.post(
                    self.APPS_SCRIPT_URL,
                    json=datos,
                    headers={'Content-Type': 'application/json'},
                    timeout=10
                )
                
                print(f"Respuesta de Google Apps Script: {response.status_code} - {response.text}")  # Debug
                
                if response.status_code == 200:
                    print(f"📝 Registrado en hoja de {tipo} (Intento {attempt + 1})")
                    return True
                else:
                    print(f"⚠️ Error al registrar (Intento {attempt + 1}): {response.text}")
                    
            except requests.exceptions.RequestException as e:
                print(f"⚠️ Error de conexión (Intento {attempt + 1}): {str(e)}")
            
            if attempt < self.MAX_RETRIES - 1:
                time.sleep(2)
        
        print(f"❌ No se pudo registrar después de {self.MAX_RETRIES} intentos")
        return False

    def usuario_existe(self, username):
        """Verificar si el usuario ya existe en Moodle"""
        params = {
            'wstoken': self.MOODLE_TOKEN,
            'wsfunction': 'core_user_get_users_by_field',
            'field': 'username',
            'values[0]': username,
            'moodlewsrestformat': 'json'
        }
        
        response = self.session.get(
            urljoin(self.MOODLE_URL, 'webservice/rest/server.php'),
            params=params,
            headers=self.headers
        )
        users = response.json()
        return isinstance(users, list) and len(users) > 0

    def crear_usuario(self, row):
        """Crear un nuevo usuario en Moodle con validación de parámetros"""
        campos_personalizados = {
            'profile_field_departamento': 'departamento',
            'profile_field_municipio': 'municipio', 
            'profile_field_modalidad': 'modalidad',
            'profile_field_lote': 'lote'
        }
        
        # Validar campos obligatorios
        campos_requeridos = ['username', 'password', 'firstname', 'lastname', 'email', 'idnumber', 'phone1']
        for campo in campos_requeridos:
            if not row.get(campo, '').strip():
                error_msg = f"Campo requerido faltante: {campo}"
                raise Exception(error_msg)
        
        user_data = {
            'wstoken': self.MOODLE_TOKEN,
            'wsfunction': 'core_user_create_users',
            'users[0][username]': row['username'].strip(),
            'users[0][password]': row['password'].strip(),
            'users[0][firstname]': row['firstname'].strip(),
            'users[0][lastname]': row['lastname'].strip(),
            'users[0][email]': row['email'].strip(),
            'users[0][auth]': 'manual',
            'users[0][idnumber]': row['idnumber'].strip(),
            'users[0][phone1]': row['phone1'].strip(),
            'moodlewsrestformat': 'json'
        }
        
        for i, (csv_field, field_type) in enumerate(campos_personalizados.items()):
            if value := row.get(csv_field, '').strip():
                user_data[f'users[0][customfields][{i}][type]'] = field_type
                user_data[f'users[0][customfields][{i}][value]'] = value
        
        print("Creando usuario...")
        response = self.session.post(
            urljoin(self.MOODLE_URL, 'webservice/rest/server.php'),
            data=user_data,
            headers=self.headers
        )
        result = response.json()
        
        if isinstance(result, list) and result and 'id' in result[0]:
            print(f"✅ Usuario creado con ID: {result[0]['id']}")
            return result[0]['id']
        
        # Manejo específico para invalid_parameter_exception
        error_msg = self.extraer_error_moodle(result)
        if "invalid_parameter_exception" in error_msg.lower():
            # Extraer detalles adicionales del error
            error_details = self.obtener_detalles_error_parametro(result)
            error_msg = f"Error en parámetros: {error_details}"
        
        raise Exception(error_msg)
    
    def obtener_detalles_error_parametro(self, response):
        """Extrae detalles específicos de errores de parámetros"""
        try:
            if isinstance(response, dict):
                debuginfo = response.get('debuginfo', '')
                if debuginfo:
                    # Buscar el parámetro problemático en el debuginfo
                    import re
                    match = re.search(r'Invalid parameter value detected:(.*?)Key:', debuginfo)
                    if match:
                        return match.group(1).strip()
                return response.get('message', 'Parámetro no válido no especificado')
            return str(response)
        except:
            return "No se pudieron extraer detalles del error de parámetro"
        
    def extraer_error_moodle(self, response):
        """Versión mejorada para manejar invalid_parameter_exception"""
        if not response:
            return "Respuesta vacía de Moodle"
        
        if isinstance(response, dict):
            if 'exception' in response:
                error_msg = f"{response.get('exception', '')}: {response.get('message', '')}"
                if 'debuginfo' in response:
                    error_msg += f" (Detalles: {response['debuginfo']})"
                return error_msg
            if 'error' in response:
                return response['error']
        
        if isinstance(response, list):
            if len(response) > 0 and isinstance(response[0], dict):
                if 'warnings' in response[0]:
                    warnings = response[0]['warnings']
                    if warnings and len(warnings) > 0:
                        return warnings[0].get('message', 'Error desconocido en warnings')
        
        try:
            return json.dumps(response, indent=2)
        except:
            return str(response)

    def matricular_en_curso(self, user_id, course_id, role_id):
        """Matricular usuario en un curso específico"""
        enrol_data = {
            'wstoken': self.MOODLE_TOKEN,
            'wsfunction': 'enrol_manual_enrol_users',
            'enrolments[0][roleid]': role_id,
            'enrolments[0][userid]': user_id,
            'enrolments[0][courseid]': course_id,
            'enrolments[0][suspend]': 0,
            'moodlewsrestformat': 'json'
        }
        
        print(f"Matriculando en curso {course_id}...")
        response = self.session.post(
            urljoin(self.MOODLE_URL, 'webservice/rest/server.php'),
            data=enrol_data,
            headers=self.headers
        )
        result = response.json()
        
        if result is None:
            print(f"✅ Matriculado en curso {course_id} con rol {role_id}")
            return True
        
        print(f"❌ Error en matriculación:", json.dumps(result, indent=2))
        return False

    def asignar_a_grupo(self, user_id, course_id, group_name):
        """Asignar usuario a un grupo/subgrupo en el curso"""
        group_id = self.obtener_id_grupo(course_id, group_name)
        if not group_id:
            print(f"⚠️ Grupo '{group_name}' no encontrado")
            return False
        
        group_data = {
            'wstoken': self.MOODLE_TOKEN,
            'wsfunction': 'core_group_add_group_members',
            'members[0][userid]': user_id,
            'members[0][groupid]': group_id,
            'moodlewsrestformat': 'json'
        }
        
        print(f"Asignando al grupo '{group_name}'...")
        response = self.session.post(
            urljoin(self.MOODLE_URL, 'webservice/rest/server.php'),
            data=group_data,
            headers=self.headers
        )
        result = response.json()
        
        if result is None:
            print(f"✅ Asignado al grupo '{group_name}' (ID: {group_id})")
            return True
        
        print(f"❌ Error al asignar al grupo:", json.dumps(result, indent=2))
        return False

    def obtener_id_grupo(self, course_id, group_name):
        """Obtener el ID de un grupo existente"""
        params = {
            'wstoken': self.MOODLE_TOKEN,
            'wsfunction': 'core_group_get_course_groups',
            'courseid': course_id,
            'moodlewsrestformat': 'json'
        }
        
        response = self.session.get(
            urljoin(self.MOODLE_URL, 'webservice/rest/server.php'),
            params=params,
            headers=self.headers
        )
        groups = response.json()
        
        if isinstance(groups, list):
            for group in groups:
                if group['name'] == group_name:
                    return group['id']
        return None

# if __name__ == "__main__":
#     moodle_manager = MoodleManager()
#     moodle_manager.matricular_usuarios('output/resultado_lotes.csv')


import pandas as pd

def extraer_columnas_reporte_1003():
    # Leer el archivo (detecta automáticamente CSV o Excel)
    try:
        if "csv" in "output/reporte_1003".lower():
            df = pd.read_csv("reporte_1003.csv", encoding="utf-8")
        else:
            df = pd.read_excel("output/reporte_1003.xlsx")
    except FileNotFoundError:
        print("❌ No se encontró el archivo 'output/reporte_1003'.")
        return

    # Verificar que las columnas existan
    columnas_necesarias = ["documento_numero", "inscripcion_aprobada"]
    for col in columnas_necesarias:
        if col not in df.columns:
            print(f"⚠️ No se encontró la columna '{col}' en el archivo.")
            return

    # Filtrar solo las columnas necesarias
    df_filtrado = df[columnas_necesarias]

    # Guardar el nuevo archivo sin índice
    df_filtrado.to_csv("reporte_1003_filtrado.csv", sep=';', encoding='utf-8', index=False)
    print("✅ Archivo 'reporte_1003_filtrado.csv' creado correctamente.")

# Ejecutar función
#extraer_columnas_reporte_1003()

import pandas as pd
import re

def _norm_doc(x):
    if pd.isna(x):
        return None
    s = str(x).strip().replace(",", "")
    if s.endswith(".0"):
        s = s[:-2]
    return s

def _fmt_grupo(v):
    # Convierte 3.0 -> "3", 3 -> "3". Si no es numérico, deja el texto como está.
    if pd.isna(v):
        return "Activar"
    s = str(v).strip()
    try:
        f = float(s)
        if f.is_integer():
            return str(int(f))
        # Si llega con decimales distintos de .0, redondea a entero
        return str(int(round(f)))
    except:
        return s or "Activar"

def combinar_reportes():
    try:
        # Leer archivos
        df_1003 = pd.read_excel("output/reporte_1003.xlsx")
        df_992  = pd.read_excel("output/reporte_992.xlsx")

        # Validar columnas
        columnas_1003 = ["documento_numero", "inscripcion_aprobada"]
        columnas_992  = ["documento_estudiante", "estado_en_ciclo", "grupo"]
        for col in columnas_1003:
            if col not in df_1003.columns:
                print(f"⚠️ Falta columna '{col}' en reporte_1003")
                return
        for col in columnas_992:
            if col not in df_992.columns:
                print(f"⚠️ Falta columna '{col}' en reporte_992")
                return

        # Normalizar claves
        df_1003 = df_1003[columnas_1003].copy()
        df_1003["doc_key"] = df_1003["documento_numero"].apply(_norm_doc)

        df_992 = df_992[columnas_992].copy()
        df_992["doc_key"] = df_992["documento_estudiante"].apply(_norm_doc)

        # Merge tipo BUSCARV
        df_final = pd.merge(
            df_1003,
            df_992[["doc_key", "estado_en_ciclo", "grupo"]],
            on="doc_key",
            how="left"
        ).drop(columns=["doc_key"])

        # Rellenar no coincidencias con "Activar"
        df_final["estado_en_ciclo"] = df_final["estado_en_ciclo"].fillna("Activar")
        # Formatear grupo como entero sin decimales; no match -> "Activar"
        df_final["grupo"] = df_final["grupo"].apply(_fmt_grupo)

        # Guardar resultado
        df_final.to_csv("reporte_1003_combinado.csv", sep=";", encoding="utf-8", index=False)
        print("✅ Archivo 'reporte_1003_combinado.csv' creado correctamente.")

    except FileNotFoundError as e:
        print(f"❌ Archivo no encontrado: {e}")

# Ejecutar
#combinar_reportes()
