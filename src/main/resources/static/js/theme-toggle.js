/* ============================================================
   CAMBIO DE TEMA CLARO/OSCURO — AutoSen
   Alterna el atributo data-theme de <html> y lo persiste en
   localStorage para que se recuerde entre páginas.
   ============================================================ */
(function () {
    var root = document.documentElement;
    var KEY = 'autosen-theme';

    // Al cargar, aplica el tema guardado
    if (localStorage.getItem(KEY) === 'light') {
        root.setAttribute('data-theme', 'light');
    }

    function esClaro() {
        return root.getAttribute('data-theme') === 'light';
    }

    function actualizarIconos() {
        var icono = esClaro() ? '☀️' : '🌙';
        document.querySelectorAll('.theme-toggle').forEach(function (btn) {
            btn.textContent = icono;
        });
    }

    function aplicar(light) {
        if (light) {
            root.setAttribute('data-theme', 'light');
            localStorage.setItem(KEY, 'light');
        } else {
            root.removeAttribute('data-theme');
            localStorage.setItem(KEY, 'dark');
        }
        actualizarIconos();
    }

    document.querySelectorAll('.theme-toggle').forEach(function (btn) {
        btn.addEventListener('click', function () {
            aplicar(!esClaro());
        });
    });

    actualizarIconos();
})();