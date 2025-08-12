import csv
import os
import requests
import json
from dotenv import load_dotenv
from urllib.parse import urljoin

class MoodleManager:
    def __init__(self):
        load_dotenv()
        self.MOODLE_URL = os.getenv('MOODLE_URL').rstrip('/') + '/'
        self.MOODLE_TOKEN = os.getenv('MOODLE_TOKEN')
        self.session = requests.Session()
        self.headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        
        if not self.MOODLE_URL or not self.MOODLE_TOKEN:
            raise ValueError("Credenciales de Moodle no encontradas en .env")

    def matricular_usuarios(self, csv_file_path):
        try:
            with open(csv_file_path, mode='r', encoding='utf-8-sig') as csvfile:
                csv_reader = csv.DictReader(csvfile, delimiter=';')
                usuarios = list(csv_reader)
                print(f"\nTotal de usuarios a procesar: {len(usuarios)}")
                
                for row in usuarios:
                    try:
                        username = row['username']
                        print(f"\nProcesando usuario: {username}")
                        
                        # Verificar si el usuario ya existe
                        if self.usuario_existe(username):
                            print("⏩ Usuario ya existe, omitiendo...")
                            continue
                            
                        # Crear nuevo usuario
                        user_id = self.crear_usuario(row)
                        if not user_id:
                            continue
                            
                        # Matricular en curso principal (ID=5)
                        if not self.matricular_en_curso(user_id, 5, 5):
                            continue
                            
                        # Asignar a grupo/subgrupo si está especificado
                        if grupo := row.get('group1', '').strip():
                            self.asignar_a_grupo(user_id, 5, grupo)
                    
                    except Exception as e:
                        print(f"⚠️ Error procesando usuario: {str(e)}")
                        continue
        
        except Exception as e:
            print(f"🚨 Error crítico: {str(e)}")
            raise

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
        """Crear un nuevo usuario en Moodle"""
        # Campos personalizados del perfil
        campos_personalizados = {
            'profile_field_departamento': 'departamento',
            'profile_field_municipio': 'municipio', 
            'profile_field_modalidad': 'modalidad',
            'profile_field_lote': 'lote'
        }
        
        # Datos básicos del usuario
        user_data = {
            'wstoken': self.MOODLE_TOKEN,
            'wsfunction': 'core_user_create_users',
            'users[0][username]': row['username'],
            'users[0][password]': row['password'],
            'users[0][firstname]': row['firstname'].strip(),
            'users[0][lastname]': row['lastname'].strip(),
            'users[0][email]': row['email'],
            'users[0][auth]': 'manual',
            'users[0][idnumber]': row['idnumber'],
            'users[0][phone1]': row['phone1'],
            'moodlewsrestformat': 'json'
        }
        
        # Añadir campos personalizados
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
        
        print("❌ Error al crear usuario:", json.dumps(result, indent=2))
        return None

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
        # Buscar el grupo existente
        group_id = self.obtener_id_grupo(course_id, group_name)
        if not group_id:
            print(f"⚠️ Grupo '{group_name}' no encontrado")
            return False
        
        # Asignar usuario al grupo
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

if __name__ == "__main__":
    moodle_manager = MoodleManager()
    moodle_manager.matricular_usuarios('output/resultado_lotes.csv')