from django.urls import path

from api import views

urlpatterns = [
    path("api/auth/register", views.registrar, name="api_registrar"),
    path("api/auth/login", views.login, name="api_login"),
    path("api/cliente/<str:correo>", views.datos_cliente, name="api_datos_cliente"),
    path("api/vehiculos/crear", views.crear_vehiculo, name="api_crear_vehiculo"),
    path("api/bluetooth/simular", views.simular, name="api_simular"),
]
