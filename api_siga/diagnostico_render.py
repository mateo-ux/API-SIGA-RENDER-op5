import os
import json
import requests
from pathlib import Path
import subprocess
import platform
from datetime import datetime

def check_render_environment():
    """Verifica si estamos en un entorno de Render"""
    return os.getenv('RENDER') is not None

def check_python_version():
    """Verifica la versión de Python"""
    return platform.python_version()

def check_file_permissions():
    """Verifica los permisos de escritura en el directorio actual"""
    test_file = "test_write_permission.txt"
    try:
        with open(test_file, 'w') as f:
            f.write("Test de escritura")
        os.remove(test_file)
        return True
    except Exception as e:
        return str(e)

def check_dependencies():
    """Verifica las dependencias necesarias"""
    dependencies = ['requests', 'flask', 'json', 'datetime']
    results = {}
    
    for dep in dependencies:
        try:
            if dep == 'json':
                __import__('json')
                results[dep] = "OK"
            else:
                __import__(dep)
                results[dep] = "OK"
        except ImportError:
            results[dep] = "Falta"
    
    return results

def simulate_json_operations():
    """Simula operaciones con JSON para detectar problemas"""
    test_data = {
        "test_time": datetime.now().isoformat(),
        "message": "Datos de prueba para verificar escritura JSON"
    }
    
    # Prueba de escritura
    try:
        with open('test_json.json', 'w') as f:
            json.dump(test_data, f, indent=2)
        write_success = True
    except Exception as e:
        write_success = str(e)
    
    # Prueba de lectura
    try:
        with open('test_json.json', 'r') as f:
            loaded_data = json.load(f)
        read_success = True
    except Exception as e:
        read_success = str(e)
    
    # Limpieza
    if os.path.exists('test_json.json'):
        os.remove('test_json.json')
    
    return {
        "escritura": write_success,
        "lectura": read_success
    }

def check_port_availability():
    """Verifica la disponibilidad del puerto"""
    try:
        # Intentar crear un socket
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(("", 0))
        port = s.getsockname()[1]
        s.close()
        return f"Puerto {port} disponible para pruebas"
    except Exception as e:
        return f"Error de socket: {str(e)}"

def generate_report():
    """Genera un reporte completo de diagnóstico"""
    report = {
        "timestamp": datetime.now().isoformat(),
        "render_environment": "Sí" if check_render_environment() else "No",
        "python_version": check_python_version(),
        "file_permissions": check_file_permissions(),
        "dependencies": check_dependencies(),
        "json_operations": simulate_json_operations(),
        "port_check": check_port_availability(),
        "current_working_directory": os.getcwd(),
        "files_in_directory": os.listdir('.')
    }
    return report

def display_report():
    """Muestra el reporte en la consola"""
    print("🔍 Ejecutando diagnóstico para API-SIGA-RENDER...")
    print("=" * 60)
    
    report = generate_report()
    
    print(f"📅 Timestamp: {report['timestamp']}")
    print(f"🌐 Entorno Render: {report['render_environment']}")
    print(f"🐍 Versión de Python: {report['python_version']}")
    
    # Permisos de archivo
    perms = report['file_permissions']
    perm_status = "✅ OK" if perms is True else f"❌ {perms}"
    print(f"📁 Permisos de escritura: {perm_status}")
    
    # Dependencias
    print("\n📦 DEPENDENCIAS:")
    deps = report['dependencies']
    for dep, status in deps.items():
        status_icon = "✅" if status == "OK" else "❌"
        print(f"   {status_icon} {dep}: {status}")
    
    # Operaciones JSON
    print("\n📄 OPERACIONES JSON:")
    json_ops = report['json_operations']
    escritura_status = "✅ OK" if json_ops['escritura'] is True else f"❌ {json_ops['escritura']}"
    lectura_status = "✅ OK" if json_ops['lectura'] is True else f"❌ {json_ops['lectura']}"
    print(f"   Escritura: {escritura_status}")
    print(f"   Lectura: {lectura_status}")
    
    # Puerto
    print(f"\n🔌 Puerto: {report['port_check']}")
    
    # Directorio
    print(f"\n📂 Directorio actual: {report['current_working_directory']}")
    
    # Archivos
    print("\n📋 Archivos en el directorio:")
    for file in report['files_in_directory']:
        print(f"   • {file}")
    
    # Recomendaciones
    print("\n" + "=" * 60)
    print("🛠️ RECOMENDACIONES:")
    
    if not report['render_environment']:
        print("""
• Configuración para Render:
  - Asegúrate de que la variable de entorno PORT esté siendo utilizada:
    ```python
    import os
    port = int(os.environ.get('PORT', 10000))
    ```
        """)
    
    json_ops = report['json_operations']
    if not (json_ops['escritura'] is True and json_ops['lectura'] is True):
        print("""
• Problemas con JSON:
  - Usa rutas absolutas para guardar archivos
  - Verifica los permisos de escritura
  - Maneja adecuadamente las excepciones
        """)
    
    if any(status == 'Falta' for status in report['dependencies'].values()):
        print("""
• Dependencias faltantes:
  - Verifica que tu requirements.txt incluya todas las dependencias
  - Ejecuta `pip freeze > requirements.txt` para actualizarlo
        """)
    
    print("""
📝 Consejos adicionales:
1. Revisa los logs en el dashboard de Render para ver errores
2. Asegúrate de configurar todas las variables de entorno en Render
3. Verifica que has creado un "Web Service" en Render
4. Revisa que los build commands son correctos para tu proyecto
    """)

if __name__ == '__main__':
    display_report()