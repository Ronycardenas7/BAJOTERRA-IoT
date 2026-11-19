// ============================================================================
// BAJOTERRA-IoT · Sección Editorial: "Más que un simple invernadero"
// Estructura:
//  - Bloque superior 2 columnas:
//      · Izquierda: rótulo «Sobre el proyecto», título y descripción
//      · Derecha: carrusel con las fotografías individuales de los microclimas
//  - Fila inferior con 5 indicadores destacados (números grandes en blanco + descripción)
// ============================================================================

// Galería reutilizable de los tres microclimas.
import CarruselZonas from "../../features/zonas/CarruselZonas.jsx";

// Los 5 indicadores destacados de la arquitectura BAJOTERRA-IoT
const METRICAS_CLAVE = [
  { numero: "3", descripcion: "Microclimas independientes" },
  { numero: "3", descripcion: "Nodos de sensores ESP32" },
  { numero: "24/7", descripcion: "Control autónomo local" },
  { numero: "2.4 GHz", descripcion: "Enlace inalámbrico ESP-NOW" },
  { numero: "6", descripcion: "Canales de relé" },
];

export default function Proyecto() {
  return (
    <section className="seccion-editorial-arquitectura" id="arquitectura" aria-labelledby="titulo-editorial">
      <div className="contenedor">
        {/* La descripción del proyecto acompaña a la galería. */}
        <div className="seccion-editorial-arquitectura__top">
          {/* Columna Izquierda: Información editorial de la arquitectura */}
          <div className="seccion-editorial-arquitectura__texto">
            <p className="rotulo-lima">Sobre el proyecto</p>
            <h2 id="titulo-editorial" className="seccion-editorial-arquitectura__titulo">
              Más que un simple invernadero
            </h2>
            <p className="seccion-editorial-arquitectura__parrafo">
              BAJOTERRA revoluciona la evaluación agronómica en el desierto de Tarapacá mediante una red distribuida de microcontroladores ESP32.
              Cada módulo opera con control autónomo en tiempo real mediante algoritmos PI térmicos y riego por pulsos precisos, eliminando la dependencia continua de internet para la supervivencia vegetal.
            </p>
            <p className="seccion-editorial-arquitectura__parrafo">
              La telemetría inalámbrica punto a punto por ESP-NOW (2.4 GHz) comunica los tres nodos sensores con el ESP32 Maestro, el cual sincroniza los eventos y lecturas con la nube Supabase para su visualización y control remoto desde cualquier dispositivo.
            </p>
          </div>

          <CarruselZonas />
        </div>

        {/* Fila de 5 Indicadores Destacados (Números grandes en blanco + descripción abajo) */}
        <div className="seccion-editorial-arquitectura__metricas">
          {METRICAS_CLAVE.map((item, idx) => (
            <div key={idx} className="metrica-destacada">
              <span className="metrica-destacada__numero">{item.numero}</span>
              <span className="metrica-destacada__descripcion">{item.descripcion}</span>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
