import os
import tempfile
import sqlite3

import pytest
from vuelavuela import create_app
from vuelavuela.db import get_db, init_db


@pytest.fixture
def app():
    db_fd, db_path = tempfile.mkstemp()

    app = create_app({
        'TESTING': True,
        'DATABASE': db_path,
    })

    with app.app_context():
        init_db()
        db = get_db()
        try:
            db.execute(""" INSERT into airports VALUES('LAX', '
            Los Angeles / Tom Bradley International Airport', 'Los Angeles',
            33.942501, -118.407997); """)
            db.execute(""" INSERT into airports VALUES('MEX', 'Aeropuerto
            Internacional Lic. Benito Juárez', 'Ciudad de México', 19.435433,
            -99.082432); """)
            db.commit()
        except sqlite3.IntegrityError: # ignore PRIMARY KEY constraint
            pass

    yield app
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def runner(app):
    return app.test_cli_runner()
