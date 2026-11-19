// ============================================================================
// BAJOTERRA-IoT · Encabezado Minimalista (Header Verde Bosque + Lima Vibrante)
// Estructura:
//  - Izquierda: hoja de BAJOTERRA y enlaces de navegación.
//  - Derecha: selector de tema y acceso al panel.
// ============================================================================

// Mantiene el selector de tema sincronizado con la apariencia de la página.
import React, { useState } from "react";
import Icono from "./Iconos.jsx";

// Enlaces de navegación con anclas internas separadas por barras verticales (|)
const ENLACES_NAV = [
  { href: "#inicio", texto: "Inicio" },
  { href: "#zonas", texto: "Zonas" },
  { href: "#arquitectura", texto: "Proyecto" },
  { href: "#hardware", texto: "Hardware" },
];

// Muestra navegación pública únicamente si no hay una sesión activa.
export default function Encabezado({ ruta, sesionActiva, cerrando, cerrarSesion }) {
  // Lee la preferencia aplicada al cargar la página.
  const [tema, setTema] = useState(() => document.documentElement.dataset.tema ?? "oscuro");

  function alternarTema() {
    // Aplica el tema en la misma página, sin volver a montar el panel.
    const siguiente = tema === "claro" ? "oscuro" : "claro";
    document.documentElement.dataset.tema = siguiente;
    setTema(siguiente);
    try {
      localStorage.setItem("bajoterra-tema", siguiente);
    } catch {
      // El cambio sigue funcionando para esta visita si se bloquea el almacenamiento.
    }
  }

  return (
    <header className="barra-editorial" role="banner">
      <div className="contenedor barra-editorial__fila">
        {/* Lado izquierdo: Isotipo emblemático, Marca y Navegación dividida por barras */}
        <div className="barra-editorial__izquierda">
          {/* La marca apunta a la vista que corresponde a la sesión. */}
          <a className="barra-marca" href={sesionActiva ? "#/panel" : "#/"} aria-label={sesionActiva ? "BAJOTERRA, ir al panel" : "BAJOTERRA, ir al inicio"}>
            <span className="barra-marca__isotipo" aria-hidden="true">
              <Icono nombre="hojaMarca" tamano={26} />
            </span>
            <span className="barra-marca__texto">BAJOTERRA</span>
          </a>

          {/* Las secciones públicas están disponibles al cerrar sesión. */}
          {!sesionActiva && (
            <>
              <span className="barra-editorial__divisor-logo" aria-hidden="true" />
              <nav className="barra-editorial__nav" aria-label="Navegación principal">
                {ENLACES_NAV.map((enlace, index) => (
                  <React.Fragment key={enlace.href}>
                    <a href={enlace.href} className="barra-editorial__link">{enlace.texto}</a>
                    {index < ENLACES_NAV.length - 1 && <span className="barra-editorial__separador" aria-hidden="true">|</span>}
                  </React.Fragment>
                ))}
              </nav>
            </>
          )}
        </div>

        {/* Lado derecho: apariencia y acceso al panel. */}
        <div className="barra-editorial__derecha">
          <button type="button" className="barra-editorial__tema" onClick={alternarTema} aria-pressed={tema === "claro"} aria-label="Modo claro">
            {tema === "claro" ? <span aria-hidden="true">☾</span> : <Icono nombre="sol" tamano={18} />}
          </button>

          {/* La salida de la vista autenticada pasa por el cierre de sesión. */}
          {sesionActiva ? (
            <button type="button" className="boton-contorno-lima" onClick={cerrarSesion} disabled={cerrando}>
              {cerrando ? "Cerrando…" : "Cerrar sesión"}
            </button>
          ) : (
            <a className="boton-contorno-lima" href="#/panel" aria-current={ruta === "panel" ? "page" : undefined}>
              <span>Ir al Panel</span>
              <Icono nombre="flecha" tamano={15} />
            </a>
          )}
        </div>
      </div>
    </header>
  );
}
