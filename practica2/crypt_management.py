""" Fichero: crypt_management.py
Modulo para gestionar los metodos de seguridad de ficheros
Autores: Andres Salas Penya - andres.salas@estudiante.uam.es
		 Francisco de Vicente Lana - francisco.vicentel@estudiante.uam.es
"""
from Crypto.PublicKey import RSA
from Crypto.Random import get_random_bytes
from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA256
from Crypto.Util import Padding

# Constantes de longitud
RSA_LEN = 2048
RSA_KEY_LEN = 256
AES_LEN = 256
AES_KEY_LEN = 32
IV_LEN = 16

def key_generate():
	"""
	 FUNCION: key_generate()
	 DESCRIPCION: genera un par de claves RSA, guardandolas en dos ficheros de tipo
	 			  pem (private_rsa_key, public_rsa_key)
	"""
	status = 'OK'
	key = RSA.generate(RSA_LEN)
	# Se guarda la clave privada
	with open('private_rsa_key.pem', 'wb') as file:
		file.write(key.exportKey())
	# Se guarda la clave publica
	with open('public_rsa_key.pem', 'wb') as file: # llamar al server ???
		file.write(key.publickey().exportKey())

	print 'Generando par de claves RSA...',status

def get_public_rsa_key():
	"""
	 FUNCION: get_public_rsa_key()
	 DESCRIPCION: devuelve la clave privada del usuario ya importada de fichero
	 			  para que se pueda leer en plano
	 ARGS_OUT: llave obtenida
	"""
	key = RSA.import_key(open('public_rsa_key.pem').read())
	key_textual = key.exportKey('OpenSSH')
	return key_textual

def encrypt(file, key_receiver):
	"""
	 FUNCION: encrypt(file, key_receiver)
	 ARGS_IN: file - nombre del fichero a encriptar
	 		  key_receiver - clave publica del receptor
	 DESCRIPCION: cifra un fichero dado por el metodo basado en RSA establecido
	 ARGS_OUT: contenido cifrado (clave, iv, info cifrada - util en enc_sign)
	"""
	status = 'OK'
	# Creacion clave simetrica (de sesion) y vector de inicializacion
	key_simetric = get_random_bytes(AES_KEY_LEN)
	init_vector = get_random_bytes(IV_LEN)

	# Cifrado mensaje
	with open(file, 'r') as f:
		cipher_aes = AES.new(key_simetric, AES.MODE_CBC, init_vector)
		content = Padding.pad(f.read(), 16)
		ciphertext = cipher_aes.encrypt(content)

	# Cifrado clave de sesion
	key = RSA.importKey(key_receiver)
	cipher_rsa = PKCS1_OAEP.new(key)
	key_enc = cipher_rsa.encrypt(key_simetric)

	# Generacion fichero de salida
	f_name = 'enc_' + file
	with open(f_name, 'wb') as file_out:
		file_out.write(key_enc)
		file_out.write(init_vector)
		file_out.write(ciphertext)

	print 'Encriptando',file,'...',status
	return key_enc + init_vector + ciphertext

def decrypt(file, key_receiver):
	"""
	 FUNCION: decrypt(file, key_receiver)
	 ARGS_IN: file - nombre del fichero a encriptar
	 		  key_receiver - clave publica del receptor
	 DESCRIPCION: descifra un fichero cifrado segun el procedimiento acordado para 
	 			  esta practica. Compruba la validez de la firma digital
	"""
	status = 'OK'
	# Lectura del fichero a descifrar
	with open(file, 'r') as f:
		content_sig_enc = f.read()

	# Obtencion clave de sesion conociendo su longitud y clave publica
	ptr = RSA_KEY_LEN + IV_LEN
	key_simetric_enc = content_sig_enc[0:RSA_KEY_LEN]

	key_rsa = RSA.import_key(open('private_rsa_key.pem', 'r').read())
	cipher_rsa = PKCS1_OAEP.new(key_rsa)
	key = cipher_rsa.decrypt(key_simetric_enc)

	# Descifrado del mensaje + firma
	init_vector = content_sig_enc[RSA_KEY_LEN:ptr]
	info_sig_enc = content_sig_enc[ptr:]

	cipher_aes = AES.new(key, AES.MODE_CBC, init_vector)
	info_sig_pad = cipher_aes.decrypt(info_sig_enc)
	info_sig = Padding.unpad(info_sig_pad, 16)
	
	# Obtencion firma
	signature = info_sig[0:AES_LEN]
	info = info_sig[AES_LEN:]

	# Comprobacion firma
	our_hash = SHA256.new(info)
	key_sig = RSA.importKey(key_receiver)
	signer = pkcs1_15.new(key_sig)

	try:
		signer.verify(our_hash, signature)
	except (ValueError, TypeError):
		status = 'ERROR [Firmas no coincidentes]'

	# Creacion fichero con la informacion obtenida
	with open('decrypted_'+file, 'wb') as file_out:
		file_out.write(info)

	print 'Descifrando',file,'...',status


def sign(file):
	"""
	 FUNCION: sign(file)
	 ARGS_IN: file - fichero a firmar
	 DESCRIPCION: firma el fichero pasado mediante el hash generado por SHA256
	 ARGS_OUT: nombre del fichero generado (util en enc_sign)
	"""
	status = 'OK'
	
	# Obtencion de la clave privada para firmar
	key = RSA.import_key(open('private_rsa_key.pem').read())
	
	# Creacion del hash a cifrar a modo de firma
	with open(file, 'r') as f:
		content = f.read()
		our_hash = SHA256.new(content)
	
	# Creacion firma
	signature = pkcs1_15.new(key).sign(our_hash)

	# Generacion fichero de salida
	f_name = 'sig_' + file
	with open(f_name, 'wb') as file_out:
		file_out.write(signature)
		file_out.write(content)

	print 'Firmando',file,'...',status
	return f_name

def enc_sign(file, key_receiver):
	"""
	 FUNCION: enc_sign(file, key_receiver)
	 ARGS_IN: file - fichero a cifrar y firmar
			  key_receiver - clave publica del receptor
	 DESCRIPCION: cifra y firma el fichero pasado. Genera otro fichero con el
	 			  contenido firmado y cifrado
	 ARGS_OUT: nombre del fichero generado
	"""	
	# Llamada a firmar
	file_sig = sign(file)
	
	# Llamada a encriptar (sobre el mensaje ya firmado)
	content_sig_enc = encrypt(file_sig, key_receiver)
	
	# Generacion fichero de salida
	f_name = 'enc_sig_' + file
	with open(f_name, 'wb') as file_out:
		file_out.write(content_sig_enc)

	return f_name