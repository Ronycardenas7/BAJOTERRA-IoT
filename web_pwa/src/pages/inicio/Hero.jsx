// ============================================================================
// BAJOTERRA-IoT · Hero Asimétrico (2 Columnas: Verde Bosque + Lima Vibrante)
// Estructura:
//  - Columna Izquierda: Título en 3 líneas de alto impacto + Subtítulo + Botón Lima
//  - Columna Derecha: Fotografía enmarcada con esquinas 24px del invernadero real
// ============================================================================

import React from "react";
import Icono from "../../components/Iconos.jsx";

export default function Hero() {
  return (
    <section className="hero-asimetrico" id="inicio" aria-labelledby="hero-titulo">
      {/* Malla de resplandor suave de fondo en verde bosque */}
      <div className="hero-asimetrico__fondo" aria-hidden="true">
        <div className="hero-asimetrico__glow-bosque" />
        <div className="hero-asimetrico__glow-lima" />
      </div>

      <div className="contenedor hero-asimetrico__grid">
        {/* Columna Izquierda: Textos y Botón Principal CTA */}
        <div className="hero-asimetrico__contenido">
          {/* Pequeña pastilla editorial */}
          <div className="hero-asimetrico__badge">
            <span className="punto-estado punto-estado--lima" aria-hidden="true" />
            <span>Automatización Agronómica en Tarapacá</span>
          </div>

          {/* Título principal en 3 líneas de alto impacto */}
          <h1 id="hero-titulo" className="hero-asimetrico__titulo">
            Invernadero inteligente con control microclimático autónomo
          </h1>

          {/* Subtítulo breve con verde salvia claro */}
          <p className="hero-asimetrico__subtitulo">
            Monitoreo en tiempo real y riego automatizado para tres ecosistemas independientes diseñados para condiciones áridas.
          </p>

          {/* Botón principal sólido en verde lima vibrante */}
          <div className="hero-asimetrico__cta">
            <a className="boton-solido-lima boton-solido-lima--grande" href="#/panel">
              <span>Abrir Panel en Vivo</span>
              <Icono nombre="flecha" tamano={18} />
            </a>
          </div>
        </div>

        {/* Columna Derecha: Fotografía real enmarcada (24px de radio) */}
        <div className="hero-asimetrico__visual">
          <div className="hero-asimetrico__marco-foto">
            <picture>
              <source srcSet="/assets/invernadero-real.svg" type="image/svg+xml" />
              <img
                src="/assets/invernadero-real.jpg"
                alt="Estructura real del invernadero automatizado BAJOTERRA de tres módulos"
                className="hero-asimetrico__foto"
                loading="eager"
                onError={(e) => {
                  // Fallback automático al SVG vectorial si el JPG no carga
                  if (!e.currentTarget.src.endsWith(".svg")) {
                    e.currentTarget.src = "/assets/invernadero-real.svg";
                  }
                }}
              />
            </picture>

            {/* Borde perimetral con brillo sutil lima */}
            <div className="hero-asimetrico__borde-luz" aria-hidden="true" />
          </div>
        </div>
      </div>
    </section>
  );
}
