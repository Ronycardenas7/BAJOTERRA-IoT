// Datos fijos de presentación de las tres zonas de evaluación (no vienen del backend).
// Los identificadores coinciden con backend/app/domain/constantes.py y con los temas MQTT.

// Lista ordenada de zonas.
export const ZONAS = [
  {
    // Identificador técnico (sin tildes), usado en la API y en los temas MQTT.
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
    descripcion: "Ecosistema de vegetación densa con poca luz directa. Se observa el CO₂ del aire y la luz difusa, que las luces LED complementan.",
    enfoque: "Prioridad: CO₂ bajo control con el extractor y luz suficiente mediante LED cuando la luz natural es baja.",
    icono: "hoja",
    metricas: ["co2", "luz", "humedad_ambiente", "temperatura"],
    etiquetas: ["CO₂", "Luz difusa", "Luces LED"],
  },
];

// Búsqueda rápida por identificador.
export const ZONA_POR_ID = Object.fromEntries(ZONAS.map((zona) => [zona.id, zona]));

// Lista de identificadores (útil para consultar el historial de cada zona).
export const IDS_ZONAS = ZONAS.map((zona) => zona.id);
