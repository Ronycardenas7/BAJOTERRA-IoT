# Guía de armado — BAJOTERRA (3 zonas: árida, húmeda y selvática)

Guía paso a paso para armar el invernadero **con el hardware real**. Se arma **por fases**: después de cada fase se sube un programa de prueba y se comprueba que todo funcione **antes** de seguir. Así, si algo falla, sabes exactamente qué parte revisar.

> Los pines y la repartición vienen de `docs/plan-hardware.md` y de `firmware/controlador/config.h`. Si cambias un pin aquí, cámbialo también en el código.

---

## 0. Seguridad antes de empezar

1. **Nunca conectes ni desconectes cables con la placa encendida.** Desenchufa el USB y la fuente de 5 V antes de cada cambio.
2. Todo funciona con **5 V o 3,3 V**. No hay 220 V en ningún punto del proyecto. Si un ventilador o una bomba fuera de 12 V o de 220 V, **para y avísame**.
3. Los sensores van a **3,3 V**. **Nunca** conectes la salida analógica (AO) de una sonda alimentada con 5 V a la ESP32: puede dañarla.
4. Las bombas y los ventiladores **no** se alimentan desde la ESP32 ni desde la MB102: van con una fuente de 5 V aparte, a través de los relés.
5. Mantén el agua lejos de las placas. Prueba las bombas primero dentro de un vaso o balde.

---

## 1. Materiales

### Lo que ya tienen

| Componente | Cantidad | Para qué |
|---|---|---|
| ESP32 DevKit (ESP-WROOM-32) | 1 | **Controlador**: lee sensores, maneja relés y envía a Supabase |
| ESP32-2432S028 (CYD, ESP32 con pantalla de 2,8") | 1 | **Pantalla** del invernadero |
| DHT22 / AM2302 (temperatura y humedad del aire) | 2 | Zona árida y zona húmeda |
| Sondas de suelo resistivas + placa LM393 | 3 | Una por zona |
| Mini-bombas de agua 5 V con mangueras | 2 | Zona húmeda y zona selvática |
| Ventiladores 5 V | 2 | Zona árida y zona selvática |
| Módulo de 4 relés (5 V, se activa en LOW) | 1 | 2 bombas + 2 ventiladores |
| Fuente de protoboard MB102 | 1 | 5 V para el módulo de relés |
| Protoboard y cables dupont | — | Conexiones |

### Lo que falta (o hay que confirmar)

| Falta | Por qué | Prioridad |
|---|---|---|
| **1 DHT22 más** | La zona selvática no tiene sensor de aire (por ahora envía `null`) | Alta |
| **Fuente de 5 V y 2 A** (por ejemplo, un cargador de celular con un cable USB cortado, o una fuente con bornera) | Alimenta las bombas y los ventiladores sin que la ESP32 se reinicie | Alta |
| **Condensador electrolítico de 470–1000 µF y 10 V o más** | Amortigua el golpe de corriente al arrancar las bombas | Media |
| **4 diodos 1N4007** (uno por bomba y por ventilador) | Absorben el pico de voltaje del motor al apagarse (menos ruido y menos reinicios) | Media |
| Recipiente para el agua (depósito) y macetas o bandejas para las 3 zonas | Montaje físico | Media |
| Cable USB de datos (no solo de carga) para cada placa | Subir el código | Alta |

> **Pregunta abierta:** el código antiguo del equipo usaba sensores de temperatura **DS18B20** (2 por cultivo) y **fotorresistencias (LDR)** en los pines 35 y 33. Si todavía los tienen, avísame: un DS18B20 puede darle temperatura a la zona selvática mientras llega el tercer DHT22.

---

## 2. Cómo se reparte el invernadero

| Zona | Sensores | Actuadores | Objetivo de prueba |
|---|---|---|---|
| **Árida** | DHT22 #1 (GPIO 4) + sonda de suelo #1 (GPIO 34) | **Ventilador 1** (relé IN3). **Sin bomba**: se riega a mano | Aire seco (20–40 % HR) y suelo seco |
| **Húmeda** | DHT22 #2 (GPIO 16) + sonda de suelo #2 (GPIO 35) | **Bomba 1** (relé IN1) | Aire 60–80 % HR, suelo húmedo |
| **Selvática** | DHT22 #3 (GPIO 13, **por comprar**) + sonda de suelo #3 (GPIO 36) | **Bomba 2** (relé IN2) y **Ventilador 2** (relé IN4) | Aire muy húmedo (80–95 % HR) y suelo húmedo |

Consejos de montaje:
- **DHT22:** a la altura de las plantas, en el centro de la zona. Que no le llegue agua ni sol directo, porque marcaría más temperatura de la real.
- **Sonda de suelo:** enterrada hasta la línea que marca la sonda, **sin** enterrar la placa LM393 ni los conectores. Lejos de donde cae el chorro de la bomba (si no, mide el chorro y no la tierra).
- **Ventilador:** en la pared de la zona, **sacando** aire hacia afuera (extractor).
- **Bomba:** dentro del depósito, sumergida por completo (las mini-bombas se dañan si funcionan en seco). La manguera va a la maceta de su zona.
- **Placas y relés:** fuera de las zonas, en una caja o tabla seca, más alta que el agua.

---

## 3. Mapa de conexiones

### 3.1 ESP32 DevKit (controlador)

En la placa, algunos pines tienen otro nombre impreso: **GPIO 16 = "RX2"**, **GPIO 17 = "TX2"** y **GPIO 36 = "VP" o "SVP"**.

| Pin DevKit | Va a | Cable sugerido |
|---|---|---|
| **3V3** | `+` de los 3 DHT22 | Rojo |
| **GND** | `−` de todos los sensores, GND del módulo de relés, GND de la MB102 y GND de la CYD | Negro |
| **GPIO 4** | `out` / DATA del DHT22 **árida** | Verde |
| **GPIO 16 (RX2)** | `out` / DATA del DHT22 **húmeda** | Verde |
| **GPIO 13** | `out` / DATA del DHT22 **selvática** (cuando lo tengas) | Verde |
| **GPIO 33** | `VCC` de las **3** placas LM393 (todas juntas) | Naranjo |
| **GPIO 34** | `AO` de la LM393 **árida** | Amarillo |
| **GPIO 35** | `AO` de la LM393 **húmeda** | Amarillo |
| **GPIO 36 (VP)** | `AO` de la LM393 **selvática** | Amarillo |
| **GPIO 25** | `IN1` del módulo de relés (**Bomba 1 → húmeda**) | Morado |
| **GPIO 26** | `IN2` (**Bomba 2 → selvática**) | Morado |
| **GPIO 27** | `IN3` (**Ventilador 1 → árida**) | Morado |
| **GPIO 32** | `IN4` (**Ventilador 2 → selvática**) | Morado |
| **GPIO 17 (TX2)** | **GPIO 22** de la CYD (datos para la pantalla) | Blanco |

Detalles:
- **DHT22 en módulo (3 pines `+ out −`):** ya trae su resistencia; conéctalo directo.
  **DHT22 suelto (4 patas):** pata 1 = VCC, pata 2 = DATA, pata 3 = sin conectar, pata 4 = GND, y pon una resistencia de **10 kΩ entre DATA y 3V3**.
- **Sonda de suelo:** la horquilla metálica se une a la placa LM393 con 2 cables (no importa el orden). De la LM393 se usan **VCC, GND y AO**; **DO no se conecta**.
- **¿Por qué el VCC de las sondas va al GPIO 33 y no a 3V3?** El programa solo las enciende unos milisegundos al medir. Así se corroen mucho menos, que fue uno de los problemas del prototipo anterior.
- Las 3 sondas juntas consumen poco (unos 10–15 mA), dentro de lo que entrega un pin. Si al conectar la tercera bajan todas las lecturas, avísame.

### 3.2 Módulo de 4 relés

**Lado de control (pines `VCC GND IN1 IN2 IN3 IN4`):**

| Pin del módulo | Va a |
|---|---|
| `VCC` | **5 V de la MB102** |
| `GND` | **GND de la MB102**, unido al GND de la DevKit |
| `IN1`–`IN4` | GPIO 25, 26, 27 y 32 de la DevKit (tabla anterior) |
| Puente `JD-VCC`–`VCC` (si existe) | **Déjalo puesto** |

**Lado de potencia (borneras `NO COM NC` de cada relé):** las bombas y los ventiladores se conectan así, uno por relé:

```
 Fuente 5 V 2 A (+) ──────► COM del relé
                            NO del relé ──────► (+) bomba o ventilador
 Fuente 5 V 2 A (−) ◄──────────────────────────  (−) bomba o ventilador
```

- Usa **COM y NO** ("normalmente abierto"): si la ESP32 se apaga o se reinicia, el motor queda **apagado**. **No** uses NC.
- Diodo 1N4007 (recomendado) **en paralelo con cada motor**: la franja plateada del diodo hacia el `+` del motor.
- Condensador de 470–1000 µF entre `+` y `−` de la fuente de 5 V, cerca de los relés. Respeta la polaridad: la pata marcada con `−` va al negativo.

| Relé | Carga | Zona |
|---|---|---|
| Relé 1 (IN1) | Bomba 1 | Húmeda |
| Relé 2 (IN2) | Bomba 2 | Selvática |
| Relé 3 (IN3) | Ventilador 1 | Árida |
| Relé 4 (IN4) | Ventilador 2 | Selvática |

### 3.3 Pantalla CYD (ESP32-2432S028)

- Se alimenta por **su propio cable USB** (un cargador o el PC).
- Usa el cable pequeño de 4 hilos que viene con la placa en el conector **CN1** (o **P3**); ambos tienen el pin **IO22**.

| CYD | Va a |
|---|---|
| **IO22** (CN1 o P3) | **GPIO 17 (TX2)** de la DevKit |
| **GND** (CN1 o P3) | **GND** de la DevKit |

Es **un solo cable de datos más GND**: la DevKit habla y la CYD solo escucha. Es el mismo pin 22 que usaba el código antiguo del equipo, que funcionaba.

### 3.4 Alimentación (resumen)

```
 USB del PC o cargador ──► DevKit (sensores a 3V3 de la DevKit)
 USB ──────────────────► CYD (pantalla)
 Fuente MB102 5 V ─────► VCC del módulo de relés
 Fuente 5 V 2 A ───────► COM de los relés ─► bombas y ventiladores

 GND común OBLIGATORIO: DevKit + MB102 + módulo de relés + CYD.
```

---

## 4. Armado por fases (con prueba después de cada una)

Para subir cada programa: Arduino IDE → placa **"ESP32 Dev Module"** → puerto COM de la placa → **Subir**. Después abre el **Monitor Serie a 115200** baudios. Las bibliotecas están en `firmware/README.md`.

### Fase 1 — Solo la DevKit
1. Conecta la DevKit al PC por USB, sin nada más.
2. Sube `firmware/prueba_01_wifi` con tu WiFi de 2,4 GHz en `secretos.h`.
3. ✅ **Debe mostrar** la IP y la hora UTC. Si no conecta: revisa que la red sea de 2,4 GHz (la ESP32 no ve redes de 5 GHz).

### Fase 2 — Sensores
1. **Desenchufa.** Conecta los 2 DHT22 y las 3 sondas de suelo según la tabla 3.1.
2. Sube `firmware/prueba_03_sensores`.
3. ✅ Cada 3 s debe mostrar temperatura y humedad de árida y húmeda, y el valor crudo de las 3 sondas.
4. **Calibra cada sonda.** Escribe `c` en el Monitor Serie:
   - sonda **al aire y seca** → anota el número ("seco");
   - sonda **en un vaso con agua** (solo hasta la línea) → anota el número ("mojado").
5. Escribe esos números en `firmware/controlador/config.h` (`SUELO_SECO` y `SUELO_MOJADO`). El código antiguo usaba seco 4095 y mojado 1480; tus sondas pueden variar un poco.
6. ❌ **Si un DHT22 marca `nan`:** revisa `+`, `−` y el pin de datos. ❌ **Si una sonda marca siempre 0 o 4095:** revisa el AO y el VCC al GPIO 33.

### Fase 3 — Relés sin motores
1. **Desenchufa.** Conecta el módulo de relés (lado de control, tabla 3.2) **sin** bombas ni ventiladores todavía.
2. Sube `firmware/prueba_04_reles`.
3. Escribe `1`, `2`, `3` y `4` en el Monitor Serie.
4. ✅ Cada relé debe hacer **"clic"** y encender su LED. `0` los apaga todos.
5. ❌ **Si al arrancar todos los relés quedan encendidos:** el módulo puede activarse en HIGH. Cambia `RELE_ACTIVO_BAJO` a `false` en la prueba 04 y avísame.
6. ❌ **Si un relé no se apaga del todo:** algunos módulos de 5 V no se apagan bien con los 3,3 V de la ESP32. Avísame y lo resolvemos (se alimenta el VCC de control a 3,3 V o se usa un transistor).

### Fase 4 — Bombas y ventiladores
1. **Desenchufa todo.** Conecta la fuente de 5 V 2 A, los motores en COM/NO, los diodos y el condensador (tabla 3.2).
2. Pon las bombas **dentro de un balde con agua** y las mangueras de vuelta al mismo balde.
3. Enciende la fuente de 5 V y conecta la DevKit. Repite la prueba 04.
4. ✅ Cada bomba y cada ventilador debe funcionar con su número. Las bombas se apagan solas a los 10 s.
5. ❌ **Si la DevKit se reinicia al arrancar una bomba:** falta el GND común, o la fuente es muy débil; pon el condensador y los diodos.

### Fase 5 — Pantalla
1. Conecta solo la CYD por USB y sube `firmware/prueba_05_pantalla_cyd` (placa "ESP32 Dev Module").
2. ✅ Deben verse las 3 zonas con valores de ejemplo.
3. ❌ **Pantalla en blanco:** tu CYD puede ser la versión de 2 puertos USB (controlador ST7789). En `firmware/pantalla/config_pantalla.h` pon `PANTALLA_ST7789 1` e instala "Adafruit ST7735 and ST7789 Library".
   ❌ **Colores en negativo (fondo blanco):** cambia `invertDisplay(true)` a `false` (o `INVERTIR_COLORES 0`).
4. Sube `firmware/pantalla` (programa final de la pantalla). Sin la DevKit, debe decir "ESPERANDO DATOS DEL CONTROLADOR".

### Fase 6 — Todo junto (control automático)
1. **Desenchufa.** Conecta el cable DevKit GPIO 17 → CYD IO22 y el GND entre ambas.
2. En `firmware/controlador/secretos.h` (ya está en tu PC de la casa; si no, copia `secretos.ejemplo.h`) escribe tu WiFi. **No** definas `MODO_WOKWI`.
3. Sube `firmware/controlador` a la DevKit.
4. ✅ **Monitor Serie:** cada 3 s se ven las 3 zonas; cada 15 s, `[nube] arida guardado` (y lo mismo para húmeda y selvática).
5. ✅ **Pantalla:** rota entre árida, húmeda y selvática; abajo dice "Dato hace 1 s | WiFi si | REAL"; el LED de la CYD queda en **verde**.
6. ✅ **Web** (`pnpm dev`, Panel): las 3 zonas con datos **reales** (sin la etiqueta "SIMULADO").
7. **Prueba de riego:** saca la sonda de la zona húmeda de la tierra y ponla sobre papel seco → la bomba 1 debe encenderse **máximo 20 s**, descansar 30 s y repetir. Si el suelo no sube después de 3 riegos, la bomba se **bloquea 1 hora** y el Monitor Serie muestra `[ALERTA]`. Es la protección contra inundaciones.

### Fase 7 — Prueba larga
Déjalo funcionando varias horas (ideal 24 h) y anota: reinicios, lecturas raras, cuánta agua se gastó y si alguna zona se inundó o se secó.

---

## 5. Lista de chequeo antes de enchufar

- [ ] Ningún cable de 5 V llega a un pin de la ESP32 (salvo VIN o 5V).
- [ ] Las sondas de suelo tienen VCC en el **GPIO 33** (no en 5 V).
- [ ] GND común entre DevKit, MB102, relés y CYD.
- [ ] Motores en **COM y NO** (no en NC).
- [ ] Condensador con la polaridad correcta.
- [ ] Bombas sumergidas y mangueras sujetas.
- [ ] Placas lejos del agua.

## 6. Problemas frecuentes

| Síntoma | Causa probable | Qué hacer |
|---|---|---|
| La DevKit se reinicia al encender una bomba | Bajón de voltaje o ruido | Fuente de 5 V aparte, GND común, condensador y diodos |
| Arduino IDE no encuentra el puerto COM | Cable USB solo de carga, o falta el driver CP210x/CH340 | Cambia el cable; instala el driver |
| "Failed to connect" al subir | La placa no entra en modo de carga | Mantén apretado **BOOT** mientras dice "Connecting…" |
| DHT22 da `nan` | Cable de datos suelto o pin equivocado | Revisa la tabla 3.1 |
| La pantalla dice "SIN DATOS NUEVOS" | Falta el cable GPIO 17 → IO22 o el GND entre placas | Revisa la tabla 3.3 |
| La web no muestra datos | `secretos.h` sin WiFi o sin clave | Mira el Monitor Serie: los errores `[http]` dicen la causa |
