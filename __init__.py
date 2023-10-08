from . import db
from .api import get_forecast
from .helpers import get_ticket_iata, get_iata_location
from flask import Flask, flash, jsonify, redirect
from flask import render_template, request, url_for
from string import Template
import pathlib


def create_app(test_config=None):
    """Función principal de Flask, crea y configura la aplicación registrando
    métodos con sus rutas asociadas.
    """
    app = Flask(__name__, static_url_path='/static')
    root_path = pathlib.Path(app.root_path)
    app.config.from_mapping(DATABASE=root_path / 'db.sqlite3')
    if test_config is None:
        app.config.from_pyfile('config.py', silent=True)
    else:
        app.config.from_mapping(test_config)
    db.init_app(app)

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/search_airports")
    def search_airports():
        return jsonify(db.search(request.args.get("term")))

    @app.route("/climate", methods=("GET", "POST"))
    def climate():
        """Función para mostrar el clima. Si recibe un GET request redirecciona
        al index. Al recibir un POST checa si recibió un número de ticket o dos
        códigos IATA. Obtiene las coordenadas correspondientes, con estas
        obtiene los pronósticos usando las funciones en api.py y muestra
        view.html usando los datos obtenidos.
        """
        if request.method == "GET":
            return redirect(url_for("index"))

        if (num_ticket := request.form.get("num_ticket")):
            if not (locations := get_ticket_iata(num_ticket)):
                s = Template("No se encontró el ticket: $ticket")
                flash(s.substitute(ticket=num_ticket))
                return redirect(url_for("index"))
            origin, dest = locations
        else:
            origin, dest = request.form["origin"], request.form["dest"]

        if not (origin_coord := get_iata_location(origin)):
            s = Template("No se encontró el aeropuerto: $iata_code")
            flash(s.substitute(iata_code=origin))
            return redirect(url_for("index"))
        if not (dest_coord := get_iata_location(dest)):
            s = Template("No se encontró el aeropuerto: $iata_code")
            flash(s.substitute(iata_code=dest))
            return redirect(url_for("index"))

        forecast = {origin: get_forecast(*origin_coord),
                    dest: get_forecast(*dest_coord)}

        return render_template("view.html", forecast=forecast,
                               origin=origin, dest=dest)

    return app
