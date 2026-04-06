import os


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "clave-super-segura")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "sqlite:///polla_mundialista.db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False