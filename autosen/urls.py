"""Rutas raíz de AutoSen: cada app declara sus rutas completas (sin barra final, como en Java)."""
from django.urls import include, path

urlpatterns = [
    path("", include("web.urls")),
    path("", include("panel.urls")),
    path("", include("reportes.urls")),
    path("", include("api.urls")),
]
