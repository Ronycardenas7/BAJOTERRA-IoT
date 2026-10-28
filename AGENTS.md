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
- Evitar instalaciones y pruebas simultáneas, dependencias pesadas y procesos innecesarios. Docker es opcional (D-002); el modo principal no lo necesita.
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

Hardware disponible (fotos revisadas el 2026-10-27; detalle en docs/plan-hardware.md y docs/guia-armado.md)
- ESP32 DevKit = controlador (sensores, relés, nube). ESP32-2432S028 "CYD" = pantalla, recibe por UART (DevKit GPIO 17 → CYD GPIO 22).
- 2 DHT22 (falta 1 para la selvática), 3 sondas de suelo resistivas con LM393, 2 mini-bombas 5 V, 2 ventiladores 5 V, módulo de 4 relés, fuente MB102.
- Sin sensores inalámbricos: todo va con cable. Sin sensor de luz por zona, CO₂, radiación ni conductividad: se envían como null.
- El montaje físico está por empezar (2026-10-28). El controlador está compilado y simulado en Wokwi; nada se ha probado en la placa real.

Stack y arquitectura acordados
- Frontend: React + Vite, JavaScript, HTML y CSS; responsive. PWA es un objetivo (hay manifiesto, no service worker).
- Nube (modo principal, D-010): el ESP32 envía por HTTPS a funciones RPC de Supabase (registrar_lectura, comandos_pendientes,
  confirmar_comando) con una clave por dispositivo guardada como hash. La web usa supabase-js, Realtime e inicio de sesión;
  solo los "operadores" pueden enviar órdenes. Proyecto Supabase: bajoterra-iot (sa-east-1, plan gratuito).
- Un solo dispositivo tipo "controlador" escribe las 3 zonas (D-012, migración 0004).
- Modo local (desarrollo sin internet): Python + Flask por capas, broker MQTT (Mosquitto o broker_local) y simulador. Se conserva, no es el principal.
- Simulador: Python, 3 zonas y 1 depósito, modo MQTT o modo nube (python -m sim.nube).
- Firmware: C/C++ del entorno Arduino, núcleo ESP32 3.x. Control local primero (funciona sin internet), millis() en vez de delay largos.
- ESP-NOW (del anteproyecto) quedó sin uso: no hay nodos inalámbricos.
- El código antiguo del equipo (Flask + MySQL + puente serial) fue reemplazado por Supabase; se revisó el 2026-10-28 (D-013).

Organización
Raíz: web_pwa/, backend/, simulador/, broker_local/, firmware/, docs/, supabase/, scripts/.
Backend (backend/app/): api/, mqtt/, services/, domain/, repositories/, infrastructure/, schemas/, config/.
Frontend (web_pwa/src/): app/, pages/, components/, services/, config/, styles/ y features/ (zonas, telemetria, actuadores, sesion).
Firmware: controlador/ (DevKit), pantalla/ (CYD) y pruebas pequeñas prueba_01 a prueba_05.
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
