from .db import get_db


def get_ticket_iata(num_ticket):
    db = get_db()
    return db.execute(
        "SELECT origin, destination from tickets "
        "WHERE num_ticket = ?", (num_ticket,)).fetchone()


def get_iata_location(location):
    db = get_db()
    return db.execute(
        "SELECT latitude, longitude from airports WHERE iata_code = ?",
        (location,)
    ).fetchone()
