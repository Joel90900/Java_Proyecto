"""python manage.py importar_mysql <archivo.sql> [--limpiar]"""
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from core.importador import ErrorImportacion, importar


class Command(BaseCommand):
    help = "Importa a PostgreSQL los datos de un dump de phpMyAdmin de la base MySQL 'vehiculos'."

    def add_arguments(self, parser):
        parser.add_argument("archivo", help="Ruta del dump .sql exportado con phpMyAdmin")
        parser.add_argument("--limpiar", action="store_true", help="Borra los datos actuales antes de importar")

    def handle(self, *args, archivo, limpiar, **opciones):
        ruta = Path(archivo)
        if not ruta.is_file():
            raise CommandError(f"No existe el archivo {ruta}.")
        avisos = []
        try:
            conteos = importar(ruta.read_text(encoding="utf-8-sig"), limpiar=limpiar, avisos=avisos)
        except ErrorImportacion as error:
            raise CommandError(str(error)) from error
        for aviso in avisos:
            self.stderr.write(aviso)
        for tabla, cantidad in conteos.items():
            self.stdout.write(f"{tabla}: {cantidad}")
        self.stdout.write(self.style.SUCCESS("Importación terminada."))
