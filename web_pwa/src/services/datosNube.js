// Acceso a los datos en Supabase: lecturas, órdenes y permisos. Es el equivalente en la nube de services/api.js.

// Cliente de Supabase.
import { supabase } from "./supabase.js";

// Convierte una fila de la tabla lecturas_zona al mismo formato que entrega el backend local.
export function filaALecturaZona(fila) {
  // Devuelve la lectura con mediciones y actuadores agrupados.
  return {
    zona: fila.zona,
    dispositivo: fila.dispositivo,
    origen: fila.origen,
    id_mensaje: fila.id_mensaje,
    medido_en: fila.medido_en,
    recibido_en: fila.recibido_en,
    calidad: fila.calidad,
    // Mediciones: un null significa dato ausente (nunca se convierte en 0).
    mediciones: {
      temperatura: fila.temperatura,
      humedad_ambiente: fila.humedad_ambiente,
      humedad_sustrato: fila.humedad_sustrato,
      luz: fila.luz,
      co2: fila.co2,
      radiacion: fila.radiacion,
    },
    // Estado REPORTADO por el dispositivo.
    actuadores: { bomba: fila.bomba, ventilador: fila.ventilador, luces: fila.luces },
    modo: fila.modo,
  };
}

// Convierte una fila de lecturas_deposito al formato del backend local.
export function filaALecturaDeposito(fila) {
  // Devuelve la lectura del depósito.
  return {
    deposito: fila.deposito,
    dispositivo: fila.dispositivo,
    origen: fila.origen,
    id_mensaje: fila.id_mensaje,
    medido_en: fila.medido_en,
    recibido_en: fila.recibido_en,
    calidad: fila.calidad,
    mediciones: { conductividad_ec: fila.conductividad_ec, nivel_agua: fila.nivel_agua, agua_disponible: fila.agua_disponible },
  };
}

// Lanza un Error con un mensaje en español a partir de un error de Supabase.
function fallar(error) {
  // Permiso denegado: la cuenta no es operador.
  if (error?.code === "42501") throw new Error("Tu cuenta no tiene permiso para enviar órdenes. Pide que te agreguen como operador.");
  // Cualquier otro error, con el mensaje original.
  throw new Error(error?.message ?? "Error al comunicarse con Supabase");
}

// Últimas "limite" lecturas de una zona, de la más antigua a la más nueva.
export async function historialZona(zona, limite) {
  // Consulta las más recientes primero (usa el índice zona + medido_en).
  const { data, error } = await supabase.from("lecturas_zona").select("*").eq("zona", zona).order("medido_en", { ascending: false }).limit(limite);
  // Si falla, lanza el error.
  if (error) fallar(error);
  // Invierte el orden y convierte cada fila.
  return data.reverse().map(filaALecturaZona);
}

// Última lectura del depósito (o null si no hay).
export async function ultimaLecturaDeposito(deposito) {
  // Consulta la más reciente.
  const { data, error } = await supabase.from("lecturas_deposito").select("*").eq("deposito", deposito).order("medido_en", { ascending: false }).limit(1);
  // Si falla, lanza el error.
  if (error) fallar(error);
  // Convierte la fila o devuelve null.
  return data.length ? filaALecturaDeposito(data[0]) : null;
}

// Escucha en tiempo real las lecturas nuevas. Devuelve una función para dejar de escuchar (evita fugas de memoria).
export function escucharLecturas({ alLeerZona, alLeerDeposito, alCambiarEstado }) {
  // Canal de Realtime con dos suscripciones a inserciones.
  const canal = supabase
    .channel("bajoterra-lecturas")
    // Cada fila nueva en lecturas_zona.
    .on("postgres_changes", { event: "INSERT", schema: "public", table: "lecturas_zona" }, (cambio) => alLeerZona(filaALecturaZona(cambio.new)))
    // Cada fila nueva en lecturas_deposito.
    .on("postgres_changes", { event: "INSERT", schema: "public", table: "lecturas_deposito" }, (cambio) => alLeerDeposito(filaALecturaDeposito(cambio.new)))
    // Informa el estado de la conexión en tiempo real (SUBSCRIBED, CHANNEL_ERROR, TIMED_OUT, CLOSED).
    .subscribe((estado) => alCambiarEstado(estado));
  // Función de limpieza.
  return () => supabase.removeChannel(canal);
}

// Mide la diferencia (ms) entre el reloj del servidor y el de este equipo. Positivo = el equipo va atrasado.
export async function medirDesfaseMs() {
  // Hora local antes de preguntar.
  const antes = Date.now();
  // Pide la hora del servidor.
  const { data, error } = await supabase.rpc("hora_servidor");
  // Hora local después de la respuesta.
  const despues = Date.now();
  // Si falla, lanza el error.
  if (error) fallar(error);
  // Desfase respecto del punto medio (descuenta la demora de la red).
  return Date.parse(data) - (antes + despues) / 2;
}

// Crea una orden (solo operadores). Devuelve { comando } igual que el backend local.
export async function solicitarComandoNube(zona, actuador, estado) {
  // Llama a la función de la base de datos que valida el permiso.
  const { data, error } = await supabase.rpc("solicitar_comando", { p_zona: zona, p_actuador: actuador, p_estado: estado });
  // Si falla, lanza el error.
  if (error) fallar(error);
  // Devuelve la orden creada.
  return { comando: data };
}

// Lee el estado actual de una orden. Devuelve { comando }.
export async function obtenerComandoNube(idComando) {
  // Busca la orden por su identificador.
  const { data, error } = await supabase.from("comandos").select("*").eq("id_comando", idComando).single();
  // Si falla, lanza el error.
  if (error) fallar(error);
  // Devuelve la orden.
  return { comando: data };
}

// Indica si el usuario con sesión iniciada es operador (puede enviar órdenes).
export async function esOperador(idUsuario) {
  // La política RLS solo deja ver la propia fila.
  const { data, error } = await supabase.from("operadores").select("usuario").eq("usuario", idUsuario).maybeSingle();
  // Ante un error se asume que no (más seguro).
  if (error) return false;
  // true si existe la fila.
  return Boolean(data);
}
