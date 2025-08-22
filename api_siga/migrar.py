# AÑADE ESTAS IMPORTACIONES AL INICIO del archivo migrar.py
import os
import json
from database_manager import nivelacion_db  # Asegúrate de que esta importación esté correcta

def migrar_datos_existentes():
    """Migra datos desde el JSON antiguo a la base de datos"""
    try:
        json_path = "input/Prueba de nivelacion Padre.json"
        
        if os.path.exists(json_path):
            print("🔄 Migrando datos existentes desde JSON a base de datos...")
            
            with open(json_path, "r", encoding="utf-8") as f:
                datos_existentes = json.load(f)
            
            # Manejar diferentes formatos de JSON
            if isinstance(datos_existentes, list):
                usuarios = datos_existentes
            elif isinstance(datos_existentes, dict):
                usuarios = datos_existentes.get("rows") or datos_existentes.get("data") or []
            else:
                usuarios = []
            
            # Migrar cada usuario
            migrados = 0
            for usuario in usuarios:
                if isinstance(usuario, dict):
                    username = usuario.get("username") or usuario.get("idnumber") or ""
                    if username:
                        nivelacion_db.agregar_usuario(str(username).strip(), "migrado")
                        migrados += 1
            
            print(f"✅ {migrados} usuarios migrados a la base de datos")
            
        else:
            print("ℹ️ No hay archivo JSON existente para migrar")
            
    except Exception as e:
        print(f"⚠️ Error en migración (puede ignorarse): {e}")

# Ejecutar migración
if __name__ == "__main__":
    migrar_datos_existentes()