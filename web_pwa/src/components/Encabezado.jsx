// Barra de navegación fija con efecto vidrio. Mantiene siempre visible el acceso al Panel de Control.

// Iconos.
import Icono from "./Iconos.jsx";

// Enlaces de la página de inicio (anclas a las secciones).
const ENLACES = [
  { href: "#proyecto", texto: "Proyecto" },
  { href: "#capacidades", texto: "Capacidades" },
  { href: "#zonas", texto: "Zonas" },
  { href: "#variables", texto: "Variables" },
];

// Props: ruta actual ("inicio" o "panel").
export default function Encabezado({ ruta }) {
  // Devuelve la barra.
  return (
    // <header> semántico; la clase "barra" la fija arriba y le da el efecto vidrio.
    <header className="barra">
      {/* Contenedor centrado. */}
      <div className="contenedor barra__fila">
        {/* Marca: vuelve al inicio. */}
        <a className="marca" href="#/" aria-label="BAJOTERRA, ir al inicio">
          {/* Icono de hoja. */}
          <Icono nombre="hoja" tamano={26} />
          {/* Nombre del proyecto. */}
          BAJOTERRA
        </a>
        {/* Enlaces a las secciones (se ocultan en pantallas angostas). */}
        <nav className="barra__enlaces" aria-label="Secciones de la página">
          {ENLACES.map(({ href, texto }) => (
            // Cada enlace apunta a una ancla de la página de inicio.
            <a key={href} href={href}>
              {texto}
            </a>
          ))}
        </nav>
        {/* Acceso al Panel de Control (se resalta cuando ya se está en él). */}
        <a className="boton boton--primario" href="#/panel" aria-current={ruta === "panel" ? "page" : undefined}>
          {/* Texto del botón. */}
          Panel de Control
          {/* Flecha. */}
          <Icono nombre="flecha" tamano={16} />
        </a>
      </div>
    </header>
  );
}
