// ============================================================================
// BAJOTERRA-IoT · Sección Editorial: "Más que un simple invernadero"
// Estructura:
//  - Bloque superior 2 columnas:
//      · Izquierda: Etiqueta "Sobre el proyecto / Arquitectura" + Título + Párrafos
//      · Derecha: Fotografía circular grande (border-radius: 50%) con borde lima sutil
//  - Fila inferior con 5 indicadores destacados (números grandes en blanco + descripción)
// ============================================================================

import React from "react";

// Los 5 indicadores destacados de la arquitectura BAJOTERRA-IoT
const METRICAS_CLAVE = [
  { numero: "3", descripcion: "Microclimas independientes" },
  { numero: "4", descripcion: "Microcontroladores ESP32" },
  { numero: "24/7", descripcion: "Control autónomo local" },
  { numero: "2.4 GHz", descripcion: "Enlace inalámbrico ESP-NOW" },
  { numero: "100%", descripcion: "Telemetría en tiempo real" },
];

export default function Proyecto() {
  return (
    <section className="seccion-editorial-arquitectura" id="arquitectura" aria-labelledby="titulo-editorial">
      <div className="contenedor">
        {/* Bloque superior de 2 columnas: Texto + Fotografía Circular */}
        <div className="seccion-editorial-arquitectura__top">
          {/* Columna Izquierda: Información editorial de la arquitectura */}
          <div className="seccion-editorial-arquitectura__texto">
            <p className="rotulo-lima">Sobre el proyecto / Arquitectura</p>
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

          {/* Columna Derecha: Fotografía circular grande con borde lima sutil */}
          <div className="seccion-editorial-arquitectura__circulo-marco">
            <div className="foto-circular-invernadero">
              <picture>
                <source srcSet="/assets/invernadero-real.svg" type="image/svg+xml" />
                <img
                  src="/assets/invernadero-real.jpg"
                  alt="Estructura e interior del invernadero BAJOTERRA"
                  className="foto-circular-invernadero__img"
                  loading="lazy"
                  onError={(e) => {
                    if (!e.currentTarget.src.endsWith(".svg")) {
                      e.currentTarget.src = "/assets/invernadero-real.svg";
                    }
                  }}
                />
              </picture>
              {/* Anillo de resplandor lima */}
              <div className="foto-circular-invernadero__anillo" aria-hidden="true" />
            </div>
          </div>
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
