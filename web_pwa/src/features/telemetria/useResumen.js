// Hook que consulta el resumen del backend cada pocos segundos y conserva el último dato bueno.
// Más adelante se puede reemplazar por Supabase Realtime sin tocar los componentes.

// useEffect ejecuta código al montar el componente; useState guarda datos; useRef guarda un valor sin redibujar.
import { useEffect, useRef, useState } from "react";
// Funciones que llaman a la API.
import { obtenerHistorial, obtenerResumen } from "../../services/api.js";
// Identificadores de las zonas (para consultar su historial).
import { IDS_ZONAS } from "../zonas/zonas.js";

// Cada cuántos milisegundos se consulta el backend.
const INTERVALO_MS = 3000;
// Máximo de lecturas por zona que se guardan para los gráficos (acota el uso de memoria).
const MAX_PUNTOS = 60;

// Une listas de lecturas sin repetir ids de mensaje, ordenadas por hora de medición y recortadas al máximo.
function fusionar(actuales, nuevas) {
  // Mapa por id para eliminar repetidas.
  const porId = new Map();
  // Recorre primero las actuales y luego las nuevas.
  for (const lectura of [...(actuales ?? []), ...nuevas]) {
    // Guarda (o reemplaza) la lectura por su id.
    porId.set(lectura.id_mensaje, lectura);
  }
  // Ordena por instante de medición (los textos ISO en UTC se ordenan bien como texto) y recorta.
  return [...porId.values()].sort((a, b) => (a.medido_en < b.medido_en ? -1 : 1)).slice(-MAX_PUNTOS);
}

// Modo nube y su hook equivalente.
import { MODO_NUBE } from "../../services/supabase.js";
import { useResumenNube } from "./useResumenNube.js";

// Elige la fuente de datos: Supabase (nube) o backend local. MODO_NUBE no cambia mientras la página está abierta,
// así que siempre se llama al mismo hook (se respetan las reglas de los hooks de React).
export function useResumen() {
  // Modo nube: Supabase + Realtime; modo local: consulta periódica al backend.
  return MODO_NUBE ? useResumenNube() : useResumenLocal();
}

// Modo local. Devuelve { resumen, historial, error, cargando }. "historial" es { zona: [lecturas] } para los gráficos.
function useResumenLocal() {
  // Último resumen recibido (null hasta la primera respuesta).
  const [resumen, setResumen] = useState(null);
  // Mensaje de error de la última consulta (null si salió bien).
  const [error, setError] = useState(null);
  // Indica si todavía no hay ninguna respuesta.
  const [cargando, setCargando] = useState(true);
  // Últimas lecturas de cada zona, para los gráficos de tendencia.
  const [historial, setHistorial] = useState({});
  // Evita lanzar una consulta nueva si la anterior sigue en curso.
  const enCurso = useRef(false);

  // Se ejecuta una vez al aparecer el componente.
  useEffect(() => {
    // Controlador para cancelar peticiones pendientes al salir.
    const controlador = new AbortController();

    // Consulta el backend una vez.
    async function consultar() {
      // Si ya hay una consulta en curso, no empieza otra.
      if (enCurso.current) return;
      // Marca la consulta como en curso.
      enCurso.current = true;
      // Intenta obtener el resumen.
      try {
        // Pide los datos al backend.
        const datos = await obtenerResumen(controlador.signal);
        // Guarda los datos nuevos.
        setResumen(datos);
        // Agrega la última lectura de cada zona al historial (si ya estaba, no se repite).
        setHistorial((previo) => {
          // Copia superficial para no modificar el estado anterior.
          const siguiente = { ...previo };
          // Recorre las zonas del resumen.
          for (const [zona, entrada] of Object.entries(datos.zonas ?? {})) {
            // Solo si hay lectura.
            if (entrada.lectura) siguiente[zona] = fusionar(previo[zona], [entrada.lectura]);
          }
          // Devuelve el historial actualizado.
          return siguiente;
        });
        // Limpia cualquier error anterior.
        setError(null);
      // Si algo falla (backend caído, red...), guarda el motivo.
      } catch (fallo) {
        // Una cancelación al salir de la página no es un error real.
        if (fallo.name !== "AbortError") {
          // Mensaje claro; el último resumen bueno se conserva en pantalla.
          setError("No hay respuesta del backend. Se muestran los últimos datos recibidos.");
        }
      // Se ejecuta siempre al terminar.
      } finally {
        // Libera la marca de consulta en curso.
        enCurso.current = false;
        // Ya hubo al menos un intento: deja de mostrarse "cargando".
        setCargando(false);
      }
    }

    // Carga una sola vez el historial reciente de cada zona para que los gráficos no empiecen vacíos.
    async function sembrarHistorial() {
      // Una petición por zona, en paralelo.
      await Promise.all(
        IDS_ZONAS.map(async (zona) => {
          // Intenta leer el historial de la zona.
          try {
            // Pide las últimas lecturas.
            const { lecturas } = await obtenerHistorial(zona, MAX_PUNTOS, controlador.signal);
            // Las fusiona con lo que ya hubiera.
            setHistorial((previo) => ({ ...previo, [zona]: fusionar(previo[zona], lecturas) }));
          // Si falla, los gráficos se irán llenando con las consultas periódicas.
          } catch {
            // Nada que hacer.
          }
        }),
      );
    }

    // Siembra el historial y hace la primera consulta inmediata.
    sembrarHistorial();
    consultar();
    // Consultas periódicas.
    const temporizador = setInterval(consultar, INTERVALO_MS);
    // Al desaparecer el componente: detiene el temporizador y cancela la petición pendiente.
    return () => {
      // Detiene las consultas periódicas.
      clearInterval(temporizador);
      // Cancela la petición en vuelo.
      controlador.abort();
    };
  }, []);

  // Devuelve el estado para que lo use el componente.
  return { resumen, historial, error, cargando };
}
