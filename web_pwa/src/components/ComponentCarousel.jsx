// ============================================================================
// BAJOTERRA-IoT · Galería de Hardware del Sistema ("Componentes del Sistema")
// Inspirada en la sección "Nuestros trabajos" de la imagen de referencia:
//  - Columna izquierda fija: Título "Hardware del Sistema" + descripción
//  - Columna derecha: 3 tarjetas horizontales con imágenes de alta fidelidad
// ============================================================================

import React from "react";
import Icono from "./Iconos.jsx";

// Los 3 bloques principales de hardware físico integrado
const GRUPOS_HARDWARE = [
  {
    id: "esp32-maestro-nodos",
    nombre: "ESP32 Maestro & Nodos",
    etiqueta: "Cerebro Central & RF",
    descripcion:
      "Microcontroladores dual-core que ejecutan algoritmos de control PI y transmisión inalámbrica ESP-NOW de 2.4 GHz cada 2 segundos sin cables.",
    imagen: "/assets/hardware/esp32-devkit.svg",
    icono: "cpu",
  },
  {
    id: "pantalla-cyd",
    nombre: "Pantalla Táctil CYD 2.8\"",
    etiqueta: "HMI Local Resistiva",
    descripcion:
      "Display a color ILI9341 con controlador táctil XPT2046 y bus UART serie bidireccional (IO22 RX / IO27 TX) para operar en terreno sin internet.",
    imagen: "/assets/hardware/pantalla-cyd.svg",
    icono: "pantalla",
  },
  {
    id: "sensores-reles",
    nombre: "Sensores & Relés de Riego",
    etiqueta: "Instrumentación & Potencia",
    descripcion:
      "Termohigrómetros DHT22, sondas de suelo energizadas por GPIO 25 para evitar electrólisis y 6 relés optoacoplados para electrobombas y extractores.",
    imagen: "/assets/hardware/modulo-reles.svg",
    icono: "rele",
  },
];

export default function ComponentCarousel() {
  return (
    <section className="seccion-hardware-galeria" id="hardware" aria-labelledby="titulo-hardware">
      <div className="contenedor seccion-hardware-galeria__layout">
        {/* Columna Izquierda Fija: Título y Contexto Técnico */}
        <div className="seccion-hardware-galeria__columna-fija">
          <p className="rotulo-lima">Arquitectura Distribuida</p>
          <h2 id="titulo-hardware" className="seccion-hardware-galeria__titulo">
            Hardware del Sistema
          </h2>
          <p className="seccion-hardware-galeria__descripcion">
            Dispositivos electrónicos físicos montados en los tres módulos de PVC y textil del invernadero, comunicados de forma autónoma y sincronizados con la nube.
          </p>

          <div className="seccion-hardware-galeria__detalle-fijo">
            <span className="pildora-estado-lima">
              <span className="punto-estado punto-estado--lima-pequeno" aria-hidden="true" />
              Hardware v3.0 Operativo
            </span>
            <p className="seccion-hardware-galeria__nota-pie">
              Diseño de bajo consumo optimizado para autonomía en terreno y comunicación sin interferencias.
            </p>
          </div>
        </div>

        {/* Columna Derecha: 3 Tarjetas Horizontales con Fotografías/Diagramas Reales */}
        <div className="seccion-hardware-galeria__tarjetas">
          {GRUPOS_HARDWARE.map((item) => (
            <article key={item.id} className="tarjeta-hardware-horizontal">
              {/* Marco con la imagen técnica o fotografía real */}
              <div className="tarjeta-hardware-horizontal__visual">
                <img
                  src={item.imagen}
                  alt={`Fotografía y diagrama de ${item.nombre}`}
                  className="tarjeta-hardware-horizontal__imagen"
                  loading="lazy"
                  onError={(e) => {
                    e.currentTarget.style.opacity = "0.7";
                  }}
                />
              </div>

              {/* Información y especificaciones del bloque de hardware */}
              <div className="tarjeta-hardware-horizontal__info">
                <div className="tarjeta-hardware-horizontal__etiqueta-fila">
                  <span className="tarjeta-hardware-horizontal__etiqueta">{item.etiqueta}</span>
                  <div className="tarjeta-hardware-horizontal__icono" aria-hidden="true">
                    <Icono nombre={item.icono} tamano={16} />
                  </div>
                </div>

                <h3 className="tarjeta-hardware-horizontal__nombre">{item.nombre}</h3>
                <p className="tarjeta-hardware-horizontal__desc">{item.descripcion}</p>
              </div>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}
