from flask import g, current_app
import click
import csv
import pathlib
import sqlite3
import urllib.request


class DBInitError(Exception):
    """Clase de error base para la inicialización de la base de datos"""
    pass


def get_db():
    """Función para obtener una conección a la base de datos desde un request
    de Flask. Es necesaria ya que el modelo de threading de Flask sólo permite
    una conección por thread. Retorna un objeto sqlite3.Connection
    """
    if 'db' not in g:
        g.db = sqlite3.connect(current_app.config['DATABASE'])
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(e=None):
    """Función teardown para que Flask pueda cerrar la base de datos"""
    if db := g.pop('db', None):
        db.close()


def init_db():
    """Función para inicializar la base de datos y popularla con información de
    aeropuertos y tickets de vuelo.
    """
    try:
        setup_tables()
        populate_airports()
        populate_tickets()
    except DBInitError as err:
        current_app.config['DATABASE'].unlink()
        raise err


def setup_tables():
    """Función para configurar las tablas de la base de datos con las columnas:
    airports: iata_code, municipality, latitude, longitude, elevation
    tickets: num_ticket, origin, destination
    """
    db = get_db()
    db.execute("DROP TABLE IF EXISTS airports;")
    db.execute("DROP TABLE IF EXISTS tickets;")

    db.execute("""
    CREATE TABLE airports (
    iata_code    TEXT PRIMARY KEY,
    name         TEXT,
    municipality TEXT,
    latitude     REAL,
    longitude    REAL
    );
    """)

    db.execute("""
    CREATE TABLE tickets (
    num_ticket   TEXT PRIMARY KEY,
    origin       TEXT,
    destination  TEXT,
    FOREIGN KEY(origin) REFERENCES airports(iata_code),
    FOREIGN KEY(destination) REFERENCES airports(iata_code)
    );
    """)
    db.commit()


def populate_airports():
    """Función para llenar la tabla airports con información tomada de
    OurAirports.
    """
    url = "https://davidmegginson.github.io/ourairports-data/airports.csv"
    db = get_db()
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            reader = csv.DictReader(row.decode("utf-8") for row in response)
            rows = ((row["iata_code"],
                     row["name"],
                     row["municipality"],
                     row["latitude_deg"],
                     row["longitude_deg"])
                    for row in reader if row["iata_code"])
            db.executemany("INSERT into airports VALUES(?,?,?,?,?)", rows)
            db.commit()
    except urllib.error.URLError:
        raise DBInitError("Error while trying to fetch airport data.")


def populate_tickets():
    """Función para llenar la tabla tickets a partir del archivo tickets.csv"""
    db = get_db()
    tickets = pathlib.Path(current_app.root_path) / "tickets.csv"
    if not tickets.exists():
        raise DBInitError("File missing: tickets.csv")
    try:
        with open(tickets) as f:
            reader = csv.reader(f)
            db.executemany("INSERT into tickets VALUES(?,?,?)",
                           (row for row in reader))
            db.commit()
    except csv.Error:
        raise DBInitError("Error while trying to read tickets.csv.")


def search(term):
    """Función para buscar la base de datos en las columnas de código IATA,
    nombre del aeropuerto y/o localidad.
    """
    db = get_db()
    results = []
    term = '%' + term + '%'
    for row in db.execute(
            "SELECT iata_code, name, municipality from airports WHERE "
            "iata_code LIKE ? OR  name LIKE ? or municipality LIKE ?",
            (term, term, term)
    ):
        results.append({"value": row["iata_code"],
                        "label": row["iata_code"] + ': '
                        + row["name"] + ' - ' + row["municipality"]})
    return results


@click.command('init-db')
def init_db_command():
    """Comando para inicializar la base de datos"""
    init_db()
    click.echo('Initialized the database.')


def init_app(app):
    """Registra close_db como función teardown e init_db como comando para la
    línea de comandos.
    """
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
