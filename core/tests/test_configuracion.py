from django.conf import settings
from django.db import connection
from django.test import TestCase


class ConfiguracionTests(TestCase):
    def test_base_de_datos_es_postgresql(self):
        self.assertEqual(connection.vendor, "postgresql")

    def test_ajustes_de_fidelidad(self):
        self.assertFalse(settings.USE_TZ)
        self.assertEqual(settings.TIME_ZONE, "America/Bogota")
        self.assertEqual(settings.LANGUAGE_CODE, "es")
        self.assertFalse(settings.APPEND_SLASH)
        self.assertEqual(settings.SESSION_COOKIE_AGE, 1800)
        self.assertTrue(settings.SESSION_SAVE_EVERY_REQUEST)
        self.assertTrue(settings.SESSION_EXPIRE_AT_BROWSER_CLOSE)
        self.assertNotIn("django.contrib.auth", settings.INSTALLED_APPS)
        self.assertNotIn("django.contrib.admin", settings.INSTALLED_APPS)
        for host in ("localhost", "127.0.0.1", "10.0.2.2"):
            self.assertIn(host, settings.ALLOWED_HOSTS)
        self.assertEqual(settings.STATIC_URL, "/static/")
        self.assertTrue(settings.WHITENOISE_USE_FINDERS)
