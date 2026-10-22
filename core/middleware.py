"""
TemaMiddleware: equivale a TemaFilter de Java.

Inyecta en toda página HTML el botón de tema claro/oscuro, su CSS y su script,
reemplazando cada "</body>" (salvo que la página ya incluya theme-toggle.js).
"""

SNIPPET = (
    '<link rel="stylesheet" href="/static/css/light-mode.css">'
    '<button type="button" class="theme-toggle theme-btn" '
    'aria-label="Cambiar tema claro/oscuro" '
    'style="position:fixed;bottom:20px;right:20px;z-index:9999;background:#1a1a1e;'
    "border:1px solid #2a2a2e;color:#e6e6e6;padding:8px 16px;border-radius:8px;"
    "font-size:12px;font-weight:700;cursor:pointer;font-family:monospace;"
    'box-shadow:0 4px 12px rgba(0,0,0,.3);">🌙</button>'
    '<script src="/static/js/theme-toggle.js"></script>'
    "</body>"
)


class TemaMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        respuesta = self.get_response(request)
        if respuesta.streaming or "text/html" not in respuesta.get("Content-Type", ""):
            return respuesta
        html = respuesta.content.decode("utf-8")
        if "</body>" in html and "theme-toggle.js" not in html:
            respuesta.content = html.replace("</body>", SNIPPET).encode("utf-8")
            respuesta["Content-Length"] = str(len(respuesta.content))
        return respuesta
