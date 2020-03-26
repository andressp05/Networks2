""" Fichero: file_management.py
Modulo para gestionar la transferencia de ficheros
Autores: Andres Salas Penya - andres.salas@estudiante.uam.es
		 Francisco de Vicente Lana - francisco.vicentel@estudiante.uam.es
"""
import requests
import json
import constants
import crypt_management

#Path final que gestiona las funciones de ficheros
FINAL_URL = 'files/'

def upload_file(file, key):
	"""
	 FUNCION: upload_file(file, key)
	 ARGS_IN: file - fichero a subir
	 		  key - clave publica del destinatario
	 DESCRIPCION: envia un fichero a otro usuario, lo sube a SecureBox 
	              firmado y cifrado
	"""
	status = 'OK'
	
	#Cifrado y firma del fichero
	file_sig_enc = crypt_management.enc_sign(file, key)
	
	#Preparacion de la peticion al servidor
	with open(file_sig_enc) as f:
		url = constants.URL + FINAL_URL + 'upload'
		head = {'Authorization': 'Bearer' + constants.TOKEN}
		r = requests.post(url, headers=head, files = {'ufile': f})
		
	#Comprobacion de errores
	d = r.json()
	if r.status_code != 200:
		status = 'ERROR'
		print 'Enviando fichero...', status
		print d['error_code'], d['description']
		return

	#El fichero se ha subido correctamente
	print 'Enviando fichero...', status
	print 'Fichero subido'
	print '\tID =', d['file_id'], ' Tamanyo =', d['file_size']


def list_files():
	"""
	 FUNCION: list_files()
	 DESCRIPCION: lista todos los ficheros pertenecientes al usuario
	"""
	status = 'OK'

	#Preparacion de la peticion al servidor
	url = constants.URL + FINAL_URL + 'list'
	head = {'Authorization': 'Bearer' + constants.TOKEN}
	r = requests.post(url, headers=head)
	
	#Comprobacion de errores
	d = r.json()
	if r.status_code != 200:
		status = 'ERROR'
		print 'Listado de ficheros...', status
		print d['error_code'], d['description']
		return

	#Caso de no poseer ningun fichero
	if d['num_files'] == 0:
		status = 'ERROR'
		print 'Listado de ficheros...', status	
		print 'No tienes ningun fichero'
		return

	#Se imprime la lista de ficheros de manera clara y concisa
	print 'Listado de ficheros...', status
	for i in range(0, d['num_files'], 1):
		print '[',i,']' , d['files_list'][i]['fileName'], d['files_list'][i]['fileID'] 
	print 'Numero de Ficheros:', d['num_files']


def download_file(file_id, key, ):
	"""
	 FUNCION: download_file(file_id, key)
	 ARGS_IN: file_id - identificador de un fichero
	 		  key - clave publica del emisor
	 DESCRIPCION: recupera el fichero cuyo id sea el pasado, lo descarga,
	              verifica la firma y descifra el contenido
	"""
	status = 'OK'

	#Preparacion de la peticion al servidor
	url = constants.URL + FINAL_URL + 'download'
	head = {'Authorization': 'Bearer' + constants.TOKEN}
	args = {'file_id':file_id}
	r = requests.post(url, headers=head, json=args)

	#Comprobacion de errores
	if r.status_code != 200:
		status = 'ERROR'
		d = r.json()
		print 'Descarga del fichero...', status
		print d['error_code'], d['description']
		return
	print 'Descarga del fichero...', status

	#El fichero se ha descargado correctamente
	f_name = 'download_'+file_id+'.dat'

	#Descifrado y comprobacion de la firma
	f = open(f_name, 'wb')
	f.write(r.content)
	f.close()
	
	crypt_management.decrypt(f_name, key)
	print 'El fichero se ha descargado en',f_name

def delete_file(file_id):
	"""
	 FUNCION: delete_file(file_id)
	 ARGS_IN: file_id - identificador de un fichero
	 DESCRIPCION: elimina el fichero cuyo id es el pasado
	"""
	status = 'OK'

	#Preparacion de la peticion al servidor
	url = constants.URL + FINAL_URL + 'delete'
	head = {'Authorization': 'Bearer' + constants.TOKEN}
	args = {'file_id':file_id}
	r = requests.post(url, headers=head, json=args)

	#Comprobacion de errores
	if r.status_code != 200:
		status = 'ERROR'
		d = r.json()
		print 'Eliminando fichero con ID',file_id,'...', status
		print d['error_code'], d['description']
		return

	#El fichero se ha eliminado bien
	print 'Eliminando fichero con ID',file_id,'...', status
	print 'Fichero con ID', file_id, 'borrado exitosamente'