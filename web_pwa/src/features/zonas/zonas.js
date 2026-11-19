// Datos fijos de presentación de las tres zonas registradas en Supabase.

// Lista ordenada de zonas.
export const ZONAS = [
  {
    // Identificador técnico sin tildes, usado en las consultas de Supabase.
    id: "arida",
    // Nombre para mostrar.
    nombre: "Zona Árida",
    // Frase corta bajo el nombre.
    lema: "Estrés hídrico · alta temperatura · radiación solar",
    // Descripción larga para la página de inicio.
    descripcion: "Ecosistema de calor intenso y aire seco. Se vigila cuánta agua conserva el sustrato, la temperatura y la radiación que recibe la planta.",
    // Qué se pone a prueba en esta zona (se muestra en el panel).
    enfoque: "Prioridad: no pasar sed ni sobrecalentarse. Riego medido y extractor cuando sube la temperatura.",
    // Icono principal.
    icono: "sol",
    // Mediciones destacadas en el panel, en orden (máximo 4).
    metricas: ["temperatura", "humedad_sustrato", "radiacion", "humedad_ambiente"],
    // Etiquetas de la página de inicio.
    etiquetas: ["Temperatura", "Humedad del sustrato", "Radiación solar"],
  },
  {
    id: "humeda",
    nombre: "Zona Húmeda",
    lema: "Alta humedad ambiental · riego constante",
    descripcion: "Ecosistema de aire saturado y sustrato siempre mojado. Se controla que el riego sea constante sin dejar el ambiente demasiado cálido.",
    enfoque: "Prioridad: mantener la humedad alta y el riego constante, con ventilación para evitar exceso de calor.",
    icono: "gota",
    metricas: ["humedad_ambiente", "humedad_sustrato", "temperatura", "luz"],
    etiquetas: ["Humedad del aire", "Humedad del sustrato", "Riego"],
  },
  {
    id: "selvatica",
    nombre: "Zona Selvática",
    lema: "Densa vegetación · niveles de CO₂ · luz difusa",
    // La descripción recoge las condiciones ambientales de la zona.
    descripcion: "Ecosistema de vegetación densa con poca luz directa. Se observa el CO₂ del aire y la luz difusa.",
    // Prioridades del panel para la zona selvática.
    enfoque: "Prioridad: vigilar el CO₂ y ventilar con el extractor cuando sube la temperatura.",
    icono: "hoja",
    metricas: ["co2", "luz", "humedad_ambiente", "temperatura"],
    // Etiquetas ambientales de la portada.
    etiquetas: ["CO₂", "Luz difusa"],
  },
];

// Lista de identificadores (útil para consultar el historial de cada zona).
export const IDS_ZONAS = ZONAS.map((zona) => zona.id);
