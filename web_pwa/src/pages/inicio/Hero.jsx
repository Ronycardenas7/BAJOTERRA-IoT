// Sección de portada: mensaje principal y accesos al Panel de Control.

// Iconos y datos de zonas.
import Icono from "../../components/Iconos.jsx";
import { ZONAS } from "../../features/zonas/zonas.js";

// Componente sin props.
export default function Hero() {
  // Devuelve la sección.
  return (
    // Sección de portada con fondo decorativo hecho con CSS.
    <section className="hero" aria-labelledby="titulo-hero">
      {/* Contenido por encima del fondo. */}
      <div className="contenedor hero__interior">
        {/* Estado honesto del sistema (no se afirma que esté "activo" con sensores reales). */}
        <p className="pastilla">
          {/* Punto que parpadea. */}
          <span className="punto" aria-hidden="true" />
          Invernadero 01 — en desarrollo, datos simulados
        </p>
        {/* Título principal. */}
        <h1 id="titulo-hero">
          Tres ecosistemas, <span>control total.</span>
        </h1>
        {/* Descripción. */}
        <p className="hero__texto">
          BAJOTERRA monitorea y controla un invernadero con tres zonas independientes —árida, húmeda y selvática—: temperatura, humedad, CO₂, luz, riego y ventilación desde un solo panel.
        </p>
        {/* Botones de acción. */}
        <div className="hero__acciones">
          {/* Acceso al panel. */}
          <a className="boton boton--primario boton--grande" href="#/panel">
            Acceder al Control
            <Icono nombre="flecha" tamano={18} />
          </a>
          {/* Baja a la sección del proyecto. */}
          <a className="enlace-sutil" href="#proyecto">
            Conocer más
          </a>
        </div>
        {/* Las tres zonas, con su color. */}
        <ul className="hero__zonas" aria-label="Zonas de evaluación" style={{ listStyle: "none", padding: 0, marginBottom: 0 }}>
          {ZONAS.map((zona) => (
            // Cada zona con su icono y color de acento.
            <li key={zona.id} className={`chip-zona zona--${zona.id}`}>
              <Icono nombre={zona.icono} tamano={18} />
              {zona.nombre}
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}
