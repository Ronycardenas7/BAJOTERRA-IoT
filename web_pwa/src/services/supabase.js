// Conexión con Supabase (modo nube). Es el modo por defecto.
// Modo local (backend Flask en este PC): iniciar la web con "corepack pnpm dev:local" (Vite usa el modo "backend").

// Función oficial para crear el cliente de Supabase.
import { createClient } from "@supabase/supabase-js";
// URL y clave publicable del proyecto (no son secretas).
import { CLAVE_PUBLICABLE, URL_SUPABASE } from "../config/nube.js";

// true si la web debe trabajar con Supabase; false si se inició en modo "backend" (backend del PC).
export const MODO_NUBE = import.meta.env.MODE !== "backend";

// Cliente único para toda la aplicación (null en modo local). Guarda la sesión en el navegador para no pedir login cada vez.
export const supabase = MODO_NUBE ? createClient(URL_SUPABASE, CLAVE_PUBLICABLE, { auth: { persistSession: true } }) : null;
