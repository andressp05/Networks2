OurVIPServer
============

CreativeCommons **(CC)** 2018, Andres Salas Peña (&&res) y Francisco Vicente Lana (p4Ko), Versión 2  

OurVIPServer es un servidor básico educativo que soporta los verbos *get, post y options*, creado para la realización de la primera práctica de la asignatura de Redes 2.

Ejecución OurVIPServer
----------------------
Aunque se incluye en el sexto subapartado de la wiki, aquí se deja una guía para ejecutar nuestro servidor: 
* Modifique el fichero de configuración, concretamente el parametro server_root poniendo la ruta hasta donde se haya descargado el código.
* Tras esto, basta con hacer make y ejecutar el ./server que se genera.
* Una vez hecho lo anterior, el servidor se encontrará corriendo en modo demonio. 
* Para establecer conexiones con el mismo y comprobar su correcto funcionamiento, deberá o bien abrir una terminal telnet localhost 8081 e introducir ahí su petición o bien abrir el navegador y poner http://localhost:8081/subfolder/multimedia/imagenes/pinguino.gif.
Esto último es un ejemplo, se puede cambiar el número del puerto en el fichero de configuración al igual que ir navegando por los distintos recursos adjuntados.
* Los scripts de prueba se adjuntan en el directorio /recursos/scripts. Allí encontrá dos carpetas, una con los scripts php y otra con los de python. Cada una de ellas contienen scripts de prueba para get y post.