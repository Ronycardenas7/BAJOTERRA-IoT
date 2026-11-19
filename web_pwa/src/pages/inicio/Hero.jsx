// Portada con el texto del proyecto sobre un fondo fotográfico.
import { FOTO_FONDO } from "../../config/fotos.js";

export default function Hero() {
  return (
    <section className="hero-asimetrico" id="inicio" aria-labelledby="hero-titulo">
      {/* Fondo ambiental de Brands&People en Unsplash. */}
      <img
        className="hero-asimetrico__fondo"
        {...FOTO_FONDO}
        fetchPriority="high"
      />

      <div className="contenedor">
        {/* Texto que presenta el proyecto. */}
        <div className="hero-asimetrico__contenido">
          {/* Pequeña pastilla editorial */}
          <div className="hero-asimetrico__badge">
            <span className="punto-estado punto-estado--lima" aria-hidden="true" />
            <span>Automatización Agronómica en Tarapacá</span>
          </div>

          {/* Título principal en 3 líneas de alto impacto */}
          <h1 id="hero-titulo" className="hero-asimetrico__titulo">
            Control autónomo de microclimas en un <span>invernadero inteligente</span>
          </h1>

          {/* Subtítulo breve con verde salvia claro */}
          <p className="hero-asimetrico__subtitulo">
            Monitoreo en tiempo real y automatizado para tres ecosistemas independientes diseñados para condiciones áridas.
          </p>
        </div>
      </div>
    </section>
  );
}
