from django.urls import path

from panel import views

urlpatterns = [
    path("admin", views.index, name="admin_index"),
    path("admin/login", views.login, name="admin_login"),
    path("admin/logout", views.logout, name="admin_logout"),
    path("admin/nosotros", views.nosotros, name="admin_nosotros"),
    # Clientes
    path("admin/cliente/<int:id>/estado", views.cliente_estado, name="admin_cliente_estado"),
    path("admin/cliente/nuevo", views.cliente_nuevo, name="admin_cliente_nuevo"),
    path("admin/cliente/crear", views.cliente_crear, name="admin_cliente_crear"),
    path("admin/cliente/<int:id>/editar", views.cliente_editar, name="admin_cliente_editar"),
    path("admin/cliente/<int:id>/eliminar", views.cliente_eliminar, name="admin_cliente_eliminar"),
    # Administradores
    path("admin/usuario/nuevo", views.usuario_nuevo, name="admin_usuario_nuevo"),
    path("admin/usuario/crear", views.usuario_crear, name="admin_usuario_crear"),
    path("admin/usuario/<int:id>/editar", views.usuario_editar, name="admin_usuario_editar"),
    path("admin/usuario/<int:id>/eliminar", views.usuario_eliminar, name="admin_usuario_eliminar"),
]
