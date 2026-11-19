// Catálogo de magnitudes. Los SVG locales son de Tabler Icons (licencia MIT).
const VARIABLES_SISTEMA = [
  { id: "temperatura", nombre: "Temperatura", icono: "temperature", rango: "−40 a 85 °C" },
  { id: "humedad-aire", nombre: "Humedad del aire", icono: "droplet-half-2", rango: "0 – 100 % HR" },
  { id: "humedad-sustrato", nombre: "Humedad del sustrato", icono: "plant-2", rango: "0 – 100 %" },
  { id: "co2", nombre: "CO₂", icono: "atom-2", rango: "Sin sensor" },
  { id: "radiacion-solar", nombre: "Radiación solar", icono: "sun-high", rango: "Sin sensor" },
  { id: "conductividad", nombre: "Conductividad", icono: "circuit-resistor", rango: "Sin sensor" },
];

export default function Variables() {
  return (
    <section className="seccion-variables-conectadas" id="variables" aria-labelledby="titulo-variables">
      <div className="contenedor">
        {/* Encabezado editorial */}
        <div className="seccion-variables-conectadas__cabecera">
          <p className="rotulo-lima">Variables Ambientales</p>
          <h2 id="titulo-variables" className="seccion-variables-conectadas__titulo">
            Magnitudes ambientales
          </h2>
          <p className="seccion-variables-conectadas__bajada">
            Los nodos miden la temperatura y la humedad del aire y del sustrato de cada zona.
          </p>
        </div>

        {/* Los iconos distinguen las magnitudes; el texto comunica el rango o la disponibilidad. */}
        <div className="seccion-variables-conectadas__fila">
          {/* Una celda por magnitud, sin elementos decorativos que ocupen espacio. */}
          {VARIABLES_SISTEMA.map((item) => (
            <div key={item.id} className="circulo-variable-item" data-magnitud={item.id}>
              {/* La máscara conserva la forma del SVG y toma el color de la magnitud. */}
              <div className="circulo-variable-item__aro" aria-hidden="true">
                <span
                  className="circulo-variable-item__icono"
                  style={{ "--grafico-magnitud": `url("/assets/iconos/tabler/${item.icono}.svg")` }}
                />
              </div>

              {/* Título de la variable */}
              <h3 className="circulo-variable-item__nombre">{item.nombre}</h3>
              <span className="circulo-variable-item__rango">{item.rango}</span>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
