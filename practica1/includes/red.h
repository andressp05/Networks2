/**************************************************************************
Fichero: red.h

Autores: Andrés Salas Peña - andres.salas@estudiante.uam.es
		 Francisco de Vicente Lana - francisco.vicentel@estudiante.uam.es
**************************************************************************/
#include <pthread.h>
#include <stdio.h>
#include <unistd.h>
#include <sys/types.h>
#include <stdlib.h> 
#include <syslog.h>
#include <sys/socket.h>
#include <netdb.h>

/* Macros de control de errores */
#define OK 0
#define ERROR -1

/********
 FUNCION: int apertura_socket()
 ARGS_IN: -
 DESCRIPCIÓN: Encapsula la llamada a socket para su creacion
 ARGS_OUT: int - descriptor del socket
********/
int apertura_socket();

/********
 FUNCION: int cierre_socket(int *socket)
 ARGS_IN: int* socket - descriptor del socket
 DESCRIPCIÓN: Encapsula la llamada a close para cerrar un socket
 ARGS_OUT: int - control de errores
********/
int cierre_socket(int *desc_cliente);

/********
 FUNCION: void emparejar(int *socket, int puerto)
 ARGS_IN: int* socket - descriptor del socket
          int puerto - puerto de conexion
 DESCRIPCIÓN: Encapsula la llamada a bind para asignar un socket a un puerto
 ARGS_OUT: -
********/
void emparejar(int *socket, int puerto);

/********
 FUNCION: void escuchar(int socket , int max_clients)
 ARGS_IN: int socket - descriptor del socket
          int max_clients - maximo numero de conexiones simultaneas al servidor
 DESCRIPCIÓN: Encapsula la llamada a listen para escuchar peticiones
 ARGS_OUT: -
********/
void escuchar(int socket , int max_clients);

/********
 FUNCION: int aceptar(int socket)
 ARGS_IN: int socket - descriptor del socket 
 DESCRIPCIÓN: Encapsula la llamada a accept para aceptar una conexion
 ARGS_OUT: int - descriptor de fichero para el socket aceptado
********/
int aceptar(int socket);

/********
 FUNCION: int main(int argc, char* argv[])
 ARGS_IN: int conexion - descriptor del socket
          int puerto - puerto de conexion
          char* dominio - cadena con el dominio
 DESCRIPCIÓN: Encapsula la llamada a connect para conectar al host
 ARGS_OUT: int - control de errores
********/
int conectar(int conexion, int puerto, char *dominio);

/********
 FUNCION: int enviar(int desc, char* buf, int size)
 ARGS_IN: int desc - descriptor del socket
          char* buf - buffer a enviar
          int size - bytes a enviar
 DESCRIPCIÓN: Encapsula la llamada a send para enviar informacion a un socket
 ARGS_OUT: int - bytes enviados
********/
int enviar(int desc, char* buf, int size);

/********
 FUNCION: int leer(int desc, char* buf, int size)
 ARGS_IN: int desc - descriptor del socket
          char* buf - buffer que almacena la informacion leida
          int size - bytes a leer
 DESCRIPCIÓN: Encapsula la llamada a read para leer informacion de un socket
 ARGS_OUT: int - bytes leidos
********/
int leer(int desc, char* buf, int size);