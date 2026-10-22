package com.example.sensores_vsc.config;
import com.example.sensores_vsc.service.ClienteUserDetailsService;
import com.example.sensores_vsc.service.AdminUserDetailsService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.core.annotation.Order;
import org.springframework.security.authentication.dao.DaoAuthenticationProvider;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.web.SecurityFilterChain;

@Configuration
@EnableWebSecurity
public class SecurityConfig {

    @Autowired
    private AdminUserDetailsService adminService;

    @Autowired
    private ClienteUserDetailsService clienteService;

    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }

    @Bean
    @Order(1)
    public SecurityFilterChain adminFilterChain(HttpSecurity http) throws Exception {
        http
            .securityMatcher("/admin/**")
            .authenticationProvider(adminProvider())
            .authorizeHttpRequests(auth -> auth
                .requestMatchers("/admin/login").permitAll()
                .anyRequest().authenticated()
            )
            .formLogin(form -> form
                .loginPage("/admin/login")
                .loginProcessingUrl("/admin/login")
                .defaultSuccessUrl("/admin", true)
                .failureUrl("/admin/login?error")
                .usernameParameter("correo")
                .passwordParameter("contrasena")
            )
            .logout(logout -> logout
                .logoutUrl("/admin/logout")
                .logoutSuccessUrl("/admin/login")
            )
            .csrf(csrf -> csrf.disable());
        return http.build();
    }

    @Bean
    @Order(2)
    public SecurityFilterChain clienteFilterChain(HttpSecurity http) throws Exception {
        http
            .authenticationProvider(clienteProvider())
            .authorizeHttpRequests(auth -> auth
                .requestMatchers("/", "/login", "/register", "/nosotros", "/error" , "/css/**", "/js/**").permitAll()
                .anyRequest().authenticated()
            )
            .formLogin(form -> form
                .loginPage("/login")
                .loginProcessingUrl("/login")
                .defaultSuccessUrl("/dashboard", true)
                .failureUrl("/login?error")
                .usernameParameter("correo")
                .passwordParameter("contrasena")
            )
            .logout(logout -> logout
                .logoutUrl("/logout")
                .logoutSuccessUrl("/login")
            )
            .csrf(csrf -> csrf.disable());
        return http.build();
    }

    private DaoAuthenticationProvider adminProvider() {
        DaoAuthenticationProvider p = new DaoAuthenticationProvider();
        p.setUserDetailsService(adminService);
        p.setPasswordEncoder(passwordEncoder());
        return p;
    }

    private DaoAuthenticationProvider clienteProvider() {
        DaoAuthenticationProvider p = new DaoAuthenticationProvider();
        p.setUserDetailsService(clienteService);
        p.setPasswordEncoder(passwordEncoder());
        return p;
    }
}
