// Hook que envía órdenes a los actuadores de UNA zona y sigue su estado hasta que haya un resultado.
// Importante: "orden enviada" NO significa "actuador encendido". El estado real viene de la telemetría reportada.

// useEffect ejecuta código cuando algo cambia; useState guarda datos.
import { useEffect, useState } from "react";
// Funciones que crean y consultan órdenes en Supabase.
import { obtenerComandoNube, solicitarComandoNube } from "../../services/datosNube.js";
// Ayuda para saber si un comando ya terminó.
import { comandoTerminado } from "../telemetria/formato.js";

// Cada cuántos milisegundos se consulta el estado de la orden pendiente.
const INTERVALO_MS = 1000;
// Margen extra (ms) que se espera tras la caducidad antes de dejar de consultar.
const MARGEN_MS = 5000;

// Devuelve { comando, error, enviando, pendiente, enviar }.
export function useComando(zona) {
  // Última orden pedida desde esta pantalla (null si ninguna).
  const [comando, setComando] = useState(null);
  // Mensaje de error si no se pudo pedir la orden.
  const [error, setError] = useState(null);
  // True mientras se espera la respuesta de Supabase.
  const [enviando, setEnviando] = useState(false);
  // Hora actual (ms) que se actualiza en cada consulta, para detectar órdenes vencidas.
  const [ahora, setAhora] = useState(Date.now());

  // Una orden que sigue "enviada" después de su caducidad nunca fue confirmada: el estado real es incierto.
  const vencido = comando?.estado === "enviado" && ahora > Date.parse(comando.caduca_en);
  // Se deja de consultar cuando hay resultado final o cuando pasó la caducidad más el margen.
  const terminado = !comando || comandoTerminado(comando) || ahora > Date.parse(comando.caduca_en) + MARGEN_MS;

  // Mientras la orden esté pendiente, consulta su estado cada segundo.
  useEffect(() => {
    // Si no hay nada pendiente, no hace nada.
    if (terminado) return undefined;
    // Evita consultas solapadas y descarta respuestas de una orden que ya no se sigue.
    let vigente = true;
    let consultando = false;
    // Programa las consultas periódicas.
    const temporizador = setInterval(async () => {
      // La caducidad avanza aunque la red se demore.
      setAhora(Date.now());
      if (consultando) return;
      consultando = true;
      // Intenta leer el estado actual de la orden.
      try {
        // Consulta el estado de la orden en Supabase.
        const { comando: actual } = await obtenerComandoNube(comando.id_comando);
        // Guarda el estado nuevo.
        if (vigente) setComando(actual);
      // Si falla una consulta, se reintenta en el próximo ciclo.
      } catch {
        // Nada que hacer: el estado anterior se conserva.
      } finally {
        consultando = false;
      }
    }, INTERVALO_MS);
    // Al terminar o cambiar de orden, detiene el temporizador.
    return () => {
      vigente = false;
      clearInterval(temporizador);
    };
  }, [terminado, comando?.id_comando]);

  // Pide una orden a Supabase.
  async function enviar(actuador, estado) {
    // Marca que se está enviando y limpia el error anterior.
    setEnviando(true);
    setError(null);
    // Intenta pedir la orden.
    try {
      // Crea la orden mediante la función RPC de Supabase.
      const { comando: nuevo } = await solicitarComandoNube(zona, actuador, estado);
      // Guarda la orden para seguirla.
      setComando(nuevo);
      // Reinicia la hora de referencia.
      setAhora(Date.now());
    // Si Supabase rechaza o no responde, muestra el motivo.
    } catch (fallo) {
      // Mensaje legible para el operador.
      setError(fallo.message);
    // Siempre al terminar:
    } finally {
      // Ya no se está enviando.
      setEnviando(false);
    }
  }

  // Versión del comando que se muestra: si venció sin confirmación, se marca como tal.
  const visible = vencido ? { ...comando, estado: "sin_confirmacion" } : comando;
  // Hay una orden pendiente si existe y todavía no terminó.
  const pendiente = Boolean(comando) && !terminado;
  // Devuelve todo lo que necesita el componente.
  return { comando: visible, error, enviando, pendiente, enviar };
}
