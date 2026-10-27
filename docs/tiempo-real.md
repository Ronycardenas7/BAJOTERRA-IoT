# Datos en tiempo real desde cualquier dispositivo

**Decisión tomada (2026-10-27): Opción A.** El ESP32 envía directo a Supabase por HTTPS (ver D-010 en `docs/decisiones.md`).
Este documento explica cómo funciona, qué está hecho y cómo lo verá cada persona.

## 1. Cómo viajan los datos

```
ESP32 o simulador ──HTTPS (registrar_lectura)──► Supabase: tablas lecturas_zona / lecturas_deposito
        ▲                                                │
        │                                                └──Realtime (WebSocket)──► Web ──► celular o PC de cada persona
        └──HTTPS (comandos_pendientes / confirmar_comando)◄── tabla comandos ◄──(solicitar_comando)── Web (operador)
```

- **Proyecto Supabase:** `bajoterra-iot` (región São Paulo, plan gratuito), URL `https://rplctnuygsmbwudjcqbt.supabase.co`.
- **Lecturas:** cada dispositivo llama a la función `registrar_lectura` con dos claves: la **clave publicable** del proyecto (en el encabezado `apikey`) y su **clave propia de dispositivo**.
  El mensaje usa el mismo JSON de `docs/mqtt-topics.md`. La base de datos lo valida (campos, tipos, rangos, fecha con zona horaria, origen) y descarta los repetidos.
- **Tiempo real:** Supabase Realtime avisa a la web cada vez que se guarda una lectura, y la pantalla se actualiza sola en 1 a 2 segundos.
- **Órdenes:** un usuario **operador** pulsa un botón y se crea una fila en `comandos`, con 30 s de vigencia. El ESP32 la consulta cada 5 s, la ejecuta y la confirma.
  Una orden pendiente **no** es un actuador encendido: el estado real es el que reporta el dispositivo.
- **Hora:** el ESP32 usa NTP. El simulador y la web comparan su reloj con la función `hora_servidor` y corrigen el desfase.
  Esto se agregó porque el PC de la universidad tenía el reloj adelantado unos 54 minutos.

## 2. Seguridad

| Qué | Cómo |
|---|---|
| Leer datos | Solo usuarios con **sesión iniciada** (RLS). Sin sesión, la API responde "permission denied". |
| Enviar órdenes | Solo usuarios en la tabla `operadores` (la función `solicitar_comando` lo comprueba). |
| Escribir lecturas | Solo a través de las funciones, con una **clave de dispositivo** válida. Nadie puede insertar directo en las tablas. |
| Claves de dispositivo | Se guardan solo como hash SHA-256 en el esquema `privado` (no expuesto). Se crean con `privado.crear_dispositivo(...)`, que muestra la clave **una sola vez**, y se anulan con `privado.revocar_dispositivo('id')`. |
| Simulador | Su clave solo puede enviar datos con origen `simulado`: un simulador no puede hacerse pasar por hardware real. |
| ESP32 | Solo escribe en su propia zona y solo ve las órdenes de esa zona. |
| Clave secreta (`sb_secret_`/`service_role`) | **No** se usa en ningún lado: ni en el ESP32, ni en la web, ni en el simulador. |

El asesor de seguridad de Supabase advierte que `registrar_lectura`, `comandos_pendientes` y `confirmar_comando` se pueden ejecutar sin iniciar sesión.
**Es intencional:** el ESP32 no inicia sesión, y cada función exige y valida la clave del dispositivo.

Limitación conocida: en la Prueba 02 el ESP32 cifra la conexión, pero no verifica el certificado del servidor (`setInsecure`). Se corregirá fijando el certificado raíz.

## 3. Cómo lo verá cada persona

1. Abre la web y entra al **Panel de Control**.
2. **Crea una cuenta** (correo y contraseña) y la confirma con el enlace que llega al correo. Después **entra**.
3. Ve las tres zonas y el depósito. Los valores y gráficos se mueven solos al llegar datos nuevos, y cada dato dice si es **REAL** o **SIMULADO**.
4. Si su cuenta es **operador**, puede encender o apagar bomba, extractor y luces. Si no, la cuenta es de **solo lectura**.

Para dar permiso de operador a una cuenta (Supabase > SQL Editor):

```sql
insert into public.operadores (usuario)
select id from auth.users where email = 'correo@ejemplo.com'
on conflict do nothing;
```

**Para que otras personas entren desde su celular falta publicar la web** con una dirección pública (Vercel, Netlify o GitHub Pages; ver el paso 5 abajo).
Mientras tanto, la web corre en tu PC y solo tú la abres, aunque los datos ya estén en la nube.

## 4. Estado de cada pieza

| Pieza | Estado |
|---|---|
| Base de datos (migraciones 0001, 0002 y 0003) | **Aplicada** en `bajoterra-iot`. Lógica probada: 16 casos en PostgreSQL local y prueba con el rol `anon` en la nube |
| Envío por HTTPS desde tu PC | **Probado**: 12 lecturas desde el navegador de tu PC → HTTP 200 y guardadas con la hora correcta |
| Simulador en modo nube (`python -m sim.nube`) | Probado contra PostgREST local (lecturas + órdenes) y con 4 pruebas automáticas. **Falta ejecutarlo en tu PC contra la nube** |
| Web en modo nube (inicio de sesión, Realtime, órdenes) | Probada contra PostgREST local con una sesión de prueba. **Falta probar el inicio de sesión real y Realtime** con tu cuenta |
| Firmware `prueba_02_supabase` | Sintaxis revisada y lógica probada en PC con respuestas imitadas; su JSON fue aceptado por la base de datos local. **No compilado para ESP32 ni probado en placa o Wokwi** |

## 5. Próximos pasos

1. Ejecutar en tu PC el simulador en modo nube y la web en modo nube; crear tu cuenta y darte permiso de operador.
2. Probar la Prueba 02 en Wokwi o en la placa.
3. Publicar la web (Vercel, Netlify o GitHub Pages) para que cualquiera la abra desde su celular.
4. Fijar el certificado raíz en el ESP32.
5. Limpiar las lecturas antiguas automáticamente. El plan gratuito tiene 500 MB, y con lecturas cada 10 s se generan unas 35 000 filas al día.
