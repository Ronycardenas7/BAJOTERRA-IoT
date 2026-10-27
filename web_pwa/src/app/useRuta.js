// Mini enrutador sin librerías: la "ruta" es el hash de la dirección (#/panel).
// Así la página funciona con cualquier servidor estático sin configurar redirecciones.

// useEffect conecta con eventos del navegador; useState guarda la ruta actual.
import { useEffect, useState } from "react";

// Convierte el hash de la dirección en el nombre de la ruta.
function leerRuta() {
  // "#/panel" abre el Panel de Control; cualquier otro hash (incluidas las anclas #zonas) es la página de inicio.
  return window.location.hash === "#/panel" ? "panel" : "inicio";
}

// Devuelve la ruta actual ("inicio" o "panel") y se actualiza al cambiar el hash.
export function useRuta() {
  // Ruta inicial según la dirección con la que se abrió la página.
  const [ruta, setRuta] = useState(leerRuta);

  // Escucha los cambios de hash mientras la aplicación esté montada.
  useEffect(() => {
    // Actualiza la ruta cuando el hash cambia.
    const alCambiar = () => setRuta(leerRuta());
    // Se registra el oyente.
    window.addEventListener("hashchange", alCambiar);
    // Al desmontar se quita, para no dejar oyentes colgados (evita fugas de memoria).
    return () => window.removeEventListener("hashchange", alCambiar);
  }, []);

  // Devuelve la ruta.
  return ruta;
}
