from flask import Flask
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)
app.secret_key = "verySecretKey"

# Configures session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Sets up database
engine = create_engine("postgresql://localhost/sherryzhang")
db = scoped_session(sessionmaker(bind=engine))

from app import routes  # noqa: E402
