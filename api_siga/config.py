# config.py
import os
import sys
from pathlib import Path

# Agregar el directorio actual al path
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

# Importar la base de datos
from database_manager import nivelacion_db

# Función de migración
def migrar_datos_existentes():
    """Migra datos desde JSON antiguo a base de datos"""
    try:
        json_path = current_dir / "input" / "Prueba de nivelacion Padre.json"
        
        if json_path.exists():
            print("🔄 Migrando datos existentes desde JSON a base de datos...")
            
            import json
            with open(json_path, "r", encoding="utf-8") as f:
                datos_existentes = json.load(f)
            
            # Manejar diferentes formatos
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

# Ejecutar migración al importar
migrar_datos_existentes()