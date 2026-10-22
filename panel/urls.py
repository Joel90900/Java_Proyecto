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
    # Vehículos
    path("admin/vehiculo/nuevo", views.vehiculo_nuevo, name="admin_vehiculo_nuevo"),
    path("admin/vehiculo/crear", views.vehiculo_crear, name="admin_vehiculo_crear"),
    path("admin/vehiculo/<int:id>/editar", views.vehiculo_editar, name="admin_vehiculo_editar"),
    path("admin/vehiculo/<int:id>/eliminar", views.vehiculo_eliminar, name="admin_vehiculo_eliminar"),
    # Sensores
    path("admin/sensor/nuevo", views.sensor_nuevo, name="admin_sensor_nuevo"),
    path("admin/sensor/crear", views.sensor_crear, name="admin_sensor_crear"),
    path("admin/sensor/<int:id>/editar", views.sensor_editar, name="admin_sensor_editar"),
    path("admin/sensor/<int:id>/eliminar", views.sensor_eliminar, name="admin_sensor_eliminar"),
    # Administradores
    path("admin/usuario/nuevo", views.usuario_nuevo, name="admin_usuario_nuevo"),
    path("admin/usuario/crear", views.usuario_crear, name="admin_usuario_crear"),
    path("admin/usuario/<int:id>/editar", views.usuario_editar, name="admin_usuario_editar"),
    path("admin/usuario/<int:id>/eliminar", views.usuario_eliminar, name="admin_usuario_eliminar"),
]
