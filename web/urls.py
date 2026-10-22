from django.urls import path

from core import errores

urlpatterns = [
    path("error", errores.pagina_error, name="error"),
]
