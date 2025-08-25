import os
import sqlite3
import psycopg2
from psycopg2.extras import RealDictCursor
import json
from api_siga.utils import nivelacion_db
def migrar_sqlite_a_postgres(sqlite_path: str = None):
    """
    Uso puntual: copia usuarios e historial desde un SQLite existente a Postgres.
    Ejecuta UNA sola vez y luego comenta/borra esta función.
    """
    import sqlite3
    if not sqlite_path:
        # ruta por defecto junto al utils.py si aún existiera
        from pathlib import Path
        sqlite_path = Path(__file__).parent / "nivelacion_data.db"

    if not os.path.exists(sqlite_path):
        print(f"ℹ️ No existe {sqlite_path}, nada que migrar.")
        return

    print(f"🔄 Migrando desde SQLite: {sqlite_path}")
    try:
        # 1) Leer SQLite
        sqlite_conn = sqlite3.connect(sqlite_path)
        s_cur = sqlite_conn.cursor()

        s_cur.execute("SELECT username, estado FROM usuarios_nivelacion;")
        usuarios = s_cur.fetchall()  # list[(username, estado)]

        try:
            s_cur.execute("SELECT username, accion, detalles, fecha FROM historial_nivelacion;")
            historial = s_cur.fetchall()  # list[(username, accion, detalles, fecha)]
        except sqlite3.OperationalError:
            historial = []

        # 2) Insertar en Postgres
        with nivelacion_db._get_conn() as pg_conn, pg_conn.cursor() as pcur:
            # usuarios
            for username, estado in usuarios:
                pcur.execute(
                    """
                    INSERT INTO usuarios_nivelacion (username, estado)
                    VALUES (%s, %s)
                    ON CONFLICT (username) DO NOTHING;
                    """,
                    (username, estado)
                )
            # historial
            for username, accion, detalles, fecha in historial:
                pcur.execute(
                    """
                    INSERT INTO historial_nivelacion (username, accion, detalles, fecha)
                    VALUES (%s, %s, %s, %s);
                    """,
                    (username, accion, detalles, fecha)
                )
            pg_conn.commit()

        sqlite_conn.close()
        print("✅ Migración completada")

    except Exception as e:
        print(f"❌ Error migrando SQLite → Postgres: {e}")
# al final del utils.py, temporalmente:
migrar_sqlite_a_postgres()  # si el archivo existe