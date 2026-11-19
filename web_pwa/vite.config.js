// Configuración de Vite (la herramienta que sirve y empaqueta la web).

// defineConfig ayuda al editor a autocompletar las opciones.
import { defineConfig } from "vite";
// Plugin que enseña a Vite a procesar React (JSX).
import react from "@vitejs/plugin-react";

// Exporta la configuración.
export default defineConfig({
  // Activa el soporte de React.
  plugins: [react()],
  // Opciones del empaquetado de producción.
  build: {
    // Minifica JavaScript con esbuild.
    minify: "esbuild",
    // Omite los mapas de código fuente en dist.
    sourcemap: false,
  },
  // Opciones del servidor de desarrollo.
  server: {
    // Solo accesible desde este equipo (no desde la red local).
    host: "127.0.0.1",
    // Puerto de la web en desarrollo.
    port: 5173,
  },
});
