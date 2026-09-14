package com.example.sensores_vsc;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableScheduling;

@SpringBootApplication
@EnableScheduling
public class SensoresVscApplication {

	public static void main(String[] args) {
		SpringApplication.run(SensoresVscApplication.class, args);
	}
}
