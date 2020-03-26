""" Fichero: peer_skap.py
Modulo para gestionar la funcionalidad tanto de la comunicacion de control (TCP)
entre pares como la de transferencia de datos (UDP)
Autores: Andres Salas Penya - andres.salas@estudiante.uam.es
		 Francisco de Vicente Lana - francisco.vicentel@estudiante.uam.es
"""
import discoveryServer
import socket
import threading
import queue
import time
import cv2
from PIL import Image, ImageTk
import numpy as np

# Constantes de puertos y tamanyos
TCP_PORT = 8056
UDP_PORT = 8150
MAX_PEERS = 5

RESP_LEN = 2048
MAX = 200000

# Inicializacion de constantes
OK = 1
ERROR = 0

CALL = 'CALLING'
HOLD = 'CALL_HOLD'
RESUME = 'CALL_RESUME'
END = 'CALL_END'

ACCEPT = 'CALL_ACCEPTED'
DENY = 'CALL_DENIED'
BUSY = 'CALL_BUSY'


class My_peer:
	'''	 
	Clase que implementa la funcionalidad de peers entre usuarios
	'''

	def __init__(self):
		"""
		 FUNCION: __init__(self)
		 ARGS_IN: self - variable de clase
		 DESCRIPCION: inicializa la clase creando puertos y sockets necesarios
		"""

		#-------------- Info local ---------------------------------------------
		# En caso de que no se propocine, calculamos nuestra IP dinamicamente
		self.my_ip = self.get_server_host()
		# El nick propio
		self.my_nick = None 
		# Puerto de escucha propio para recibir comunicacion de control
		self.tcp_port = TCP_PORT
		# Puerto de escucha propio para recibir datos
		self.udp_port = UDP_PORT 

		#-------------- Info interlocutor --------------------------------------
		# Ip del usuario con el que queremos contactar
		self.dest_ip = None
		# Nick del usuario con el que se quiere contactar
		self.dest_nick = None
		# Puerto para enviar mansajes TCP de control al otro peer
		self.tcp_port_dest = None
		# Puerto al que enviar los frames
		self.udp_port_dest = None

		#-------------- Sockets ------------------------------------------------
		# Socket para enviar peticiones tcp al otro peer
		self.tcp_socket = None
		# Socket para escuchar peticiones tcp del otro peer
		self.tcp_listen_socket = None
		# Socket a donde mandar video
		self.udp_src_socket = None
		# Socket de donde mandamos videos
		self.udp_listen_socket = None

		#-------------- Extra --------------------------------------------------
		self.interface = None
		self.cap = None
		self.width = 384
		self.height = 384
		# Buffer de recepcion (Si fps = 30, el buffer se llenaria en 2 segundos)
		self.buf = queue.PriorityQueue(60)
		# Flag para detener el bucle de escucha tcp
		self.finish = False
		# Resolucion del video ppal
		self.res = '384x384'
		# Contador para identificar los paquetes
		self.cont = 0
		

	
	def get_server_host(self):
		"""
		 FUNCION: get_server_host(self)
		 ARGS_IN: self - variable de clase
		 DESCRIPCION: Intento de conectarse a un host de internet para obtener 
		              la IP actual
		 ARGS_OUT: direccion privada de nuestra maquina
		"""
		s = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
		s.connect(("www.google.com", 80))
		address = s.getsockname()[0]
		s.close()
		return address

################################################################################
# Recepcion TCP
################################################################################

	def create_listen_socket(self):
		"""
		 FUNCION: create_listen_socket(self, port)
		 ARGS_IN: self - variable de clase
		 DESCRIPCION: Crea un socket que escucha en el puerto dado
		"""
		self.tcp_listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.tcp_listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self.tcp_listen_socket.bind( ('', self.tcp_port) )
		# Actualizamos el puerto para poder reusar el socket
		self.interface.ds.register(self.interface.nick, self.my_ip, self.tcp_port, \
			self.interface.pwd)
		self.tcp_port = self.tcp_port + 1
		self.tcp_listen_socket.listen(MAX_PEERS)

	def create_listen_udp_socket(self):
		"""
		 FUNCION: create_listen_udp_socket(self)
		 ARGS_IN: self - variable de clase
		 DESCRIPCION: Crea un socket que escucha en el flujo de video UDP
		"""
		self.udp_listen_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self.udp_listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self.udp_listen_socket.bind( ('', UDP_PORT) )

	def calling_process(self, nick, udp_port):
		"""
		 FUNCION: calling_process(self, nick, udp_port, sock)
		 ARGS_IN: self - variable de clase
		          nick - nombre de usuario emisor
		          udp_port - puerto udp emisor
		 DESCRIPCION: Procesa una peticion de llamada
		"""
		ip, port = self.interface.ds.query(nick)

		if (self.interface.is_calling == False):
			msg = 'Estas recibiendo una llamada de {} ¿Deseas contestar?'.format(nick)
			
			if (self.interface.app.yesNoBox("LLamada", msg, parent = None) == False):
				self.deny(ip, port)

			else:
				# Inicializar Valores clase
				self.dest_nick = nick
				self.udp_port_dest = udp_port
				self.dest_ip = ip
				self.tcp_port_dest = port

				self.accept(ip, port, nick)

		else: # Otra llamada en curso
			self.busy(ip, port)

	def resume_process(self, nick):
		"""
		 FUNCION: resume_process(self, nick)
		 ARGS_IN: self - variable de clase
		          nick - nombre de usuario emisor
		 DESCRIPCION: Procesa una peticion de retomar una llamada
		"""
		if (self.interface.is_calling == True):
			self.interface.pause = False

	def hold_process(self, nick):
		"""
		 FUNCION: hold_process(self, nick)
		 ARGS_IN: self - variable de clase
		          nick - nombre de usuario emisor
		 DESCRIPCION: Procesa una peticion de detener una llamada
		"""
		if (self.interface.is_calling == True):
			self.interface.pause = True
			self.interface.app.infoBox("Info", "Video pausado")

	def end_process(self, nick):
		"""
		 FUNCION: end_process(self, nick)
		 ARGS_IN: self - variable de clase
		          nick - nombre de usuario emisor
		 DESCRIPCION: Procesa una peticion de terminar una llamada
		"""
		if (self.interface.is_calling == True):
			self.interface.prepare_end_call()
			# Liberar udp
			self.stop_udp()

	def accept_process(self, nick, port):
		"""
		 FUNCION: acceot_process(self, nick)
		 ARGS_IN: self - variable de clase
		          nick - nombre de usuario emisor
		          port - puerto de escucha udp
		 DESCRIPCION: Procesa una respuesta de aceptar una llamada
		"""
		if (self.interface.is_calling == False):
			# Obtencion datos interlocutor
			ip, port_tcp = self.interface.ds.query(nick)

			self.dest_ip = ip
			self.udp_port_dest = port
			
			# Comenzar escucha udp y inicializar llamada
			self.set_udp_socket()
			self.interface.prepare_call(self.dest_nick)

			# Retroalimentacion
			msg = 'El usuario {} acepta tu llamada'.format(nick)
			self.interface.app.infoBox("Llamada", msg, parent = None)

	def busy_process(self):
		"""
		 FUNCION: busy_process(self, nick)
		 ARGS_IN: self - variable de clase
		          nick - nombre de usuario emisor
		 DESCRIPCION: Procesa una respuesta de linea ocupada
		"""
		self.interface.app.is_calling = False
		
		# Retroalimentacion
		msg = 'El interlocutor se encuentra ocupado'
		self.interface.app.infoBox('Linea ocupada', msg, parent = None)

	def deny_process(self, nick):
		"""
		 FUNCION: deny_process(self, nick)
		 ARGS_IN: self - variable de clase
		          nick - nombre de usuario emisor
		 DESCRIPCION: Procesa una respuesta que rechaza una llamada
		"""
		self.interface.app.is_calling = False

		# Retroalimentacion
		msg = 'El usuario {} ha rechazado tu llamada'.format(nick)
		self.interface.app.infoBox('Llamada rechazada', msg, parent = None)

	def request_process(self, msg, sock = None):
		"""
		 FUNCION: request_process(self, msg, sock = None)
		 ARGS_IN: self - variable de clase
				  msg - mensaje a procesas
				  sock - socket para el caso de recibir un call
		 DESCRIPCION: Procesa una petición TCP recibida
		"""
		msg_parse = msg.split()
		# Codigo comando
		code = msg_parse[0]

		if (code == CALL):
			# nick + port
			self.calling_process(msg_parse[1], int(msg_parse[2]))

		elif (code == RESUME):
			self.resume_process(msg_parse[1])
			
		elif (code == HOLD):
			self.hold_process(msg_parse[1])

		elif (code == END):
			self.end_process(msg_parse[1])

		elif (code == ACCEPT):
			# nick + udp port
			self.accept_process(msg_parse[1], int(msg_parse[2]))

		elif (code == BUSY):
			self.busy_process()

		elif (code == DENY):
			self.deny_process(msg_parse[1])

		#else:
			# Debug
			# print('Peticion no soportada')

	def control_listener(self):
		"""
		 FUNCION: control_listener(self)
		 ARGS_IN: self - variable de clase
		 DESCRIPCION: Bucle principal para aceptar conexiones entrantes
		"""
		# Inicializacion socket de escucha
		self.create_listen_socket()
		self.create_listen_udp_socket()
		self.finish = False
		
		while self.finish == False:
			try:
				connection_socket, addr = self.tcp_listen_socket.accept()

				request = connection_socket.recv(RESP_LEN)

				# Debug
				# print('He recibido ===> ' + request.decode())

				self.request_process(request.decode())
				
			except KeyboardInterrupt:
				self.finish = True
				break

	def end_peer(self):
		"""
		 FUNCION: end_peer(self)
		 ARGS_IN: self - variable de clase
		 DESCRIPCION: Activa el flag para terminar con el hilo de escucha ademas 
		              de cerrar el socket de escucha TCP y UDP
		"""
		self.finish = True
		self.tcp_listen_socket.close()
		self.udp_listen_socket.close()

################################################################################
# Envio TCP
################################################################################

	def create_tcp_socket(self, destName, destPort):
		"""
		 FUNCION: create_tcp_socket(self, destName, destPort)
		 ARGS_IN: self - variable de clase
				  destName - ip destino
				  destPort - puerto destino
		 DESCRIPCION: Crea un socket conectado a otro peer para transferir 
		              paquetes
		"""
		self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		try:
			self.tcp_socket.settimeout(5)
			self.tcp_socket.connect((destName, int(destPort)))
			self.tcp_socket.settimeout(None)
		except socket.error:
			self.interface.app.infoBox('Atencion', \
				'El usuario no puede atender tu llamada')
			return -1
		
	def send_request(self, request, destName, destPort):
		"""
		 FUNCION: send_request(self, request, destName, destPort)
		 ARGS_IN: self - variable de clase
		 		  request - peticion en forma de cadena
		 		  destName - direccion ip destino
		 		  destPort - puerto destino
		 DESCRIPCION: Inicializacion del socket TCP para la comunicacion de control
		 			  además del envío de peticiones por este mismo
		"""
		if (self.create_tcp_socket(destName, destPort) == -1):
			return -1

		self.tcp_socket.send(bytes(request, 'utf-8'))
		self.tcp_socket.close()

		return 0

	
	def calling(self, dest_name, tcp_port_dest):
		"""
		 FUNCION: calling(self, dst_name, tcp_port_dest)
		 ARGS_IN: self - variable de clase
		 		  dst_name - ip destinatario
		 		  tcp_port_dest - puerto tcp destinatario
		 DESCRIPCION: Comando para realizar una llamada
		"""
		# Formacion del comando correspondiente
		command = '{} {} {}'.format(CALL, self.my_nick, self.udp_port)

		# Debug
		# print('Envio ---> ' + command + ' (' + dest_name + ', ' + tcp_port_dest + ')')
		return self.send_request(command, dest_name, tcp_port_dest)

	
	def accept(self, destName, tcp_port_dest, nick):
		"""
		 FUNCION: accept(self, destName, tcp_port_dest)
		 ARGS_IN: self - variable de clase
		 	      destName - direccion envio
		 	      tcp_port_dest - puerto envio
		 DESCRIPCION: Comando para aceptar una llamada. La prepara
		"""
		command = '{} {} {}'.format(ACCEPT, self.my_nick, self.udp_port)

		# Debug
		# print('Envio ---> ' + command + ' (' + destName + ', ' + tcp_port_dest + ')')
		self.set_udp_socket()

		self.interface.prepare_call(nick)

		self.send_request(command, destName, tcp_port_dest)
		
	def deny(self, destName, tcp_port_dest):
		"""
		 FUNCION: deny(self, destName, tcp_port_dest)
		 ARGS_IN: self - variable de clase
			 	  destName - direccion envio
			 	  tcp_port_dest - puerto envio
		 DESCRIPCION: Comando para rechazar una llamada
		"""
		command = '{} {}'.format(DENY, self.my_nick)

		# Debug
		# print('Envio ---> ' + command + ' (' + destName + ', ' + tcp_port_dest + ')')

		self.send_request(command, destName, tcp_port_dest)

	def busy(self, destName, tcp_port_dest):
		"""
		 FUNCION: busy(self, destName, tcp_port_dest)
		 ARGS_IN: self - variable de clase
			 	  destName - direccion envio
			 	  tcp_port_dest - puerto envio
		 DESCRIPCION: Comando para indicar que se encuentra ocupado
		"""
		command = '{}'.format(BUSY)

		# Debug
		# print('Envio ---> ' + command + ' (' + destName + ', ' + tcp_port_dest + ')')
		self.send_request(command, destName, tcp_port_dest)

	def hold(self, destName, tcp_port_dest):
		"""
		 FUNCION: hold(self, destName, tcp_port_dest)
		 ARGS_IN: self - variable de clase
			 	  destName - direccion envio
			 	  tcp_port_dest - puerto envio
		 DESCRIPCION: Comando para pausar una llamada
		"""
		command = '{} {}'.format(HOLD, self.my_nick)
		
		# Debug
		# print('Envio ---> ' + command + ' (' + destName + ', ' + tcp_port_dest + ')')
		self.send_request(command, destName, tcp_port_dest)

	def resume(self, destName, tcp_port_dest):
		"""
		 FUNCION: resume(self, destName, tcp_port_dest)
		 ARGS_IN: self - variable de clase
			 	  destName - direccion envio
			 	  tcp_port_dest - puerto envio
		 DESCRIPCION: Comando para reanudar una llamada
		"""
		command = '{} {}'.format(RESUME, self.my_nick)
		
		# Debug
		# print('Envio ---> ' + command + ' (' + destName + ', ' + tcp_port_dest + ')')
		self.send_request(command, destName, tcp_port_dest)
	
	def end(self, destName, tcp_port_dest):
		"""
		 FUNCION: end(self, destName, tcp_port_dest)
		 ARGS_IN: self - variable de clase
		 		  destName - direccion envio
		 		  tcp_port_dest - puerto envio
		 DESCRIPCION: Comando para terminar una llamada
		"""
		command = '{} {}'.format(END, self.my_nick)
		
		# Debug
		# print('Envio ---> ' + command + ' (' + destName + ', ' + tcp_port_dest + ')')
		self.send_request(command, destName, tcp_port_dest)

		# Liberar recursos udp
		self.stop_udp()


################################################################################
# Gestion UDP
################################################################################

	def set_udp_socket(self):
		"""
	 	 FUNCION: set_udp_socket(self)
	 	 ARGS_IN: self - variable de clase
	 	 DESCRIPCION: Inicializacion del socket UDP que envia video
		"""
		self.udp_src_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self.udp_src_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

	def send_data(self, data):
		"""
	 	 FUNCION: send_data(self, data)
	 	 ARGS_IN: self - variable de clase
	 	          data - carga a enviar
	 	 DESCRIPCION: Envía por el socket adecuado el video
		"""
		self.udp_src_socket.sendto(data, (self.dest_ip, int(self.udp_port_dest)))

	def recv_data(self):
		"""
	 	 FUNCION: recv_data(self)
	 	 ARGS_IN: self - variable de clase
	 	 DESCRIPCION: Recibe por el socket adecuado el video
	 	 ARGS_OUT: carga recibida
		"""
		return self.udp_listen_socket.recv(MAX)

	def stop_udp(self):
		"""
	 	 FUNCION: stop_udp(self)
	 	 ARGS_IN: self - variable de clase
	 	 DESCRIPCION: Cierra y libera los recursos correspondientes al flujo UDP
		"""
		self.udp_src_socket.close()

		while not self.buf.empty():
			try:
				self.buf.get(False)
			except Empty:
				continue;
			self.buf.task_done()

		self.udp_src_socket = None
		self.cap.release()


# ENVIO UDP ====================================================================

	def frame_create(self):
		"""
	 	 FUNCION: frame_create(self)
	 	 ARGS_IN: self - variable de clase
	 	 DESCRIPCION: Crea un frame para su posterior envio y reproduccion local
	 	 ARGS_OUT: frame del video sin cabecera
		"""
		ret, frame = self.cap.read()
		if (ret == False or frame is None):
			return None

		# Disposicion tamanyos frame
		frame1 = cv2.resize(frame, (self.width, self.height)) # Principal

		frame2 = cv2.resize(frame, (192, 192)) # Secundario
		cv2_im = cv2.cvtColor(frame2, cv2.COLOR_BGR2RGB)
		img_tk = ImageTk.PhotoImage(Image.fromarray(cv2_im))
		self.interface.display_frame_secondary(img_tk)

		# Compresion de la imagen a enviar
		encode_param = [cv2.IMWRITE_JPEG_QUALITY, 50]
		result, encimg = cv2.imencode('.jpg', frame1, encode_param)
		
		if result == False: 
			return None
		
		return encimg.tobytes()
	
	def frame_send(self):
		"""
	 	 FUNCION: frame_send(self)
	 	 ARGS_IN: self - variable de clase
	 	 DESCRIPCION: Crea y envia un frame
		"""
		# Creacion cabecera
		num_fps = int(self.cap.get(cv2.CAP_PROP_FPS))
		msg = '{}#{}#{}x{}#{}#'.format(self.cont, time.time(), self.width, \
			self.height, num_fps)

		# Debug
		# print('Envio [frame] ---> ' + '(' + msg + ')')

		# Creacion frame
		frame = self.frame_create()

		if (frame != None):
			# Formacion paquete a enviar
			msg = bytearray(msg.encode('utf-8')) + frame
		else:
			msg = bytearray(msg.encode('utf-8'))

		self.cont += 1
		if (self.udp_src_socket != None):
			self.send_data(msg)

	def video_capture(self):
		"""
	 	 FUNCION: capturaVideo(self)
	 	 ARGS_IN: self - variable de clase
	 	 DESCRIPCION: Realiza todo el proceso para generar el video del usuario
		"""
		self.cap = cv2.VideoCapture(0)

		while (self.interface.is_calling == True):
			while (self.interface.pause == False):
				num_fps = self.cap.get(cv2.CAP_PROP_FPS)
				self.interface.set_fps(num_fps)
				self.frame_send()
				if (self.interface.is_calling == False):
					break

# Recepcion UDP ================================================================

	def frame_recv(self):
		"""
	 	 FUNCION: frame_recv(self)
	 	 ARGS_IN: self - variable de clase
	 	 DESCRIPCION: Recibe frames del interlocutor
		"""
		end = False
		empty = False
		if self.buf.empty():
			empty = True

		while end == False:
			ans = self.recv_data()

			ans_parse = ans.split(b'#')

			self.buf.put( (int(ans_parse[0]), ans) )

			if (empty == True):
				if (self.buf.full()):
					end = True
			else:
				end = True

	def frame_generate(self):
		"""
	 	 FUNCION: frame_generate(self)
	 	 ARGS_IN: self - variable de clase
	 	 DESCRIPCION: Procesa y muestra los frames recibidos realizando el control
	 	              de flujo pertinente
		"""
		if self.buf.empty():
			return

		ans = self.buf.get()[1]

		# Parseo paquete entrante
		ans_parse = ans.split(b'#', 4)
		# Obtencion resolucion
		size = ans_parse[2].split(b'x')
		self.width = int(size[0])
		self.height = int(size[1])

		encimg = ans_parse[4]

		# Debug
		# print('Recibo [frame] ---> ' + '(' + str(width) + 'x' + str(height) + ',' \
		#  + str(ans_parse[0]) + ';' + ')')
		
		# Descompresion de la imagen
		decimg = cv2.imdecode(np.frombuffer(encimg, np.uint8), 1)
		frame = cv2.resize(decimg, (self.width, self.height))
		cv2_im = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
		img_tk = ImageTk.PhotoImage(Image.fromarray(cv2_im))
		
		self.interface.display_frame_principal(img_tk)

	def video_reception(self):
		"""
	 	 FUNCION: recepcionVideo(self)
	 	 ARGS_IN: self - variable de clase
	 	 DESCRIPCION: Proceso para recibir video del interlocutor
		"""
		while (self.interface.is_calling == True): # En llamada
			while (self.interface.pause == False): # No pausada
				self.frame_recv()
				self.frame_generate()
				if (self.interface.is_calling == False):
					break
			while not self.buf.empty():
				try:
					self.buf.get(False)
				except Empty:
					continue;
