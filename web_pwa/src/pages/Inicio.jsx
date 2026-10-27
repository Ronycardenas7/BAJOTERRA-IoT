// Página de inicio: presentación del proyecto, inspirada en el prototipo de Figma (GreenLab).

// Secciones de la página, cada una en su propio módulo.
import Hero from "./inicio/Hero.jsx";
import Proyecto from "./inicio/Proyecto.jsx";
import Capacidades from "./inicio/Capacidades.jsx";
import ZonasEvaluacion from "./inicio/ZonasEvaluacion.jsx";
import Variables from "./inicio/Variables.jsx";
import LlamadaFinal from "./inicio/LlamadaFinal.jsx";

// Componente sin props: solo ordena las secciones.
export default function Inicio() {
  // Devuelve las secciones en orden.
  return (
    <>
      {/* Portada. */}
      <Hero />
      {/* Sobre el proyecto. */}
      <Proyecto />
      {/* Capacidades. */}
      <Capacidades />
      {/* Zonas de evaluación. */}
      <ZonasEvaluacion />
      {/* Variables monitoreadas. */}
      <Variables />
      {/* Llamada final. */}
      <LlamadaFinal />
    </>
  );
}
