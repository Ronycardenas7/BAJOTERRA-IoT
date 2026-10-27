// Punto de entrada: le dice a React dónde dibujar la aplicación.

// StrictMode activa advertencias extra en desarrollo para detectar errores temprano.
import { StrictMode } from "react";
// createRoot conecta React con un elemento del HTML.
import { createRoot } from "react-dom/client";
// Componente raíz de la aplicación.
import App from "./app/App.jsx";
// Estilos globales.
import "./styles/global.css";

// Busca el <div id="root"> de index.html, crea la raíz de React y dibuja la aplicación.
createRoot(document.getElementById("root")).render(
  // StrictMode envuelve la aplicación.
  <StrictMode>
    {/* Aplicación completa. */}
    <App />
  </StrictMode>,
);
