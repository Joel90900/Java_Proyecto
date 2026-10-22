from django.urls import path

from api import views

urlpatterns = [
    path("api/auth/register", views.registrar, name="api_registrar"),
    path("api/auth/login", views.login, name="api_login"),
    path("api/cliente/<str:correo>", views.datos_cliente, name="api_datos_cliente"),
    path("api/vehiculos/crear", views.crear_vehiculo, name="api_crear_vehiculo"),
    path("api/bluetooth/simular", views.simular, name="api_simular"),
    path("api/obd2/lecturas", views.guardar_lectura, name="api_obd2_lecturas"),
    path("api/obd2/vehiculo/<int:id>/elm", views.elm, name="api_obd2_elm"),
    path("api/obd2/historial/<int:id_vehiculo>", views.historial, name="api_obd2_historial"),
    path("api/obd2/alertas/<int:id_vehiculo>", views.alertas, name="api_obd2_alertas"),
    path("api/obd2/ultima/<int:id_vehiculo>", views.ultima, name="api_obd2_ultima"),
    path("api/obd2/conectar", views.conectar, name="api_obd2_conectar"),
]
