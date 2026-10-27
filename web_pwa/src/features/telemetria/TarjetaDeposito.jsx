// Tarjeta del depósito de agua: conductividad (EC) y disponibilidad de agua.
// No se inventa un nivel en porcentaje: sin sensor de nivel solo se sabe si hay agua o no.

// Etiqueta visual.
import Etiqueta from "../../components/Etiqueta.jsx";
// Funciones de formato.
import { NOMBRES_MEDICION, describirConexion, formatearHora, formatearMedicion } from "./formato.js";

// Traduce el valor de agua_disponible a texto.
function textoAgua(valor) {
  // true / false son datos reales.
  if (valor === true) return "Sí";
  if (valor === false) return "No";
  // null = sin dato.
  return "—";
}

// Props: entrada (lectura y conexión) y unidades.
export default function TarjetaDeposito({ entrada, unidades }) {
  // Última lectura (puede ser null).
  const lectura = entrada.lectura;
  // Texto y tono de la conexión.
  const conexion = describirConexion(entrada.conexion);

  // Devuelve la tarjeta.
  return (
    // La clase "zona--deposito" le da su color azul de acento.
    <section className="tarjeta zona--deposito" aria-labelledby="deposito-principal">
      {/* Cabecera. */}
      <header className="tarjeta__cabecera">
        {/* Nombre y aclaración de que la configuración es provisional. */}
        <div>
          {/* Título. */}
          <h2 id="deposito-principal">Depósito principal</h2>
          {/* Aclaración: aún no se decide si es compartido o uno por zona. */}
          <p className="tarjeta__cientifico">Configuración provisional (compartido o por zona: por definir)</p>
        </div>
        {/* Etiquetas de estado. */}
        <div className="tarjeta__etiquetas">
          {/* Conexión. */}
          <Etiqueta tono={conexion.tono}>{conexion.texto}</Etiqueta>
          {/* Origen del dato. */}
          {lectura ? (
            <Etiqueta tono={lectura.origen === "simulado" ? "simulado" : "neutro"}>{lectura.origen === "simulado" ? "SIMULADO" : "REAL"}</Etiqueta>
          ) : (
            <Etiqueta tono="neutro">Sin datos</Etiqueta>
          )}
        </div>
      </header>

      {/* Mediciones o mensaje de ausencia de datos. */}
      {lectura ? (
        // Lista de definiciones.
        <dl className="medidas">
          {/* Conductividad eléctrica. */}
          <div className="medida">
            {/* Nombre. */}
            <dt>{NOMBRES_MEDICION.conductividad_ec}</dt>
            {/* Valor con unidad. */}
            <dd>{formatearMedicion("conductividad_ec", lectura.mediciones.conductividad_ec, unidades)}</dd>
          </div>
          {/* Disponibilidad de agua. */}
          <div className="medida">
            {/* Nombre. */}
            <dt>Agua disponible</dt>
            {/* Sí / No / —. */}
            <dd>{textoAgua(lectura.mediciones.agua_disponible)}</dd>
          </div>
          {/* Nivel en porcentaje: solo si hay un sensor que lo mida. */}
          <div className="medida">
            {/* Nombre. */}
            <dt>{NOMBRES_MEDICION.nivel_agua}</dt>
            {/* Valor o aclaración de que no hay sensor. */}
            <dd>{typeof lectura.mediciones.nivel_agua === "number" ? formatearMedicion("nivel_agua", lectura.mediciones.nivel_agua, unidades) : "Sin sensor de nivel"}</dd>
          </div>
        </dl>
      ) : (
        // Mensaje cuando todavía no hay lecturas.
        <p className="vacio">Todavía no llegan lecturas del depósito.</p>
      )}

      {/* Aclaración técnica sobre qué mide la conductividad. */}
      <p className="tarjeta__hora">
        La conductividad mide la solución en el punto del sensor; no indica nutrientes individuales.
        {/* Hora de la medición. */}
        {" "}Medido: {formatearHora(lectura?.medido_en)}
      </p>
    </section>
  );
}
