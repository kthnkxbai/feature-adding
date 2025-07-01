
import pytest
from app import app, db 

@pytest.fixture(scope="session")
def flask_app():
    """
    Fixture that provides a Flask app instance for tests.
    Connects to an existing MariaDB database for read-only operations.
    No schema creation or deletion is performed.
    """
    app.config["TESTING"] = True
   
    app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://YOUR_USERNAME:YOUR_PASSWORD@YOUR_HOST:YOUR_PORT/YOUR_DATABASE_NAME"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["WTF_CSRF_ENABLED"] = False

    with app.app_context():
       
        yield app

   
