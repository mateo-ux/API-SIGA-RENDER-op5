# api_siga/database_manager.py
import sqlite3
import json
import os
from pathlib import Path
from datetime import datetime

class NivelacionDatabase:
    def __init__(self):
        # ✅ RUTA CORRECTA: la base de datos está en la misma carpeta
        self.db_path = Path(__file__).parent / "nivelacion_data.db"
        self._init_database()
    
    def _init_database(self):
        """Inicializa la base de datos con todas las tablas necesarias"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tabla principal de usuarios (reemplaza tu JSON)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios_nivelacion (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            estado TEXT DEFAULT 'pendiente',
            fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Tabla de historial para tracking
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS historial_nivelacion (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            accion TEXT NOT NULL,
            detalles TEXT,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        conn.commit()
        conn.close()
        print("✅ Base de datos inicializada correctamente")
    
    def usuario_existe(self, username):
        """Verifica si un usuario ya existe en la base de datos"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT COUNT(*) FROM usuarios_nivelacion WHERE username = ?',
            (username,)
        )
        
        resultado = cursor.fetchone()[0] > 0
        conn.close()
        
        return resultado
    
    def agregar_usuario(self, username, estado="pendiente"):
        """Agrega un nuevo usuario a la base de datos"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(
                'INSERT OR IGNORE INTO usuarios_nivelacion (username, estado) VALUES (?, ?)',
                (username, estado)
            )
            
            # Registrar en historial
            cursor.execute(
                'INSERT INTO historial_nivelacion (username, accion) VALUES (?, ?)',
                (username, f"usuario_agregado_{estado}")
            )
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"❌ Error agregando usuario {username}: {e}")
            return False
    
    def obtener_usuarios_por_estado(self, estado="pendiente"):
        """Obtiene todos los usuarios con un estado específico"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT username FROM usuarios_nivelacion WHERE estado = ?',
            (estado,)
        )
        
        resultados = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        return resultados
    
    def actualizar_estado_usuario(self, username, nuevo_estado, detalles=None):
        """Actualiza el estado de un usuario y registra en historial"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Actualizar estado
            cursor.execute(
                'UPDATE usuarios_nivelacion SET estado = ?, fecha_actualizacion = CURRENT_TIMESTAMP WHERE username = ?',
                (nuevo_estado, username)
            )
            
            # Registrar en historial
            cursor.execute(
                'INSERT INTO historial_nivelacion (username, accion, detalles) VALUES (?, ?, ?)',
                (username, f"estado_actualizado_{nuevo_estado}", json.dumps(detalles) if detalles else None)
            )
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"❌ Error actualizando usuario {username}: {e}")
            return False
    
    def exportar_a_json(self, estado=None):
        """Exporta datos a formato JSON (para compatibilidad con código existente)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if estado:
            cursor.execute(
                'SELECT username, estado, fecha_creacion FROM usuarios_nivelacion WHERE estado = ?',
                (estado,)
            )
        else:
            cursor.execute(
                'SELECT username, estado, fecha_creacion FROM usuarios_nivelacion'
            )
        
        resultados = cursor.fetchall()
        conn.close()
        
        return [
            {
                "username": row[0],
                "estado": row[1],
                "fecha_creacion": row[2]
            }
            for row in resultados
        ]

# Instancia global para usar en toda la aplicación
nivelacion_db = NivelacionDatabase()