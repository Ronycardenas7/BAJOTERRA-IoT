// ============================================================================
// BAJOTERRA-IoT · Catálogo de Iconos Vectoriales Minimalistas
// Estilo depurado inspirado en CanvasUI e ItsFree.dev (trazos geométricos 24x24,
// sin librerías externas pesadas, ultra ligero para equipos de 4 GB RAM).
// ============================================================================

import React from "react";

// Definición de trazados SVG (viewBox 0 0 24 24 con currentColor).
const TRAZADOS = {
  // Logotipo depurado: Hoja botánica fusionada con circuito y nodos IoT
  logo: [
    "M12 2C6.48 2 2 6.48 2 12c0 4.42 2.87 8.17 6.84 9.5.5.08.66-.23.66-.5v-1.69c-2.77.6-3.36-1.34-3.36-1.34-.46-1.16-1.11-1.47-1.11-1.47-.91-.62.07-.6.07-.6 1 .07 1.53 1.03 1.53 1.03.87 1.52 2.34 1.07 2.91.83.1-.65.35-1.09.63-1.34-2.22-.25-4.55-1.11-4.55-4.92 0-1.11.38-2 1.03-2.71-.1-.25-.45-1.29.1-2.64 0 0 .84-.27 2.75 1.02.79-.22 1.65-.33 2.5-.33.85 0 1.71.11 2.5.33 1.91-1.29 2.75-1.02 2.75-1.02.55 1.35.2 2.39.1 2.64.65.71 1.03 1.6 1.03 2.71 0 3.82-2.34 4.66-4.57 4.91.36.31.69.92.69 1.85V21c0 .27.16.59.67.5C19.14 20.16 22 16.42 22 12A10 10 0 0 0 12 2z",
  ],

  // Hoja botánica minimalista de trazo simple (CanvasUI)
  hoja: [
    "M12 22c4.97 0 9-4.03 9-9-4-1-7-3-9-7-2 4-5 6-9 7 0 4.97 4.03 9 9 9z",
    "M12 22V6",
  ],

  // Símbolo de la marca BAJOTERRA: Hoja + Red de nodos de circuito
  marca: [
    "M20.24 12.24a6 6 0 0 0-8.49-8.49L5 10.5V19h8.5z",
    "M16 8 2 22",
    "M17.5 15H9",
  ],

  // Isotipo emblemático de BAJOTERRA: Invernadero geométrico + hoja central
  logoInvernadero: [
    "M12 3L3 9v11a1 1 0 0 0 1 1h16a1 1 0 0 0 1-1V9L12 3z",
    "M12 3v18",
    "M3 9h18",
    "M7.5 21V9",
    "M16.5 21V9",
    "M12 11c1.5 0 3 1.2 3 3s-1.5 3-3 3-3-1.2-3-3 1.5-3 3-3z",
  ],

  // 1. Temperatura (Termómetro de precisión)
  termometro: [
    "M14 14.76V3.5a2.5 2.5 0 0 0-5 0v11.26a4.5 4.5 0 1 0 5 0z",
    "M11.5 12.5v4",
  ],

  // 2. Humedad del aire (Gota de agua condensada)
  gota: [
    "M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z",
  ],

  // 3. Humedad del sustrato (Sonda con electrodos en tierra)
  sonda: [
    "M12 2v13",
    "M7 7h10",
    "M9 11h6",
    "M10 15l2 7 2-7",
  ],

  // 4. CO2 (Molécula / Microclima gaseoso)
  nube: [
    "M17.5 19H9a7 7 0 1 1 6.71-9h1.79a4.5 4.5 0 1 1 0 9z",
  ],

  // 5. Radiación solar (Sol radiante con haces geométricos)
  sol: [
    "M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8z",
    "M12 2v2",
    "M12 20v2",
    "M4.93 4.93l1.41 1.41",
    "M17.66 17.66l1.41 1.41",
    "M2 12h2",
    "M20 12h2",
    "M6.34 17.66l-1.41 1.41",
    "M19.07 4.93l-1.41 1.41",
  ],

  // 6. Conductividad eléctrica (Impulso iónico / Rayo de sales disueltas)
  conductividad: [
    "M13 2L3 14h9l-1 8 10-12h-9l1-8z",
  ],

  // Microcontrolador / CPU Dual Core (ESP32)
  cpu: [
    "M4 4h16v16H4z",
    "M9 9h6v6H9z",
    "M9 1v3",
    "M15 1v3",
    "M9 20v3",
    "M15 20v3",
    "M1 9h3",
    "M1 15h3",
    "M20 9h3",
    "M20 15h3",
  ],

  // Transmisión inalámbrica RF (ESP-NOW 2.4 GHz)
  radio: [
    "M4.93 4.93a10 10 0 0 1 14.14 0",
    "M7.76 7.76a6 6 0 0 1 8.48 0",
    "M12 11a1.5 1.5 0 1 0 0 3 1.5 1.5 0 0 0 0-3z",
    "M12 14v8",
  ],

  // Pantalla táctil HMI (ESP32 CYD 2.8")
  pantalla: [
    "M2 4h20v14H2z",
    "M8 21h8",
    "M12 18v3",
    "M6 8h12",
    "M6 12h8",
  ],

  // Módulo de Relés de Potencia (6 canales optoacoplados)
  rele: [
    "M3 6h18v12H3z",
    "M7 10h3v4H7z",
    "M14 10h3v4h-3z",
    "M3 12h4",
    "M17 12h4",
  ],

  // Actuadores: Ventilador / Extractor axial térmico
  ventilador: [
    "M12 12m-3 0a3 3 0 1 0 6 0a3 3 0 1 0 -6 0",
    "M12 9C10.5 5 12 2 14 2c1.5 2 1 5-2 7z",
    "M15 12c4 1.5 7 0 7-2-2-1.5-5-1-7 2z",
    "M12 15c1.5 4 0 7-2 7-1.5-2-1-5 2-7z",
    "M9 12c-4-1.5-7 0-7 2 2 1.5 5 1 7-2z",
  ],

  // Actuadores: Mini Bomba Sumergible de Riego
  bomba: [
    "M12 2v6",
    "M6 8h12v12H6z",
    "M9 14h6",
    "M2 18h4",
    "M18 18h4",
  ],

  // Flecha direccional
  flecha: [
    "M5 12h14",
    "M12 5l7 7-7 7",
  ],

  // Capas de microclimas
  capas: [
    "M12 2L2 7l10 5 10-5-10-5z",
    "M2 17l10 5 10-5",
    "M2 12l10 5 10-5",
  ],

  // Escudo de seguridad / confirmación de órdenes
  escudo: [
    "M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z",
    "M9 12l2 2 4-4",
  ],

  // Gráfico analítico
  grafico: [
    "M3 3v18h18",
    "M7 16l4-4 4 2 5-6",
  ],
};

// Componente Icono: renderiza SVG ultra-liviano según nombre.
export default function Icono({ nombre, tamano = 22, className = "" }) {
  // Si el nombre no existe, se usa 'hoja' por defecto o null.
  const trazados = TRAZADOS[nombre] ?? TRAZADOS.hoja;
  if (!trazados) return null;

  return (
    <svg
      width={tamano}
      height={tamano}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden="true"
      focusable="false"
    >
      {trazados.map((d, i) => (
        <path key={`${d.slice(0, 8)}-${i}`} d={d} />
      ))}
    </svg>
  );
}
