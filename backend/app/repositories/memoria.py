# Implementación de los repositorios EN MEMORIA. Los datos se pierden al reiniciar el backend.
# Sirve para desarrollar y probar sin depender de Supabase. No es almacenamiento histórico definitivo.

# Permite anotaciones de tipos modernas.
from __future__ import annotations

# deque es una cola con tamaño máximo: al llenarse descarta lo más antiguo.
from collections import OrderedDict, deque
# Lock evita que dos hilos (MQTT y HTTP) modifiquen los datos a la vez.
from threading import Lock

# Zonas y depósitos conocidos, para preparar una cola por cada uno.
from app.domain.constantes import DEPOSITOS, ZONAS
# Entidades que se guardan.
from app.domain.modelos import Comando, EstadoDispositivo, LecturaDeposito, LecturaZona


# Guarda lecturas de zonas y depósitos en colas de tamaño fijo.
class RepositorioTelemetriaMemoria:
    # max_lecturas = cuántas lecturas se conservan por zona o depósito.
    def __init__(self, max_lecturas: int) -> None:
        # Cerrojo para acceso seguro desde varios hilos.
        self._cerrojo = Lock()
        # Una cola de lecturas por cada zona conocida.
        self._zonas = {zona: deque(maxlen=max_lecturas) for zona in ZONAS}
        # Una cola de lecturas por cada depósito conocido.
        self._depositos = {deposito: deque(maxlen=max_lecturas) for deposito in DEPOSITOS}
        # Cola con los últimos id_mensaje vistos, para detectar duplicados (QoS 1 puede repetir mensajes).
        self._ids_orden = deque(maxlen=max_lecturas * 4)
        # Conjunto con los mismos ids para consultar rápido si uno ya existe.
        self._ids_vistos = set()

    # Registra un id_mensaje; devuelve False si ya existía. Debe llamarse con el cerrojo tomado.
    def _registrar_id(self, id_mensaje: str) -> bool:
        # Si el id ya se vio, es un duplicado.
        if id_mensaje in self._ids_vistos:
            # Se avisa al llamador para que lo ignore.
            return False
        # Si la cola de ids está llena, el id más antiguo saldrá: se quita también del conjunto.
        if len(self._ids_orden) == self._ids_orden.maxlen:
            # Quita del conjunto el id más antiguo (el primero de la cola).
            self._ids_vistos.discard(self._ids_orden[0])
        # Agrega el nuevo id a la cola.
        self._ids_orden.append(id_mensaje)
        # Agrega el nuevo id al conjunto.
        self._ids_vistos.add(id_mensaje)
        # Confirma que era un id nuevo.
        return True

    # Guarda una lectura de zona si no es duplicada.
    def guardar_zona(self, lectura: LecturaZona) -> bool:
        # Toma el cerrojo mientras se modifica la memoria.
        with self._cerrojo:
            # Si el id ya existía, no se guarda.
            if not self._registrar_id(lectura.id_mensaje):
                # Informa que fue un duplicado.
                return False
            # Agrega la lectura a la cola de su zona.
            self._zonas[lectura.zona].append(lectura)
            # Informa que se guardó.
            return True

    # Guarda una lectura de depósito si no es duplicada.
    def guardar_deposito(self, lectura: LecturaDeposito) -> bool:
        # Toma el cerrojo mientras se modifica la memoria.
        with self._cerrojo:
            # Si el id ya existía, no se guarda.
            if not self._registrar_id(lectura.id_mensaje):
                # Informa que fue un duplicado.
                return False
            # Agrega la lectura a la cola de su depósito.
            self._depositos[lectura.deposito].append(lectura)
            # Informa que se guardó.
            return True

    # Devuelve la última lectura de una zona.
    def ultima_zona(self, zona: str) -> LecturaZona | None:
        # Toma el cerrojo para leer sin que cambie a mitad de camino.
        with self._cerrojo:
            # Cola de la zona pedida.
            cola = self._zonas[zona]
            # El último elemento es el más reciente; si la cola está vacía, None.
            return cola[-1] if cola else None

    # Devuelve las últimas "limite" lecturas de una zona, de la más antigua a la más reciente.
    def historial_zona(self, zona: str, limite: int) -> list[LecturaZona]:
        # Toma el cerrojo para copiar los datos de forma segura.
        with self._cerrojo:
            # Convierte la cola a lista y se queda con las últimas "limite".
            return list(self._zonas[zona])[-limite:]

    # Devuelve la última lectura de un depósito.
    def ultima_deposito(self, deposito: str) -> LecturaDeposito | None:
        # Toma el cerrojo para leer de forma segura.
        with self._cerrojo:
            # Cola del depósito pedido.
            cola = self._depositos[deposito]
            # El último elemento es el más reciente; si la cola está vacía, None.
            return cola[-1] if cola else None


# Guarda el último estado de conexión conocido de cada dispositivo.
class RepositorioDispositivosMemoria:
    # Constructor sin parámetros.
    def __init__(self) -> None:
        # Cerrojo para acceso seguro desde varios hilos.
        self._cerrojo = Lock()
        # Diccionario dispositivo -> último estado.
        self._estados: dict[str, EstadoDispositivo] = {}

    # Guarda o reemplaza el estado de un dispositivo.
    def guardar(self, estado: EstadoDispositivo) -> None:
        # Toma el cerrojo mientras se modifica el diccionario.
        with self._cerrojo:
            # Reemplaza el estado anterior.
            self._estados[estado.dispositivo] = estado

    # Devuelve el estado de un dispositivo, o None si nunca informó.
    def obtener(self, dispositivo: str) -> EstadoDispositivo | None:
        # Toma el cerrojo para leer de forma segura.
        with self._cerrojo:
            # get devuelve None si la clave no existe.
            return self._estados.get(dispositivo)


# Guarda los comandos más recientes, indexados por id.
class RepositorioComandosMemoria:
    # max_comandos = cuántos comandos se conservan.
    def __init__(self, max_comandos: int) -> None:
        # Cerrojo para acceso seguro desde varios hilos.
        self._cerrojo = Lock()
        # Límite de comandos conservados.
        self._maximo = max_comandos
        # OrderedDict recuerda el orden de inserción: el primero es el más antiguo.
        self._comandos: OrderedDict[str, Comando] = OrderedDict()

    # Guarda o reemplaza un comando.
    def guardar(self, comando: Comando) -> None:
        # Toma el cerrojo mientras se modifica el diccionario.
        with self._cerrojo:
            # Guarda (o reemplaza) el comando por su id.
            self._comandos[comando.id_comando] = comando
            # Mientras haya más comandos que el máximo...
            while len(self._comandos) > self._maximo:
                # ...elimina el más antiguo (last=False = el primero insertado).
                self._comandos.popitem(last=False)

    # Devuelve un comando por id.
    def obtener(self, id_comando: str) -> Comando | None:
        # Toma el cerrojo para leer de forma segura.
        with self._cerrojo:
            # get devuelve None si el id no existe.
            return self._comandos.get(id_comando)

    # Devuelve los últimos comandos de una zona, del más reciente al más antiguo.
    def listar_zona(self, zona: str, limite: int) -> list[Comando]:
        # Toma el cerrojo para copiar los datos de forma segura.
        with self._cerrojo:
            # Filtra por zona (reversed = del más reciente al más antiguo) y recorta al límite.
            propios = [c for c in reversed(self._comandos.values()) if c.zona == zona]
            # Devuelve solo los primeros "limite".
            return propios[:limite]
