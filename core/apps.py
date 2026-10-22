from django.apps import AppConfig


class CoreConfig(AppConfig):
    name = "core"
    verbose_name = "Núcleo: modelos, autenticación, utilidades y patrones"

    def ready(self):
        # Suscribe el observador de alertas (patrón Observer).
        from core.patrones.observador import alerta_critica, atender_alerta_critica

        alerta_critica.connect(atender_alerta_critica, dispatch_uid="atender_alerta_critica")
