// Hook de sesión (modo nube): usuario con sesión iniciada y si tiene permiso de operador.

// useEffect escucha cambios de sesión; useState guarda el usuario.
import { useEffect, useState } from "react";
// Cliente de Supabase y consulta de permisos.
import { supabase } from "../../services/supabase.js";
import { esOperador } from "../../services/datosNube.js";

// Devuelve { usuario, operador, cargando }.
export function useSesion() {
  // Usuario actual (null sin sesión).
  const [usuario, setUsuario] = useState(null);
  // true si puede enviar órdenes.
  const [operador, setOperador] = useState(false);
  // true hasta saber si hay sesión.
  const [cargando, setCargando] = useState(true);

  // Al montar: lee la sesión guardada y escucha inicios/cierres de sesión.
  useEffect(() => {
    // Evita actualizar el estado tras desmontar.
    let activo = true;
    // Actualiza usuario y permiso.
    async function aplicar(sesion) {
      // Usuario de la sesión (o null).
      const nuevo = sesion?.user ?? null;
      // Consulta el permiso solo si hay usuario.
      const permiso = nuevo ? await esOperador(nuevo.id) : false;
      // Guarda si sigue montado.
      if (!activo) return;
      setUsuario(nuevo);
      setOperador(permiso);
      setCargando(false);
    }
    // Sesión guardada en el navegador.
    supabase.auth.getSession().then(({ data }) => aplicar(data.session));
    // Cambios posteriores (login, logout, renovación del token). setTimeout evita llamar a Supabase dentro del aviso.
    const { data } = supabase.auth.onAuthStateChange((_evento, sesion) => {
      setTimeout(() => aplicar(sesion), 0);
    });
    // Limpieza: deja de escuchar.
    return () => {
      activo = false;
      data.subscription.unsubscribe();
    };
  }, []);

  // Devuelve el estado de la sesión.
  return { usuario, operador, cargando };
}
