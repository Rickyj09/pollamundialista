from flask import Blueprint

jornadas_bp = Blueprint("jornadas", __name__)

from . import routes