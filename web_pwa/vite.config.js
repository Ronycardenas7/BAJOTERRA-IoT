// Configuración de Vite (la herramienta que sirve y empaqueta la web).

// defineConfig ayuda al editor a autocompletar las opciones.
import { defineConfig } from "vite";
// Plugin que enseña a Vite a procesar React (JSX).
import react from "@vitejs/plugin-react";

// Dirección del backend para el modo desarrollo (pnpm dev). Se puede cambiar con la variable BACKEND_URL.
const backend = process.env.BACKEND_URL ?? "http://127.0.0.1:5000";

// Exporta la configuración.
export default defineConfig({
  // Activa el soporte de React.
  plugins: [react()],
  // Opciones del servidor de desarrollo.
  server: {
    // Solo accesible desde este equipo (no desde la red local).
    host: "127.0.0.1",
    // Puerto de la web en desarrollo.
    port: 5173,
    // Reenvía las llamadas a la API al backend para que el navegador vea un único origen (sin problemas de CORS).
    proxy: {
      // Todo lo que empiece con /api va al backend.
      "/api": backend,
      // La ruta de salud también.
      "/salud": backend,
    },
  },
});
