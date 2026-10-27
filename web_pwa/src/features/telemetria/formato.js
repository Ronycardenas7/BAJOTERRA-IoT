// Funciones para mostrar valores, horas y estados de forma clara y honesta.

// Zona horaria con la que se muestran las horas (el sistema guarda todo en UTC).
export const ZONA_HORARIA = "America/Santiago";

// Nombres legibles de cada medición.
export const NOMBRES_MEDICION = {
  temperatura: "Temperatura",
  humedad_ambiente: "Humedad del aire",
  humedad_sustrato: "Humedad del sustrato",
  luz: "Luz",
  co2: "CO₂",
  radiacion: "Radiación solar",
  conductividad_ec: "Conductividad (EC)",
  nivel_agua: "Nivel de agua",
};

// Decimales a mostrar en cada medición.
const DECIMALES = { temperatura: 1, humedad_ambiente: 1, humedad_sustrato: 1, luz: 0, co2: 0, radiacion: 0, conductividad_ec: 2, nivel_agua: 0 };

// Unidades de cada medición (iguales a backend/app/domain/constantes.py). En modo nube no hay backend que las envíe.
export const UNIDADES = {
  temperatura: "°C",
  humedad_ambiente: "% HR",
  humedad_sustrato: "% rel.",
  luz: "lux",
  co2: "ppm",
  radiacion: "W/m²",
  conductividad_ec: "mS/cm",
  nivel_agua: "%",
};

// Nombres legibles de cada actuador (el identificador técnico "ventilador" se muestra como "Extractor").
export const NOMBRES_ACTUADOR = {
  bomba: "Bomba de agua",
  ventilador: "Extractor",
  luces: "Luces LED",
};

// Formatea solo el número de una medición (sin unidad); un dato ausente se muestra como "—", nunca como 0.
export function formatearNumero(nombre, valor) {
  // Sin dato numérico, muestra una raya.
  if (typeof valor !== "number") return "—";
  // Cantidad de decimales según la medición (1 por defecto).
  const decimales = DECIMALES[nombre] ?? 1;
  // Formato numérico en español de Chile (coma decimal).
  return valor.toLocaleString("es-CL", { minimumFractionDigits: decimales, maximumFractionDigits: decimales });
}

// Formatea el valor de una medición con su unidad. Un dato ausente se muestra como "—", nunca como 0.
export function formatearMedicion(nombre, valor, unidades) {
  // Si no hay dato (null o indefinido), muestra una raya.
  if (typeof valor !== "number") return "—";
  // Cantidad de decimales según la medición (1 por defecto).
  const decimales = DECIMALES[nombre] ?? 1;
  // Formato numérico en español de Chile (coma decimal).
  const numero = valor.toLocaleString("es-CL", { minimumFractionDigits: decimales, maximumFractionDigits: decimales });
  // Une el número con su unidad (si existe).
  return unidades?.[nombre] ? `${numero} ${unidades[nombre]}` : numero;
}

// Convierte un instante en UTC (texto ISO) a una hora legible indicando la zona horaria.
export function formatearHora(iso) {
  // Sin dato no hay hora.
  if (!iso) return "—";
  // Intl.DateTimeFormat da formato de hora según idioma y zona horaria.
  return new Intl.DateTimeFormat("es-CL", {
    // Muestra horas, minutos y segundos (no se usa "timeStyle" porque no se puede combinar con timeZoneName).
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    // Convierte desde UTC a la zona horaria elegida.
    timeZone: ZONA_HORARIA,
    // Agrega la abreviatura de la zona (por ejemplo "GMT-3") para que no haya dudas.
    timeZoneName: "short",
  }).format(new Date(iso));
}

// Texto y tipo visual de la conexión de un dispositivo, considerando si los datos están desactualizados.
export function describirConexion(conexion) {
  // Sin información de conexión se declara desconocida.
  if (!conexion) return { texto: "Sin información", tono: "neutro" };
  // Un dispositivo que se declaró desconectado.
  if (conexion.estado === "desconectado") return { texto: "Desconectado", tono: "malo" };
  // Datos viejos aunque el dispositivo diga estar en línea: no se debe confiar en ellos.
  if (conexion.desactualizada) return { texto: "Datos desactualizados", tono: "aviso" };
  // En línea y con datos recientes.
  if (conexion.estado === "en_linea") return { texto: "En línea", tono: "bueno" };
  // Cualquier otro caso (por ejemplo, "desconocido").
  return { texto: "Conexión desconocida", tono: "neutro" };
}

// Texto del estado de un comando para mostrar al usuario. Una orden enviada NO es una orden ejecutada.
export function describirComando(comando) {
  // Sin comando no hay texto.
  if (!comando) return null;
  // Verbo según lo pedido.
  const accion = `${comando.estado_solicitado === "encendido" ? "Encender" : "Apagar"} ${NOMBRES_ACTUADOR[comando.actuador] ?? comando.actuador}`;
  // Texto según la etapa del comando.
  switch (comando.estado) {
    // Entregada al broker; falta que el dispositivo responda.
    case "enviado":
      return { texto: `${accion}: orden enviada, esperando confirmación…`, tono: "aviso" };
    // El dispositivo informó que la ejecutó.
    case "ejecutado":
      return { texto: `${accion}: confirmado por ${comando.dispositivo}${comando.origen_confirmacion === "simulado" ? " (simulado)" : ""}`, tono: "bueno" };
    // El dispositivo la rechazó.
    case "rechazado":
      return { texto: `${accion}: rechazado (${comando.detalle ?? "sin detalle"})`, tono: "malo" };
    // La orden llegó demasiado tarde.
    case "caducado":
      return { texto: `${accion}: caducó antes de ejecutarse`, tono: "malo" };
    // Ya se había procesado.
    case "duplicado":
      return { texto: `${accion}: el dispositivo ya la había procesado`, tono: "neutro" };
    // La orden venció y nadie la confirmó: no se sabe qué pasó con el actuador.
    case "sin_confirmacion":
      return { texto: `${accion}: sin confirmación; la orden caducó y el estado real del actuador es incierto`, tono: "aviso" };
    // No salió del backend.
    case "fallido_envio":
      return { texto: `${accion}: no se pudo enviar (${comando.detalle ?? "sin conexión con el broker"})`, tono: "malo" };
    // Estado no reconocido.
    default:
      return { texto: `${accion}: ${comando.estado}`, tono: "neutro" };
  }
}

// Indica si un comando ya llegó a un resultado final (deja de consultarse).
export function comandoTerminado(comando) {
  // Solo "enviado" sigue pendiente; los demás son finales.
  return comando.estado !== "enviado";
}
