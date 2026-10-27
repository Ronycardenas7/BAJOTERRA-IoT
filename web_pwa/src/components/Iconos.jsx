// Iconos SVG propios (trazo simple, 24x24). Sin librerías: cada icono pesa unos pocos bytes.

// Trazados de cada icono. Cada valor es una lista de "d" de <path> (la forma del dibujo).
const TRAZADOS = {
  // Hoja (marca y zona selvática).
  hoja: ["M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.5 19 2c1 2 2 4.2 2 8 0 5.5-4.8 10-10 10Z", "M2 21c0-3 1.9-5.4 5.1-6 2.4-.5 4.9-2 5.9-3"],
  // Gota de agua (zona húmeda y riego).
  gota: ["M12 2.7s6 6.1 6 10.6a6 6 0 0 1-12 0c0-4.5 6-10.6 6-10.6Z"],
  // Sol (zona árida y radiación).
  sol: ["M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8Z", "M12 2v2", "M12 20v2", "M4.9 4.9l1.4 1.4", "M17.7 17.7l1.4 1.4", "M2 12h2", "M20 12h2", "M4.9 19.1l1.4-1.4", "M17.7 6.3l1.4-1.4"],
  // Termómetro.
  termometro: ["M14 14.8V4a2 2 0 0 0-4 0v10.8a4 4 0 1 0 4 0Z"],
  // Nube (CO2).
  nube: ["M17.5 19a4.5 4.5 0 1 0-1.4-8.8A6 6 0 0 0 4.6 12 3.5 3.5 0 0 0 6 19h11.5Z"],
  // Bombilla (luces LED).
  bombilla: ["M9 18h6", "M10 21h4", "M12 3a6 6 0 0 0-3.5 10.9c.6.5 1 1.2 1 2.1h5c0-.9.4-1.6 1-2.1A6 6 0 0 0 12 3Z"],
  // Ventilador / extractor (tres aspas y un centro).
  ventilador: ["M12 11a1 1 0 1 0 0 2 1 1 0 0 0 0-2Z", "M12 11C10.5 7.500 11 4.500 13 3c1.300 2.800.9 5.600-1 8Z", "M12.900 12.500c3.500-.9 6.400.3 7.100 2.800-2.700 1.200-5.400.3-7.100-2.800Z", "M11.100 12.500c-1.700 3.100-4.400 4-7.100 2.800.7-2.500 3.600-3.700 7.100-2.800Z"],
  // Flecha a la derecha.
  flecha: ["M5 12h14", "M13 6l6 6-6 6"],
  // Chip / microcontrolador.
  chip: ["M6 5h12a1 1 0 0 1 1 1v12a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1V6a1 1 0 0 1 1-1Z", "M9 9h6v6H9z", "M9 2v3", "M15 2v3", "M9 19v3", "M15 19v3", "M2 9h3", "M2 15h3", "M19 9h3", "M19 15h3"],
  // Escudo con visto (confirmación de órdenes).
  escudo: ["M12 3l8 3v6c0 5-3.500 8-8 9-4.500-1-8-4-8-9V6l8-3Z", "M9 12l2 2 4-4"],
  // Gráfico de línea.
  grafico: ["M3 3v18h18", "M7 15l4-4 3 3 5-6"],
  // Capas (zonas independientes).
  capas: ["M12 2 2 7l10 5 10-5-10-5Z", "M2 17l10 5 10-5", "M2 12l10 5 10-5"],
};

// Componente: nombre del icono y tamaño en píxeles. Es decorativo (aria-hidden) porque siempre va junto a texto.
export default function Icono({ nombre, tamano = 22 }) {
  // Si el nombre no existe, no dibuja nada.
  const trazados = TRAZADOS[nombre];
  if (!trazados) return null;
  // Devuelve el SVG con trazo redondeado que hereda el color del texto (currentColor).
  return (
    <svg width={tamano} height={tamano} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" focusable="false">
      {/* Un <path> por cada trazado del icono. */}
      {trazados.map((d) => (
        // La propia cadena sirve de clave (es única dentro del icono).
        <path key={d} d={d} />
      ))}
    </svg>
  );
}
