from django.urls import path

from panel import views

urlpatterns = [
    path("admin/login", views.login, name="admin_login"),
    path("admin/logout", views.logout, name="admin_logout"),
]
