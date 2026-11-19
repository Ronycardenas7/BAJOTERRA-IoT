// ============================================================================
// BAJOTERRA-IoT · Página de Inicio (Estilo Editorial Verde Bosque + Lima)
// Estructura adaptada de la referencia visual:
//   1. Hero Asimétrico (2 columnas: texto de alto impacto + foto 24px)
//   2. Fila de Módulos (4 tarjetas simétricas: 3 zonas + depósito central + botón lima)
//   3. Sección Editorial ("Más que un simple invernadero", foto circular y 5 métricas)
//   4. Galería de Hardware ("Hardware del Sistema", columna fija + 3 tarjetas horizontales)
//   5. Sección Final de Variables (6 círculos simétricos conectados con iconos en lima)
// ============================================================================

import React from "react";
import Hero from "./inicio/Hero.jsx";
import Zonas from "./inicio/Zonas.jsx";
import Proyecto from "./inicio/Proyecto.jsx";
import ComponentCarousel from "../components/ComponentCarousel.jsx";
import Variables from "./inicio/Variables.jsx";

export default function Inicio() {
  return (
    <div className="pagina-inicio-editorial">
      {/* 1. Hero Asimétrico de 2 columnas */}
      <Hero />

      {/* 2. Fila de 4 tarjetas de microclimas y depósito */}
      <Zonas />

      {/* 3. Bloque editorial "Más que un simple invernadero" + 5 métricas clave */}
      <Proyecto />

      {/* 4. Galería de componentes de hardware real */}
      <ComponentCarousel />

      {/* 5. Variables monitoreadas en círculos simétricos conectados */}
      <Variables />
    </div>
  );
}
