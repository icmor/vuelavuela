from flask import Flask
import pathlib


def create_app(test_config=None):
    app = Flask(__name__, static_url_path='/static')
    root_path = pathlib.Path(app.root_path)
    app.config.from_mapping(SECRET_KEY='dev', DATABASE=root_path / 'db.sqlite')
    return app
