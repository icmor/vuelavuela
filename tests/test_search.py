# import pytest
from vuelavuela.db import search


def test_search_iata(app):
    with app.app_context():
        assert search("MEX")
        assert search("ME")
        assert search("LAX")
        assert search("AX")
        assert not search("FSOC")


def test_search_name(app):
    with app.app_context():
        assert search("Felipe Áng")
        assert search("nacional")
        assert search("KeNnEdY")
        assert not search("BADAIRPORT")


def test_search_municipality(app):
    with app.app_context():
        assert search("Cancún")
        assert search("Cozumel")
        assert search("Tulum")
        assert not search("Terabithia")
