""" Fichero: securebox_client.py
Modulo para gestionar la entrada por terminal
Autores: Andres Salas Penya - andres.salas@estudiante.uam.es
		 Francisco de Vicente Lana - francisco.vicentel@estudiante.uam.es
"""
import argparse
import user_management
import file_management
import crypt_management
import constants
import sys

# Creacion clase de parseo
parser = argparse.ArgumentParser(description="Cliente que consume el servicio ofrecido por securebox")
# Define dependencias entre ciertos comandos
group = parser.add_mutually_exclusive_group()

group.add_argument("--create_id", nargs=2, help="Creacion identidad", metavar=('nombre','email'))
group.add_argument("--search_id", nargs=1, help="Busqueda usuario", metavar=('cadena'))
group.add_argument("--delete_id", nargs=1, help="Eliminacion identidad", metavar=('id'))
parser.add_argument("--upload", nargs=1, help="Envio fichero", metavar=('fichero'))
parser.add_argument("--source_id", nargs=1, help="ID emisor fichero", metavar=('id_fichero'))
parser.add_argument("--dest_id", nargs=1, help="ID receptor fichero", metavar=('id_fichero'))
group.add_argument("--list_files", action='store_true', help="Lista ficheros")
parser.add_argument("--download", nargs=1, help="Recupera fichero", metavar=('id_fichero'))
group.add_argument("--delete_file", nargs=1, help="Elimina fichero", metavar=('id_fichero'))
parser.add_argument("--encrypt", nargs=1, help="Cifra fichero", metavar=('fichero'))
parser.add_argument("--sign", nargs=1, help="Firma fichero", metavar=('fichero'))
parser.add_argument("--enc_sign", nargs=1, help="Cifra y firma fichero", metavar=('fichero'))

args = parser.parse_args()

if len(sys.argv) == 1:
	print 'No ha especificado argumentos de entrada. Puede obtener ayuda mediante la opcion -h'

if args.create_id:
	# Creacion identidad
	nombre = args.create_id[0]
	email = args.create_id[1]
	user_management.create_identity(nombre, email)

if args.search_id:
	# Busqueda identidades
	string = args.search_id[0]
	user_management.search_identity(string)

if args.delete_id:
	# Eliminacion identidad
	id = args.delete_id[0]
	user_management.delete_identity(id)
	
if args.upload and args.dest_id:
	# Obtencion clave publica destinatario
	key = user_management.get_public_key(args.dest_id[0])
	if key != constants.ERROR:
		# Firma + Cifrado * Upload
		file = args.upload[0]
		file_management.upload_file(file, key)

if args.list_files:
	# Listado ficheros
	file_management.list_files()

if args.download and args.source_id:
	# Obtencion clave publica emisor
	key = user_management.get_public_key(args.source_id[0])
	if key != constants.ERROR:
		# Descarga fichero
		file_id = args.download[0]
		file_management.download_file(file_id, key)

if args.delete_file:
	# Eliminacion fichero
	file_id = args.delete_file[0]
	file_management.delete_file(file_id)

if args.encrypt and args.dest_id:
	# Obtencion clave publica destinatario
	key = user_management.get_public_key(args.dest_id[0])
	if key != constants.ERROR:
		# Cifrado
		crypt_management.encrypt(args.encrypt[0], key)

if args.sign:
	# Firma
	crypt_management.sign(args.sign[0])

if args.enc_sign and args.dest_id:
	# Obtencion clave publica destinatario
	key = user_management.get_public_key(args.dest_id[0])
	if key != constants.ERROR:
		# Cifrado + firma
		crypt_management.enc_sign(args.enc_sign[0], key)