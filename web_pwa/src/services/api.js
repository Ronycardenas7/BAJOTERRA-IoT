// Cliente de la API del backend. Es el único archivo que sabe cómo se hacen las peticiones HTTP.
// En modo nube (Supabase configurado) las órdenes se envían a Supabase en lugar del backend local.

// Indica si se usa Supabase y funciones equivalentes en la nube.
import { MODO_NUBE } from "./supabase.js";
import { obtenerComandoNube, solicitarComandoNube } from "./datosNube.js";

// Convierte la respuesta HTTP en datos, o lanza un Error legible si el backend informó un problema.
async function leerRespuesta(respuesta) {
  // Intenta leer el cuerpo como JSON; si no es JSON devuelve null.
  const datos = await respuesta.json().catch(() => null);
  // Si el código HTTP indica error (400, 404, 503...), lanza un Error con el mensaje del backend.
  if (!respuesta.ok) {
    // El backend responde { error: { codigo, mensaje } }.
    const mensaje = datos?.error?.mensaje ?? `Error ${respuesta.status} al hablar con el backend`;
    // Crea el error con ese mensaje.
    const error = new Error(mensaje);
    // Guarda el código estable para poder reaccionar según el tipo de error.
    error.codigo = datos?.error?.codigo ?? "error_desconocido";
    // Lanza el error.
    throw error;
  }
  // Si todo salió bien, devuelve los datos.
  return datos;
}

// Pide el resumen de zonas y depósito. "senal" permite cancelar la petición si el componente desaparece.
export async function obtenerResumen(senal) {
  // GET /api/resumen.
  const respuesta = await fetch("/api/resumen", { signal: senal });
  // Devuelve los datos ya leídos.
  return leerRespuesta(respuesta);
}

// Solicita una orden para un actuador de una zona.
export async function solicitarComando(zona, actuador, estado) {
  // En modo nube, la orden la crea Supabase (exige ser operador).
  if (MODO_NUBE) return solicitarComandoNube(zona, actuador, estado);
  // POST /api/zonas/{zona}/comandos con el cuerpo en JSON.
  const respuesta = await fetch(`/api/zonas/${encodeURIComponent(zona)}/comandos`, {
    // Método HTTP.
    method: "POST",
    // Indica que el cuerpo es JSON.
    headers: { "Content-Type": "application/json" },
    // Cuerpo de la petición.
    body: JSON.stringify({ actuador, estado }),
  });
  // Devuelve { comando }.
  return leerRespuesta(respuesta);
}

// Consulta el estado de un comando por su identificador.
export async function obtenerComando(idComando) {
  // En modo nube, se lee de la tabla comandos.
  if (MODO_NUBE) return obtenerComandoNube(idComando);
  // GET /api/comandos/{id}.
  const respuesta = await fetch(`/api/comandos/${encodeURIComponent(idComando)}`);
  // Devuelve { comando }.
  return leerRespuesta(respuesta);
}

// Pide el historial reciente de una zona (las últimas "limite" lecturas, de la más antigua a la más nueva).
export async function obtenerHistorial(zona, limite, senal) {
  // GET /api/zonas/{zona}/telemetria?limite=N.
  const respuesta = await fetch(`/api/zonas/${encodeURIComponent(zona)}/telemetria?limite=${limite}`, { signal: senal });
  // Devuelve { zona, lecturas }.
  return leerRespuesta(respuesta);
}
