// Llamada final a la acción: invita a entrar al Panel de Control.

// Icono.
import Icono from "../../components/Iconos.jsx";

// Componente sin props.
export default function LlamadaFinal() {
  // Devuelve la sección.
  return (
    // Sección centrada.
    <section className="seccion llamada" aria-labelledby="titulo-llamada">
      {/* Contenedor. */}
      <div className="contenedor">
        {/* Título. */}
        <h2 className="titulo-seccion" id="titulo-llamada">
          ¿Listo para monitorear tu invernadero?
        </h2>
        {/* Texto. */}
        <p className="bajada">Entra al panel de control y revisa las tres zonas en tiempo casi real.</p>
        {/* Botón. */}
        <a className="boton boton--primario boton--grande" href="#/panel">
          Ir al Panel de Control
          <Icono nombre="flecha" tamano={18} />
        </a>
      </div>
    </section>
  );
}
