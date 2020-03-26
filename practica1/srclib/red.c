/**************************************************************************
Fichero: red.c
Implementacion de una libreria con funciones de bajo nivel para manejar 
la gestion de red

Autores: Andrés Salas Peña - andres.salas@estudiante.uam.es
		 Francisco de Vicente Lana - francisco.vicentel@estudiante.uam.es
**************************************************************************/
#include "../includes/red.h"

/********
 FUNCION: int apertura_socket()
 ARGS_IN: -
 DESCRIPCIÓN: Encapsula la llamada a socket para su creacion
 ARGS_OUT: int - descriptor del socket
********/
int apertura_socket() {
    int desc;

    /* Creacion del socket */
    desc = socket(AF_INET, SOCK_STREAM, 0); 
    if (desc == -1) {
        return ERROR;
    }

    return desc;
}

/********
 FUNCION: int cierre_socket(int *socket)
 ARGS_IN: int* socket - descriptor del socket
 DESCRIPCIÓN: Encapsula la llamada a close para cerrar un socket
 ARGS_OUT: int - control de errores
********/
int cierre_socket(int *socket) {
    if (socket == NULL) {
        return ERROR;
    }

    /* Cierre del socket */
    if (close(*socket) == 0) {
        *socket = 0;
        return OK;
    }

    return ERROR;
}

/********
 FUNCION: void emparejar(int *socket, int puerto)
 ARGS_IN: int* socket - descriptor del socket
          int puerto - puerto de conexion
 DESCRIPCIÓN: Encapsula la llamada a bind para asignar un socket a un puerto
 ARGS_OUT: -
********/
void emparejar(int *socket, int puerto) {
	/* Estructura para configurar el emparejamiento */
	struct sockaddr_in dir;
	dir.sin_family = AF_INET;
	dir.sin_port = htons(puerto);
	dir.sin_addr.s_addr = INADDR_ANY;

	/* Asignacion del puerto al socket */
	if (bind(*socket, (struct sockaddr *) &dir, sizeof(dir)) < 0) {
		syslog(LOG_ERR, "Error en el emparejamiento");
		close(*socket);
	}

	return;
}

/********
 FUNCION: void escuchar(int socket , int max_clients)
 ARGS_IN: int socket - descriptor del socket
          int max_clients - maximo numero de conexiones simultaneas al servidor
 DESCRIPCIÓN: Encapsula la llamada a listen para escuchar peticiones
 ARGS_OUT: -
********/
void escuchar(int socket , int max_clients) {
	/* Escucha de la peticion */
	if (listen(socket, max_clients) < 0) {
		syslog(LOG_ERR, "Error en la escucha");
		close(socket);	
	}

	return;
}

/********
 FUNCION: int aceptar(int socket)
 ARGS_IN: int socket - descriptor del socket 
 DESCRIPCIÓN: Encapsula la llamada a accept para aceptar una conexion
 ARGS_OUT: int - descriptor de fichero para el socket aceptado
********/
int aceptar(int socket) {
	int desc_conexion;
	socklen_t len;
	/* Estructura para la aceptacion de una conexion */
	struct sockaddr conexion;

	len = sizeof(conexion);
	if ((desc_conexion = accept(socket, &conexion, &len)) < 0 ) {
		syslog(LOG_ERR, "Error en la aceptacion de la conexion");
		close(socket);
		return ERROR;
	}
	syslog(LOG_INFO, "Se acepta una conexion\n");

	return desc_conexion;
}

/********
 FUNCION: unsigned long resolver_dominio(char *dominio)
 ARGS_IN: char* dominio - cadena con el dominio a resolver
 DESCRIPCIÓN: Auxiliar que resuelve un dominio para conectarse
 ARGS_OUT: unsigned long - direccion resuelta
********/
unsigned long resolver_dominio(char* dominio) {
	/* Estructura para almacenar informacion del dominio */
	struct hostent *servidor;
	servidor = gethostbyname(dominio);
	if (servidor == NULL) {
		syslog(LOG_ERR, "Error en la resolucion del dominio");
		return ERROR;
	}
	
	return ((struct in_addr*)(servidor->h_addr))->s_addr;
}

/********
 FUNCION: int main(int argc, char* argv[])
 ARGS_IN: int conexion - descriptor del socket
          int puerto - puerto de conexion
          char* dominio - cadena con el dominio
 DESCRIPCIÓN: Encapsula la llamada a connect para conectar al host
 ARGS_OUT: int - control de errores
********/
int conectar(int conexion, int puerto, char* dominio) {
	struct sockaddr_in dir;
	dir.sin_family = AF_INET;
	dir.sin_port = htons(puerto);
	dir.sin_addr.s_addr = resolver_dominio(dominio);

	if (connect(conexion, (struct sockaddr *) &dir, sizeof(dir)) < 0) {
		syslog(LOG_ERR, "Error en la conexion");
		return ERROR;
	}

	return OK;
}

/********
 FUNCION: int enviar(int desc, char* buf, int size)
 ARGS_IN: int desc - descriptor del socket
          char* buf - buffer a enviar
          int size - bytes a enviar
 DESCRIPCIÓN: Encapsula la llamada a send para enviar informacion a un socket
 ARGS_OUT: int - bytes enviados
********/
int enviar(int desc, char* buf, int size) {
	if (buf == NULL || size < 0) {
		return ERROR;
	}

	return send(desc, buf, size, 0);
}

/********
 FUNCION: int leer(int desc, char* buf, int size)
 ARGS_IN: int desc - descriptor del socket
          char* buf - buffer que almacena la informacion leida
          int size - bytes a leer
 DESCRIPCIÓN: Encapsula la llamada a read para leer informacion de un socket
 ARGS_OUT: int - bytes leidos
********/
int leer(int desc, char* buf, int size) {
	if (buf == NULL || size < 0) {
		return ERROR;
	}
	
	return read(desc, buf, size);
}


/**
	Lanza un proceso de servicio
*/
// void lanzar(int conexion) {
// 	int pid;
// 	long aux;
// 	//long type;

// 	pid = fork();
// 	if (pid < 0) exit(EXIT_FAILURE);
// 	if (pid == 0) return;

// 	syslog (LOG_INFO, "Nuevo acceso");
// 	recv(conexion, &aux, sizeof(long), 0);
	
// 	//type = ntohl(aux);
// 	// database_access(connval, type, NULL);
// 	close(conexion);
// 	syslog(LOG_INFO, "Servicio existente");
// 	exit(EXIT_SUCCESS);
// }