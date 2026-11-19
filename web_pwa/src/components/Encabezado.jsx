// ============================================================================
// BAJOTERRA-IoT · Encabezado Minimalista (Header Verde Bosque + Lima Vibrante)
// Estructura:
//  - Izquierda: Isotipo circular invernadero/hoja + Marca BAJOTERRA + enlaces con barra |
//  - Derecha: Indicador de estado del sistema + Botón de contorno redondeado "Ir al Panel"
// ============================================================================

import React from "react";
import Icono from "./Iconos.jsx";

// Enlaces de navegación con anclas internas separadas por barras verticales (|)
const ENLACES_NAV = [
  { href: "#inicio", texto: "Inicio" },
  { href: "#zonas", texto: "Zonas" },
  { href: "#arquitectura", texto: "Arquitectura" },
  { href: "#hardware", texto: "Hardware" },
];

// Props: ruta actual de la aplicación ("inicio" o "panel")
export default function Encabezado({ ruta }) {
  return (
    <header className="barra-editorial" role="banner">
      <div className="contenedor barra-editorial__fila">
        {/* Lado izquierdo: Isotipo emblemático, Marca y Navegación dividida por barras */}
        <div className="barra-editorial__izquierda">
          {/* Logo emblemático con isotipo circular de invernadero en línea fina blanca/lima */}
          <a className="barra-marca" href="#/" aria-label="BAJOTERRA, ir al inicio">
            <span className="barra-marca__isotipo" aria-hidden="true">
              <Icono nombre="logoInvernadero" tamano={18} />
            </span>
            <span className="barra-marca__texto">BAJOTERRA</span>
          </a>

          {/* Separador sutil */}
          <span className="barra-editorial__divisor-logo" aria-hidden="true" />

          {/* Enlaces de navegación separados por barras verticales (|) */}
          <nav className="barra-editorial__nav" aria-label="Navegación principal">
            {ENLACES_NAV.map((enlace, index) => (
              <React.Fragment key={enlace.href}>
                <a href={enlace.href} className="barra-editorial__link">
                  {enlace.texto}
                </a>
                {/* Agrega una barra vertical entre cada enlace excepto en el último */}
                {index < ENLACES_NAV.length - 1 && (
                  <span className="barra-editorial__separador" aria-hidden="true">
                    |
                  </span>
                )}
              </React.Fragment>
            ))}
          </nav>
        </div>

        {/* Lado derecho: Indicador de estado en Tarapacá y botón redondeado al Panel */}
        <div className="barra-editorial__derecha">
          {/* Indicador discreto de estado físico del sistema */}
          <div className="barra-editorial__estado" title="Sistema distribuido en Tarapacá operando">
            <span className="punto-estado punto-estado--lima" aria-hidden="true" />
            <span className="barra-editorial__estado-texto">Invernadero IoT v3.0 · Tarapacá</span>
          </div>

          {/* Botón con contorno redondeado hacia el panel de control */}
          <a
            className="boton-contorno-lima"
            href="#/panel"
            aria-current={ruta === "panel" ? "page" : undefined}
          >
            <span>Ir al Panel</span>
            <Icono nombre="flecha" tamano={15} />
          </a>
        </div>
      </div>
    </header>
  );
}
