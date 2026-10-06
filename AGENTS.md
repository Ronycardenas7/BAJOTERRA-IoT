BAJOTERRA — instrucciones y contexto de continuidad
Contexto transferido desde la conversación del proyecto el 5 de octubre de 2026 (Chile).
Este archivo contiene decisiones y antecedentes; NO demuestra que las funciones estén implementadas.
Al iniciar, leer también docs/estado-actual.md si existe y contrastar con los archivos y Git.
Las instrucciones nuevas del usuario prevalecen sobre este contexto.
Forma de trabajo
- Responder en español claro. Explicar el propósito de los cambios y de cada comando que deba ejecutar el usuario.
- El usuario está aprendiendo. Dar pasos pequeños, comandos cortos y salidas acotadas.
- Si tienes acceso al repositorio local, realizar directamente el trabajo autorizado; no pedir al usuario que copie código largo que puedes editar tú.
- Usar exclusivamente pnpm para JavaScript. No usar npm, npx ni Yarn para gestionar este proyecto. Conservar pnpm-lock.yaml y registrar la versión de pnpm comprobada.
- Mantener VS Code, sus extensiones, Git, Node, Python y el kit de herramientas instalado. No reinstalar ni eliminar herramientas globales sin necesidad.
- Equipo del usuario: Linux Mint, 3,3 GiB de RAM total; se observaron 1,5 GiB disponibles, swap de 4,3 GiB con 689 MiB usados y 413 GB libres en home. Son mediciones puntuales.
- Evitar instalaciones y pruebas simultáneas, dependencias pesadas y procesos innecesarios. No introducir Docker, modelos locales ni subagentes paralelos por defecto.
- Trabajar por hitos pequeños y comprobables. No declarar pruebas aprobadas si no se ejecutaron.
- No cambiar el stack, los cultivos o la estructura acordada por iniciativa propia sin explicar la necesidad y acordarlo.
- Conservar credenciales fuera de Git. No imprimir secretos. Usar .env.example con valores ficticios y excluir .env, node_modules, entornos Python y compilados.
Propósito y alcance
Invernadero con dos microclimas independientes para monitoreo y control de riego y ventilación:
1. Zona lechuga: Lactuca sativa, ambiente templado y húmedo.
2. Zona cactus: Acanthocereus tetragonus, ambiente árido con riego restringido.
El usuario actualmente NO dispone de ESP32 ni prototipo físico para desarrollar y probar.
Comenzar con simulación; nunca presentar datos simulados como mediciones reales.
Problemas históricos: reinicios al arrancar bombas, caídas de tensión, ruido inductivo, corrosión de sensores resistivos y dependencia de un PC encendido.
El anteproyecto académico describe una estructura física y una implementación previa; no confundirlas con hardware disponible o funcionamiento validado de esta nueva versión.
Stack y arquitectura acordados
- Frontend: React + Vite, JavaScript, HTML y CSS; responsive. PWA es un objetivo, no una funcionalidad ya comprobada.
- Gestor de paquetes: pnpm, instalado según el usuario; versión pendiente de verificar.
- Backend propuesto en la conversación: Python + Flask, con arquitectura por capas. Usar entorno virtual para dependencias Python.
- Comunicación de dispositivos: MQTT mediante broker por seleccionar. Supabase NO sustituye al broker.
- Datos: Supabase/PostgreSQL. Actualizaciones web mediante Realtime según permisos y esquema final. Autenticación y RLS pendientes de comprobar.
- Simulador: Python, con dos zonas independientes y recepción/confirmación de comandos.
- Hardware futuro: ESP32, firmware C/C++ del entorno Arduino, sensores y actuadores.
- ESP-NOW figura en el informe como enlace local. MQTT es un requisito posterior del usuario. Definir si habrá nodos ESP-NOW y un gateway MQTT o ESP32 conectados directamente al broker; no implementar ambas topologías sin necesidad.
- Diseño anterior: Figma; solicitar o inspeccionar la referencia si se requiere fidelidad, no inventar su contenido.
- Codex en VS Code: instalado según el último mensaje. OpenCode era una propuesta de auditor adicional, aún no instalado; no bloquear el trabajo por ello.
Organización propuesta
Raíz: web_pwa/, backend/, simulador/, firmware/, docs/, supabase/.
Backend, dentro de backend/app/:
- api/: entrada HTTP y respuestas.
- mqtt/: recepción y adaptación de mensajes MQTT.
- services/: casos de uso y coordinación.
- domain/: entidades, reglas y estados.
- repositories/: acceso a datos.
- infrastructure/: clientes de broker y Supabase.
- schemas/: validación de mensajes.
- config/: configuración de ejecución.
Frontend, dentro de web_pwa/src/:
- app/, pages/, components/, services/, hooks/, styles/.
- features/zonas/, features/telemetria/, features/actuadores/, features/historial/, features/alertas/, features/auth/.
Crear módulos cuando se necesiten; evitar código vacío o abstracciones innecesarias.
Datos y pantallas
Cada zona tendrá sus propias mediciones:
- temperatura: °C, aire del compartimento.
- humedad_ambiente: % HR, aire del compartimento.
- humedad_sustrato: porcentaje relativo a la calibración del sensor y sustrato.
- luz: lux solamente si hay medición/calibración que respalde esa unidad; una LDR mapeada linealmente no demuestra lux reales.
- Estado reportado de bomba y ventilador, modo automático/manual, instante de actualización y estado de conexión.
Depósito: definir si es compartido o uno por zona. conductividad_ec en mS/cm corresponde al punto de medición de la solución; no mide nutrientes individuales. nivel_agua porcentual requiere sensor adecuado; un interruptor de nivel solo permite un indicador como agua_disponible. No duplicar una lectura compartida como si proviniera de sensores independientes.
Cada mensaje/registro deberá identificar zona o depósito, dispositivo, origen real/simulado, identificador de mensaje, instante de medición, recepción y calidad del dato. Fechas en UTC; interfaz con zona horaria indicada. Datos ausentes como nulos, no ceros inventados.
UI prevista:
- Resumen con tarjetas separadas de lechuga y cactus, depósito, conectividad y alertas.
- Detalle por zona con unidades, rangos configurados, gráficos y controles.
- Historial por variable, zona y fechas; eventos y resultados de comandos.
- Etiquetas visibles para datos simulados, ausentes o desactualizados.
- Una orden pendiente no equivale a un actuador encendido. Sin caudalímetro o realimentación no afirmar flujo real ni litros medidos.
Rangos de la tabla operativa del informe, solo referencias provisionales:
- Lechuga: 18–21 °C, 60–80 % HR, 50–70 % humedad relativa de sustrato.
- Cactus: 20–25 °C, 20–40 % HR, 10–30 % humedad relativa de sustrato.
  Revisar y calibrar antes de automatización física. No prometer control de humedad/temperatura fuera de la capacidad real de los actuadores.
MQTT y control
Temas propuestos:
- bajoterra/01/zonas/{zona}/telemetria
- bajoterra/01/zonas/{zona}/comandos
- bajoterra/01/zonas/{zona}/confirmaciones
- bajoterra/01/depositos/{deposito}/telemetria
- bajoterra/01/dispositivos/{id}/estado
Las órdenes incluirán identificador, zona, actuador, estado solicitado y caducidad. Registrar solicitud, envío y confirmación por separado. Tratar duplicados y comandos vencidos; no reproducir acciones peligrosas después de una reconexión. Una confirmación de transporte no demuestra ejecución física.
El firmware futuro mantendrá control local básico y límites de funcionamiento aun sin internet. Evitar pines conflictivos del ESP32 concreto y temporización bloqueante; preferir millis(). La comunicación inalámbrica no resuelve por sí sola los problemas de alimentación de bombas.
Estado conocido y reinicio solicitado
- Existía un proyecto previo llamado BAJORTERRA-Proyecto (con R adicional en el nombre del repositorio). URL histórica: https://github.com/Ronycardenas7/BAJORTERRA-Proyecto . Verificar propietario, remoto y contenido antes de actuar.
- La ruta /home/rony/Proyectos/BAJORTERRA-Proyecto devolvió que no existía. No se localizó otra copia en esta conversación.
- El usuario pidió reiniciar código, GitHub y Supabase. Ninguna eliminación está confirmada. Identificar recursos exactos, preparar respaldo y concretar el alcance antes de ejecutar cambios destructivos; esta petición no autoriza borrar otras carpetas o proyectos.
- Se dieron instrucciones para crear /home/rony/Proyectos/BAJOTERRA-v2, iniciar Git con rama main y crear las seis carpetas principales. Falta salida de terminal que confirme su estado. Inspeccionar la carpeta abierta; no repetir scaffolding sobre archivos existentes.
- Git, Node, Python y VS Code estaban disponibles. Ruta observada de Node: /home/rony/.nvm/versions/node/v24.21.0/bin/node; verificar versión efectiva.
- Supabase anterior tenía lecturas y comandos, con Realtime habilitado según el historial. Estado remoto actual, acceso, nombre de proyecto y datos no comprobados.
- Esquema histórico: lecturas con zona lechuga/cactus, temperatura, humedad_ambiente, humedad_sustrato, conductividad_ec, luz, bomba_activa y ventilador_activo. Comandos con zona, actuador bomba/ventilador, estado y ejecutado.
- Corregir si se reutiliza: NUMERIC(4,2) no admite 100,00 y NUMERIC(5,2) no admite miles de lux. Separar mediciones de depósito según topología final y ampliar seguimiento de comandos.
- No están comprobados: conexión integral MQTT-backend-Supabase-web, autenticación Google/RLS, instalación PWA, hardware o control físico. Nunca presentarlos como terminados.
Próximo hito y continuidad entre sesiones
Primer paso: inspeccionar carpeta abierta, instrucciones aplicables, estado Git, versiones Node/pnpm y archivos existentes. No leer ni volcar secretos.
Hito inmediato: base React/Vite con pnpm y vista mínima de ambas zonas con datos explícitamente simulados. Comprobar instalación, compilación y lint si existen scripts. No afirmar que esta vista ya utiliza MQTT si los datos aún son locales.
Hito siguiente: simulador Python -> MQTT -> backend por capas -> Supabase -> web, con una orden virtual y confirmación trazable. Elegir servicios y credenciales cuando esa integración corresponda. La simulación de software no sustituye las pruebas eléctricas y agronómicas.
Al terminar cada sesión, crear o actualizar docs/estado-actual.md con:
1. Fecha y objetivo de la sesión.
2. Archivos cambiados y cambios comprobados.
3. Comandos de verificación y resultados reales.
4. Decisiones nuevas y dudas pendientes.
5. Próxima tarea concreta y bloqueos.
6. Último commit cuando exista.
Mantener docs/decisiones.md para decisiones arquitectónicas y docs/auditorias.md para hallazgos con gravedad, archivo, evidencia y corrección. Crear estos documentos cuando haya contenido real que registrar.
Actualizar este AGENTS.md solo cuando cambien acuerdos estables; llevar el progreso cotidiano a estado-actual.md. El código y las pruebas actuales determinan lo implementado; el usuario determina los objetivos.