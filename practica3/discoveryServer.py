""" Fichero: discoveryServer.py
Modulo para gestionar la conexion al servidor de descubrimiento y sus comandos
Autores: Andres Salas Penya - andres.salas@estudiante.uam.es
		 Francisco de Vicente Lana - francisco.vicentel@estudiante.uam.es
"""
import socket

# Inicializacion de constantes
DS_NAME = 'vega.ii.uam.es'
DS_PORT = 8000
OK = 'OK'
ERROR = 'NOK'
END = 'BYE'
REG_OK = 'WELCOME'
REG_ERROR = 'WRONG_PASS'
USER_OK = 'USER_FOUND'
USER_ERROR = 'USER_UNKNOWN'
LIST_USERS = 'LIST_USERS'


class My_socket:
	'''
	Clase para gestionar los sockets. 
	'''
	def __init__(self):
		"""
		 FUNCION: __init__(self)
		 ARGS_IN: self - variable de clase
		 DESCRIPCION: inicializa la clase creando y conectando el socket
		"""
		self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.socket.connect((DS_NAME, DS_PORT))

	def users_parse(self, firstUser, restUsers, n):
		"""
		 FUNCION: users_parse(self, firstUser, restUsers, n)
		 ARGS_IN: self - variable de clase
		 ARGS_IN: firstUser - primer usuario (se pasa a parte)
		 ARGS_IN: restUsers - usuarios (salvo el primero)
		 ARGS_IN: n - numero de usuarios
		 DESCRIPCION: auxiliar para el parseo de usuarios
		 ARGS_OUT: listado de nicks de usuarios
		"""
		# Inicializacion de la lista a devolver
		lst = [firstUser[0]]
		# Requiere una iteracion menos ya que el primer elemento ya esta
		for i in range(0, int(n)-1):
			user_parse = restUsers[i].split()
			# Anyade a la lista el nick de cada usuario iterado
			lst.append(user_parse[0])
		return lst

	def resp_parse_users(self, resp):
		"""
		 FUNCION: resp_parse_users(self, resp)
		 ARGS_IN: self - variable de clase
		 ARGS_IN: resp - respuesta dada por el servidor
		 DESCRIPCION: parsea la serie de usuarios devueltos por el servidor 
		 ARGS_OUT: listado de nicks de usuarios
		"""
		# Tokenizado de la serie de usuarios en bruto
		new_resp = resp.decode().split('#')
		new_users = new_resp[0].split()

		# Obtencion del codigo de error
		code = new_users[0]
		# Obtencion del mensaje de informacion
		info = new_users[1]

		if (code == OK):
			# Pasamos el primer usuario, una serie del resto y su cardinal para
			# procesarlo en una funcion aparte que facilita la tarea
			return self.users_parse(new_users[3:], new_resp[1:], new_users[2])

	def resp_parse(self, resp):
		"""
		 FUNCION: resp_parse_users(self, resp)
		 ARGS_IN: self - variable de clase
		 ARGS_IN: resp - respuesta dada por el servidor
		 DESCRIPCION: parsea la respuesta del servidor en otros casos que no sea el
		              listado de usuarios
		 ARGS_OUT: informacion relevante de cada comando
		"""
		# Convierte la cadena de caracteres en una lista con cada palabra
		resp_parse = resp.decode().split()
		# Obtencion del codigo de error
		code = resp_parse[0]

		if (code != END): # Caso QUIT
			# Obtencion del mensaje de informacion
			info = resp_parse[1]

			# Casos correctos
			if (code == OK):
				if (info == REG_OK): # Caso REGISTER
					nick = resp_parse[2]
					ts = resp_parse[3]

				elif (info == USER_OK): # Caso QUERY
					nick = resp_parse[2]
					ip_address = resp_parse[3]
					port = resp_parse[4]
					protocol = resp_parse[5]
					
					# Degug
					# print('obtengo la ip {} de {}'.format(ip_address, nick))

					return ip_address, port

			# Casos erroneos
			elif (code == ERROR):
				if (info == REG_ERROR): # error de REGISTER
					return None
				elif (info == USER_ERROR): # error de QUERY
					return None, None
			# Sintaxis erronea
			else:
				return None

			return info

	def get_N_users(self, resp):
		"""
		 FUNCION: get_N_users(self, resp)
		 ARGS_IN: self - variable de clase
		 ARGS_IN: resp - respuesta dada por el servidor
		 DESCRIPCION: obtiene la cantidad total de usuarios registrados
		 ARGS_OUT: cantidad de usuarios registrados indicado por el servidor
		"""
		resp_parse = resp.split()
		# Obtiene la tercera palabra de la respuesta
		return int(resp_parse[2])

	def get_N_separators(self, resp):
		"""
		 FUNCION: get_N_separators(self, resp)
		 ARGS_IN: self - variable de clase
		 ARGS_IN: resp - fragemnto de respuesta dada por el servidor
		 DESCRIPCION: calcula la cantidad de usuarios en un fragmento de respuesta
		 ARGS_OUT: cantidad de usuarios registrados pasados en un fragmento
		"""
		# Obtiene el numero de almohadillas que aparecen en el fragmento
		return (resp.decode()).count('#')

	def send_msg_list_users(self, msg):
		"""
		 FUNCION: send_msg_list_users(self, msg)
		 ARGS_IN: self - variable de clase
		 ARGS_IN: msg - mensaje a enviar al servidor
		 DESCRIPCION: envia un mensaje indicado al servidor y procesa su respuesta
		              para el caso del listado de usuarios
		 ARGS_OUT: respuesta total (union de fragmentos) del rervidor
		"""
		# Envio en el formato adecuado
		(self.socket).send(msg.encode('utf-8'))
		# Recibe respuesta (4096 deberia bastar para cualquier fragmento)
		resp = self.socket.recv(4096)
		
		# Obtencion de usuarios totales registrados
		N = self.get_N_users(resp)
		# Obtencion de usuarios recibidos hasta el momento
		nSeparator = self.get_N_separators(resp)

		while (N > nSeparator): # Lee todos los fragmentos existentes
			aux = self.socket.recv(4096)
			# Formacion del resultado final
			resp = resp + aux

			nSeparator = self.get_N_separators(resp)
		return resp

	def send_msg(self, msg):
		"""
		 FUNCION: send_msg(self, msg)
		 ARGS_IN: self - variable de clase
		 ARGS_IN: msg - mensaje a enviar al servidor
		 DESCRIPCION: envia un mensaje indicado al servidor y procesa su respuesta
		              para el resto de casos
		 ARGS_OUT: respuesta obtenida por parte del rervidor
		"""	
		# Envio en el formato adecuado
		(self.socket).send(msg.encode('utf-8'))
		# Recibe respuesta (4096 deberia bastar para cualquier otro comando)
		resp = self.socket.recv(4096)

		return resp

	def disconnect(self):
		"""
		 FUNCION: disconnect(self)
		 ARGS_IN: self - variable de clase
		 DESCRIPCION: cierra el socket al finalizar al salir de la aplicacion
		"""	
		self.socket.close()

	def request_users(self, msg):
		"""
		 FUNCION: request_users(self, msg):
		 ARGS_IN: self - variable de clase
		 ARGS_IN: msg - mensaje a enviar al servidor
		 DESCRIPCION: Envia la peticion de listar usuarios y precesa su respuesta
		 ARGS_OUT: lista de usuarios registrados en el servidor
		"""	
		# Envio peticion
		resp = self.send_msg_list_users(msg)
		# Recepcion y parseo extendido de la respuesta
		ret = self.resp_parse_users(resp)
		return ret

	def request(self, msg):
		"""
		 FUNCION: request(self, msg):
		 ARGS_IN: self - variable de clase
		 ARGS_IN: msg - mensaje a enviar al servidor
		 DESCRIPCION: Envia el resto de peticiones y procesa adecuadamente su 
		              respuesta
		 ARGS_OUT: informacion relevante devuelta por el servidor
		"""	
		# Envio peticion
		resp = self.send_msg(msg)
		# Recepcion y parseo de la respuesta
		return self.resp_parse(resp)

	def register(self, nick, ip, port, psw):
		"""
		 FUNCION: register(self, nick, psw)
		 ARGS_IN: self - variable de clase
		 ARGS_IN: nick - nombre de usuario
		 ARGS_IN: psw - contrasenya de usuario
		 DESCRIPCION: registra un nuevo usuario o actualiza uno ya existente en 
		              el servidor
		 ARGS_OUT: informacion de respuesta
		"""	
		if ('#' in nick):
			return -1 # Evita registrar usuarios con nombre erratico
		else:
			comando = 'REGISTER {} {} {} {} V1'.format(nick, \
				ip, port, psw)
			return self.request(comando)

	def query(self, nick):
		"""
		 FUNCION: query(self, nick):
		 ARGS_IN: self - variable de clase
		 ARGS_IN: nick - nombre de usuario
		 DESCRIPCION: forma el la peticion de solicitar datos de un usuario para
		              enviarla y  procesar adecuadamente su respuesta
		 ARGS_OUT: informacion de respuesta
		"""	
		comando = 'QUERY {}'.format(nick)
		return self.request(comando)

	def list_users(self):
		"""
		 FUNCION: list_users(self):
		 ARGS_IN: self - variable de clase
		 DESCRIPCION: forma el la peticion de listar usuarios para enviarlas y 
		              procesar adecuadamente su respuesta
		 ARGS_OUT: lista de usuarios registrados en el servidor
		"""	
		comando = LIST_USERS
		return self.request_users(comando)

	def quit(self):
		"""
		 FUNCION: quit(self):
		 ARGS_IN: self - variable de clase
		 DESCRIPCION: forma la peticion para salir del cliente para que sea enviada
		"""	
		comando = 'QUIT'
		self.request(comando)
		self.disconnect()