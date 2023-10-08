from .db import get_db


def get_ticket_iata(num_ticket):
    """Función para obtener el código IATA del origen y destino de un vuelo
    en base al número de ticket.
    """
    db = get_db()
    return db.execute(
        "SELECT origin, destination from tickets "
        "WHERE num_ticket = ?", (num_ticket,)).fetchone()


def get_iata_location(location):
    """Función para obtener las coordenadas geográficas de un aeropuerto a
    partir de su código IATA.
    """
    db = get_db()
    return db.execute(
        "SELECT latitude, longitude from airports WHERE iata_code = ?",
        (location,)
    ).fetchone()
