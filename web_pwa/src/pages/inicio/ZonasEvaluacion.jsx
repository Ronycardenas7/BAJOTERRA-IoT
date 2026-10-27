// Sección "Zonas de evaluación": las tres zonas con su enfoque y acceso al panel.

// Iconos y datos de zonas.
import Icono from "../../components/Iconos.jsx";
import { ZONAS } from "../../features/zonas/zonas.js";

// Componente sin props.
export default function ZonasEvaluacion() {
  // Devuelve la sección.
  return (
    // Sección ancla "#zonas".
    <section className="seccion" id="zonas" aria-labelledby="titulo-zonas">
      {/* Contenedor. */}
      <div className="contenedor">
        {/* Rótulo, título y bajada. */}
        <p className="rotulo">Zonas de evaluación</p>
        <h2 className="titulo-seccion" id="titulo-zonas">
          Tres ecosistemas en paralelo
        </h2>
        <p className="bajada">Cada zona tiene su propio clima objetivo, sus sensores y sus actuadores. Se evalúan al mismo tiempo para comparar su comportamiento.</p>
        {/* Rejilla de cartas, una por zona. */}
        <div className="rejilla-cartas">
          {ZONAS.map((zona) => (
            // La clase de la zona define el color de acento.
            <article className={`carta zona--${zona.id}`} key={zona.id}>
              {/* Icono. */}
              <div className="carta__icono">
                <Icono nombre={zona.icono} />
              </div>
              {/* Nombre y descripción. */}
              <h3>{zona.nombre}</h3>
              <p>{zona.descripcion}</p>
              {/* Variables que se vigilan. */}
              <div className="chips">
                {zona.etiquetas.map((etiqueta) => (
                  // Una etiqueta por variable.
                  <span className="chip" key={etiqueta}>
                    {etiqueta}
                  </span>
                ))}
              </div>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}
