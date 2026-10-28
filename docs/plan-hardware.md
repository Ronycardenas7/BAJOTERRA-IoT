# Plan de hardware — BAJOTERRA (3 zonas)

Plan de trabajo con el hardware **real** que tiene el equipo (revisado con fotos el 2026-10-27).
Para armarlo paso a paso, con tablas de cables y pruebas por fase: **[guia-armado.md](guia-armado.md)**.
Sin sensores inalámbricos: todo va **con cable** a dos placas ESP32.

## 1. Inventario

| Componente | Cantidad | Nota |
|---|---|---|
| ESP32 DevKit (ESP-WROOM-32, 38 pines) | 1 | **Controlador**: sensores, relés y envío a Supabase |
| ESP32-2432S028 ("Cheap Yellow Display", CYD) | 1 | **Es una ESP32 con pantalla táctil de 2,8" integrada**. Será la **pantalla** del invernadero. Trae un sensor de luz (LDR) en GPIO 34 |
| DHT22 / AM2302 (temperatura y humedad del aire) | 2 | Alcanzan para 2 zonas. **Para la 3ª zona falta 1 DHT22** |
| Sondas de humedad de suelo resistivas (horquilla y U) con placa LM393 | 3 | Una por zona. Las "patas largas de metal" son estas sondas, **no** el sensor de luz |
| Mini-bombas de agua 5 V | 2 | Con sus mangueras |
| Ventiladores 5 V (80 mm) | 2 | Extractores |
| Módulo de 4 relés (5 V, se activa en LOW) | 1 | 4 canales = 2 bombas + 2 ventiladores |
| Fuente de protoboard MB102 (3,3 V / 5 V) | 1 | Solo para lógica y relés (máximo unos 700 mA en total) |
| Protoboard y cables | — | |

**No hay sensor de luz por zona.** El LDR de la CYD mide la luz donde esté la pantalla: se informará como luz **relativa (%)** del invernadero, no en lux.
CO₂ y radiación no tienen sensor: con hardware real se envían como `null`, y la web los muestra como "sin sensor".

## 2. Arquitectura

```
Sensores ──cable──► ESP32 DevKit (controlador) ──WiFi/HTTPS──► Supabase ──Realtime──► Web (cualquier dispositivo)
                          │  ▲
                 relés ◄──┘  └── órdenes desde la web (cada 5 s)
                          │
                          └──UART (1 cable + GND)──► CYD (pantalla con datos en vivo, funciona aunque no haya internet)
```

- **Control local primero:** la DevKit decide sola (riego y ventilación con histéresis y límites de seguridad), aunque se caiga el WiFi. La nube solo registra y envía órdenes manuales.
- **UART de un solo sentido** (DevKit TX → CYD RX) a 115200 baudios, con una línea JSON por actualización. Es lo más simple y robusto (el anteproyecto ya usaba UART/Serial2) y no requiere sensores inalámbricos.

## 3. Asignación de zonas y actuadores (configurable en el código)

| Zona | Objetivo (lámina del proyecto) | Sensores | Actuadores |
|---|---|---|---|
| **Árida** | Aire 20–40 % HR, riego mínimo | DHT22 #1, sonda de suelo #1 | **Ventilador 1** (calor). Riego manual (sin bomba propia) |
| **Húmeda** | Aire 60–80 % HR, riego frecuente | DHT22 #2, sonda de suelo #2 | **Bomba 1** |
| **Selvática** | Aire ~80–95 % HR, suelo húmedo | (DHT22 #3 **por comprar**), sonda de suelo #3 | **Bomba 2**, **Ventilador 2** |

Si prefieres otra repartición (por ejemplo, una bomba en la árida), solo cambia la tabla de configuración del firmware.

**Por confirmar:** el código antiguo del equipo usaba sensores DS18B20 (temperatura) y fotorresistencias (LDR) por cultivo. Si todavía existen, pueden sumarse (un DS18B20 cubriría la temperatura de la selvática mientras falta el DHT22).

## 4. Pines

### ESP32 DevKit (controlador)

| Función | GPIO | Nota |
|---|---|---|
| DHT22 árida / húmeda / selvática | 4 / 16 / 13 | Datos. El módulo DHT22 ya trae su resistencia |
| Sonda suelo árida / húmeda / selvática (salida AO) | 34 / 35 / 36 | Entradas analógicas ADC1 (funcionan con WiFi) |
| Alimentación de las 3 sondas de suelo (VCC) | 33 | Se enciende **solo al medir** para que no se corroan |
| Relé IN1 → Bomba 1 (húmeda) | 25 | |
| Relé IN2 → Bomba 2 (selvática) | 26 | |
| Relé IN3 → Ventilador 1 (árida) | 27 | |
| Relé IN4 → Ventilador 2 (selvática) | 32 | |
| UART TX hacia la CYD | 17 | Serial2 |
| LED de estado | 2 | LED integrado |

### CYD ESP32-2432S028 (pantalla)

| Función | GPIO | Dónde |
|---|---|---|
| UART RX desde la DevKit | 22 | Conector **CN1** (GND, IO22, IO27, 3.3V) o **P3** (GND, IO35, IO22, IO21). Es el pin que usaba el código antiguo del equipo |
| Pantalla (ILI9341, bus HSPI) | SCK 14, MOSI 13, MISO 12, CS 15, DC 2, luz de fondo 21 | Interno |
| Sensor de luz (LDR) | 34 | Interno |
| LED RGB (se enciende en LOW) | R 4, G 16, B 17 | Interno |

Algunas placas CYD nuevas ("v3", con dos puertos USB) usan el controlador **ST7789** en lugar de ILI9341. Si la pantalla queda en blanco, avísame y cambio la librería.

## 5. Alimentación (evita los reinicios por las bombas)

1. **DevKit y CYD**: por su cable USB.
2. **Sensores**: a **3,3 V** de la DevKit. Las sondas de suelo se alimentan desde el GPIO 33. **Nunca a 5 V**: su salida analógica podría dañar la ESP32.
3. **Módulo de relés**: VCC a 5 V de la MB102, GND común, IN1–IN4 a los GPIO.
4. **Bombas y ventiladores**: con una **fuente de 5 V y 2 A aparte** (por ejemplo, un cargador de celular), pasando por COM/NO de cada relé. **No** se alimentan desde la ESP32 ni desde la MB102.
5. **Todas las tierras (GND) unidas.** Pon un condensador de 470–1000 µF entre 5 V y GND cerca de los relés si notas reinicios.

## 6. Fases

| Fase | Carpeta | Qué se comprueba | Estado |
|---|---|---|---|
| 1 | `firmware/prueba_03_sensores/` | DHT22 y sondas de suelo con calibración (seco y en agua), en el Monitor Serie | Compilado; falta probar en la placa |
| 2 | `firmware/prueba_04_reles/` | Cada relé, ventilador y bomba, uno por uno, con límite de tiempo | Compilado; falta probar en la placa |
| 3 | `firmware/prueba_05_pantalla_cyd/` | Pantalla de la CYD con las 3 zonas y el LDR | Compilado; falta probar en la placa |
| 4 | `firmware/controlador/` + `firmware/pantalla/` | Control automático por zona + UART DevKit → CYD (sin internet) | Ambos compilados; controlador probado en Wokwi; falta la placa real |
| 5 | (mismo) | + envío de lecturas **reales** a Supabase y órdenes desde la web | Código listo (dispositivo `controlador`, migración 0004); falta probar |
| 6 | web y Supabase | Mostrar solo sensores existentes, luz en %, la placa reporta 3 zonas | Pendiente |
| 7 | — | Funcionamiento continuo 24 h (estabilidad, agua, reinicios) | Pendiente |

## 7. Bibliotecas de Arduino IDE

Instálalas desde *Herramientas → Gestionar bibliotecas*:

- **DHT sensor library** (Adafruit) y **Adafruit Unified Sensor**, para las pruebas 03 y siguientes.
- **Adafruit ILI9341** y **Adafruit GFX Library**, para la pantalla CYD.
- **ArduinoJson** (versión 7), para la nube y el UART.

Las placas se instalan con *Gestor de tarjetas → "esp32 by Espressif Systems"*. Usa la placa **ESP32 Dev Module** tanto para la DevKit como para la CYD.
