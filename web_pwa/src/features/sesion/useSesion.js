// Hook de sesión (modo nube): usuario con sesión iniciada y si tiene permiso de operador.

// useEffect escucha cambios de sesión; useState guarda el usuario.
import { useEffect, useState } from "react";
// Devuelve la sesión y el permiso de control para todas las rutas.
export function useSesion() {
  // Usuario actual (null sin sesión).
  const [usuario, setUsuario] = useState(null);
  // El permiso queda asociado a la cuenta que se consultó.
  const [cuentaOperadora, setCuentaOperadora] = useState(null);
  // true hasta saber si hay sesión.
  const [cargando, setCargando] = useState(true);
  const [errorSesion, setErrorSesion] = useState(false);

  // Supabase emite INITIAL_SESSION y los cambios posteriores de la sesión.
  useEffect(() => {
    let vigente = true;
    let suscripcion;
    // Carga el cliente sin incluirlo en el archivo inicial de la portada.
    import("../../services/supabase.js").then(({ supabase }) => {
      if (!vigente) return;
      const { data } = supabase.auth.onAuthStateChange((_evento, sesion) => {
        if (!vigente) return;
        setUsuario(sesion?.user ?? null);
        setCargando(false);
      });
      suscripcion = data.subscription;
    }).catch(() => {
      if (!vigente) return;
      setErrorSesion(true);
      setCargando(false);
    });
    // Mantiene la misma suscripción al cambiar de ruta y la limpia al desmontar.
    return () => {
      vigente = false;
      suscripcion?.unsubscribe();
    };
  }, []);

  // Consulta el permiso al cambiar de cuenta y descarta respuestas de una sesión anterior.
  const cuenta = usuario?.id;
  useEffect(() => {
    setCuentaOperadora(null);
    if (!cuenta) return undefined;
    let vigente = true;
    import("../../services/datosNube.js").then(({ esOperador }) => esOperador(cuenta)).then((permiso) => {
      if (vigente && permiso) setCuentaOperadora(cuenta);
    }).catch(() => {
      // Conserva el acceso de solo lectura si la consulta falla.
    });
    return () => { vigente = false; };
  }, [cuenta]);

  // Devuelve el estado de la sesión.
  return { usuario, operador: Boolean(cuenta) && cuenta === cuentaOperadora, cargando, errorSesion };
}
