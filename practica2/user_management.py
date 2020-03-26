""" Fichero: user_management.py
Modulo para gestionar la identidad de usuarios
Autores: Andres Salas Penya - andres.salas@estudiante.uam.es
		 Francisco de Vicente Lana - francisco.vicentel@estudiante.uam.es
"""
import requests
import json
import constants
import crypt_management

# Path final que gestiona las funciones de usuarios
FINAL_URL = 'users/'

def create_identity(nombre, email):
	"""
	 FUNCION: create_identity(nombre, email)
	 ARGS_IN: nombre - cadena que expresa el nombre del usuario a registrar
	 		  email - cadena que indica el correo correspondiente al usuario
	 DESCRIPCION: crea una nueva identidad (claves publica y privada) y las registra
				  en SecureBox
	"""
	status = 'OK'

	# Generacion del par de claves
	crypt_management.key_generate()
	publicKey = crypt_management.get_public_rsa_key()
	
	# Preparacion de la peticion al servidor
	url = constants.URL + FINAL_URL + 'register'
	head = {'Authorization': 'Bearer' + constants.TOKEN}
	args = {'nombre':nombre, 'email':email, 'publicKey':publicKey}
	r = requests.post(url, headers=head, json=args)
	
	# Comprobacion de errores
	d = r.json()
	if r.status_code != 200:
		status = 'ERROR'
		print 'Creando identidad...',status
		print d['error_code'], d['description']
		return

	# Se crea correctamente la identidad
	print 'Creando identidad...',status
	print 'Identidad creada'
	print '\t Nombre =', d['nombre'], ' Email =', email, ' [ Timestamp:' , d['ts'], ']'
	
def get_public_key(userId):
	"""
	 FUNCION: get_public_key(userID)
	 ARGS_IN: userID - id del usuario
	 DESCRIPCION: busca y devuelve la clave publica del usuario cuya id es pasada
	 ARGS_OUT: pulbicKey - clave publica del usuario buscado, ERROR si falla
	"""
	status = 'OK'

	# Preparacion de la peticion al servidor
	url = constants.URL + FINAL_URL + 'getPublicKey'
	head = {'Authorization': 'Bearer' + constants.TOKEN}
	args = {'userID':userId}
	r = requests.post(url, headers=head, json=args)

	# Comprobacion de errores
	d = r.json()
	if r.status_code != 200: # Error
		status = 'ERROR'
		print 'Buscando clave publica de la id', userId,'...', status
		print d['error_code'], d['description']
		return ERROR

	# Se devuelve la clave publica encontrada
	print 'Buscando clave publica de la id', userId,'...', status
	return d['publicKey'] 

def search_identity(string):
	"""
	 FUNCION: search_identity(string)
	 ARGS_IN: string - cadena a buscar
	 DESCRIPCION: busca en las identidades de SecureBox
	              un usuario cuyo nombre o correo contenga cadena
	"""
	status = 'OK'
	
	#Preparacion de la peticion al servidor
	url = constants.URL + FINAL_URL + 'search'
	head = {'Authorization': 'Bearer' + constants.TOKEN}
	args = {'data_search':string}
	r = requests.post(url, headers=head, json=args)
	
	#Comprobacion de errores
	d = r.json()
	#Caso de no encontrar ninguna coincidencia
	if len(d) == 0:
		status = 'ERROR'
		print 'Buscando usuario',string,'en el servidor...', status
		print 'No encontrado',string
		return
	elif r.status_code != 200:
		status = 'ERROR'
		print 'Buscando usuario',string,'en el servidor...', status
		print d['error_code'], d['description']
		return

	#Se imprime la lista de coincidencias de manera clara y concisa
	print 'Buscando usuario',string,'en el servidor...', status
	for i, resultado in zip(range(len(d)), d):
		print '[', i, ']',resultado['nombre'], resultado['email'], 'id:', resultado['userID']

def delete_identity(id):
	"""
	 FUNCION: delete_identity(id)
	 ARGS_IN: id - identificador de la identidad a borrar
	 DESCRIPCION: borra la identidad correspondiente al id pasado.
	"""
	status = 'OK'

	#Preparacion de la peticion al servidor
	url = constants.URL + FINAL_URL + 'delete'
	head = {'Authorization': 'Bearer' + constants.TOKEN}
	args = {'userID':id}
	r = requests.post(url, headers=head, json=args)

	#Comprobacion de errores
	d = r.json()
	if r.status_code != 200:
		status = 'ERROR'
		print 'Borrando usuario con ID',id,'...',status
		print d['error_code'], d['description']
		return

	#Se borra correctamente la identidad del usuario
	print 'Borrando usuario con ID',id,'...',status
	print 'Usuario con ID', id, 'borrado exitosamente'