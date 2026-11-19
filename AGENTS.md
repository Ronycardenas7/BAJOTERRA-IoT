BAJOTERRA — instrucciones y contexto de continuidad
Contexto inicial transferido el 5 de octubre de 2026 (Chile). Actualizado el 28 de octubre de 2026 con los acuerdos estables
tomados desde entonces (3 zonas, Supabase directo, hardware real). El detalle de cada cambio está en docs/decisiones.md.
Este archivo contiene decisiones y antecedentes; NO demuestra que las funciones estén implementadas.
Al iniciar, leer también docs/estado-actual.md y contrastar con los archivos y Git.
Las instrucciones nuevas del usuario prevalecen sobre este contexto.

Forma de trabajo
- Responder en español claro. Explicar el propósito de los cambios y de cada comando que deba ejecutar el usuario.
- El usuario está aprendiendo (nivel de inglés A1). Dar pasos pequeños, comandos cortos y salidas acotadas.
- Todo archivo de código o configuración lleva comentarios línea por línea que expliquen cada instrucción.
- Si tienes acceso al repositorio local, realizar directamente el trabajo autorizado; no pedir al usuario que copie código largo que puedes editar tú.
- Usar exclusivamente pnpm para JavaScript (vía corepack). No usar npm, npx ni Yarn para gestionar este proyecto. Conservar pnpm-lock.yaml.
- Mantener VS Code, sus extensiones, Git, Node, Python y el kit de herramientas instalado. No reinstalar ni eliminar herramientas globales sin necesidad.
- Equipos del usuario: Linux Mint con 3,3 GiB de RAM (casa); PC Windows "moniropc"; PCs Windows de la universidad (sin permisos de administrador).
  En Windows, Node se instaló con winget el 2026-10-27 en moniropc; git no está en el PATH (se usa GitHub Desktop).
- Evitar instalaciones y pruebas simultáneas, dependencias pesadas y procesos innecesarios.
- Trabajar por hitos pequeños y comprobables. No declarar pruebas aprobadas si no se ejecutaron.
- No cambiar el stack, las zonas o la estructura acordada por iniciativa propia sin explicar la necesidad y acordarlo.
- Conservar credenciales fuera de Git. No imprimir secretos. Plantillas con valores ficticios (*.ejemplo.*); excluir secretos.h,
  secretos_nube.conf, clave_*.txt, .env, node_modules, entornos Python y compilados.
- No borrar ni modificar recursos remotos de GitHub o Supabase sin acuerdo. Trabajar en ramas (rama actual: PruebaOnline).

Propósito y alcance
Invernadero con TRES zonas de evaluación independientes (acordado el 2026-10-27, D-009; reemplaza a lechuga y cactus):
1. Árida: aire seco (20–40 % HR), riego mínimo (manual por ahora), ventilación por calor.
2. Húmeda: aire 60–80 % HR, riego frecuente.
3. Selvática: aire muy húmedo (~80–95 % HR), suelo húmedo, riego y ventilación.
Identificadores sin tildes: arida, humeda, selvatica. Los umbrales del firmware y del simulador son valores de PRUEBA, no agronómicos.
Contexto: aridez y escasez de agua de la región de Tarapacá (Iquique, Universidad de Tarapacá).
Nunca presentar datos simulados como mediciones reales.
Problemas históricos: reinicios al arrancar bombas, caídas de tensión, ruido inductivo, corrosión de sensores resistivos y dependencia de un PC encendido.

Hardware y arquitectura distribuida v3.0 (adoptada en noviembre 2026; sustituye al esquema cableado de 1 placa con 4 relés)
- 3 Nodos ESP-NOW independientes (firmware/nodo/): 1 módulo por zona (árida, húmeda/templada, selvática). Cada nodo lee DHT22 (GPIO 4) y sonda de suelo (GPIO 34 alimentada por GPIO 25 para evitar electrólisis) y transmite por ESP-NOW al Maestro cada 2 s.
- 1 ESP32 Maestro dual-core (firmware/controlador/): Núcleo 1 ejecuta el control autónomo (lazo PI de ventilación sobre temperatura, riego por pulsos con histéresis y alarma de fallo) y UART bidireccional hacia la pantalla. Núcleo 0 gestiona la red Wi-Fi, hora NTP y telemetría/órdenes HTTPS directas con Supabase. Controla 6 relés (pines 33, 25, 26, 27, 14, 13) para bombas y ventiladores de las 3 zonas.
- 1 Pantalla CYD táctil ESP32-2432S028 (firmware/pantalla/ v3.1): Pantalla TFT_eSPI con controlador táctil XPT2046. Enlace UART bidireccional con el Maestro: Maestro TX GPIO 17 → Pantalla RX IO22 (telemetría de zonas), Pantalla TX IO27 → Maestro RX GPIO 16 (comandos táctiles de modo, actuadores y temperatura objetivo TOBJ).
- Sin sensor de luz por zona, CO₂, radiación ni conductividad: viajan como null ("Sin dato" en la web).

Stack y arquitectura acordados
- Frontend: React + Vite, JavaScript, HTML y CSS; responsive. PWA es un objetivo (hay manifiesto, no service worker).
- Nube (modo principal, D-010): el ESP32 Maestro envía por HTTPS a funciones RPC de Supabase (registrar_lectura, comandos_pendientes,
  confirmar_comando) con una clave por dispositivo guardada como hash. La web usa supabase-js, Realtime e inicio de sesión;
  solo los "operadores" pueden enviar órdenes. Proyecto Supabase: bajoterra-iot (sa-east-1, plan gratuito).
- Dispositivo tipo "controlador" escribe las 3 zonas (D-012, migración 0004 y 0005).
- Desarrollo y despliegue web: Vite consume Supabase directamente. Vercel sirve el frontend desde `web_pwa/`.
- Firmware: C/C++ del entorno Arduino, núcleo ESP32 3.x. Control distribuido con ESP-NOW entre nodos y Maestro, y UART bidireccional con pantalla CYD.
- El código antiguo del equipo (Flask + MySQL + puente serial) fue reemplazado por Supabase; se revisó el 2026-10-28 (D-013).

Organización
Raíz: web_pwa/, firmware/, docs/, supabase/.
Frontend (web_pwa/src/): app/, pages/, components/, services/, config/, styles/ y features/ (zonas, telemetria, actuadores, sesion).
Firmware: controlador/ (Maestro dual-core), nodo/ (Nodos sensores ESP-NOW), pantalla/ (CYD táctil bidireccional) y pruebas de apoyo.
Crear módulos cuando se necesiten; evitar código vacío o abstracciones innecesarias.

Datos y pantallas
Cada zona tiene: temperatura (°C), humedad_ambiente (% HR), humedad_sustrato (% relativo a la calibración), luz, co2, radiacion,
estado reportado de bomba, ventilador y luces, modo automático/manual, instante y conexión.
- luz en lux solo si hay calibración que lo respalde; una LDR mapeada linealmente no demuestra lux reales.
- Depósito único "principal" (D-006): conductividad_ec, nivel_agua y agua_disponible; hoy sin sensores (null).
Cada mensaje identifica zona o depósito, dispositivo, origen real/simulado, id de mensaje, instante de medición, recepción y calidad.
Fechas en UTC; la interfaz muestra la zona horaria. Datos ausentes como null, no ceros inventados.
- Una orden pendiente no equivale a un actuador encendido. Sin caudalímetro no afirmar flujo ni litros medidos.

Órdenes y seguridad del control
Las órdenes llevan id, zona, actuador, estado solicitado y caducidad; se registran solicitud y confirmación por separado.
Se tratan duplicados y órdenes vencidas. El firmware limita cada riego (20 s), exige descanso (30 s), no riega sin dato de suelo
y bloquea la bomba 1 h si 3 riegos seguidos no suben la humedad (D-014). Los temas MQTT del modo local están en docs/mqtt-topics.md.

Continuidad entre sesiones
Al terminar cada sesión, actualizar docs/estado-actual.md (fecha y objetivo, archivos cambiados, verificaciones con resultados reales,
decisiones y dudas, próxima tarea y bloqueos, último commit) y docs/decisiones.md para decisiones de arquitectura.
Actualizar este AGENTS.md solo cuando cambien acuerdos estables. El código y las pruebas determinan lo implementado; el usuario determina los objetivos.
