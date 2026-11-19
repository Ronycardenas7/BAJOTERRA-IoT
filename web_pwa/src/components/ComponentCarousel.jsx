// React administra la pausa y mide cuándo la galería está visible.
import { useEffect, useRef, useState } from "react";
// El mismo juego de iconos distingue los componentes sin ilustración propia.
import Icono from "./Iconos.jsx";

// Una ficha por tipo de hardware del firmware activo.
const HARDWARE = [
  {
    id: "esp32",
    nombre: "ESP32",
    categoria: "Control y red ESP-NOW",
    descripcion: "Los nodos leen los sensores y envían sus datos por ESP-NOW. El Maestro coordina riego y ventilación y sincroniza las lecturas con Supabase.",
    imagen: "esp32-devkit.svg",
    icono: "cpu",
  },
  {
    id: "pantalla",
    nombre: "Pantalla táctil CYD",
    categoria: "Control local",
    descripcion: "Muestra lecturas y permite enviar órdenes al Maestro mediante un enlace serie UART bidireccional.",
    imagen: "pantalla-cyd.svg",
    icono: "pantalla",
  },
  {
    id: "dht22",
    nombre: "Sensor DHT22",
    categoria: "Medición ambiental",
    descripcion: "Mide la temperatura y la humedad relativa del aire de cada microclima.",
    imagen: "sensor-dht22.svg",
    icono: "termometro",
  },
  {
    id: "fc28",
    nombre: "Sonda de suelo FC-28",
    categoria: "Medición del sustrato",
    descripcion: "Estima la humedad del sustrato. El nodo alimenta la sonda solo al tomar la lectura para limitar la corrosión.",
    imagen: "sonda-suelo.svg",
    icono: "sonda",
  },
  {
    id: "reles",
    nombre: "Módulo de seis relés",
    categoria: "Conmutación",
    descripcion: "El Maestro usa un canal de riego y uno de ventilación por zona para accionar bombas y extractores.",
    imagen: "modulo-reles.svg",
    icono: "rele",
  },
  {
    id: "bombas",
    nombre: "Bombas de agua",
    categoria: "Riego",
    descripcion: "Distribuyen agua a los sustratos. El Maestro controla la duración y la espera entre pulsos de riego.",
    icono: "bomba",
  },
  {
    id: "extractores",
    nombre: "Ventiladores extractores",
    categoria: "Ventilación",
    descripcion: "Renuevan el aire de cada zona. El Maestro regula su tiempo de encendido según la temperatura.",
    icono: "ventilador",
  },
];

// Velocidad constante en píxeles por segundo, independiente de la tasa de refresco.
const VELOCIDAD = 34;

function TarjetaHardware({ item }) {
  return (
    <li className="tarjeta-hardware-horizontal">
      {/* Las ilustraciones complementan el nombre de cada pieza. */}
      <div className="tarjeta-hardware-horizontal__visual" aria-hidden="true">
        {item.imagen ? (
          <img src={`/assets/hardware/${item.imagen}`} alt="" className="tarjeta-hardware-horizontal__imagen" loading="lazy" />
        ) : (
          <Icono nombre={item.icono} tamano={66} />
        )}
      </div>
      <div>
        <div className="tarjeta-hardware-horizontal__etiqueta-fila">
          <span className="tarjeta-hardware-horizontal__etiqueta">{item.categoria}</span>
          <div className="tarjeta-hardware-horizontal__icono" aria-hidden="true">
            <Icono nombre={item.icono} tamano={16} />
          </div>
        </div>
        <h3 className="tarjeta-hardware-horizontal__nombre">{item.nombre}</h3>
        <p className="tarjeta-hardware-horizontal__desc">{item.descripcion}</p>
      </div>
    </li>
  );
}

export default function ComponentCarousel() {
  // La ventana desplaza la única lista de componentes.
  const ventana = useRef(null);
  const [enMarcha, setEnMarcha] = useState(() => !matchMedia("(prefers-reduced-motion: reduce)").matches);
  const [visible, setVisible] = useState(false);
  const [bajoRaton, setBajoRaton] = useState(false);
  const [conFoco, setConFoco] = useState(false);

  useEffect(() => {
    // Evita mover la cinta fuera de la pantalla.
    const observador = new IntersectionObserver(([entrada]) => setVisible(entrada.isIntersecting));
    observador.observe(ventana.current);
    return () => observador.disconnect();
  }, []);

  useEffect(() => {
    // Si se activa el movimiento reducido, el paso a modo manual es inmediato.
    const preferencia = matchMedia("(prefers-reduced-motion: reduce)");
    const alCambiar = (evento) => { if (evento.matches) setEnMarcha(false); };
    preferencia.addEventListener("change", alCambiar);
    return () => preferencia.removeEventListener("change", alCambiar);
  }, []);

  useEffect(() => {
    if (!enMarcha || !visible || bajoRaton || conFoco) return undefined;
    const lista = ventana.current;
    let posicion = lista.scrollTop;
    let anterior = null;
    let cuadro;

    function avanzar(ahora) {
      // Al llegar al final de la lista, el recorrido comienza desde arriba.
      const fin = Math.max(0, lista.scrollHeight - lista.clientHeight);
      const transcurrido = anterior === null ? 0 : Math.min(50, ahora - anterior);
      posicion = posicion >= fin ? 0 : Math.min(fin, posicion + transcurrido * VELOCIDAD / 1000);
      lista.scrollTop = posicion;
      anterior = ahora;
      cuadro = requestAnimationFrame(avanzar);
    }

    cuadro = requestAnimationFrame(avanzar);
    return () => cancelAnimationFrame(cuadro);
  }, [enMarcha, visible, bajoRaton, conFoco]);

  return (
    <section className="seccion-hardware-galeria" id="hardware" aria-labelledby="titulo-hardware">
      <div className="contenedor seccion-hardware-galeria__layout">
        {/* La introducción queda fija mientras las fichas se desplazan. */}
        <div className="seccion-hardware-galeria__columna-fija">
          <p className="rotulo-lima">Arquitectura distribuida</p>
          <h2 id="titulo-hardware" className="seccion-hardware-galeria__titulo">Hardware del sistema</h2>
          <p className="seccion-hardware-galeria__descripcion">
            Los componentes que miden, comunican y controlan los tres microclimas.
          </p>
          <button
            type="button"
            className="boton-contorno-lima"
            aria-controls="carrusel-hardware"
            onClick={() => setEnMarcha((marcha) => !marcha)}
          >
            {enMarcha ? "Pausar desplazamiento" : "Iniciar desplazamiento"}
          </button>
        </div>

        {/* Se puede detener con el ratón, el foco o un gesto táctil para leer y recorrer la lista. */}
        <div
          className="seccion-hardware-galeria__visor"
          id="carrusel-hardware"
          role="region"
          aria-label="Componentes del hardware"
          tabIndex={0}
          ref={ventana}
          onPointerEnter={(evento) => { if (evento.pointerType === "mouse") setBajoRaton(true); }}
          onPointerLeave={() => setBajoRaton(false)}
          onFocus={() => setConFoco(true)}
          onBlur={() => setConFoco(false)}
          onTouchStart={() => setEnMarcha(false)}
        >
          <ul className="seccion-hardware-galeria__tarjetas">
            {HARDWARE.map((item) => <TarjetaHardware key={item.id} item={item} />)}
          </ul>
        </div>
      </div>
    </section>
  );
}
