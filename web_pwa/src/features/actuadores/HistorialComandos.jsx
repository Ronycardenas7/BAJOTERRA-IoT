// El historial se consulta al abrirlo y se puede actualizar manualmente.
import { useState } from "react";
import { historialComandosNube } from "../../services/datosNube.js";
import { describirComando } from "../telemetria/formato.js";
import { ZONAS } from "../zonas/zonas.js";

// Las fechas largas distinguen órdenes emitidas en días diferentes.
const FECHA = new Intl.DateTimeFormat("es-CL", {
  dateStyle: "short",
  timeStyle: "short",
  timeZone: "America/Santiago",
});

export default function HistorialComandos() {
  const [ordenes, setOrdenes] = useState([]);
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState(false);

  async function cargar() {
    if (cargando) return;
    setCargando(true);
    setError(false);
    try {
      // Conserva la vista anterior si falla una actualización.
      setOrdenes(await historialComandosNube());
    } catch {
      setError(true);
    } finally {
      setCargando(false);
    }
  }

  return (
    <details className="historial-ordenes" onToggle={(evento) => { if (evento.currentTarget.open) cargar(); }}>
      <summary>Órdenes recientes</summary>
      <p>Solicitudes y respuestas de los dispositivos. Hora de Santiago.</p>
      <button type="button" className="boton-contorno-lima" onClick={cargar} disabled={cargando}>Actualizar órdenes</button>
      {cargando && <p className="vacio" role="status">Consultando órdenes…</p>}
      {error && <p className="aviso aviso--malo" role="alert">No se pudieron consultar las órdenes. Intenta actualizar.</p>}
      {!cargando && !error && ordenes.length === 0 && <p className="vacio">No hay órdenes recientes.</p>}
      <ul className="historial-ordenes__lista">
        {ordenes.map((orden) => {
          const fecha = Date.parse(orden.solicitado_en);
          const vencida = orden.estado === "enviado" && Date.parse(orden.caduca_en) <= Date.now();
          // Una orden vencida sin respuesta no se presenta como ejecutada.
          const resultado = describirComando(vencida ? { ...orden, estado: "sin_confirmacion" } : orden);
          const zona = ZONAS.find((item) => item.id === orden.zona)?.nombre ?? orden.zona;
          return (
            <li key={orden.id_comando} className={`orden orden--${resultado.tono}`}>
              <strong>{zona}</strong>
              <time dateTime={orden.solicitado_en}>{Number.isFinite(fecha) ? FECHA.format(fecha) : "Fecha sin dato"}</time>
              <span>{resultado.texto}</span>
            </li>
          );
        })}
      </ul>
    </details>
  );
}
