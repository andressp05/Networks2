#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <syslog.h>
#include <pthread.h>
#include <strings.h>
#include <string.h>
#include <assert.h>
#include <sys/types.h>
#include <fcntl.h>
#include <time.h>
#include <sys/socket.h>
#include "picohttpparser.h"
#include "red.h"

#define VERB_GET 101
#define VERB_POST 102
#define VERB_OPTIONS 103
#define FILE_NOT_FOUND 104
#define VERB_ERROR 100

#define EXTENSION_TEXT_PLAIN 201
#define EXTENSION_TEXT_HTML 202
#define EXTENSION_IMAGE_GIF 203
#define EXTENSION_IMAGE_JPEG 204
#define EXTENSION_VIDEO_MPEG 205
#define EXTENSION_APPLICATION_MSWORD 206
#define EXTENSION_APPLICATION_PDF 207
#define EXTENSION_SCRIPT_PYTHON 208
#define EXTENSION_SCRIPT_PHP 209
#define EXTENSION_SUBFOLDER 210
#define EXTENSION_ERROR 200

#define MAX 4096
#define TAM_PATH 512
#define TAM 64

typedef struct {
	int connfd;
	char resources_path[TAM_PATH];
	char server_name[TAM];
} Args;

/********
 FUNCION: void process_request(int conffd, char* initial_path, char* server_name)
 ARGS_IN: int conffd - descriptor devuelto al aceptar una conexion
          char* initial_path - ruta indicada en server.conf
          char* server_name - nombre del servidor indicado en el fichero de configuracion
 DESCRIPCIÓN: Procesa la petición de entrada, leyendo dicha peticion para despues llevar
              a cabo la accion correspondiente
 ARGS_OUT: void*
********/
void process_request(int conffd, char* initial_path, char* server_name);