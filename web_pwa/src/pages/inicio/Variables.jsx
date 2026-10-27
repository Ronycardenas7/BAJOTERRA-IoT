// Sección "Variables monitoreadas": rangos que acepta el sistema.
// Son los límites de validación del contrato de datos, NO la precisión de sensores concretos (aún no están elegidos).

// Variables: nombre, rango aceptado y nota.
const VARIABLES = [
  { nombre: "Temperatura", rango: "−40 a 85 °C", nota: "Aire del compartimento" },
  { nombre: "Humedad del aire", rango: "0 – 100 % HR", nota: "Humedad relativa" },
  { nombre: "Humedad del sustrato", rango: "0 – 100 %", nota: "Relativa a la calibración del sensor" },
  { nombre: "CO₂", rango: "250 – 5000 ppm", nota: "Zona selvática" },
  { nombre: "Radiación solar", rango: "0 – 1500 W/m²", nota: "Zona árida" },
  { nombre: "Conductividad (EC)", rango: "0 – 20 mS/cm", nota: "Solución del depósito" },
];

// Componente sin props.
export default function Variables() {
  // Devuelve la sección.
  return (
    // Sección ancla "#variables" con fondo alternativo.
    <section className="seccion seccion--alt" id="variables" aria-labelledby="titulo-variables">
      {/* Contenedor. */}
      <div className="contenedor">
        {/* Rótulo y título. */}
        <p className="rotulo">Variables monitoreadas</p>
        <h2 className="titulo-seccion" id="titulo-variables">
          Lo que el sistema mide
        </h2>
        {/* Rejilla de variables. */}
        <div className="variables">
          {VARIABLES.map(({ nombre, rango, nota }) => (
            // Una tarjeta por variable.
            <div className="variable" key={nombre}>
              {/* Nombre, rango y nota. */}
              <div className="variable__nombre">{nombre}</div>
              <div className="variable__rango">{rango}</div>
              <div className="variable__nota">{nota}</div>
            </div>
          ))}
        </div>
        {/* Aclaración honesta. */}
        <p className="nota-pequena">Rango aceptado por el sistema para validar los datos. La precisión real dependerá de los sensores que se elijan y de su calibración.</p>
      </div>
    </section>
  );
}
