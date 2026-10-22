"""
Autenticación propia de AutoSen (equivale a SecurityConfig y los UserDetailsService de Java).

Contraseñas: bcrypt compatible con BCryptPasswordEncoder de Spring y con los
hashes $2y$ que generó la versión PHP del proyecto.
"""
import bcrypt


def verificar_contrasena(plano: str, hash_guardado: str | None) -> bool:
    """BCryptPasswordEncoder.matches: False ante un hash vacío o inválido."""
    if not hash_guardado:
        return False
    if hash_guardado.startswith("$2y$"):
        hash_guardado = "$2b$" + hash_guardado[4:]
    try:
        return bcrypt.checkpw(plano.encode("utf-8"), hash_guardado.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def cifrar_contrasena(plano: str) -> str:
    """BCryptPasswordEncoder.encode: prefijo $2a$ y costo 10, como Spring."""
    return bcrypt.hashpw(plano.encode("utf-8"), bcrypt.gensalt(rounds=10, prefix=b"2a")).decode("ascii")
