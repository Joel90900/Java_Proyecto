"""Rutas raíz de AutoSen: cada app declara sus rutas completas (sin barra final, como en Java)."""
from django.urls import include, path

urlpatterns = [
    path("", include("web.urls")),
    path("", include("panel.urls")),
    path("", include("reportes.urls")),
    path("", include("api.urls")),
]

handler400 = "core.errores.error_400"
handler403 = "core.errores.error_403"
handler404 = "core.errores.error_404"
handler500 = "core.errores.error_500"
