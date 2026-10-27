// Sección "Capacidades": lo que el sistema hace. Solo se listan funciones que existen en el proyecto.

// Iconos.
import Icono from "../../components/Iconos.jsx";

// Capacidades: icono, título y descripción.
const CAPACIDADES = [
  { icono: "termometro", titulo: "Monitoreo ambiental", texto: "Temperatura, humedad del aire y del sustrato, luz, CO₂ y radiación según los sensores de cada zona." },
  { icono: "gota", titulo: "Sistema de riego", texto: "Bomba de agua por zona con control automático según la humedad del sustrato y orden manual desde el panel." },
  { icono: "bombilla", titulo: "Luces LED", texto: "Luces de apoyo que se encienden cuando la luz natural es baja, o por orden manual." },
  { icono: "ventilador", titulo: "Extractores", texto: "Ventilación que se activa con el calor o con exceso de CO₂, para mantener cada ecosistema estable." },
  { icono: "capas", titulo: "Zonas independientes", texto: "Árida, húmeda y selvática se controlan por separado, cada una con su propio dispositivo y sus propios umbrales." },
  { icono: "escudo", titulo: "Órdenes confirmadas", texto: "Una orden enviada no es una orden cumplida: el panel muestra el estado real que informa el dispositivo." },
];

// Componente sin props.
export default function Capacidades() {
  // Devuelve la sección.
  return (
    // Sección ancla "#capacidades" con fondo alternativo.
    <section className="seccion seccion--alt" id="capacidades" aria-labelledby="titulo-capacidades">
      {/* Contenedor. */}
      <div className="contenedor">
        {/* Rótulo y título. */}
        <p className="rotulo">Capacidades</p>
        <h2 className="titulo-seccion" id="titulo-capacidades">
          Todo bajo control
        </h2>
        {/* Rejilla de cartas. */}
        <div className="rejilla-cartas">
          {CAPACIDADES.map(({ icono, titulo, texto }) => (
            // Una carta por capacidad.
            <article className="carta" key={titulo}>
              {/* Icono dentro de un recuadro de color. */}
              <div className="carta__icono">
                <Icono nombre={icono} />
              </div>
              {/* Título y texto. */}
              <h3>{titulo}</h3>
              <p>{texto}</p>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}
