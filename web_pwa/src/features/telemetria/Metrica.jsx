// Recuadro de una medición: nombre, valor actual y mini gráfico de tendencia.

// Gráfico y formato.
import Sparkline from "./Sparkline.jsx";
import { NOMBRES_MEDICION, formatearNumero } from "./formato.js";

// Props: nombre (clave de la medición), valor actual, unidades y valores (serie histórica).
export default function Metrica({ nombre, valor, unidades, valores }) {
  // ¿Hay un dato actual? Si no, se declara ausente (nunca se muestra 0).
  const hayDato = typeof valor === "number";
  // Devuelve el recuadro.
  return (
    // La clase "ausente" atenúa el recuadro si el sensor no entrega dato.
    <div className={`metrica${hayDato ? "" : " metrica--ausente"}`}>
      {/* Nombre de la medición. */}
      <div className="metrica__nombre">{NOMBRES_MEDICION[nombre]}</div>
      {/* Valor y unidad, o una explicación si no hay dato. */}
      <div className="metrica__valor">
        {/* Número formateado (o "—"). */}
        {formatearNumero(nombre, valor)}
        {/* Unidad solo si hay dato. */}
        {hayDato && <small>{unidades?.[nombre]}</small>}
      </div>
      {/* Mini gráfico de línea con la tendencia. */}
      <Sparkline valores={valores} etiqueta={NOMBRES_MEDICION[nombre]} />
    </div>
  );
}
