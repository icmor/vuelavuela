from . import db
from flask import Flask, render_template
import pathlib


def create_app(test_config=None):
    app = Flask(__name__, static_url_path='/static')
    root_path = pathlib.Path(app.root_path)
    app.config.from_mapping(SECRET_KEY='dev', DATABASE=root_path / 'db.sqlite')
    if test_config is None:
        app.config.from_pyfile('config.py', silent=True)
    else:
        app.config.from_mapping(test_config)
    db.init_app(app)

    @app.route("/")
    def index():
        return render_template("index.html")

    return app
