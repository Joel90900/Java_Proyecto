package com.example.sensores_vsc.config;

import jakarta.servlet.Filter;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.ServletOutputStream;
import jakarta.servlet.ServletRequest;
import jakarta.servlet.ServletResponse;
import jakarta.servlet.WriteListener;
import jakarta.servlet.http.HttpServletResponse;
import jakarta.servlet.http.HttpServletResponseWrapper;
import org.springframework.stereotype.Component;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.OutputStreamWriter;
import java.io.PrintWriter;
import java.nio.charset.StandardCharsets;

            
@Component
public class TemaFilter implements Filter {

    private static final String SNIPPET =
        "<link rel=\"stylesheet\" href=\"/css/light-mode.css\">" +
        "<button type=\"button\" class=\"theme-toggle theme-btn\" " +
        "aria-label=\"Cambiar tema claro/oscuro\" " +
        "style=\"position:fixed;bottom:20px;right:20px;z-index:9999;background:#1a1a1e;" +
        "border:1px solid #2a2a2e;color:#e6e6e6;padding:8px 16px;border-radius:8px;" +
        "font-size:12px;font-weight:700;cursor:pointer;font-family:monospace;" +
        "box-shadow:0 4px 12px rgba(0,0,0,.3);\">🌙</button>" +
        "<script src=\"/js/theme-toggle.js\"></script>" +
        "</body>";

    @Override
    public void doFilter(ServletRequest req, ServletResponse res, FilterChain chain)
            throws IOException, ServletException {

        HttpServletResponse httpRes = (HttpServletResponse) res;
        CapturaRespuesta captura = new CapturaRespuesta(httpRes);

        chain.doFilter(req, captura);

        String contentType = captura.getContentType();
        byte[] datos = captura.getBytes();

        if (contentType != null && contentType.contains("text/html")) {
            String html = new String(datos, StandardCharsets.UTF_8);
            if (html.contains("</body>") && !html.contains("theme-toggle.js")) {
                html = html.replace("</body>", SNIPPET);
                byte[] salida = html.getBytes(StandardCharsets.UTF_8);
                httpRes.setContentLength(salida.length);
                httpRes.getOutputStream().write(salida);
            } else {
                httpRes.getOutputStream().write(datos);
            }
        } else {
            httpRes.getOutputStream().write(datos);
        }
    }

    private static class CapturaRespuesta extends HttpServletResponseWrapper {
        private final ByteArrayOutputStream buffer = new ByteArrayOutputStream();
        private final ServletOutputStream sos = new ServletOutputStream() {
            @Override public boolean isReady() { return true; }
            @Override public void setWriteListener(WriteListener l) { }
            @Override public void write(int b) { buffer.write(b); }
        };
        private final PrintWriter writer =
                new PrintWriter(new OutputStreamWriter(buffer, StandardCharsets.UTF_8), true);

        public CapturaRespuesta(HttpServletResponse response) {
            super(response);
        }

        @Override public ServletOutputStream getOutputStream() { return sos; }
        @Override public PrintWriter getWriter() { return writer; }

        public byte[] getBytes() {
            writer.flush();
            return buffer.toByteArray();
        }
    }
}
