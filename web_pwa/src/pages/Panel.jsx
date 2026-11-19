// Panel de Control: tres zonas en paralelo (árida, húmeda y selvática) más el depósito de agua.

// Hook que carga el historial de Supabase y recibe lecturas por Realtime.
import { useResumenNube } from "../features/telemetria/useResumenNube.js";
// Tarjetas y datos de zonas.
import TarjetaDeposito from "../features/telemetria/TarjetaDeposito.jsx";
import TarjetaZona from "../features/zonas/TarjetaZona.jsx";
import { ZONAS } from "../features/zonas/zonas.js";
// Formato de horas.
import { formatearHora } from "../features/telemetria/formato.js";
// Formulario de acceso y registro de las órdenes.
import Acceso from "../features/sesion/Acceso.jsx";
import HistorialComandos from "../features/actuadores/HistorialComandos.jsx";
// Etiqueta visual.
import Etiqueta from "../components/Etiqueta.jsx";

// Usa la sesión que ya comprobó la aplicación.
export default function Panel({ recuperando, usuario, operador }) {
  // La recuperación abre el formulario antes de mostrar las lecturas y controles.
  if (recuperando) return <Acceso key="recuperar" modoInicial={usuario ? "cambiar" : "recuperar"} />;
  if (!usuario) return <Acceso />;
  // Reinicia lecturas y seguimiento de órdenes si cambia la cuenta.
  return (
    <ContenidoPanel
      key={usuario.id}
      puedeOrdenar={operador}
      cuenta={
        // Correo y permiso. El cierre está en la barra superior.
        <div className="cuenta">
          <span>{usuario.email}</span>
          <Etiqueta tono={operador ? "bueno" : "neutro"}>{operador ? "Operador" : "Control no disponible"}</Etiqueta>
        </div>
      }
    />
  );
}

// Muestra las lecturas y habilita las órdenes para operadores.
function ContenidoPanel({ puedeOrdenar, cuenta }) {
  // Último resumen, historial para gráficos, error de la última consulta y estado de carga.
  const { resumen, historial, error, cargando, avisoReloj } = useResumenNube();

  // Mientras no haya ninguna respuesta, se muestra un mensaje de carga.
  if (cargando && !resumen) {
    // Mensaje simple.
    return (
      <div className="contenedor panel">
        <p className="vacio">Conectando con Supabase…</p>
      </div>
    );
  }

  // Entradas de las tres zonas del invernadero.
  const entradasZonas = resumen ? ZONAS.map((zona) => resumen.zonas?.[zona.id]).filter(Boolean) : [];
  // Entrada del depósito principal (puede faltar).
  const deposito = resumen?.depositos?.principal;
  // Todas las entradas (zonas y depósito) del resumen.
  const entradas = deposito ? [...entradasZonas, deposito] : entradasZonas;
  // ¿Alguna lectura visible es simulada? Se usa para el aviso permanente.
  const hayDatosSimulados = entradas.some((e) => e.lectura?.origen === "simulado");
  // Cuántas zonas están en línea con datos recientes.
  const zonasEnLinea = entradasZonas.filter((e) => e.conexion.estado === "en_linea" && !e.conexion.desactualizada).length;
  // Cuántos actuadores están REPORTADOS como encendidos (no es lo mismo que "pedidos").
  const actuadoresEncendidos = entradasZonas.reduce((total, e) => total + Object.values(e.lectura?.actuadores ?? {}).filter((estado) => estado === "encendido" || estado === true).length, 0);

  // Devuelve la página.
  return (
    // Contenedor centrado del panel.
    <div className="contenedor panel">
      {/* Cabecera del panel. */}
      <div className="panel__cabecera">
        {/* Título y descripción. */}
        <div>
          <h1>Panel de Control</h1>
          <p>Zonas árida, húmeda y selvática. Datos en tiempo real desde Supabase.</p>
        </div>
        {/* Cuenta de la sesión actual. */}
        {cuenta}
      </div>

      {/* Error de comunicación con Supabase (se conservan los últimos datos). */}
      {error && (
        // role="alert" anuncia el error de inmediato.
        <p className="aviso aviso--malo" role="alert">
          {error}
        </p>
      )}
      {/* Aviso si el reloj del equipo está desfasado. */}
      {avisoReloj && (
        <p className="aviso aviso--simulado" role="note">
          {avisoReloj}
        </p>
      )}
      {/* Aviso permanente cuando hay datos simulados. */}
      {hayDatosSimulados && (
        // role="note" marca una nota informativa.
        <p className="aviso aviso--simulado" role="note">
          <strong>Datos SIMULADOS.</strong> Las lecturas provienen de pruebas del sistema.
        </p>
      )}

      {/* Muestra los indicadores y tarjetas al terminar la carga. */}
      {resumen && (
        <>
          {/* Indicadores generales. */}
          <div className="resumen">
            {/* Zonas en línea. */}
            <div className="indicador">
              <span>Zonas en línea</span>
              <strong>
                {zonasEnLinea} / {ZONAS.length}
              </strong>
            </div>
            {/* Actuadores reportados como encendidos. */}
            <div className="indicador">
              <span>Actuadores encendidos (reportados)</span>
              <strong>{actuadoresEncendidos}</strong>
            </div>
            {/* Hora de generación del resumen. */}
            <div className="indicador">
              <span>Resumen generado</span>
              <strong style={{ fontSize: "1.05rem" }}>{formatearHora(resumen.generado_en)}</strong>
            </div>
          </div>
          {/* Rejilla responsive: una columna en móvil, tres en pantallas anchas. */}
          <div className="rejilla-zonas">
            {/* Una tarjeta por zona. */}
            {ZONAS.map((zona) => (
              // La clave ayuda a React a distinguir los elementos de la lista.
              <TarjetaZona key={zona.id} zona={zona} entrada={resumen.zonas?.[zona.id]} unidades={resumen.unidades} historial={historial[zona.id]} puedeOrdenar={puedeOrdenar} />
            ))}
          </div>
          {/* Tarjeta del depósito, debajo de las zonas. */}
          {deposito && (
            <div style={{ marginTop: 20 }}>
              <TarjetaDeposito entrada={deposito} unidades={resumen.unidades} />
            </div>
          )}
        </>
      )}
      {/* Cualquier cuenta con sesión puede revisar órdenes de los dispositivos. */}
      <HistorialComandos />
    </div>
  );
}
