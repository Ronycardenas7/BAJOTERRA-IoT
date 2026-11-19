// ============================================================================
// BAJOTERRA-IoT · Componente ZonaCard (Fila de Módulos - Estilo Verde Bosque / Lima)
// Diseño:
//  - Imagen superior enmarcada
//  - Título en negrita + subtítulo de módulo
//  - Viñetas con las características del módulo.
// ============================================================================

// Props:
//  - modulo: objeto con la información de la zona o depósito
export default function ZonaCard({ modulo }) {
  const {
    titulo,
    subtitulo,
    imagen,
    especificaciones = [],
  } = modulo;

  return (
    <article className="tarjeta-modulo-editorial" aria-labelledby={`modulo-${modulo.id}`}>
      {/* 1. Imagen superior enmarcada */}
      <div className="tarjeta-modulo-editorial__marco-visual">
        <img
          {...imagen}
          className="tarjeta-modulo-editorial__imagen"
          loading="lazy"
        />
      </div>

      {/* 2. Cabecera con título en negrita y subtítulo */}
      <div className="tarjeta-modulo-editorial__cuerpo">
        <h3 id={`modulo-${modulo.id}`} className="tarjeta-modulo-editorial__titulo">
          {titulo}
        </h3>
        <p className="tarjeta-modulo-editorial__subtitulo">{subtitulo}</p>

        {/* Características del módulo. */}
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
      </div>
    </article>
  );
}
