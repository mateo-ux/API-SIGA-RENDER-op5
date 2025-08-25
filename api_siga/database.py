import os
import sqlite3
import psycopg2
from psycopg2.extras import RealDictCursor
from urllib.parse import urlparse
from dotenv import load_dotenv

load_dotenv()

class DatabaseManager:
    def __init__(self):
        self.db_engine = os.getenv('DB_ENGINE', 'sqlite')
        self.connection = None
        
    def get_connection(self):
        """Obtiene conexión a la base de datos según el engine"""
        if self.db_engine == 'postgresql':
            return self._get_postgres_connection()
        else:
            return self._get_sqlite_connection()
    
    def _get_sqlite_connection(self):
        """Conexión SQLite para desarrollo local"""
        db_path = os.path.join(os.path.dirname(__file__), "nivelacion_data.db")
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _get_postgres_connection(self):
        """Conexión PostgreSQL para producción"""
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            raise ValueError("DATABASE_URL no está configurada")
        
        parsed_url = urlparse(database_url)
        
        conn = psycopg2.connect(
            database=parsed_url.path[1:],
            user=parsed_url.username,
            password=parsed_url.password,
            host=parsed_url.hostname,
            port=parsed_url.port,
            cursor_factory=RealDictCursor
        )
        return conn
    
    def execute_query(self, query, params=None, fetchone=False, fetchall=False):
        """Ejecuta consultas de manera genérica"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            if fetchone:
                result = cursor.fetchone()
            elif fetchall:
                result = cursor.fetchall()
            else:
                result = None
            
            conn.commit()
            return result
            
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()

# Instancia global
db_manager = DatabaseManager()