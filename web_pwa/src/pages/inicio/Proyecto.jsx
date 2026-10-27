// Sección "Sobre el proyecto": contexto y las tres zonas en resumen.

// Iconos y datos de zonas.
import Icono from "../../components/Iconos.jsx";
import { ZONAS } from "../../features/zonas/zonas.js";

// Componente sin props.
export default function Proyecto() {
  // Devuelve la sección.
  return (
    // Sección ancla "#proyecto".
    <section className="seccion" id="proyecto" aria-labelledby="titulo-proyecto">
      {/* Contenedor de dos columnas. */}
      <div className="contenedor dos-columnas">
        {/* Columna de texto. */}
        <div className="texto-largo">
          {/* Rótulo. */}
          <p className="rotulo">Sobre el proyecto</p>
          {/* Título. */}
          <h2 className="titulo-seccion" id="titulo-proyecto">
            Agricultura de precisión para zonas áridas
          </h2>
          {/* Contexto del proyecto (basado en la descripción del anteproyecto). */}
          <p>
            BAJOTERRA nace en la región de Tarapacá, donde el agua escasea. Un invernadero automatizado permite mantener condiciones distintas para cada cultivo y usar el agua con más criterio.
          </p>
          {/* Cómo funciona. */}
          <p>
            Sensores y microcontroladores ESP32 miden cada zona y accionan bombas, extractores y luces. Mientras no exista el hardware, un simulador entrega datos de prueba que la web identifica siempre como SIMULADOS.
          </p>
        </div>
        {/* Columna visual: una franja por zona. */}
        <div className="franjas">
          {ZONAS.map((zona) => (
            // Cada franja usa el color de su zona.
            <div key={zona.id} className={`franja zona--${zona.id}`}>
              {/* Icono. */}
              <Icono nombre={zona.icono} tamano={28} />
              {/* Nombre y lema. */}
              <div>
                <strong>{zona.nombre}</strong>
                <span>{zona.lema}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
