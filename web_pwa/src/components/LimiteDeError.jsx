// Red de seguridad: si un componente falla al dibujarse, muestra un mensaje en vez de dejar la página en blanco.
// React solo permite esto con una clase (los "hooks" todavía no tienen equivalente).

// Component es la clase base de los componentes con clase.
import { Component } from "react";

// Componente que envuelve a otros y captura sus errores de dibujo.
export default class LimiteDeError extends Component {
  // Estado inicial: sin error.
  state = { fallo: null };

  // React llama a este método cuando un hijo lanza un error; devuelve el nuevo estado.
  static getDerivedStateFromError(error) {
    // Guarda el error para mostrarlo.
    return { fallo: error };
  }

  // React llama a este método después, para poder registrar el error.
  componentDidCatch(error, info) {
    // Deja el detalle en la consola del navegador para depurar.
    console.error("Error al dibujar la interfaz:", error, info.componentStack);
  }

  // Dibuja el contenido normal o el mensaje de error.
  render() {
    // Si hubo un error, muestra un aviso con el motivo y una forma de reintentar.
    if (this.state.fallo) {
      // Aviso de error.
      return (
        // role="alert" anuncia el error de inmediato.
        <div className="aviso aviso--malo" role="alert">
          {/* Mensaje principal. */}
          <strong>La pantalla tuvo un problema y no pudo mostrarse.</strong>
          {/* Detalle técnico para quien depura. */}
          <p>{String(this.state.fallo.message)}</p>
          {/* Botón que intenta dibujar de nuevo. */}
          <button type="button" onClick={() => this.setState({ fallo: null })}>
            Reintentar
          </button>
        </div>
      );
    }
    // Sin error: muestra los componentes hijos.
    return this.props.children;
  }
}
