// ============================================================================
// BAJOTERRA-IoT · Componente ZonaCard (Fila de Módulos - Estilo Verde Bosque / Lima)
// Diseño:
//  - Imagen superior enmarcada
//  - Título en negrita + subtítulo de módulo
//  - 3 viñetas de especificaciones (planta, sustrato, régimen)
//  - Doble píldora inferior: estado en lima + botón oscuro "Ver zona" (-> #/panel)
// ============================================================================

import React from "react";
import Icono from "../../components/Iconos.jsx";

// Props:
//  - modulo: objeto con la información de la zona o depósito
export default function ZonaCard({ modulo }) {
  const {
    titulo,
    subtitulo,
    imagen,
    especificaciones = [],
    estado = "Operativo",
    enlace = "#/panel",
  } = modulo;

  return (
    <article className="tarjeta-modulo-editorial" aria-labelledby={`modulo-${modulo.id}`}>
      {/* 1. Imagen superior enmarcada */}
      <div className="tarjeta-modulo-editorial__marco-visual">
        <img
          src={imagen}
          alt={`Visualización botánica/técnica de ${titulo}`}
          className="tarjeta-modulo-editorial__imagen"
          loading="lazy"
          onError={(e) => {
            // Fallback en caso de error de carga
            e.currentTarget.style.opacity = "0.7";
          }}
        />
      </div>

      {/* 2. Cabecera con título en negrita y subtítulo */}
      <div className="tarjeta-modulo-editorial__cuerpo">
        <h3 id={`modulo-${modulo.id}`} className="tarjeta-modulo-editorial__titulo">
          {titulo}
        </h3>
        <p className="tarjeta-modulo-editorial__subtitulo">{subtitulo}</p>

        {/* 3. Tres especificaciones breves con viñetas limpias */}
        <ul className="tarjeta-modulo-editorial__lista">
          {especificaciones.map((item, idx) => (
            <li key={idx} className="tarjeta-modulo-editorial__item">
              <span className="tarjeta-modulo-editorial__vineta" aria-hidden="true">
                •
              </span>
              <span>{item}</span>
            </li>
          ))}
        </ul>

        {/* 4. Doble píldora inferior: Estado en lima + Botón oscuro "Ver zona" */}
        <div className="tarjeta-modulo-editorial__pie">
          <span className="pildora-estado-lima">
            <span className="punto-estado punto-estado--lima-pequeno" aria-hidden="true" />
            {estado}
          </span>

          <a
            className="boton-ver-zona"
            href={enlace}
            title={`Abrir panel en tiempo real de ${titulo}`}
          >
            <span>Ver zona</span>
            <Icono nombre="flecha" tamano={13} />
          </a>
        </div>
      </div>
    </article>
  );
}
