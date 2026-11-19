// Tarjeta de una zona: mediciones con gráfico de tendencia, estado de conexión y actuadores.

// Componentes y funciones auxiliares.
import Etiqueta from "../../components/Etiqueta.jsx";
import Icono from "../../components/Iconos.jsx";
import PanelActuadores from "../actuadores/PanelActuadores.jsx";
import Metrica from "../telemetria/Metrica.jsx";
import { describirConexion, formatearHora } from "../telemetria/formato.js";

// Entrada vacía para una zona sin datos en el resumen.
const ENTRADA_VACIA = { lectura: null, conexion: { estado: "desconocido", desactualizada: false, segundos_desde_ultima_lectura: null } };

// Props: zona (datos fijos), entrada (lectura y conexión, puede faltar), unidades e historial (lecturas recientes).
export default function TarjetaZona({ zona, entrada: entradaRecibida, unidades, historial, puedeOrdenar = true }) {
  // Usa la entrada vacía para mostrar la tarjeta aunque falten los datos.
  const entrada = entradaRecibida || ENTRADA_VACIA;
  // Última lectura (puede ser null si aún no llegó ninguna).
  const lectura = entrada.lectura;
  // La antigüedad solo se muestra si la conexión informa un número.
  const antiguedad = entrada.conexion?.segundos_desde_ultima_lectura;
  // Texto y tono de la conexión.
  const conexion = describirConexion(entrada.conexion);
  // ¿El dispositivo está en línea con datos recientes?
  const enLinea = entrada.conexion?.estado === "en_linea" && !entrada.conexion.desactualizada;
  // Las órdenes solo se habilitan con permiso y con el dispositivo en línea.
  const habilitado = puedeOrdenar && enLinea;
  // Explicación que se muestra si las órdenes están bloqueadas.
  const motivo = !puedeOrdenar ? "el permiso de control aún no está disponible para esta sesión." : "el dispositivo no está en línea o sus datos están desactualizados.";

  // Devuelve la tarjeta.
  return (
    // La clase "zona--id" define el color de acento de la zona.
    <section className={`tarjeta zona--${zona.id}`} aria-labelledby={`zona-${zona.id}`}>
      {/* Cabecera con nombre y etiquetas. */}
      <header className="tarjeta__cabecera">
        {/* Icono, nombre y lema. */}
        <div className="tarjeta__titulo">
          {/* Icono de la zona. */}
          <div className="tarjeta__icono">
            <Icono nombre={zona.icono} />
          </div>
          <div>
            {/* Nombre de la zona. */}
            <h2 id={`zona-${zona.id}`}>{zona.nombre}</h2>
            {/* Lema con las variables clave. */}
            <p className="tarjeta__cientifico">{zona.lema}</p>
          </div>
        </div>
        {/* Etiquetas de estado. */}
        <div className="tarjeta__etiquetas">
          {/* Conexión. */}
          <Etiqueta tono={conexion.tono}>{conexion.texto}</Etiqueta>
          {/* Origen del dato: simulado o real. Si no hay lectura, se dice que no hay datos. */}
          {lectura ? (
            <Etiqueta tono={lectura.origen === "simulado" ? "simulado" : "neutro"}>{lectura.origen === "simulado" ? "SIMULADO" : "REAL"}</Etiqueta>
          ) : (
            <Etiqueta tono="neutro">Sin datos</Etiqueta>
          )}
        </div>
      </header>

      {/* Qué se prioriza en esta zona. */}
      <p className="tarjeta__enfoque">{zona.enfoque}</p>

      {/* Mediciones destacadas o mensaje de ausencia de datos. */}
      {lectura ? (
        // Rejilla de recuadros de medición.
        <div className="metricas">
          {/* Una métrica por cada medición destacada de esta zona. */}
          {zona.metricas.map((nombre) => (
            // Cada recuadro recibe el valor actual y la serie histórica de esa medición.
            <Metrica key={nombre} nombre={nombre} valor={lectura.mediciones?.[nombre]} unidades={unidades} valores={Array.isArray(historial) ? historial.map((l) => l?.mediciones?.[nombre]) : []} />
          ))}
        </div>
      ) : (
        // Mensaje cuando todavía no llegan lecturas.
        <p className="vacio tarjeta__sin-lecturas">Todavía no llegan lecturas de esta zona.</p>
      )}

      {/* Pie con la hora de medición (indicando zona horaria) y la antigüedad del dato. */}
      <p className="tarjeta__hora">
        {/* Hora en que se midió. */}
        Medido: {formatearHora(lectura?.medido_en)}
        {/* Antigüedad calculada a partir de la recepción en Supabase. */}
        {typeof antiguedad === "number" && ` · hace ${Math.round(antiguedad)} s`}
        {/* Aviso si el dispositivo declaró calidad distinta de buena. */}
        {lectura && lectura.calidad !== "buena" && ` · calidad: ${lectura.calidad}`}
      </p>

      {/* Panel de actuadores de la zona. */}
      <PanelActuadores zona={zona.id} actuadores={lectura?.actuadores} modo={lectura?.modo} recibidoEn={lectura?.recibido_en} habilitado={habilitado} motivo={motivo} />
    </section>
  );
}
