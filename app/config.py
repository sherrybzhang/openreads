import os

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "verySecretKey")
    DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://localhost/sherryzhang")
