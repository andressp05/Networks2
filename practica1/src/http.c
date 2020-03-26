/**************************************************************************
Fichero: http.c
Se encarga de procesar peticiones, realizando el parseo http y generando las
respuestas adecuadas.

Autores: Andrés Salas Peña - andres.salas@estudiante.uam.es
		 Francisco de Vicente Lana - francisco.vicentel@estudiante.uam.es
**************************************************************************/
#include "../includes/http.h"

/********
 FUNCION: int is_supported_verb(char *method)
 ARGS_IN: char* method - metodo pedido
 DESCRIPCIÓN: comprueba si el verbo indicado esta soportado y de que que tipo se 
              trata
 ARGS_OUT: int - Tipo de verbo
********/
int is_supported_verb(char* method) {
	if (strcmp(method, "GET") == 0) {
		return VERB_GET;
	}
	else if (strcmp(method, "POST") == 0) {
		return VERB_POST;
	}
	else if (strcmp(method, "OPTIONS") == 0) {
		return VERB_OPTIONS;
	}
	return VERB_ERROR; /* No es uno de los verbos soportados */
}

/********
 FUNCION: void path_precess(char* path, char* ext, char* first_path, char* args)
 ARGS_IN: char* path - ruta solicitada (copia)
          char* ext - almacena la extension sin punto
          char* first_path - string anterior a '?' en scripts
          char* args - string posterior a '?' en scripts
 DESCRIPCIÓN: dada una ruta obtiene la extension del fichero solicitado. Además para
              scripts separa la parte de ruta y la de argumentos.
              Modifica path por lo que es reomendable pasar una copia
 ARGS_OUT: void
********/
void path_process(char* path, char* ext, char* first_path, char* args) {
   char delimitador[] = "?";
   char* delimitador_ext = ".";
   char* ret;
   char* argumentos;
   char path_real[512];
   char extension[256];
   char* token;

   if (!path || !ext || !first_path || !args) {
      syslog(LOG_ERR, "error en los argumentos de entrada de path_process\n");
      return;
   }

   /* Separacion por el signo de interrogacion para sciprts */
   ret = strtok(path, delimitador);
   argumentos = strtok(NULL, delimitador);
   if (argumentos != NULL) {    /* Hay '?' */
      strcpy(path_real, ret);
      strcpy(first_path, ret);
      strcpy(args, argumentos);
   }
   else {                       /* No hay '?' */
      strcpy(path_real, path);
      strcpy(first_path, path);
   }

   /* Obtencion de la extension de la ruta */
   token = strtok(path_real, delimitador_ext);
   while(token != NULL) {
      strcpy(extension, token);
      token = strtok(NULL, delimitador_ext);
   }
   strcpy(ext, extension);
}

/********
 FUNCION: int is_supported_extension(char *extension)
 ARGS_IN: char* extension - extension a comprobar
 DESCRIPCIÓN: comprueba si la extension indicada esta soportada y devuelve 
              de que que tipo se trata
 ARGS_OUT: int - Tipo de extension
********/
int is_supported_extension(char* extension) {
	if (strcmp(extension, "txt") == 0) {
		return EXTENSION_TEXT_PLAIN; /* text/plain */
	}
	else if ((strcmp(extension, "html") == 0) || (strcmp(extension, "htm") == 0)) {
		return EXTENSION_TEXT_HTML; /* text/html */
	}
	else if (strcmp(extension, "gif") == 0) {
		return EXTENSION_IMAGE_GIF; /* image/gif */
	}
	else if ((strcmp(extension, "jpeg") == 0) || (strcmp(extension, "jpg") == 0)) {
		return EXTENSION_IMAGE_JPEG; /* image/jpeg */
	}
	else if ((strcmp(extension, "mpeg") == 0) || (strcmp(extension, "mpg") == 0)) {
		return EXTENSION_VIDEO_MPEG; /* video/mpeg */
	}
	else if ((strcmp(extension, "doc") == 0) || (strcmp(extension, "docx") == 0)) {
		return EXTENSION_APPLICATION_MSWORD; /* application/msword */
	}
	else if (strcmp(extension, "pdf") == 0) {
		return EXTENSION_APPLICATION_PDF; /* application/pdf */
	}
	else if (strcmp(extension, "py") == 0) {
		return EXTENSION_SCRIPT_PYTHON; /* text/html */
	}
	else if (strcmp(extension, "php") == 0) {
		return EXTENSION_SCRIPT_PHP; /* text/html */
	}
	else if (extension[strlen(extension) - 1] == '/') {
			return EXTENSION_SUBFOLDER; /* subfolder */
	}
	else { /* No es ninguna de las extensiones soportadas */
		return EXTENSION_ERROR; 
	}
}

/********
 FUNCION: void options_response(int conffd, char* path, int ext, int minor_version, char* server_name)
 ARGS_IN: int conffd - descriptor devuelto al aceptar una conexion
 		  char* path - ruta del archivo
 		  int ext - extension del fichero solicitado
          int minor_version - version http, 0 o 1
          char* server_name - nombre del servidor indicado en el conf
 DESCRIPCIÓN: elabora la respuesta a una peticion options
 ARGS_OUT: void
********/
void options_response(int conffd, char* path, int ext, int minor_version, char* server_name) {
	char http_version[32];     /* Variables para la linea de estado */
	char minor_version_aux[4];
	int status_code;
	char reason_phrase[32];

	char date[128];            /* Variables para la cabecera */
	char content_type[32];
	off_t content_length = 0;
	char allow[128];

	char buffer[MAX];          /* buffer para leer de fichero y enviar al socket */

	/* Linea de estado */
	strcpy(http_version, "HTTP/1.");
	sprintf(minor_version_aux, "%d", minor_version);
	strcat(http_version, minor_version_aux);

	status_code = 200;
	strcpy(reason_phrase, "Ok");
	
	/* Cabecera Date */
	time_t t = time(NULL);
	struct tm *my_date = gmtime(&t);
	strftime(date, sizeof(date), "%a, %d %b %Y %H:%M:%S GMT", my_date);

	/* Cabecera de Content-Type */
	if (strcmp(path, "*") == 0) {
		strcpy(allow, "GET POST OPTIONS");
		strcpy(content_type, "No path specified");	
	}
	else {
		switch(ext) {
			case EXTENSION_TEXT_PLAIN:
				strcpy(allow, "GET OPTIONS");
				strcpy(content_type, "text/plain");
				break;
			case EXTENSION_TEXT_HTML:
				strcpy(allow, "GET OPTIONS");
				strcpy(content_type, "text/html");
				break;
			case EXTENSION_IMAGE_GIF:
				strcpy(allow, "GET OPTIONS");
				strcpy(content_type, "image/gif");
				break;
			case EXTENSION_IMAGE_JPEG:
				strcpy(allow, "GET OPTIONS");
				strcpy(content_type, "image/jpeg");
				break;
			case EXTENSION_VIDEO_MPEG:
				strcpy(allow, "GET OPTIONS");
				strcpy(content_type, "video/mpeg");
				break;
			case EXTENSION_APPLICATION_MSWORD:
				strcpy(allow, "GET OPTIONS");
				strcpy(content_type, "application/msword");
				break;
			case EXTENSION_APPLICATION_PDF:
				strcpy(allow, "GET OPTIONS");
				strcpy(content_type, "application/pdf");
				break;
			case EXTENSION_SCRIPT_PYTHON:
				strcpy(allow, "GET POST OPTIONS");
				strcpy(content_type, "script");
				break;
			case EXTENSION_SCRIPT_PHP:
				strcpy(allow, "GET POST OPTIONS");
				strcpy(content_type, "script");
				break;
			case EXTENSION_SUBFOLDER:
				strcpy(allow, "GET POST OPTIONS");
				strcpy(content_type, "folder");
				break;
			default:
				syslog(LOG_ERR, "No deberia llegar nunca (extension en options)\n");
		}
	}

	/* Respuesta final */
	sprintf(buffer, "%s %d %s\r\nDate: %s\r\nServer: %s\r\nContent-Length: %ld\r\n"
		"Content-Type: %s\r\nAllow: %s\r\nConnection: close\r\n\r\n", http_version, status_code, 
		reason_phrase, date, server_name, content_length, content_type, allow);

	enviar(conffd, buffer, strlen(buffer)*sizeof(char));

	return;
} 

/********
 FUNCION: void post_response(int conffd, char* path, int ext, int minor_version, int desc, char* args, char* server_name)
 ARGS_IN: char* conffd - descriptor devuelto al aceptar una conexion
          char* path - ruta del archivo
          int ext - extension del fichero solicitado
          int minor_version - version http, 0 o 1
          int desc - descriptor del fichero a leer
          char* args - argumentos recibidos en el body de la peticion
          char* server_name - nombre del fichero recibido por server.conf
 DESCRIPCIÓN: elabora la respuesta a una peticion post
 ARGS_OUT: void
********/
void post_response(int conffd, char* path, int ext, int minor_version, int desc, char* args, char* server_name) {
	char date[128];               /* Variables para la cabecera */
	char content_type[32];
	struct stat file_info;
	off_t content_length = 0;
	char date_modif[128];
	
	char http_version[32];        /* Variables para la linea de estado */
	int status_code;
	char reason_phrase[32];
	char minor_version_aux[4];
	
	ssize_t readen = 1;           /* Variables para el envio de la respuesta */
	char response[MAX];
	char body[MAX];

	char comando[MAX];            /* Variables para la ejecucion de scripts */
	FILE *salida;

	/* Linea de estado */
	strcpy(http_version, "HTTP/1.");
	sprintf(minor_version_aux, "%d", minor_version);
	strcat(http_version, minor_version_aux);

	status_code = 200;
	strcpy(reason_phrase, "OK");

	/* Cabecera Date */
	time_t t = time(NULL);
	struct tm *my_date = gmtime(&t);
	strftime(date, sizeof(date), "%a, %d %b %Y %H:%M:%S GMT", my_date);

	/* Cabecera de Last-Modified y Content-Length */
	fstat(desc, &file_info);
	struct tm *my_date_modif = gmtime(&(file_info.st_mtime));
	strftime(date_modif, sizeof(date_modif), "%a, %d %b %Y %H:%M:%S GMT", my_date_modif);

	/* Cabecera de Content-Type */
	switch(ext) {
		case EXTENSION_SCRIPT_PYTHON:
			strcpy(content_type, "text/html");
			break;
		case EXTENSION_SCRIPT_PHP:
			strcpy(content_type, "text/html");
			break;
		default:
			syslog(LOG_ERR, "No deberia llegar nunca (extension post)\n");
	}

	/* Ejecucion de scripts */
	if (ext == EXTENSION_SCRIPT_PYTHON) {
		sprintf(comando, "echo %s | python %s", args, path);
	}
	else {
		sprintf(comando, "echo %s | php %s", args, path);
	}
	/* Apertura del fichero donde se redirige la salida del script */
	memset(body, 0, sizeof(body));
	salida = popen(comando, "r");
	readen = fread(body, 1, MAX, salida);
	content_length = readen;

	/* Envio de la respuesta*/
	sprintf(response, "%s %d %s\r\nDate: %s\r\nServer: %s\r\nLast-Modified: %s\r\nContent-Length: %ld\r\n"
		"Content-Type: %s\r\n\r\n%s\r\n", http_version, status_code, reason_phrase, date, server_name, 
		date_modif, content_length, content_type, body);

	enviar(conffd, response, strlen(response)*sizeof(char));
	
	/* Cierre de ficheros */
	pclose(salida);

	return;
}

/********
 FUNCION: void get_response(char* buffer, char* path, int ext, int minor_version)
 ARGS_IN: int conffd - descriptor devuelto al aceptar una conexion
          char* path - ruta del archivo
          int ext - extension del fichero solicitado
          int minor_version - version http, 0 o 1
          int desc - descriptor del fichero a leer
          char* args - argumentos recibidos en el path de la peticion
          char* server_name - nombre del fichero recibido por server.conf
 DESCRIPCIÓN: elabora la respuesta a una peticion get
 ARGS_OUT: void
********/
void get_response(int conffd, char* path, int ext, int minor_version, int desc, char* args, char* server_name) {
	char date[128];               /* Variables para la cabecera */
	char content_type[32];
	struct stat file_info;
	off_t content_length = 0;
	char date_modif[128];
	
	char http_version[32];        /* Variables para la linea de estado */
	int status_code;
	char reason_phrase[32];
	char minor_version_aux[4];
	
	ssize_t readen = 1;           /* Variables para el envio de la respuesta */
	char request_msg_hdr[MAX];
	char body[MAX];

	char comando[MAX];            /* Variables para la ejecucion de scripts */
	FILE *salida;
	int flag_script = 0; /* 0 si no es script, 1 en caso contrario */

	/* Linea de estado */
	strcpy(http_version, "HTTP/1.");
	sprintf(minor_version_aux, "%d", minor_version);
	strcat(http_version, minor_version_aux);

	status_code = 200;
	strcpy(reason_phrase, "OK");

	/* Cabecera Date */
	time_t t = time(NULL);
	struct tm *my_date = gmtime(&t);
	strftime(date, sizeof(date), "%a, %d %b %Y %H:%M:%S GMT", my_date);

	/* Cabecera de Last-Modified y Content-Length */
	fstat(desc, &file_info);
	struct tm *my_date_modif = gmtime(&(file_info.st_mtime));
	strftime(date_modif, sizeof(date_modif), "%a, %d %b %Y %H:%M:%S GMT", my_date_modif);

	content_length = file_info.st_size;

	/* Cabecera de Content-Type */
	switch(ext) {
		case EXTENSION_TEXT_PLAIN:
			strcpy(content_type, "text/plain");
			break;
		case EXTENSION_TEXT_HTML:
			strcpy(content_type, "text/html");
			break;
		case EXTENSION_IMAGE_GIF:
			strcpy(content_type, "image/gif");
			break;
		case EXTENSION_IMAGE_JPEG:
			strcpy(content_type, "image/jpeg");
			break;
		case EXTENSION_VIDEO_MPEG:
			strcpy(content_type, "video/mpeg");
			break;
		case EXTENSION_APPLICATION_MSWORD:
			strcpy(content_type, "application/msword");
			break;
		case EXTENSION_APPLICATION_PDF:
			strcpy(content_type, "application/pdf");
			break;
		case EXTENSION_SCRIPT_PYTHON:
			strcpy(content_type, "text/html");
			break;
		case EXTENSION_SCRIPT_PHP:
			strcpy(content_type, "text/html");
			break;
		default:
			syslog(LOG_ERR, "No deberia llegar nunca (extension get)\n");
	}

	/* Ejecucion de scripts */
	if ((ext == EXTENSION_SCRIPT_PYTHON) || (ext == EXTENSION_SCRIPT_PHP)) {
		if (ext == EXTENSION_SCRIPT_PYTHON) {
			sprintf(comando, "python %s \"%s\"", path, args);
		}
		else {
			sprintf(comando, "php %s \"%s\"", path, args);
		}
		flag_script = 1;
		salida = popen(comando, "r");
		readen = fread(body, 1, MAX, salida);
		content_length = readen;
	}

	/* Envio de la cabecera */
	sprintf(request_msg_hdr, "%s %d %s\r\nDate: %s\r\nServer: %s\r\nLast-Modified: %s\r\nContent-Length: %ld\r\n"
		"Content-Type: %s\r\n\r\n", http_version, status_code, reason_phrase, date, server_name, 
		date_modif, content_length, content_type);

	enviar(conffd, request_msg_hdr, strlen(request_msg_hdr)*sizeof(char));

	/* Envio del fichero pertinente dentro del body */
	if (flag_script == 0) {
		/* Fichero solicitado, envio fragmentado */
		while (readen > 0) {
			readen = leer(desc, body, sizeof(body));
			if (readen == 0) {
				strcat(body, "\n");
				enviar(conffd, body, strlen(body)*sizeof(char));
				break;
			}
			enviar(conffd, body, readen);
			memset(body, 0, sizeof(body));
		}
	}
	else {
		/* Envio de la salida dada por el script */
		enviar(conffd, body, readen);
		
		pclose(salida);
	}

	return;
}

/********
 FUNCION: void bad_request_response(int conffd, int ext, int minor_version, char *server_name)
 ARGS_IN: int conffd - descriptor devuelto al aceptar una conexion
          int ext - extension del fichero solicitado
          int minor_version - version http, 0 o 1
          char* server_name - nombre del fichero recibido por server.conf
 DESCRIPCIÓN: elabora la respuesta a una peticion mal formulada
 ARGS_OUT: void
********/
void bad_request_response(int conffd, int ext, int minor_version, char *server_name) {
	char http_version[32];      /* Variables para la linea de estado */
	int status_code;
	char reason_phrase[32];
	char minor_version_aux[4];

	char date[128];             /* Variables para la cabecera */
	char content_type[32];

	char body[MAX];             /* Varibles para el envio de la respuesta */
	char buffer[MAX];

	/* Linea de estado */
	strcpy(http_version, "HTTP/1.");
	sprintf(minor_version_aux, "%d", minor_version);
	strcat(http_version, minor_version_aux);

	status_code = 400;
	strcpy(reason_phrase, "Bad Request");

	/* Cabecera Date */
	time_t t = time(NULL);
	struct tm *my_date = gmtime(&t);
	strftime(date, sizeof(date), "%a, %d %b %Y %H:%M:%S GMT", my_date);

	/* Cabecera de Content-Type */
	strcpy(content_type, "text/html");

	/* Body */
	strcpy(body, "<!DOCTYPE HTML PUBLIC \"-//IETF//DTD HTML 2.0//EN\"><HTML><HEAD>"
		"<TITLE>400 Bad Request</TITLE></HEAD><BODY><H1>400 Bad Request</H1>"
	    "The request can not be parsed successfully.<P>"
	    "</BODY></HTML>");

	/* Respuesta final */
	sprintf(buffer, "%s %d %s\r\nDate: %s\r\nServer: %s\r\nContent-type: %s\r\nConnection: close\r\n\r\n%s\r\n",
	       http_version, status_code, reason_phrase, date, server_name, content_type, body);

	enviar(conffd, buffer, strlen(buffer)*sizeof(char));

	return;
}

/********
 FUNCION: void not_found_response(int conffd, int ext, int minor_version, char *server_name)
 ARGS_IN: int conffd - descriptor devuelto al aceptar una conexion
          int ext - extension del fichero solicitado
          int minor_version - version http, 0 o 1
          char* server_name - nombre del fichero recibido por server.conf
 DESCRIPCIÓN: elabora la respuesta a una peticion cuyo fichero solicitado no se encuentra
 ARGS_OUT: void
********/
void not_found_response(int conffd, int ext, int minor_version, char* server_name) {
	char http_version[32];   /* Variables para la linea de estado */
	int status_code;
	char reason_phrase[32];
	char minor_version_aux[4];

	char date[128];          /* Variables para cabecera */
	char content_type[32];

	char body[MAX];          /* Varibles para enviar la respuesta */
	char buffer[MAX];

	/* Linea de estado */
	strcpy(http_version, "HTTP/1.");
	sprintf(minor_version_aux, "%d", minor_version);
	strcat(http_version, minor_version_aux);

	status_code = 404;
	strcpy(reason_phrase, "Not Found");

	/* Cabecera Date */
	time_t t = time(NULL);
	struct tm *my_date = gmtime(&t);
	strftime(date, sizeof(date), "%a, %d %b %Y %H:%M:%S GMT", my_date);

	/* Cabecera de Content-Type */
	strcpy(content_type, "text/html");

	/* Body */
	strcpy(body, "<!DOCTYPE HTML PUBLIC \"-//IETF//DTD HTML 2.0//EN\"><html><head>"
		"<title>404 Not Found</title></head><body><h1>404 Not Found</h1>"
		"<p>The requested URL was not found on this server.</p></body></html>");

	/* Respuesta final */
	sprintf(buffer, "%s %d %s\r\nDate: %s\r\nServer: %s\r\nContent-type: %s\r\nConnection: close\r\n\r\n%s\r\n",
	       http_version, status_code, reason_phrase, date, server_name, content_type, body);

	enviar(conffd, buffer, strlen(buffer)*sizeof(char));

	return;
}

/********
 FUNCION: void not_allowed_response(int conffd, int ext, int minor_version, char *server_name)
 ARGS_IN: int conffd - descriptor devuelto al aceptar una conexion
          int ext - extension del fichero solicitado
          int minor_version - version http, 0 o 1
          char* server_name - nombre del fichero recibido por server.conf
 DESCRIPCIÓN: elabora la respuesta a una peticion con un verbo erroneo
 ARGS_OUT: void
********/
void not_allowed_response(int conffd, int ext, int minor_version, char* server_name) {
	char http_version[32];   /* Variables para la linea de estado */
	int status_code;
	char reason_phrase[32];
	char minor_version_aux[4];

	char date[128];          /* Variables para cabecera */
	char content_type[32];

	char body[MAX];          /* Varibles para enviar la respuesta */
	char buffer[MAX];

	/* Linea de estado */
	strcpy(http_version, "HTTP/1.");
	sprintf(minor_version_aux, "%d", minor_version);
	strcat(http_version, minor_version_aux);

	status_code = 405;
	strcpy(reason_phrase, "Not Allowed");

	/* Cabecera Date */
	time_t t = time(NULL);
	struct tm *my_date = gmtime(&t);
	strftime(date, sizeof(date), "%a, %d %b %Y %H:%M:%S GMT", my_date);

	/* Cabecera de Content-Type */
	strcpy(content_type, "text/html");

	/* Body */
	strcpy(body, "<!DOCTYPE HTML PUBLIC \"-//IETF//DTD HTML 2.0//EN\"><html><head>"
		"<title>405 Not Allowed</title></head><body><h1>405 Not Allowed</h1>"
		"<p>The requested URL was not allowed on this server.</p></body></html>");

	/* Respuesta final */
	sprintf(buffer, "%s %d %s\r\nDate: %s\r\nServer: %s\r\nContent-type: %s\r\nConnection: close\r\n\r\n%s\r\n",
	       http_version, status_code, reason_phrase, date, server_name, content_type, body);

	enviar(conffd, buffer, strlen(buffer)*sizeof(char));

	return;
}

/********
 FUNCION: void process_request(int conffd, char* initial_path, char* server_name)
 ARGS_IN: int conffd - descriptor devuelto al aceptar una conexion
          char* initial_path - ruta indicada en server.conf
          char* server_name - nombre del servidor indicado en el fichero de configuracion
 DESCRIPCIÓN: Procesa la petición de entrada, leyendo dicha peticion para despues llevar
              a cabo la accion correspondiente
 ARGS_OUT: void
********/
void process_request(int conffd, char* initial_path, char* server_name) {
	char buffer[MAX];                  /* Variables de parseo */
	const char *method, *path;
	int ret_parse, minor_version = 1;
	struct phr_header headers[TAM];
	size_t buflen = 0, prevbuflen = 0, method_len, path_len, num_headers;
	ssize_t ret_read;
	int our_version = 0; /* Este servidor trabaja con HTTP/1.0 */
	
	int verb = VERB_ERROR;  /* Varibles para manejar el verbo */
	char just_verb[TAM]; 

	char just_path[MAX];    /* Variables para manejar la ruta y la extension */
	char total_path[MAX];
	char total_path_aux[MAX];
	char real_path[MAX];
	int ext = EXTENSION_ERROR;
	char extension[TAM];
	
	char args[MAX];         /* Variables para recibir argumentos de scripts */
	char args_post[MAX];
	
	int desc;               /* Descriptor del fichero a leer */

	while (1) {
    	/* Lectura de la peticion */
    	while ((ret_read = read(conffd, buffer + buflen, sizeof(buffer) - buflen)) == -1);
    	if (ret_read <= 0) {
    		syslog(LOG_ERR, "Error leyedo la peticion\n");
        	return;
    	}

    	prevbuflen = buflen;
    	buflen += ret_read;

    	/* parseo de la peticion */
    	num_headers = sizeof(headers) / sizeof(headers[0]);

    	ret_parse = phr_parse_request(buffer, buflen, &method, &method_len, 
    		&path, &path_len, &minor_version, headers, &num_headers, prevbuflen);
    	if (ret_parse > 0) { /* peticion parseada con exito */
        	break; 
    	}
    	else if (ret_parse == -1) {
    	    syslog(LOG_ERR, "Error en el parseo de la peticion\n");
    	    bad_request_response(conffd, ext, our_version, server_name);

    	    return; /* Se responde con bad request y termina el procesado */
    	}
    	assert(ret_parse == -2);
    	if (buflen == sizeof(buffer)) {
        	return;
    	}
	}

    /* Comprobacion verbo */
	sprintf(just_verb, "%.*s", (int)method_len, method);
	verb = is_supported_verb(just_verb);

	/* Comprobacion path */
	sprintf(just_path, "%.*s", (int)path_len, path);
	strcpy(total_path, initial_path);
	strcat(total_path, just_path);
		
	strcpy(total_path_aux, total_path);
	path_process(total_path_aux, extension, real_path, args);
	ext = is_supported_extension(extension);

	/* Apertura de fichero a leer */
	if (verb == VERB_GET && ext == EXTENSION_SUBFOLDER) {
		strcat(real_path, "index.html");
	}

	if (verb != VERB_OPTIONS || (ext != EXTENSION_SUBFOLDER && ext != EXTENSION_ERROR)) {
		desc = open(real_path, O_RDONLY);
		if (desc == -1) {
			syslog(LOG_ERR, "Error abriendo el fichero pedido\n");
			verb = FILE_NOT_FOUND;
		}
	}
	/* El verbo post no se puede aplicar sobre ficheros que no sean scripts */
	if (verb == VERB_POST && (ext != EXTENSION_SCRIPT_PYTHON && ext != EXTENSION_SCRIPT_PHP)) {
		verb = VERB_ERROR;
	}

	/* Obtencion de los argumentos para post */
	sprintf(args_post, "%s", buffer + ret_parse);
	
	memset(buffer, 0, sizeof(buffer));

	switch(verb) {
		case VERB_GET:
			get_response(conffd, real_path, ext, our_version, desc, args, server_name);
			break;
		case VERB_POST:
			post_response(conffd, real_path, ext, our_version, desc, args_post, server_name);
			break;
		case VERB_OPTIONS:
			options_response(conffd, just_path, ext, our_version, server_name);
			break;
		case FILE_NOT_FOUND:
			not_found_response(conffd, ext, our_version, server_name);
			break;
		case VERB_ERROR:
			not_allowed_response(conffd, ext, our_version, server_name);
			break;
		default:
			syslog(LOG_ERR, "No deberia llegar aqui (process_request)");
	}

	if (verb != VERB_OPTIONS || (ext != EXTENSION_SUBFOLDER && ext != EXTENSION_ERROR)) {
		close(desc);
	}

	return;
}