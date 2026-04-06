from flask import render_template
from app.blueprints.public import public_bp


@public_bp.route("/")
def home():
    return render_template("public/home.html")