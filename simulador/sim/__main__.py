# Permite ejecutar el simulador con: python -m sim

# Importa la función principal.
from sim.main import ejecutar

# Solo se ejecuta si el archivo se lanza directamente.
if __name__ == "__main__":
    # raise SystemExit(código) termina el programa devolviendo el código de salida de ejecutar().
    raise SystemExit(ejecutar())
