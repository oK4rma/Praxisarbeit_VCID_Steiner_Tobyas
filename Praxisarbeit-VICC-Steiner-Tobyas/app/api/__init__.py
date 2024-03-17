from flask import Blueprint

bp = Blueprint("api", __name__)
from app.api import tokens, errors, vehicles, accounting, reservations  # noqa: E402, F401