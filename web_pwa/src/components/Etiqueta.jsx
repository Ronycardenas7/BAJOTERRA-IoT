// Etiqueta pequeña para estados (SIMULADO, En línea, Desactualizado...). El texto siempre dice el estado:
// el color solo refuerza, nunca es la única señal (accesibilidad).

// Componente: "tono" puede ser bueno, aviso, malo, neutro o simulado.
export default function Etiqueta({ tono = "neutro", children }) {
  // Devuelve un <span> con la clase del tono elegido.
  return <span className={`etiqueta etiqueta--${tono}`}>{children}</span>;
}
