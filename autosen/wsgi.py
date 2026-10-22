"""Punto de entrada WSGI de AutoSen."""
import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "autosen.settings")

application = get_wsgi_application()
