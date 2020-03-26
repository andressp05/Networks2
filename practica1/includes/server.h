/**************************************************************************
Fichero: servidor.h

Autores: Andrés Salas Peña - andres.salas@estudiante.uam.es
		 Francisco de Vicente Lana - francisco.vicentel@estudiante.uam.es
**************************************************************************/
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <syslog.h>
#include <pthread.h>
#include <strings.h>
#include <string.h>
#include "red.h"
#include "http.h"
#include "confuse.h"