// ============================================================================
// BAJOTERRA-IoT · Sección Fila de Módulos / Zonas (4 Columnas)
// Muestra las 3 zonas reales (Árida, Húmeda, Selvática) más el Depósito Central
// en una rejilla que se adapta al ancho de la pantalla.
// ============================================================================

// Tarjetas de los módulos y su catálogo fotográfico.
import ZonaCard from "../../features/zonas/ZonaCard.jsx";
import { FOTOS_ZONAS } from "../../config/fotos.js";

// Los 4 módulos físicos del sistema BAJOTERRA-IoT
const MODULOS_INVERNADERO = [
  {
    id: "arida",
    titulo: FOTOS_ZONAS.arida.titulo,
    subtitulo: "Módulo derecho kraft/arena · Ambiente seco",
    imagen: FOTOS_ZONAS.arida.imagen,
    especificaciones: [
      "Planta: Cactus (adaptado a estrés hídrico)",
      "Régimen: Aire seco con riego dosificado espaciado",
    ],
  },
  {
    id: "humeda",
    titulo: FOTOS_ZONAS.humeda.titulo,
    subtitulo: "Módulo central verde lima · Ambiente húmedo",
    imagen: FOTOS_ZONAS.humeda.imagen,
    especificaciones: [
      `Planta: ${FOTOS_ZONAS.humeda.planta}`,
      "Régimen: Micro-riego por pulsos automáticos",
    ],
  },
  {
    id: "selvatica",
    titulo: FOTOS_ZONAS.selvatica.titulo,
    subtitulo: "Módulo izquierdo bosque · Follaje denso",
    imagen: FOTOS_ZONAS.selvatica.imagen,
    especificaciones: [
      "Planta: Schefflera (follaje perenne denso)",
      "Régimen: Ventilación térmica por lazo PI y sombra",
    ],
  },
  {
    id: "deposito",
    titulo: "Depósito Central",
    subtitulo: "Sistema Hídrico · Abastecimiento",
    imagen: { src: "/assets/plantas/deposito.svg", alt: "Ilustración del depósito de agua" },
    especificaciones: [
      "Reserva de agua para el riego de las zonas",
    ],
  },
];

export default function Zonas() {
  return (
    <section className="seccion-modulos" id="zonas" aria-labelledby="titulo-modulos">
      <div className="contenedor">
        {/* Encabezado de la fila de módulos */}
        <div className="seccion-modulos__cabecera">
          <p className="rotulo-lima">Ecosistemas Agronómicos</p>
          <h2 id="titulo-modulos" className="seccion-modulos__titulo">
            Modelos de Control Microclimático
          </h2>
          <p className="seccion-modulos__bajada">
            Ambientes independientes con sensado dedicado y actuación de potencia autónoma.
          </p>
        </div>

        {/* Fila horizontal de 4 tarjetas simétricas */}
        <div className="seccion-modulos__rejilla">
          {MODULOS_INVERNADERO.map((modulo) => (
            <ZonaCard key={modulo.id} modulo={modulo} />
          ))}
        </div>
      </div>
    </section>
  );
}
