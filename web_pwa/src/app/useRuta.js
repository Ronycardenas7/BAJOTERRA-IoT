// Mini enrutador sin librerías: la "ruta" es el hash de la dirección (#/panel).
// Así la página funciona con cualquier servidor estático sin configurar redirecciones.

// useEffect conecta con eventos del navegador; useState guarda la ruta actual.
import { useEffect, useState } from "react";

// Conserva el hash completo para detectar cambios entre secciones de la portada.
export function useRuta() {
  // Lee la dirección con la que se abrió la página.
  const [hash, setHash] = useState(() => window.location.hash);

  // Escucha los cambios de hash mientras la aplicación esté montada.
  useEffect(() => {
    // Actualiza la dirección cuando cambia.
    const alCambiar = () => setHash(window.location.hash);
    // Se registra el oyente.
    window.addEventListener("hashchange", alCambiar);
    // Al desmontar se quita, para no dejar oyentes colgados (evita fugas de memoria).
    return () => window.removeEventListener("hashchange", alCambiar);
  }, []);

  // El panel y el cambio de contraseña comparten la comprobación de sesión.
  const recuperando = hash === "#/recuperar";
  return { hash, recuperando, ruta: hash === "#/panel" || recuperando ? "panel" : "inicio" };
}
