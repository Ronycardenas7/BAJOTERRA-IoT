// ============================================================================
// BAJOTERRA-IoT · Sección Final: Variables Monitoreadas (Círculos Conectados)
// Inspirada en la fila inferior de iconos de la referencia visual:
//  - Círculos simétricos con iconos vectoriales limpios en lima y blanco
//  - Las 6 magnitudes ambientales medidas por el sistema
// ============================================================================

import React from "react";
import Icono from "../../components/Iconos.jsx";

// Catálogo de las 6 variables monitoreadas
const VARIABLES_SISTEMA = [
  { id: "temperatura", nombre: "Temperatura", icono: "termometro", rango: "−40 a 85 °C" },
  { id: "humedad-aire", nombre: "Humedad del Aire", icono: "gota", rango: "0 – 100 % HR" },
  { id: "humedad-sustrato", nombre: "Humedad del Sustrato", icono: "sonda", rango: "0 – 100 %" },
  { id: "co2", nombre: "CO₂", icono: "nube", rango: "250 – 5000 ppm" },
  { id: "radiacion-solar", nombre: "Radiación Solar", icono: "sol", rango: "0 – 1500 W/m²" },
  { id: "conductividad", nombre: "Conductividad", icono: "conductividad", rango: "0 – 20 mS/cm" },
];

export default function Variables() {
  return (
    <section className="seccion-variables-conectadas" id="variables" aria-labelledby="titulo-variables">
      <div className="contenedor">
        {/* Encabezado editorial */}
        <div className="seccion-variables-conectadas__cabecera">
          <p className="rotulo-lima">Variables Ambientales</p>
          <h2 id="titulo-variables" className="seccion-variables-conectadas__titulo">
            Magnitudes Monitoreadas en Tiempo Real
          </h2>
          <p className="seccion-variables-conectadas__bajada">
            Sensores de precisión que reportan continuamente las condiciones de cada microclima hacia la red de control.
          </p>
        </div>

        {/* Fila de círculos simétricos conectados visualmente */}
        <div className="seccion-variables-conectadas__fila">
          {/* Línea conectora horizontal sutil en el fondo */}
          <div className="seccion-variables-conectadas__linea-guia" aria-hidden="true" />

          {VARIABLES_SISTEMA.map((item, index) => (
            <div key={item.id} className="circulo-variable-item">
              {/* Círculo simétrico con borde y acento en lima */}
              <div className="circulo-variable-item__aro" tabIndex={0} aria-label={`${item.nombre}: rango ${item.rango}`}>
                {/* Indicador numérico de paso sutil */}
                <span className="circulo-variable-item__indice" aria-hidden="true">
                  0{index + 1}
                </span>

                {/* Icono vectorial limpio en lima/blanco */}
                <div className="circulo-variable-item__icono">
                  <Icono nombre={item.icono} tamano={28} />
                </div>
              </div>

              {/* Título de la variable */}
              <h3 className="circulo-variable-item__nombre">{item.nombre}</h3>
              <span className="circulo-variable-item__rango">{item.rango}</span>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
