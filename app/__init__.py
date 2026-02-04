from flask import Flask
from dotenv import load_dotenv
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

load_dotenv()
app = Flask(__name__)
app.config.from_object("app.config.Config")
app.secret_key = app.config["SECRET_KEY"]

# Configures session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_FILE_DIR"] = "flask_session_data"
Session(app)

# Sets up database
engine = create_engine(app.config["DATABASE_URL"])
db = scoped_session(sessionmaker(bind=engine))

from app import routes  # noqa: E402
