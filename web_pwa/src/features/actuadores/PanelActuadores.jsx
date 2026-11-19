// Panel de actuadores de una zona: muestra el estado REPORTADO y permite pedir órdenes.
// Una orden pedida NO es un actuador encendido: el estado real es el que informa el dispositivo.

// Hook que envía órdenes y sigue su resultado.
import { useComando } from "./useComando.js";
// Texto y tono de un comando, y nombres de actuadores.
import { NOMBRES_ACTUADOR, describirComando } from "../telemetria/formato.js";
// Etiqueta visual e iconos.
import Etiqueta from "../../components/Etiqueta.jsx";
import Icono from "../../components/Iconos.jsx";

// Controles de encendido y apagado para la bomba y el extractor.
const ACTUADORES = [
  { id: "bomba", icono: "gota" },
  { id: "ventilador", icono: "ventilador" },
];

// Traduce el estado reportado a texto. null significa que el dispositivo no lo informó.
function textoEstado(estado) {
  // La telemetría puede informar el estado como texto o como booleano.
  if (estado === "encendido" || estado === true) return "Encendido";
  if (estado === "apagado" || estado === false) return "Apagado";
  // Dato ausente: no se inventa.
  return "Sin dato";
}

// Props: zona, actuadores (estado reportado), modo, habilitado (hay datos frescos) y motivo (por qué no).
export default function PanelActuadores({ zona, actuadores, modo, recibidoEn, habilitado, motivo }) {
  // Estado de las órdenes de esta zona.
  const { comando, error, enviando, pendiente, enviar } = useComando(zona);
  // Descripción de la última orden (o null).
  const descripcion = describirComando(comando);
  // Los botones se bloquean mientras se envía o hay una orden pendiente, o si no hay datos frescos.
  const bloqueado = enviando || pendiente || !habilitado;
  // Usa la confirmación del Maestro hasta que una lectura más reciente informe el modo.
  const confirmacionReciente = comando?.actuador === "modo" &&
    comando.estado === "ejecutado" && Date.parse(comando.confirmado_en) > (Date.parse(recibidoEn) || 0);
  const modoActual = confirmacionReciente ? comando.estado_solicitado : modo;
  const siguienteModo = modoActual === "manual" ? "automatico" : "manual";
  // El Maestro gobierna el riego y el extractor con el mismo modo de zona.
  const estadoRiego = modoActual === "automatico" ? "Activo" : modoActual === "manual" ? "Desactivado" : "Sin dato";

  // Devuelve el panel.
  return (
    <div className="actuadores">
      {/* Encabezado del panel con el modo de la zona y botón para alternarlo. */}
      <div className="actuadores__titulo" style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "8px" }}>
        {/* Título. */}
        <h3>Actuadores</h3>
        {/* Modo informado o confirmado por el dispositivo y botón para alternar. */}
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <Etiqueta tono={modoActual === "manual" ? "aviso" : "neutro"}>Modo: {modoActual === "manual" ? "manual" : modoActual === "automatico" ? "automático" : "sin dato"}</Etiqueta>
          <button
            type="button"
            disabled={bloqueado}
            onClick={() => enviar("modo", siguienteModo)}
            title="Cambiar modo de control de la zona"
            style={{ padding: "4px 8px", fontSize: "0.75rem", cursor: "pointer" }}
          >
            {siguienteModo === "automatico" ? "Pasar a Automático" : "Pasar a Manual"}
          </button>
        </div>
      </div>
      {/* Una fila por actuador. */}
      {ACTUADORES.map(({ id, icono }) => (
        // Fila con el estado reportado y los botones.
        <div className="actuador" key={id}>
          {/* Icono, nombre y estado REPORTADO (lo que el dispositivo dice que tiene, no lo que se pidió). */}
          <div className="actuador__nombre">
            {/* Icono del actuador. */}
            <Icono nombre={icono} tamano={20} />
            <div>
              {/* Nombre del actuador. */}
              <strong>{NOMBRES_ACTUADOR[id]}</strong>
              {/* Punto de color + texto del estado reportado (el texto siempre está: el color no es la única señal). */}
              <span className="actuador__estado">
                <i className={`led${textoEstado(actuadores?.[id]) === "Encendido" ? " led--encendido" : ""}`} aria-hidden="true" />
                Reportado: {textoEstado(actuadores?.[id])}
              </span>
            </div>
          </div>
          {/* Botones para pedir la orden. */}
          <div className="actuador__botones">
            {/* Pedir encender. */}
            <button type="button" disabled={bloqueado} onClick={() => enviar(id, "encendido")} title={!habilitado ? motivo : undefined} aria-label={`Encender ${NOMBRES_ACTUADOR[id]}`}>
              Encender
            </button>
            {/* Pedir apagar. */}
            <button type="button" disabled={bloqueado} onClick={() => enviar(id, "apagado")} title={!habilitado ? motivo : undefined} aria-label={`Apagar ${NOMBRES_ACTUADOR[id]}`}>
              Apagar
            </button>
          </div>
        </div>
      ))}
      {/* La automatización se cambia mediante el modo, sin mandar un pulso a la bomba. */}
      <div className="actuador">
        <div className="actuador__nombre">
          <Icono nombre="gota" tamano={20} />
          <div>
            <strong>Riego automático</strong>
            <span className="actuador__estado">Automatización: {estadoRiego}</span>
            <span className="actuador__estado">Comparte el modo con el extractor.</span>
          </div>
        </div>
        <div className="actuador__botones">
          <button
            type="button"
            disabled={bloqueado || modoActual === "automatico"}
            onClick={() => enviar("modo", "automatico")}
            aria-label="Encender riego automático"
          >
            Encender
          </button>
          <button
            type="button"
            disabled={bloqueado || modoActual === "manual"}
            onClick={() => enviar("modo", "manual")}
            aria-label="Apagar riego automático"
          >
            Apagar
          </button>
        </div>
      </div>
      {/* Control de Temperatura Objetivo (TOBJ) para el algoritmo PI del Maestro. */}
      <div className="actuador" key="tobj">
        <div className="actuador__nombre">
          <Icono nombre="termometro" tamano={20} />
          <div>
            <strong>Temp. Objetivo (TOBJ)</strong>
            <span className="actuador__estado">Ajustar consigna del ventilador</span>
          </div>
        </div>
        <div className="actuador__botones" style={{ display: "flex", gap: "4px" }}>
          <button type="button" disabled={bloqueado} onClick={() => enviar("TOBJ", "22.0")} title="Ajustar consigna a 22.0 °C">
            22°C
          </button>
          <button type="button" disabled={bloqueado} onClick={() => enviar("TOBJ", "24.0")} title="Ajustar consigna a 24.0 °C">
            24°C
          </button>
          <button type="button" disabled={bloqueado} onClick={() => enviar("TOBJ", "26.0")} title="Ajustar consigna a 26.0 °C">
            26°C
          </button>
        </div>
      </div>
      {/* Si los botones están bloqueados por falta de datos frescos, se explica el motivo. */}
      {!habilitado && <p className="actuadores__nota">Órdenes bloqueadas: {motivo}</p>}
      {/* Resultado de la última orden, con su tono. */}
      {descripcion && (
        // role="status" hace que los lectores de pantalla anuncien los cambios.
        <p className={`orden orden--${descripcion.tono}`} role="status">
          {descripcion.texto}
        </p>
      )}
      {/* Error devuelto al solicitar una orden. */}
      {error && (
        // role="alert" anuncia el error de inmediato.
        <p className="orden orden--malo" role="alert">
          {error}
        </p>
      )}
    </div>
  );
}
