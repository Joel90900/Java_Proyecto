import bcrypt
from django.test import SimpleTestCase

from core.auth import cifrar_contrasena, verificar_contrasena


class ContrasenasTests(SimpleTestCase):
    def test_cifrar_produce_2a_costo_10(self):
        h = cifrar_contrasena("clave123")
        self.assertTrue(h.startswith("$2a$10$"))
        self.assertEqual(len(h), 60)
        self.assertTrue(verificar_contrasena("clave123", h))

    def test_verificar_acepta_prefijos_2a_2b_2y(self):
        h = bcrypt.hashpw(b"clave123", bcrypt.gensalt(rounds=4)).decode()
        for prefijo in ("$2a$", "$2b$", "$2y$"):
            self.assertTrue(verificar_contrasena("clave123", prefijo + h[4:]), prefijo)
        self.assertFalse(verificar_contrasena("otra", h))

    def test_hash_invalido_devuelve_false(self):
        self.assertFalse(verificar_contrasena("x", "no-es-un-hash"))
        self.assertFalse(verificar_contrasena("x", None))
        self.assertFalse(verificar_contrasena("x", ""))
