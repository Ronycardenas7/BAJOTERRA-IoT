// ============================================================================
// BAJOTERRA-IoT · Sección Fila de Módulos / Zonas (4 Columnas)
// Muestra las 3 zonas reales (Árida, Húmeda, Selvática) más el Depósito Central
// asegurando simetría en escritorio, y botón centrado "Explorar Panel Completo".
// ============================================================================

import React from "react";
import ZonaCard from "../../features/zonas/ZonaCard.jsx";
import Icono from "../../components/Iconos.jsx";

// Los 4 módulos físicos del sistema BAJOTERRA-IoT
const MODULOS_INVERNADERO = [
  {
    id: "arida",
    titulo: "Zona Árida",
    subtitulo: "Módulo derecho kraft/arena · Ambiente seco",
    imagen: "/assets/plantas/cactus.svg",
    especificaciones: [
      "Planta: Cactus (adaptado a estrés hídrico)",
      "Sustrato: Arena silícea y grava drenante",
      "Régimen: Aire seco con riego dosificado espaciado",
    ],
    estado: "Operativo",
    enlace: "#/panel",
  },
  {
    id: "humeda",
    titulo: "Zona Húmeda",
    subtitulo: "Módulo central verde lima · Ambiente húmedo",
    imagen: "/assets/plantas/oreja-oso.svg",
    especificaciones: [
      "Planta: Oreja de Oso y Tagete (brote floral)",
      "Sustrato: Tierra vegetal con retención de humedad",
      "Régimen: Micro-riego por pulsos automáticos",
    ],
    estado: "En riego",
    enlace: "#/panel",
  },
  {
    id: "selvatica",
    titulo: "Zona Selvática",
    subtitulo: "Módulo izquierdo bosque · Follaje denso",
    imagen: "/assets/plantas/schefflera.svg",
    especificaciones: [
      "Planta: Schefflera (follaje perenne denso)",
      "Sustrato: Mezcla enriquecida con humus",
      "Régimen: Ventilación térmica por lazo PI y sombra",
    ],
    estado: "Lazo PI activo",
    enlace: "#/panel",
  },
  {
    id: "deposito",
    titulo: "Depósito Central",
    subtitulo: "Sistema Hídrico · Abastecimiento",
    imagen: "/assets/plantas/deposito.svg",
    especificaciones: [
      "Reserva: Tanque de 50L con sensor de boya",
      "Bomba: Sumergible 5V con protección anti-atasco",
      "Régimen: Suministro por electrobombas a demanda",
    ],
    estado: "Nivel óptimo",
    enlace: "#/panel",
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

        {/* Botón centrado en verde lima: "Explorar Panel Completo" */}
        <div className="seccion-modulos__accion-central">
          <a className="boton-solido-lima boton-solido-lima--grande" href="#/panel">
            <span>Explorar Panel Completo</span>
            <Icono nombre="flecha" tamano={18} />
          </a>
        </div>
      </div>
    </section>
  );
}
