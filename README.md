# VuelaVuela
Aplicación web, basada en Flask, para mostrar el clima en dos aeropuertos
distintos. Usará web-services abiertos para obtener la información necesaria
manteniendo un caché para peticiones repetidas. Además usará una base de datos
SQLite para obtener información geográfica a partir de códigos IATA.

## Instalar
Para obtener el repositorio se puede
descargar como archivo zip desde github o clonandolo con:
```bash
git clone https://github.com/icmor/vuelavuela
```

Requisitos:
- Versión de Python >= 3.8
- Gestor de paquetes pip

Una vez con el repositorio sólo hay que moverse al directorio `vuelavuela` e
instalar las dependencias con:

```bash
pip install -r requirements.txt
```

Para correr cualquier comando se tiene que hacer desde el directorio ancestro.
Antes de correr la aplicación hay que inicializar la base de datos corriendo:

```bash
python -m flask --app vuelavuela init-db
```

Con eso ya podemos ejecutar la aplicación corriendo:

```bash
python -m flask --app vuelavuela run
```

La aplicación estará disponible en la dirección https://127.0.0.1:5000

Para correr las pruebas es necesario instalar los módulos:

```bash
pip install -r requirements_test.txt
```

y basta con correr `pytest` dentro del directorio ``vuelavuela``

## Planeación
### API
La app usará el web-service de [Open-meteo](https://api.open-meteo.com/) (el servicio
en /v1/forecast) para obtener información sobre el clima. Jugando un poco con el
API usando urllib terminé eligiendo la siguiente forma para el request:

```python
data = {"latitude": latitude,
	    "longitude": longitude,
        "forecast_days": 2,
        "timezone": "auto",
        "hourly":
        "temperature_2m,relativehumidity_2m,precipitation_probability",
        "current_weather": "true"}
```

Donde latitude y longitude son las coordenadas que obtendremos como argumentos a
la función que se comunique con el API, se obtienen dos días de pronóstico, todo
en tiempo local y el clima actual. El valor de data["hourly"] es la información
de clima que a obtener: temperatura, humedad y probabilidad de lluvia.

Habrá un archivo api.py dedicado a comunicarse con el API del clima y con
lru_cache podemos se puede crear un caché de forma bastante sencilla.
functools.lru\_cache es un caché que expulsa al miembro menos recientemente
usado. Funciona decorando una función y construyendo un caché (thread-safe) en
base a los argumentos con los que se llama la función. Podemos aprovechar esto
para agregar una fecha de expiración de una hora a las llamadas en el caché al
incluir la hora como un argumento más (probablemente sea más corto el periodo de
expiración, no queremos darle el clima de las 14:02 a alguien a las 14:59).

### Base de Datos
Como el API recibe información de cordenadas habrá que mantener una base de
datos con los códigos IATA (código único identificador de un aeropuerto) de cada
aeropuerto junto con el nombre de la ciudad donde está (para así facilitar que
el usuario pueda encontrar el aeropuerto) y su ubicación geográfica (WGS84).
Para esto es útil el dataset en
[ourairports-data](https://davidmegginson.github.io/ourairports-data/airports.csv)
para incluir la mayor cantidad de aeropuertos posibles. El esquema para la tabla
sería:

```sql
	iata_code    TEXT PRIMARY KEY,
    name         TEXT,
    municipality TEXT,
    latitude     REAL,
    longitude    REAL
```

Como vimos, el código IATA es único así que es una perfecta PRIMARY KEY, sí
sqlite arroja un error sabremos que hay un error con nuestros datos. Además de
códigos IATA, el usuario debe poder buscar el nombre de la ciudad y el nombre
del aeropuerto. Esto lo resolveremos proveyendo autocompleción en el front end
de la aplicación usando Jquery UI. Esta libreria viene con el widget
[Autocomplete](https://api.jqueryui.com/autocomplete/) al cuál le podemos
asociar un callback de javascript para proveer candidatos a compleción. Esta
función de javascript llamaría un endpoint de la aplicación por medio ajax
y realizará una busqueda de la siguiente forma:

```sql
SELECT iata_code, name, municipality from airports
WHERE iata_code LIKE ? OR name LIKE ? OR municipality LIKE ?
```

Podría usar la extensión "ft5" de sqlite para hacer fuzzy-matching ya que en
este caso sólo se hace matching básico al rodear los queries con signos
de porcentaje (sintaxis de sqlite para LIKE, equivalente al regex .*). El
problema con FTS es que la extensión no está disponible en muchas plataformas
(incluyendo mi computadora gracias Arch).

Falta un aspecto más de la base de datos, esta debe almacenar números de boletos
para saber a que aeropuertos corresponde un boleto. Para esto modificamos el csv
dataset2.csv para sólo dejar los campos num_ticket, origin y destination.
Usamos:

```emacs-lisp
(query-replace-regexp "^\(.*?\),\(.*?\),\(.*?\),.*"
	"\1, \2, \3")
```

y renombramos el archivo a tickets.csv. El esquema de la tabla en la base de datos
es:

```sql
num_ticket   TEXT PRIMARY KEY,
origin       TEXT,
destination  TEXT,
FOREIGN KEY(origin) REFERENCES airports(iata_code),
FOREIGN KEY(destination) REFERENCES airports(iata_code)
```

de nuevo como los códigos IATA son únicos la tabla va a tener constraints tipo
FOREIGN KEY ya que origin y destination deben corresponder a códigos IATA en la
otra tabla.

### Flask
El resto de la complejidad recae en organizar la aplicación web entorno a la
filosofía del framework Flask y un poco de diseño web con HTML y CSS. Para Flask
sólo tenemos que inicializar la aplicación de acuerdo a la guía en los docs y
manejar las llamadas a rutas. Por el momento tendremos sólo dos vistas, la
principal "index.html" dónde le pedimos al usuario que ingrese datos
(nombre/info del aeropuerto o ticket) y otra para mostrar el pronóstico de ambos
lugares. Esto nos dice que abrá tres rutas, para index, para ver los pronósticos y
como endpoint para el callback de autocomplete.

Para index.html usaremos un simple layout de grid CSS para tener una tabla 2x2
(4fr, 1fr) con los inputs en una columna y los botones para ingresar las formas
en otra. Para la vista de los pronósticos seguiremos el modelo card (como
bootstrap) con un contenedor estilo flex. Finalmente, el callback de autocomplete
va a llamar a una ruta que sólo reciba peticiones POST, la cuál va a llamar una función
del módulo de la base datos con el término de busqueda y regresará un diccionario json
con los resultados.

### Estructura
Considerando los módulos mencionados y las convenciones de Flask la estructura del
proyecto seguiría la siguiente plantilla:
```
├── flaskr/
│   ├── __init__.py
│   ├── db.py
│   ├── api.py
│   ├── helpers.py
│   ├── tickets.csv
│   ├── templates/
│   │   ├── index.html
│   │   └── view.html
│   └── static/
│       ├── index.css
│       ├── view.css
│       └── static/
│           ├── favicon.ico
│           └── background.jpg
│
├── tests/
│   ├── conftest.py
│   ├── data.sql
│   ├── test_factory.py
│   ├── test_api.py
│   └── test_db.py
├── .venv/
└── pyproject.toml
```
