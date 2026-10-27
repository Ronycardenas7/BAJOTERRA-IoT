// Componente raíz: barra fija, página según la ruta (inicio o panel) y pie.

// useEffect se usa para volver arriba o ir a la sección pedida al cambiar de ruta.
import { useEffect } from "react";
// Piezas comunes.
import Encabezado from "../components/Encabezado.jsx";
import LimiteDeError from "../components/LimiteDeError.jsx";
import Pie from "../components/Pie.jsx";
// Páginas.
import Inicio from "../pages/Inicio.jsx";
import Panel from "../pages/Panel.jsx";
// Hook de ruta.
import { useRuta } from "./useRuta.js";

// Componente de la aplicación.
export default function App() {
  // Ruta actual: "inicio" o "panel".
  const ruta = useRuta();

  // Al cambiar de página: si la dirección trae un ancla (#zonas) se baja a ella; si no, se sube al comienzo.
  useEffect(() => {
    // Nombre del ancla sin el "#"; "/" y "/panel" no son anclas.
    const ancla = window.location.hash.slice(1);
    // Elemento de la ancla, si existe.
    const destino = ancla && !ancla.startsWith("/") ? document.getElementById(ancla) : null;
    // Baja a la sección o vuelve al comienzo de la página.
    if (destino) destino.scrollIntoView();
    else window.scrollTo(0, 0);
  }, [ruta]);

  // Devuelve la estructura de la página.
  return (
    // Contenedor general de la aplicación.
    <div className="app">
      {/* Barra de navegación fija (siempre con acceso al Panel de Control). */}
      <Encabezado ruta={ruta} />
      {/* Contenido principal. */}
      <main className="app__contenido">
        {/* Red de seguridad: si algo falla al dibujar, se muestra un aviso en lugar de una página en blanco. */}
        <LimiteDeError>
          {/* Elige la página según la ruta. */}
          {ruta === "panel" ? <Panel /> : <Inicio />}
        </LimiteDeError>
      </main>
      {/* Pie de página. */}
      <Pie />
    </div>
  );
}
