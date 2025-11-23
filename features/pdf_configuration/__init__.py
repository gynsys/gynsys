# features/pdf_configuration/__init__.py
from . import handlers

def register(app):
    handlers.register(app)