// Componente raíz: barra fija, página según la ruta (inicio o panel) y pie.

// useEffect se usa para volver arriba o ir a la sección pedida al cambiar de ruta.
import { lazy, Suspense, useEffect, useState } from "react";
// Piezas comunes.
import Encabezado from "../components/Encabezado.jsx";
import LimiteDeError from "../components/LimiteDeError.jsx";
import Pie from "../components/Pie.jsx";
// Páginas.
import Inicio from "../pages/Inicio.jsx";
// Hook de ruta.
import { useRuta } from "./useRuta.js";
import { useSesion } from "../features/sesion/useSesion.js";

// Descarga el panel y sus dependencias al abrir la ruta del panel.
const Panel = lazy(() => import("../pages/Panel.jsx"));

// Captura el tipo de enlace antes de que Supabase limpie el fragmento.
function leerRetornoDeAcceso() {
  const parametros = new URLSearchParams(window.location.hash.slice(1));
  if (!parametros.has("access_token") && !parametros.has("error_code")) return null;
  return { recuperar: parametros.get("type") === "recovery", vencido: parametros.has("error_code") };
}

// Componente de la aplicación.
export default function App() {
  // Usa la ruta para elegir la página y el hash para desplazarse a su sección.
  const { ruta, hash, recuperando } = useRuta();
  // El enlace de confirmación puede abrir la portada sin una sesión previa.
  const [retorno, setRetorno] = useState(leerRetornoDeAcceso);
  const [errorConfirmacion, setErrorConfirmacion] = useState(false);
  const [cerrando, setCerrando] = useState(false);
  const [errorCierre, setErrorCierre] = useState(false);
  const { usuario, operador, cargando, errorSesion } = useSesion();
  const sesionActiva = Boolean(usuario);
  // Si cambia el hash durante la sesión, se sigue mostrando el panel desde el primer dibujo.
  const rutaVisible = sesionActiva ? "panel" : ruta;

  useEffect(() => {
    // La recuperación de contraseña sigue disponible mientras se procesa su enlace.
    if (sesionActiva && ruta !== "panel" && !retorno) window.location.replace("#/panel");
  }, [sesionActiva, ruta, hash, retorno]);

  async function cerrarSesion() {
    setCerrando(true);
    setErrorCierre(false);
    try {
      // Vuelve al inicio cuando el navegador ya no conserva la sesión.
      const { supabase } = await import("../services/supabase.js");
      const { error } = await supabase.auth.signOut();
      if (error) {
        // Supabase puede eliminar la sesión local aunque falle la revocación remota.
        const { data, error: errorLocal } = await supabase.auth.getSession();
        if (errorLocal || data.session) throw error;
      }
      setErrorConfirmacion(false);
      window.location.replace("#/");
    } catch {
      setErrorCierre(true);
    } finally {
      setCerrando(false);
    }
  }

  useEffect(() => {
    if (!retorno) return undefined;
    let vigente = true;

    async function restaurarAcceso() {
      let enlaceValido = false;
      try {
        // Supabase valida el enlace, guarda la sesión y limpia el fragmento con las credenciales.
        const { supabase } = await import("../services/supabase.js");
        const { error: falloEnlace } = await supabase.auth.initialize();
        const { data, error } = await supabase.auth.getSession();
        enlaceValido = !retorno.vencido && !falloEnlace && !error && Boolean(data.session);
      } catch {
        // El formulario normal permite recuperar el acceso si el enlace no funciona.
      } finally {
        if (vigente) {
          setErrorConfirmacion(!enlaceValido);
          window.location.replace(enlaceValido && retorno.recuperar ? "#/recuperar" : "#/panel");
          setRetorno(null);
        }
      }
    }

    restaurarAcceso();
    return () => { vigente = false; };
  }, [retorno]);

  // Al cambiar de página: si la dirección trae un ancla (#zonas) se baja a ella; si no, se sube al comienzo.
  useEffect(() => {
    // Nombre del ancla sin el "#"; "/" y "/panel" no son anclas.
    const ancla = hash.slice(1);
    // Elemento de la ancla, si existe.
    const destino = ancla && !ancla.startsWith("/") ? document.getElementById(ancla) : null;
    // Baja a la sección o vuelve al comienzo de la página.
    if (destino) destino.scrollIntoView();
    else window.scrollTo(0, 0);
  }, [hash, cargando]);

  // Devuelve la estructura de la página.
  return (
    // Contenedor general de la aplicación.
    <div className={sesionActiva ? "app app--sesion" : "app"}>
      {/* La barra ofrece el cierre de sesión aunque la telemetría siga cargando. */}
      <Encabezado ruta={rutaVisible} sesionActiva={sesionActiva} cerrando={cerrando} cerrarSesion={cerrarSesion} />
      {/* Contenido principal. */}
      <main className="app__contenido">
        {/* Red de seguridad: si algo falla al dibujar, se muestra un aviso en lugar de una página en blanco. */}
        <LimiteDeError key={rutaVisible}>
          {errorCierre && sesionActiva && <p className="contenedor aviso aviso--malo" role="alert">No se pudo cerrar la sesión. Intenta de nuevo.</p>}
          {/* Muestra un estado de carga mientras se descarga el panel. */}
          {retorno ? (
            <p className="contenedor vacio" role="status">Comprobando enlace de acceso…</p>
          ) : errorSesion ? (
            <div className="contenedor panel">
              <p role="alert">No se pudo comprobar la sesión.</p>
              <button type="button" className="boton-contorno-lima" onClick={() => window.location.reload()}>Reintentar</button>
            </div>
          ) : cargando ? (
            <p className="contenedor vacio" role="status">Comprobando sesión…</p>
          ) : rutaVisible === "panel" ? (
            <Suspense fallback={<p role="status">Cargando panel…</p>}>
              {errorConfirmacion && <p className="contenedor aviso aviso--malo" role="alert">No se pudo completar el acceso con ese enlace. Entra con tu correo y contraseña.</p>}
              <Panel recuperando={recuperando} usuario={usuario} operador={operador} />
            </Suspense>
          ) : <Inicio />}
        </LimiteDeError>
      </main>
      {/* Pie de página. */}
      <Pie />
    </div>
  );
}
