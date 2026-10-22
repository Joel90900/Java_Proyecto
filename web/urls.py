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
]
