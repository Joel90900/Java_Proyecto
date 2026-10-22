from django.urls import path

from core import errores
from web import views

urlpatterns = [
    path("", views.inicio, name="inicio"),
    path("nosotros", views.nosotros, name="nosotros"),
    path("login", views.login, name="login"),
    path("logout", views.logout, name="logout"),
    path("register", views.register, name="register"),
    path("error", errores.pagina_error, name="error"),
    path("dashboard", views.dashboard, name="dashboard"),
    path("vehiculos", views.mis_vehiculos, name="vehiculos"),
    path("sensores", views.sensores, name="sensores"),
    path("vehiculos/crear", views.vehiculo_crear, name="vehiculo_crear"),
    path("vehiculos/<int:id>/editar", views.vehiculo_editar, name="vehiculo_editar"),
    path("vehiculos/<int:id>/eliminar", views.vehiculo_eliminar, name="vehiculo_eliminar"),
]
