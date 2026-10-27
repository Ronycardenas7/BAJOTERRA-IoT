// Panel de Control: tres zonas en paralelo (árida, húmeda y selvática) más el depósito de agua.

// Hook que consulta el backend periódicamente y guarda el historial para los gráficos.
import { useResumen } from "../features/telemetria/useResumen.js";
// Tarjetas y datos de zonas.
import TarjetaDeposito from "../features/telemetria/TarjetaDeposito.jsx";
import TarjetaZona from "../features/zonas/TarjetaZona.jsx";
import { ZONAS } from "../features/zonas/zonas.js";
// Formato de horas.
import { formatearHora } from "../features/telemetria/formato.js";
// Modo nube, sesión y formulario de acceso.
import { MODO_NUBE, supabase } from "../services/supabase.js";
import { useSesion } from "../features/sesion/useSesion.js";
import Acceso from "../features/sesion/Acceso.jsx";
// Etiqueta visual.
import Etiqueta from "../components/Etiqueta.jsx";

// Página del panel: en modo nube exige sesión; en modo local muestra el contenido directamente.
export default function Panel() {
  // Modo local: sin cuentas, se puede ordenar.
  if (!MODO_NUBE) return <ContenidoPanel puedeOrdenar fuente="Backend local" />;
  // Modo nube: pasa por la sesión.
  return <PanelNube />;
}

// Envoltorio del modo nube: pide iniciar sesión y muestra la cuenta.
function PanelNube() {
  // Usuario, permiso de operador y estado de carga de la sesión.
  const { usuario, operador, cargando } = useSesion();
  // Mientras se revisa la sesión guardada.
  if (cargando) return <div className="contenedor panel"><p className="vacio">Comprobando sesión…</p></div>;
  // Sin sesión: formulario de acceso.
  if (!usuario) return <div className="contenedor"><Acceso /></div>;
  // Con sesión: el panel con la barra de la cuenta.
  return (
    <ContenidoPanel
      puedeOrdenar={operador}
      fuente="Supabase (nube, tiempo real)"
      cuenta={
        // Correo, permiso y botón para salir.
        <div className="cuenta">
          <span>{usuario.email}</span>
          <Etiqueta tono={operador ? "bueno" : "neutro"}>{operador ? "Operador" : "Solo lectura"}</Etiqueta>
          <button type="button" onClick={() => supabase.auth.signOut()}>Cerrar sesión</button>
        </div>
      }
    />
  );
}

// Contenido del panel. Props: puedeOrdenar (permiso para enviar órdenes), fuente (texto) y cuenta (barra opcional).
function ContenidoPanel({ puedeOrdenar, fuente, cuenta = null }) {
  // Último resumen, historial para gráficos, error de la última consulta y estado de carga.
  const { resumen, historial, error, cargando, avisoReloj } = useResumen();

  // Mientras no haya ninguna respuesta, se muestra un mensaje de carga.
  if (cargando && !resumen) {
    // Mensaje simple.
    return (
      <div className="contenedor panel">
        <p className="vacio">Conectando con el backend…</p>
      </div>
    );
  }

  // Zonas que la web espera pero el backend no envió (pasa si el backend corre una versión antigua del código).
  const zonasFaltantes = resumen ? ZONAS.filter((zona) => !resumen.zonas?.[zona.id]) : [];
  // Entradas de las zonas conocidas por la web (se ignoran zonas antiguas que el backend aún envíe).
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
  const actuadoresEncendidos = entradasZonas.reduce((total, e) => total + Object.values(e.lectura?.actuadores ?? {}).filter((estado) => estado === "encendido").length, 0);

  // Devuelve la página.
  return (
    // Contenedor centrado del panel.
    <div className="contenedor panel">
      {/* Cabecera del panel. */}
      <div className="panel__cabecera">
        {/* Título y descripción. */}
        <div>
          <h1>Panel de Control</h1>
          <p>Zonas de evaluación en paralelo: árida, húmeda y selvática. Fuente de datos: {fuente}.</p>
        </div>
        {/* Cuenta (solo en modo nube). */}
        {cuenta}
      </div>

      {/* Error de comunicación con el backend (se conservan los últimos datos). */}
      {error && (
        // role="alert" anuncia el error de inmediato.
        <p className="aviso aviso--malo" role="alert">
          {error}
        </p>
      )}
      {/* Aviso si el reloj del equipo está desfasado (solo modo nube). */}
      {avisoReloj && (
        <p className="aviso aviso--simulado" role="note">
          {avisoReloj}
        </p>
      )}
      {/* Aviso si el backend no conoce alguna zona: casi siempre significa que sigue corriendo una versión antigua. */}
      {zonasFaltantes.length > 0 && (
        // role="alert" anuncia el problema de inmediato.
        <p className="aviso aviso--malo" role="alert">
          <strong>El backend no informa las zonas: {zonasFaltantes.map((zona) => zona.nombre).join(", ")}.</strong> Probablemente sigue corriendo una versión anterior del código. Detén los servicios (Ctrl+C en su terminal) y vuelve a iniciarlos con <code>python scripts/iniciar_local.py</code>.
        </p>
      )}
      {/* Aviso permanente cuando hay datos simulados. */}
      {hayDatosSimulados && (
        // role="note" marca una nota informativa.
        <p className="aviso aviso--simulado" role="note">
          <strong>Datos SIMULADOS.</strong> No son mediciones reales: provienen del simulador de software. La luz, el CO₂ y la radiación son valores inventados.
        </p>
      )}

      {/* Si el backend nunca respondió, no hay nada más que mostrar. */}
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
          {/* Tarjeta del depósito, debajo de las zonas (solo si el backend la informa). */}
          {deposito && (
            <div style={{ marginTop: 20 }}>
              <TarjetaDeposito entrada={deposito} unidades={resumen.unidades} />
            </div>
          )}
        </>
      )}
    </div>
  );
}
