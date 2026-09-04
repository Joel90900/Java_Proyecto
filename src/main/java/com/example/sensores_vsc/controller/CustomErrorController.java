package com.example.sensores_vsc.controller;

import jakarta.servlet.RequestDispatcher;
import jakarta.servlet.http.HttpServletRequest;
import org.springframework.boot.web.servlet.error.ErrorController;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.RequestMapping;

@Controller
public class CustomErrorController implements ErrorController {

    @RequestMapping("/error")
    public String handleError(HttpServletRequest request, Model model) {
        Object status = request.getAttribute(RequestDispatcher.ERROR_STATUS_CODE);
        Object message = request.getAttribute(RequestDispatcher.ERROR_MESSAGE);
        Object exception = request.getAttribute(RequestDispatcher.ERROR_EXCEPTION);

        int statusCode = 500;
        if (status != null) {
            statusCode = Integer.parseInt(status.toString());
        }

        String errorName = HttpStatus.valueOf(statusCode).getReasonPhrase();
        String errorMessage = message != null && !message.toString().isBlank()
            ? message.toString()
            : switch (statusCode) {
                case 404 -> "El recurso solicitado no fue encontrado.";
                case 403 -> "No tienes permisos para acceder aquí.";
                case 500 -> "Error interno del servidor.";
                default  -> "Ocurrió un error inesperado.";
            };

        model.addAttribute("status", statusCode);
        model.addAttribute("error", errorName);
        model.addAttribute("message", errorMessage);

        return "error";
    }
}