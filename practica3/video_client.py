""" Fichero: video_client.py
Modulo para gestionar la interfaz del video cliente
Autores: Andres Salas Penya - andres.salas@estudiante.uam.es
		 Francisco de Vicente Lana - francisco.vicentel@estudiante.uam.es
"""
import peer_skap
import discoveryServer

import sys
import time
import signal
import threading
import numpy as np
from appJar import gui
from PIL import Image, ImageTk

def signal_handler(signal, frame):
	"""
	 FUNCION: signal_handler(signal, frame)
	 ARGS_IN: signal - senyal a controlar
	 ARGS_IN: frame
	 DESCRIPCION: controla en caso de ser necesario la interrupcion por teclado
	"""
	sys.exit(0)

class VideoClient(object):
	'''
	Clase para gestionar el cliente de video. 
	'''

	def __init__(self, window_size, ds, peer):
		"""
		 FUNCION: __init__(self)
		 ARGS_IN: self - variable de clase
		 ARGS_IN: window_size - tamanyo de ventana
		 ARGS_IN: ds - instancia del discovery server
		 DESCRIPCION: inicializa la clase con ciertas especificaciones de la interfaz
		"""
		# # Creamos una variable que contenga el GUI principal
		self.app = gui("SKA-P", window_size)
		self.app.setIcon("imgs/gif/skape_main_logo.gif")
		self.app.setResizable(canResize = False)
		# # Preparacion de la interfaz
		self.app.setBg("black")
		self.app.setFg("white")
		self.app.removeAllWidgets()
		self.loginScreen()
		# Flags
		self.is_calling = False # decide si boton de llamada es para colgar o iniciar
		self.pause = False # maneja si el video esta pausado o no
		self.flag_status_bar = False # se encarga de cargar la status bar solo 1 vez
		# Variables para componentes de Status Bar
		self.duration = 0
		self.fps = 0
		self.time = "00:00:00"
		#Variables Threads
		self.t = None
		self.t_time = None # thread para contador del tiempo de status bar
		self.t_video = None # thread para controlar el video
		# # Modulos adicionales
		self.ds = ds
		self.peer = peer
		self.peer.interface = self
		# # Variables interface para comunicacion entre usuarios
		self.user1 = "imgs/gif/user1.gif"
		self.user2 = "imgs/gif/user2.gif"

		signal.signal(signal.SIGINT, signal_handler)


	def start(self):
		"""
		 FUNCION: start(self)
		 ARGS_IN: self - variable de clase
		 DESCRIPCION: comienza la aplicacion
		"""
		self.app.go()

	def checkStop(self):
		"""
		 FUNCION: checkStop(self)
		 ARGS_IN: self - variable de clase
		 DESCRIPCION: controla el boton de cierre de la ventana del programa
		"""
		self.exit_button()
		return True

	def loginScreen(self):
		"""
		 FUNCION: loginScreen(self)
		 ARGS_IN: self - variable de clase
		 DESCRIPCION: carga pantalla de inicio de la app
		"""
		# Logo Principal
		self.app.addImage("logo_login", "imgs/gif/skape_login_logo.gif", 0, 1)
		self.app.zoomImage("logo_login", -2)
		# Insercion Nick + Password
		self.app.startLabelFrame("", 1, 1)
		self.app.setSticky("ew")
		self.app.addLabel("userNick", "Nick:", 1, 1)
		self.app.addEntry("nickEnt", 1, 2)
		self.app.addLabel("userPass", "Contraseña:", 2, 1)
		self.app.addSecretEntry("passEnt", 2, 2)
		self.app.stopLabelFrame()

		self.app.addButtons(["Login", "Exit"], self.buttonsCallbackLoginScreen, 3, 1)
		self.app.setButtonImage("Login", "imgs/gif/login.gif")
		self.app.setButtonImage("Exit", "imgs/gif/exit.gif")

		self.app.setEntryFocus("nickEnt")


	def buttonsCallbackLoginScreen(self, button):
		"""
		 FUNCION: buttonsCallbackLoginScreen(self, button)
		 ARGS_IN: self - variable de clase
		 ARGS_IN: button - boton al que daremos funcionalidad
		 DESCRIPCION: maneja las tareas que se hacen al pulsar los botones de loginscreen
		"""
		#Damos funcionalidad a los botones de la primera pantalla
		if button == "Login":
			# Se cuelga la llamada
			self.nick = self.app.getEntry("nickEnt")
			self.pwd = self.app.getEntry("passEnt")
			self.app.bell()
			if self.nick == "" or self.pwd == "":
				self.app.errorBox("ERROR", "Rellena todos los campos para registrarte")
			else: 
				ret = self.ds.register(self.nick, self.peer.my_ip, peer_skap.TCP_PORT, self.pwd)
				if (ret == -1):
					self.app.errorBox('Error', 'No se admite el caracter \'#\' en el nombre')
				elif ret == discoveryServer.REG_ERROR:
					self.app.errorBox("ERROR", "Contraseña incorrecta")	
				else:
					self.peer.my_nick = self.nick
					self.app.removeAllWidgets()
					self.mainScreen()

		elif button == "Exit":
			# Salimos de la aplicación
			self.app.bell()
			self.ds.quit()
			self.app.stop()

	def mainScreen(self):
		"""
		 FUNCION: mainScreen(self)
		 ARGS_IN: self - variable de clase
		 DESCRIPCION: carga pantalla principal de la app
		"""
		#Elementos de Arriba-Abajo e Izquierda-Derecha

		# Parte Izquierda:

		# Busqueda por nick
		self.app.startLabelFrame("Buscar usuario", 1, 0)
		self.app.setSticky("ew")
		self.app.addLabel("nick_label", "Nick", 1, 0)
		self.app.addEntry("Nick", 1, 1)
		self.app.addImageButton("Search", self.buttonsCallbackMainScreen, "imgs/gif/search.gif", 1, 2)
		self.app.stopLabelFrame()

		#Listado usuarios
		self.app.addListBox("users_list", self.ds.list_users(), 2, 0)
		
		#Boton listado usuarios
		self.app.addButton("Listar Usuarios", self.buttonsCallbackMainScreen, 3,0)

		# Parte Central:

		# Logo app
		self.app.addImage("logo", "imgs/gif/skape_main_logo.gif", 0, 1)
		
		self.app.addLabel("video_title", "Transmision de Video", 1,1)
		self.app.setLabelFg("video_title", "white")
		self.app.addImage("User", self.user1, 2, 1)
		self.app.addButtons(["Call", "Play", "Pause"], self.buttonsCallbackMainScreen, 3, 1)
		self.app.setButtonImage("Call", "imgs/gif/colgar.gif")
		self.app.setButtonImage("Play", "imgs/gif/play.gif")
		self.app.setButtonImage("Pause", "imgs/gif/pause.gif")


		# Parte Derecha:

		# Datos Usuario
		self.app.startLabelFrame("Datos Personales", 1, 2)
		self.app.setSticky("ew")
		self.app.addLabel("my_nick_label", "Nick: " + self.nick, 1, 2)
		self.app.setLabelFg("my_nick_label", "white")
		self.app.stopLabelFrame()

		self.app.addImage("video", self.user2, 2, 2)
		
		# Añadir los botones		
		self.app.addButtons(["Logout", "Exit"], self.buttonsCallbackMainScreen, 3, 2)
		self.app.setButtonImage("Logout","imgs/gif/logout.gif")
		self.app.setButtonImage("Exit", "imgs/gif/exit.gif")

		# Status Bar
		if self.flag_status_bar == False:
			self.flag_status_bar = True
			self.app.addStatusbar(fields=3)
		self.app.setStatusbar(self.time, 0)
		self.app.setStatusbar("FPS: 0", 1)
		self.app.setStatusbar("Nick: ", 2)

		self.app.setEntryFocus("Nick")

		# Inicializacion de la escucha tcp para recibir llamadas
		self.t = threading.Thread(target = self.peer.control_listener)
		self.t.setDaemon(True)
		self.t.start()

	def buttonsCallbackMainScreen(self, button):
		"""
		 FUNCION: buttonsCallbackMainScreen(self)
		 ARGS_IN: self - variable de clase
		 ARGS_IN: 
		 DESCRIPCION: inicializa la clase creando y conectando el socket
		"""
		if button == "Listar Usuarios":
			self.listUsers_button()

		elif button == "Call":
			self.call_button()
					
		elif button == "Play":
			# Reanudar llamada
			self.play_button()

		elif button == "Pause":
			self.pause_button()

		elif button == "Search":
			# Entrada del nick del usuario a conectar
			self.search_button()

		elif button == "Logout":
			# Cerramos Usuario
			self.logout_button()

		elif button == "Exit":
			# Salimos de la aplicación
			self.exit_button()

	def listUsers_button(self):
		"""
		 FUNCION: listUsers_button(self)
		 ARGS_IN: self - variable de clase
		 DESCRIPCION: dota de funcionalidad al boton Listar Usuarios
		"""
		# Se listan todos los usuarios
		self.app.bell()
		self.app.clearListBox("users_list")
		self.app.addListItems("users_list", self.ds.list_users())

	def call_button(self):
		"""
		 FUNCION: call_button(self)
		 ARGS_IN: self - variable de clase
		 DESCRIPCION: dota de funcionalidad al boton Call
		"""
		self.app.bell()
		if self.is_calling == False:
			nicks = self.app.getListBox("users_list")
			if not nicks:
				self.app.errorBox("ERROR", "Ningun usuario seleccionado para llamar")
			else:
				self.nick_other = nicks[0]
				if self.nick_other == None or self.nick_other == self.nick:
					self.app.errorBox("ERROR", "Seleccione un usuario adecuado para llamar")
				else:
				#Llamando...
					ip, port = self.ds.query(self.nick_other)
					self.peer.dest_nick = self.nick_other
					self.peer.dest_ip = ip
					self.peer.send_port = port
					
					ret = self.peer.calling(ip, port)
					if (ret != -1):
						self.call_in_course()

		else:
			ip1, port1 = self.ds.query(self.peer.dest_nick)
			self.peer.end(ip1, port1)
			self.prepare_end_call()

	def prepare_call(self, nick):
		"""
		 FUNCION: prepare_call(self, nick)
		 ARGS_IN: self - variable de clase
		 		  nick - nombre del interlocutor
		 DESCRIPCION: hace los ajustes necesarios para comenzar una llamada
		"""
		self.is_calling = True
		self.t_time = threading.Thread(target=self.ini_time)
		self.t_video1 = threading.Thread(target=self.peer.video_capture)
		self.t_video2 = threading.Thread(target=self.peer.video_reception)
		self.t_video1.setDaemon(True)
		self.t_video2.setDaemon(True)
		self.t_time.setDaemon(True)
		self.t_video1.start()
		self.t_video2.start()
		self.t_time.start()
		self.app.setStatusbar("Nick: " + nick, 2)

	def prepare_end_call(self):
		"""
		 FUNCION: prepare_end_call(self)
		 ARGS_IN: self - variable de clase
		 DESCRIPCION: realiza los ajustes necesarios para terminar una llamada
		"""
		self.is_calling = False

		self.app.infoBox("Info", "La llamada con " + self.peer.dest_nick + \
			" tuvo una duracion de: " + self.time)
				
		img =  ImageTk.PhotoImage(Image.open(self.user2, "r")) 
		self.display_frame_secondary(img)
		img =  ImageTk.PhotoImage(Image.open(self.user1, "r")) 
		self.display_frame_principal(img)

		self.restart_time()

		# Actualizamos Status Bar a valores iniciales
		self.time = "00:00:00"
		self.fps = "FPS: 0"
		self.app.setStatusbar(self.time, 0)
		self.app.setStatusbar(self.fps, 1)
		self.app.setStatusbar("Nick: ", 2)
	
	def play_button(self):
		"""
		 FUNCION: play_button(self)
		 ARGS_IN: self - variable de clase
		 DESCRIPCION: dota de funcionalidad al boton Play
		"""
		self.app.bell()
		if self.is_calling == True and self.pause == True:
			self.pause = False
			ip, port = self.ds.query(self.peer.dest_nick)
			self.peer.resume(ip, port)
		else:
			self.app.errorBox("ERROR", "No puedes reanudar")

	def pause_button(self):
		"""
		 FUNCION: pause_button(self)
		 ARGS_IN: self - variable de clase
		 DESCRIPCION: dota de funcionalidad al boton Pause
		"""
		self.app.bell()
		#self.app.questionBox("Llamada entrante", "Aceptar llamada de " + self.nick, parent=None)
		if self.is_calling == True and self.pause == False:
			self.pause = True
			ip, port = self.ds.query(self.peer.dest_nick)
			self.peer.hold(ip, port)
			self.app.infoBox("Info", "Video pausado")
		else:
			self.app.errorBox("Error", "No puedes pausar")

	def search_button(self):
		"""
		 FUNCION: search_button(self)
		 ARGS_IN: self - variable de clase
		 DESCRIPCION: dota de funcionalidad al boton Search
		"""
		self.app.bell()
		self.nick_search = self.app.getEntry("Nick")
		if self.nick_search == "":
			# lista entera
			self.app.clearListBox("users_list")
			self.app.addListItems("users_list", self.ds.list_users())
		else:
			ret1, ret2 = self.ds.query(self.nick_search)
			if (ret1 != None) and (ret2 != None):
				# actualizar lista
				self.app.clearListBox("users_list")
				self.app.addListItem("users_list", self.nick_search)
			else:
				# lista como estaba
				self.app.errorBox("ERROR", "Nick no encontrado")

	def logout_button(self):
		"""
		 FUNCION: logout_button(self)
		 ARGS_IN: self - variable de clase
		 DESCRIPCION: dota de funcionalidad al boton Logout
		"""
		self.app.bell()
		# Colgar en caso de teenr una llamada abierta
		if self.is_calling == True:
			self.call_button()
		self.restart_time()
		self.peer.end_peer()
		self.app.clearStatusbar()
		self.app.removeAllWidgets()
		self.loginScreen()

	def exit_button(self):
		"""
		 FUNCION: exit_button(self)
		 ARGS_IN: self - variable de clase
		 DESCRIPCION: dota de funcionalidad al boton Exit
		"""
		self.app.bell()
		if self.is_calling == True:
			self.call_button()
		self.ds.quit()
		self.peer.end_peer()
		self.app.stop()

	def display_frame_secondary(self, img):
		"""
		 FUNCION: display_frame_secondary(self, img)
		 ARGS_IN: self - variable de clase
		 		  img - imagen a mostrar
		 DESCRIPCION: muestra imagenes en el panel secundario
		"""
		# Lo mostramos en el GUI
		self.app.setImageData("video", img, fmt = 'PhotoImage')

	def display_frame_principal(self, img):
		"""
		 FUNCION: display_frame_principal(self, img)
		 ARGS_IN: self - variable de clase
		 		  img - imagen a mostrar
		 DESCRIPCION: muestra imagenes en el panel principal
		"""
		# Lo mostramos en el GUI
		self.app.setImageData("User", img, fmt = 'PhotoImage')

	def set_fps(self, num_fps):
		"""
		 FUNCION: set_fps(self, num_fps)
		 ARGS_IN: self - variable de clase
		 		  num_fps - frames por segundo del video
		 DESCRIPCION: indica los fps del video reproducido
		"""
		self.fps = "FPS: " + str(num_fps)
		self.app.setStatusbar(self.fps, 1)
			
	def setImageResolution(self, resolution):		
		"""
		 FUNCION: setImageResolution(self, resolution)
		 ARGS_IN: self - variable de clase
		 ARGS_IN: resolution - resolucion de la imagen
		 DESCRIPCION: establece la resolucion de la imagen
		"""
		# Se establece la resolución de captura de la webcam
		# Puede añadirse algún valor superior si la cámara lo permite
		# pero no modificar estos
		if resolution == "LOW":
			self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 160) 
			self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 120) 
		elif resolution == "MEDIUM":
			self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320) 
			self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240) 
		elif resolution == "HIGH":
			self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640) 
			self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480) 

	def ini_time(self):
		"""
		 FUNCION: ini_time(self)
		 ARGS_IN: self - variable de clase
		 DESCRIPCION: inicia el contador de llamada
		"""
		while self.is_calling == True:
			if self.pause == False:
				self.update_time()
				self.app.setStatusbar(self.time, 0)

	def update_time(self):
		"""
		 FUNCION: update_time(self)
		 ARGS_IN: self - variable de clase
		 DESCRIPCION: actualiza el tiempo segundo a segundo
		"""
		time.sleep(1)
		self.duration += 1
		secs = self.duration
		mins = 0
		hours = 0
		if secs >= 60:
			secs = self.duration % 60
			mins = self.duration // 60
			if mins >= 60:
				mins = mins % 60
				hours = mins // 60
		self.time = str(hours) + ":" + str(mins) + ":" + str(secs)

	def restart_time(self):
		"""
		 FUNCION: restart_time(self)
		 ARGS_IN: self - variable de clase
		 DESCRIPCION: reinicia el reloj
		"""
		self.duration = 0
		self.pause = False

	def call_in_course(self):
		"""
		 FUNCION: call_in_course(self)
		 ARGS_IN: self - variable de clase
		 DESCRIPCION: llamada en curso
		"""
		self.app.infoBox("Llamando...","Llamando a " + self.nick_other +"(" + self.peer.send_port + ")", parent = None)


if __name__ == '__main__':
	'''
	Main de la clase
	'''
	# Creacion de las clases necesarias
	ds = discoveryServer.My_socket()
	peer = peer_skap.My_peer()
	vc = VideoClient("1000x700", ds, peer)
	# Comienzo de la interfaz
	vc.start()