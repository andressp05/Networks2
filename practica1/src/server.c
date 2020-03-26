/**************************************************************************
Fichero: server.c
Se encarga de llevar a cabo la funcionalidad más a alto nivel de la práctica

Autores: Andrés Salas Peña - andres.salas@estudiante.uam.es
		 Francisco de Vicente Lana - francisco.vicentel@estudiante.uam.es
**************************************************************************/
#include "../includes/server.h"

/********
 FUNCION: int demonizar(char * cadena)
 ARGS_IN: char* service - identificador del servicio
 DESCRIPCIÓN: pasa la ejecucion del servidor a modo demonio
 ARGS_OUT: void
********/
int demonizar(char * service) {
	pid_t pid;

	pid = fork();                    /* Creacion de un proceso hijo */
	if (pid < 0) exit(EXIT_FAILURE); /* Error en fork */
	if (pid > 0) exit(EXIT_SUCCESS); /* Eliminacion del proceso padre */

	umask(0); /* Cambia la máscara de modo de ficheros */

	setlogmask(LOG_UPTO(LOG_INFO)); /* Apertura del log del sitema */
	openlog("Sistema de mensajes del servidor:", LOG_CONS | LOG_PID | LOG_NDELAY, LOG_LOCAL3);
	syslog(LOG_ERR, "Inicializando [%s]", service);
	
	if (setsid() < 0) { /* creacion de un nuevo SID para el proceso */
		syslog (LOG_ERR, "Error en la creacion de un sid para el proceso hijo");
		return ERROR;
	}
	if ((chdir("/")) < 0) { /* Establece el directorio raiz como directorio de trabajo */
		syslog (LOG_ERR, "Error al cambiar el directorio actual = \"/\"");
		return ERROR;
	}

	close(STDIN_FILENO);  /* Cierre de los descriptores de fichero que pueda haber abiertos */
	close(STDOUT_FILENO); 
	close(STDERR_FILENO); 

	syslog(LOG_INFO, "Demonizacion finalizada\n"); 
	return OK;
}

/********
 FUNCION: int demonizar(char * cadena)
 ARGS_IN: int port - puerto de conexion
          int max_clients - maximo numero de conexiones simultaneas al servidor
 DESCRIPCIÓN: Auxiliar para llamar a socket, bind y listen para configurar un socket
 ARGS_OUT: int - descriptor del socket creado
********/
int conf_socket(int port, int max_clients) {
	int socket;

	socket = apertura_socket();
	if (socket == ERROR) {
		syslog(LOG_ERR, "Error en la apertura del socket");
		return ERROR;
	}
	emparejar(&socket, port);
	escuchar(socket, max_clients);

	return socket;
}

/********
 FUNCION: void* doit(void* arg)
 ARGS_IN: void* args - estructura con los argumentos que el procesado necesita
 DESCRIPCIÓN: Funcion auxiliar para manejar el proceso que se le asigna a cada
 			  hilo para que procese una peticion
 ARGS_OUT: void* -
********/
void* doit(void* arg) {
	Args* argumentos; /* Casting de los argumentos */
	argumentos = (Args *)arg;
	
	pthread_detach(pthread_self());
	/* Procesado de la peticion */
	process_request(argumentos->connfd, argumentos->resources_path, argumentos->server_name);
	
	/* Se termina la conexion */
	close(argumentos->connfd);

	return(NULL);
}

/********
 FUNCION: int main(int argc, char* argv[])
 ARGS_IN: int argc - numero de argumentos de entrada
          int char* argv[] - argumentos de entrada
 DESCRIPCIÓN: Funcion principal del programa. Se encarga de la inicializacion del 
              entorno y realizar las llamadas pertinentes para crear los threads, 
              leer el fichero de configuracion, aceptar un soket y quedar a la 
              escucha de una conexion
 ARGS_OUT: int - control de errores
********/
int main(int argc, char* argv[]) {
	
	int listenfd, connfd; /* Descriptores de conexion e identificacion de threads*/
	pthread_t tid;
	Args args; 
	
	long listen_port;     /* Variables del fichero de configuracion */
	long max_clients;
	char* server_root = NULL;
	char* server_signature = NULL;

	/* Configuracion del servidor */
	cfg_opt_t opts[] = {
        CFG_SIMPLE_STR("server_root", &server_root),
        CFG_SIMPLE_INT("max_clients", &max_clients),
        CFG_SIMPLE_INT("listen_port", &listen_port),
        CFG_SIMPLE_STR("server_signature", &server_signature),
        CFG_END()
    };
    cfg_t* cfg;
    cfg = cfg_init(opts, 0);
    if (cfg_parse(cfg, "server.conf") == CFG_PARSE_ERROR) {
    	return EXIT_FAILURE;
    }

	/* Contiene las llamadas a socket(), bind() y listen() */
	listenfd = conf_socket(cfg_getint(cfg, "listen_port"), cfg_getint(cfg, "max_clients"));
	if (listenfd == ERROR) {
		return EXIT_FAILURE;
	}
	
	/* Demoniza el programa y abre syslog */
	if (demonizar("Server - Redes 2") == -1) {
		syslog(LOG_ERR, "demonizacion fallida\n");
	    return EXIT_FAILURE;	
	}

	strcpy(args.resources_path, cfg_getstr(cfg, "server_root"));
	strcpy(args.server_name, cfg_getstr(cfg, "server_signature"));

	/* Bucle de escucha para nuevas conexiones */
	for ( ; ; ) {
		/* Aceptacion de conexion */
		connfd = aceptar(listenfd);
		if (connfd == ERROR) {
			syslog(LOG_ERR, "Error en la aceptacion de la conexion");
			continue;
		}
		args.connfd = connfd;
		
		/* Crea un hilo por cada peticion para procesarla */
		pthread_create(&tid, NULL, &doit, (void *) &args);
	}

	/* Nunca se debe llegar aqui */
	return EXIT_SUCCESS;
}