// Carga el historial desde Supabase y recibe las lecturas nuevas por Realtime.

// useEffect conecta y desconecta Realtime; useMemo arma el resumen; useState guarda datos.
import { useEffect, useMemo, useState } from "react";
// Acceso a Supabase.
import { escucharLecturas, historialZona, medirDesfaseMs, ultimaLecturaDeposito } from "../../services/datosNube.js";
// Zonas y unidades.
import { IDS_ZONAS } from "../zonas/zonas.js";
import { UNIDADES } from "./formato.js";

// Máximo de lecturas por zona en memoria (acota el uso de RAM aunque la página quede abierta días).
const MAX_PUNTOS = 60;
// Las lecturas más antiguas que este umbral se marcan como desactualizadas.
const UMBRAL_S = 60;
// Cada cuánto se recalcula la antigüedad de los datos (no hace peticiones: solo actualiza la pantalla).
const TIC_MS = 5000;
// Cada cuánto se vuelve a medir el desfase del reloj de este equipo con el servidor (10 minutos).
const RELOJ_MS = 600000;
// Desfase a partir del cual se avisa en pantalla (1 minuto).
const AVISO_DESFASE_MS = 60000;

// Agrega lecturas sin repetir, ordenadas por hora de medición, y recorta al máximo.
function fusionar(actuales, nuevas) {
  // Mapa por id de mensaje para descartar repetidas.
  const porId = new Map();
  // Primero las actuales, luego las nuevas.
  for (const lectura of [...(actuales ?? []), ...nuevas]) porId.set(lectura.id_mensaje, lectura);
  // Ordena por fecha real (Date.parse) y deja las últimas MAX_PUNTOS.
  return [...porId.values()].sort((a, b) => Date.parse(a.medido_en) - Date.parse(b.medido_en)).slice(-MAX_PUNTOS);
}

// Conserva la lectura más reciente aunque las respuestas lleguen en otro orden.
function lecturaMasReciente(anterior, nueva) {
  if (!nueva) return anterior;
  if (!anterior) return nueva;
  const fechaAnterior = Date.parse(anterior.medido_en);
  const fechaNueva = Date.parse(nueva.medido_en);
  return !Number.isFinite(fechaAnterior) || fechaNueva >= fechaAnterior ? nueva : anterior;
}

// Estado de conexión calculado a partir de la última lectura.
function conexionDesde(lectura, ahora) {
  // Una fecha inválida tampoco permite confirmar la conexión.
  const recepcion = Date.parse(lectura?.recibido_en);
  if (!Number.isFinite(recepcion)) return { estado: "desconocido", desactualizada: false, segundos_desde_ultima_lectura: null };
  // Segundos desde que Supabase recibió la lectura.
  const edad = Math.max(0, (ahora - recepcion) / 1000);
  // Reciente = en línea; antigua = desactualizada (no se afirma que esté desconectado).
  return { estado: edad <= UMBRAL_S ? "en_linea" : "desconocido", desactualizada: edad > UMBRAL_S, segundos_desde_ultima_lectura: edad };
}

// Hook principal del modo nube.
export function useResumenNube() {
  // Lecturas recientes por zona.
  const [historial, setHistorial] = useState({});
  // Última lectura del depósito.
  const [deposito, setDeposito] = useState(null);
  // Mensaje de error (null si todo bien).
  const [error, setError] = useState(null);
  // El estado del canal no debe ocultar errores al consultar el historial.
  const [errorRealtime, setErrorRealtime] = useState(null);
  // true hasta terminar la carga inicial.
  const [cargando, setCargando] = useState(true);
  // Diferencia entre el reloj del servidor y el de este equipo (ms); corrige PCs con la hora mal configurada.
  const [desfase, setDesfase] = useState(0);
  // Hora actual del equipo, para calcular la antigüedad (se le suma el desfase).
  const [ahoraLocal, setAhoraLocal] = useState(Date.now());
  // Hora corregida con el desfase.
  const ahora = ahoraLocal + desfase;

  // Al montar: carga inicial + suscripción en tiempo real + reloj. Al desmontar: se limpia todo.
  useEffect(() => {
    // Evita actualizar el estado si el componente ya se desmontó.
    let activo = true;
    // Carga inicial del historial de cada zona y del depósito.
    async function cargar() {
      // Intenta todas las consultas en paralelo.
      try {
        // Historial de las tres zonas y última lectura del depósito.
        const [series, ultimaDep] = await Promise.all([
          Promise.all(IDS_ZONAS.map((zona) => historialZona(zona, MAX_PUNTOS))),
          ultimaLecturaDeposito("principal"),
        ]);
        // Si el componente sigue montado, guarda los datos.
        if (!activo) return;
        // Une con lo que haya llegado por Realtime mientras tanto.
        setHistorial((previo) => Object.fromEntries(IDS_ZONAS.map((zona, i) => [zona, fusionar(previo[zona], series[i])])));
        // Conserva la lectura más reciente entre la consulta y el canal.
        setDeposito((previo) => lecturaMasReciente(previo, ultimaDep));
        // Limpia errores.
        setError(null);
      // Error de red o de permisos.
      } catch (fallo) {
        // Mensaje visible.
        if (activo) setError(`No se pudieron cargar los datos de Supabase: ${fallo.message}`);
      // Siempre al terminar.
      } finally {
        // Ya no está cargando.
        if (activo) setCargando(false);
      }
    }
    // Se suscribe a las lecturas nuevas y repone el historial tras reconectar.
    let recargarAlConectar = false;
    const dejarDeEscuchar = escucharLecturas({
      // Lectura nueva de una zona: se agrega a su historial.
      alLeerZona: (lectura) => setHistorial((previo) => ({ ...previo, [lectura.zona]: fusionar(previo[lectura.zona], [lectura]) })),
      // Lectura nueva del depósito: conserva la de mayor fecha.
      alLeerDeposito: (lectura) => setDeposito((previo) => lecturaMasReciente(previo, lectura)),
      // Estado de la conexión en tiempo real.
      alCambiarEstado: (estado) => {
        // Descarta avisos de una suscripción que ya se desmontó.
        if (!activo) return;
        if (estado === "SUBSCRIBED") {
          setErrorRealtime(null);
          if (recargarAlConectar) cargar();
          recargarAlConectar = true;
        }
        // Problemas: se avisa (supabase-js reintenta solo).
        else if (estado === "CHANNEL_ERROR" || estado === "TIMED_OUT" || estado === "CLOSED") {
          recargarAlConectar = true;
          setErrorRealtime("La conexión en tiempo real se interrumpió.");
        }
      },
    });
    // Mide el desfase del reloj (si falla, se mantiene el último valor).
    const medir = () => medirDesfaseMs().then((ms) => {
      if (activo && Number.isFinite(ms)) setDesfase(ms);
    }).catch(() => {});
    // Carga inicial y primera medición del reloj.
    cargar();
    medir();
    // Reloj para recalcular antigüedades.
    const reloj = setInterval(() => setAhoraLocal(Date.now()), TIC_MS);
    // Nueva medición del desfase cada 10 minutos.
    const relojServidor = setInterval(medir, RELOJ_MS);
    // Limpieza al salir del panel: corta Realtime y los temporizadores.
    return () => {
      activo = false;
      dejarDeEscuchar();
      clearInterval(reloj);
      clearInterval(relojServidor);
    };
  }, []);

  // Arma el resumen para las tarjetas cuando cambian los datos o el reloj.
  const resumen = useMemo(() => {
    // Mientras carga no hay resumen.
    if (cargando) return null;
    // Resumen completo.
    return {
      generado_en: new Date(ahora).toISOString(),
      umbral_desactualizado_s: UMBRAL_S,
      unidades: UNIDADES,
      zonas: Object.fromEntries(
        IDS_ZONAS.map((zona) => {
          // Última lectura de la zona (la más nueva está al final).
          const lista = historial[zona] ?? [];
          const ultima = lista.length ? lista[lista.length - 1] : null;
          // Entrada de la zona.
          return [zona, { zona, lectura: ultima, conexion: conexionDesde(ultima, ahora) }];
        }),
      ),
      depositos: { principal: { deposito: "principal", lectura: deposito, conexion: conexionDesde(deposito, ahora) } },
    };
  }, [cargando, historial, deposito, ahora]);

  // Aviso si el reloj de este equipo está desfasado (la web lo corrige, pero conviene arreglar la hora del equipo).
  const avisoReloj =
    Math.abs(desfase) > AVISO_DESFASE_MS
      ? `El reloj de este equipo está ${desfase < 0 ? "adelantado" : "atrasado"} ${Math.round(Math.abs(desfase) / 60000)} min respecto del servidor. La web lo corrige, pero conviene ajustar la hora de Windows (hora automática y zona horaria).`
      : null;
  // Devuelve el estado.
  return { resumen, historial, error: error ?? errorRealtime, cargando, avisoReloj };
}
