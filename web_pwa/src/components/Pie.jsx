// Pie de página con una aclaración honesta sobre el estado del proyecto.

// Componente sin props.
export default function Pie() {
  // Devuelve el pie.
  return (
    // <footer> semántico.
    <footer className="pie">
      {/* Contenedor centrado con dos textos. */}
      <div className="contenedor pie__fila">
        {/* Nombre y año. */}
        <span>BAJOTERRA · Invernadero inteligente · Iquique, Tarapacá</span>
        {/* Aviso: mientras no haya hardware, todo es simulación. */}
        <span>Invernadero IoT · Telemetría en Supabase</span>
      </div>
    </footer>
  );
}
