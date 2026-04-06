from flask import Blueprint

apuestas_bp = Blueprint("apuestas", __name__)

from . import routes