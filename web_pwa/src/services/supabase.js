// Cliente de Supabase para autenticación, telemetría y órdenes.

// Función oficial para crear el cliente de Supabase.
import { createClient } from "@supabase/supabase-js";
// URL y clave publicable del proyecto (no son secretas).
import { CLAVE_PUBLICABLE, URL_SUPABASE } from "../config/nube.js";

// Guarda la sesión en el navegador para reutilizarla al abrir el panel.
export const supabase = createClient(URL_SUPABASE, CLAVE_PUBLICABLE, { auth: { persistSession: true } });
