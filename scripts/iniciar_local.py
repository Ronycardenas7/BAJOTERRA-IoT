"""Inicia broker + backend + simulador SIN Docker, todo desde Python, con un solo comando.

Uso (desde la raiz del proyecto, con el entorno virtual activo):
    python scripts/iniciar_local.py

Detener todo: Ctrl+C en esta ventana.
La web se inicia aparte (ver README: seccion "Sin Docker").
"""

# Anotaciones de tipo modernas en cualquier version de Python.
from __future__ import annotations

# os: leer y copiar variables de entorno.
import os
# subprocess: lanzar los programas hijos (broker, backend, simulador).
import subprocess
# sys: ruta del Python actual y codigos de salida.
import sys
# time: esperas cortas entre pasos.
import time
# signal: convertir la senal de terminacion en una parada ordenada.
import signal
# socket: comprobar que el broker ya acepta conexiones.
import socket
# Path: rutas compatibles con Windows y Linux.
from pathlib import Path

# Carpeta raiz del proyecto (un nivel arriba de scripts/).
RAIZ = Path(__file__).resolve().parent.parent


def leer_env(ruta: Path) -> dict[str, str]:
    """Lee un archivo .env sencillo (CLAVE=valor); ignora comentarios y lineas vacias."""
    # Diccionario de resultados.
    valores: dict[str, str] = {}
    # Si no hay .env, devuelve vacio y el programa avisara despues.
    if not ruta.is_file():
        return valores
    # Recorre las lineas del archivo.
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        # Quita espacios sobrantes.
        linea = linea.strip()
        # Salta comentarios, vacias y lineas sin "=".
        if not linea or linea.startswith("#") or "=" not in linea:
            continue
        # Divide en la primera "=".
        clave, valor = linea.split("=", 1)
        # Guarda el par limpio.
        valores[clave.strip()] = valor.strip()
    # Devuelve el diccionario.
    return valores


def esperar_puerto(host: str, puerto: int, segundos: float) -> bool:
    """Espera hasta que (host, puerto) acepte conexiones TCP; devuelve False si se agota el tiempo."""
    # Momento limite para rendirse.
    limite = time.monotonic() + segundos
    # Reintenta hasta el limite.
    while time.monotonic() < limite:
        try:
            # Intenta conectar con 1 s de tolerancia; si funciona, el puerto esta abierto.
            with socket.create_connection((host, puerto), timeout=1):
                return True
        except OSError:
            # Aun no esta listo: espera un momento y reintenta.
            time.sleep(0.3)
    # Se acabo el tiempo.
    return False


def main() -> int:
    """Lanza los tres procesos y los vigila hasta Ctrl+C o hasta que uno se caiga."""
    # Variables del .env; las del entorno real tienen prioridad.
    env_archivo = leer_env(RAIZ / ".env")
    if not env_archivo.get("MQTT_PASSWORD"):
        print("No hay .env o falta MQTT_PASSWORD. Ejecuta: copy .env.example .env  y edita la clave.", file=sys.stderr)
        return 1
    # Entorno comun de los tres programas: .env + valores para que se encuentren en este equipo.
    entorno = {**env_archivo, **os.environ}
    puerto = entorno.get("MQTT_PUERTO_HOST", "1883")
    # El broker estara en este mismo equipo, en el puerto elegido.
    entorno["MQTT_HOST"] = "127.0.0.1"
    entorno["MQTT_PUERTO"] = puerto
    # Muestra la salida de Python sin retraso (util para ver los registros).
    entorno["PYTHONUNBUFFERED"] = "1"

    # Si el sistema pide terminar (SIGTERM), se trata igual que Ctrl+C para detener bien a los hijos.
    signal.signal(signal.SIGTERM, lambda *_: (_ for _ in ()).throw(KeyboardInterrupt()))

    # Lista de procesos hijos: (nombre, comando, carpeta de trabajo).
    py = sys.executable
    plan = [
        ("broker", [py, "broker.py"], RAIZ / "broker_local"),
        ("backend", [py, "run.py"], RAIZ / "backend"),
        ("simulador", [py, "-m", "sim"], RAIZ / "simulador"),
    ]
    # Procesos ya iniciados (para poder detenerlos al final).
    procesos: list[tuple[str, subprocess.Popen]] = []
    try:
        for nombre, comando, carpeta in plan:
            # Lanza el programa hijo en su carpeta, con el entorno comun.
            proceso = subprocess.Popen(comando, cwd=carpeta, env=entorno)
            procesos.append((nombre, proceso))
            print(f"[iniciar_local] {nombre} iniciado (pid {proceso.pid})")
            # Despues del broker, espera a que acepte conexiones antes de lanzar los clientes.
            if nombre == "broker" and not esperar_puerto("127.0.0.1", int(puerto), 20):
                print("[iniciar_local] el broker no abrio el puerto a tiempo", file=sys.stderr)
                return 1
        print("[iniciar_local] Listo. Backend: http://127.0.0.1:5000/salud   (Ctrl+C para detener todo)")
        # Vigila: si algun hijo termina, se informa y se detiene todo.
        while True:
            time.sleep(1)
            for nombre, proceso in procesos:
                if proceso.poll() is not None:
                    print(f"[iniciar_local] {nombre} termino con codigo {proceso.returncode}; se detiene todo.", file=sys.stderr)
                    return 1
    except KeyboardInterrupt:
        # Ctrl+C: parada normal pedida por el usuario.
        print("\n[iniciar_local] Deteniendo...")
        return 0
    finally:
        # Pide a cada hijo que termine (en orden inverso: simulador, backend, broker).
        for nombre, proceso in reversed(procesos):
            if proceso.poll() is None:
                proceso.terminate()
        # Espera hasta 5 s por proceso y fuerza el cierre si no obedece.
        for nombre, proceso in procesos:
            try:
                proceso.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proceso.kill()


# Solo se ejecuta si se lanza el archivo directamente.
if __name__ == "__main__":
    sys.exit(main())
