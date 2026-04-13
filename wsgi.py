"""
wsgi.py — Point d'entrée WSGI pour production.
Utilisé par gunicorn : gunicorn wsgi:app
"""
import os
from init_db import init_db

# Initialiser la BDD si nécessaire avant le premier request
try:
    init_db()
except Exception as e:
    print(f"[WSGI] Init DB: {e}")

from app import app

if __name__ == '__main__':
    app.run()
