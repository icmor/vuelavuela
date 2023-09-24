from flask import g, current_app
import click
import csv
import pathlib
import sqlite3
import urllib.request


class DBError(Exception):
    pass


def get_db():
    # flask's threading model only allows a single connection per-request
    if 'db' not in g:
        g.db = sqlite3.connect(current_app.config['DATABASE'])
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(e=None):
    if db := g.pop('db', None):
        db.close()


def init_db():
    try:
        setup_tables()
        populate_airports()
        populate_tickets()
    except DBError as err:
        print(err)
        current_app.config['DATABASE'].unlink()


def setup_tables():
    """ Setup the database tables:
    airports: iata_code, municipality, latitude, longitude, elevation
    tickets: num_ticket, origin, destination """
    db = get_db()
    db.execute("DROP TABLE IF EXISTS airports;")
    db.execute("DROP TABLE IF EXISTS tickets;")

    # iata_codes guaranteed to be unique
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
            # using only generators to avoid loading everything into memory
            db.executemany("INSERT into airports VALUES(?,?,?,?,?)", rows)
            db.commit()
    except urllib.error.URLError:
        raise DBError("Error while trying to fetch airport data.")


def populate_tickets():
    db = get_db()
    tickets = pathlib.Path(current_app.root_path) / "tickets.csv"
    if not tickets.exists():
        raise DBError("File missing: tickets.csv")
    try:
        with open(tickets) as f:
            reader = csv.reader(f)
            db.executemany("INSERT into tickets VALUES(?,?,?)",
                           (row for row in reader))
            db.commit()
    except csv.Error:
        raise DBError("Error while trying to read tickets.csv.")


@click.command('init-db')
def init_db_command():
    init_db()
    click.echo('Initialized the database.')


def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
