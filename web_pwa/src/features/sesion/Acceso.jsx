// Formulario de acceso, registro y recuperación de la cuenta.
import { useState } from "react";
// Usa el mismo fondo que la portada.
import { FOTO_FONDO } from "../../config/fotos.js";
// Supabase envía los enlaces de correo y actualiza la contraseña de la sesión.
import { supabase } from "../../services/supabase.js";

// Cada paso pide solo los campos necesarios.
const MODOS = {
  entrar: {
    titulo: "Entrar al Panel de Control",
    texto: "Inicia sesión para consultar las lecturas y controlar los actuadores.",
    accion: "Entrar",
  },
  registrar: {
    titulo: "Crear una cuenta",
    texto: "Confirma tu correo para acceder al panel y controlar el invernadero.",
    accion: "Crear cuenta",
  },
  recuperar: {
    titulo: "Restablecer contraseña",
    texto: "Te enviaremos un enlace para elegir una contraseña nueva.",
    accion: "Enviar enlace",
  },
  cambiar: {
    titulo: "Elige una contraseña nueva",
    texto: "Escribe tu nueva contraseña dos veces para guardarla.",
    accion: "Guardar contraseña",
  },
};

// Traduce los errores de Auth que requieren una acción concreta.
function mensajeAcceso(error) {
  // Compatibilidad con respuestas de Auth que solo traen un mensaje.
  if (error.code === "invalid_credentials" || /invalid login credentials/i.test(error.message)) return "Correo o contraseña incorrectos.";
  if (error.code === "email_not_confirmed" || /email not confirmed/i.test(error.message)) return "Confirma tu correo antes de iniciar sesión.";
  if (error.code === "same_password") return "Elige una contraseña distinta a la anterior.";
  if (error.code === "weak_password") return "La contraseña no cumple los requisitos de seguridad.";
  if (error.status === 429) return "Demasiados intentos. Espera unos minutos y vuelve a probar.";
  if (error.status === 401 || error.code === "session_not_found") return "Tu sesión venció. Solicita un nuevo enlace.";
  return "No se pudo completar la solicitud. Revisa tu conexión e inténtalo de nuevo.";
}

export default function Acceso({ modoInicial = "entrar" }) {
  // Conserva el correo al alternar entre acceso, registro y recuperación.
  const [modo, setModo] = useState(modoInicial);
  const [correo, setCorreo] = useState("");
  const [clave, setClave] = useState("");
  const [confirmacion, setConfirmacion] = useState("");
  const [claveVisible, setClaveVisible] = useState(false);
  const [enviando, setEnviando] = useState(false);
  const [error, setError] = useState("");
  const [aviso, setAviso] = useState("");
  const [cambioGuardado, setCambioGuardado] = useState(false);
  const { titulo, texto, accion } = MODOS[modo];

  function seleccionarModo(siguiente) {
    // No arrastra credenciales ni mensajes a otro paso.
    setClave("");
    setConfirmacion("");
    setClaveVisible(false);
    setError("");
    setAviso("");
    setModo(siguiente);
  }

  async function alEnviar(evento) {
    evento.preventDefault();
    if (enviando) return;
    setError("");
    setAviso("");
    if (modo === "cambiar" && clave !== confirmacion) {
      setError("Las contraseñas no coinciden.");
      return;
    }

    setEnviando(true);
    // El retorno a la raíz reutiliza la URL permitida para confirmar cuentas.
    const redirectTo = window.location.origin;
    try {
      if (modo === "recuperar") {
        const { error: fallo } = await supabase.auth.resetPasswordForEmail(correo.trim(), { redirectTo });
        if (fallo && fallo.code !== "user_not_found") throw fallo;
        // El mensaje es el mismo aunque el correo no corresponda a una cuenta.
        setAviso("Si el correo está registrado, recibirás un enlace. Revisa también la carpeta de correo no deseado.");
      } else if (modo === "cambiar") {
        const { error: fallo } = await supabase.auth.updateUser({ password: clave });
        if (fallo) throw fallo;
        setClave("");
        setConfirmacion("");
        setCambioGuardado(true);
      } else {
        // El registro puede requerir que se confirme el correo antes de tener sesión.
        const credenciales = { email: correo.trim(), password: clave };
        const { data, error: fallo } = modo === "entrar"
          ? await supabase.auth.signInWithPassword(credenciales)
          : await supabase.auth.signUp({ ...credenciales, options: { emailRedirectTo: redirectTo } });
        if (fallo) throw fallo;
        if (modo === "registrar" && !data.session) {
          setAviso("Revisa tu correo y pulsa el enlace de confirmación para activar tu cuenta.");
        }
      }
    } catch (fallo) {
      setError(mensajeAcceso(fallo));
    } finally {
      setEnviando(false);
    }
  }

  return (
    <section className="acceso-pagina" aria-labelledby="titulo-acceso">
      {/* La fotografía es ambiental; la información de acceso se lee en la tarjeta. */}
      <img {...FOTO_FONDO} className="acceso-pagina__fondo" fetchPriority="high" />
      <div className="contenedor acceso-pagina__layout">
        <div className="acceso">
          <h1 id="titulo-acceso">{cambioGuardado ? "Contraseña actualizada" : titulo}</h1>
          {cambioGuardado ? (
            <>
              <p className="acceso__texto" role="status">Ya puedes usar tu nueva contraseña.</p>
              <a href="#/panel" className="boton-solido-lima">Volver al panel</a>
            </>
          ) : (
            <>
              <p className="acceso__texto">{texto}</p>
              <form onSubmit={alEnviar} className="acceso__formulario" aria-busy={enviando}>
                {modo !== "cambiar" && (
                  <label>
                    Correo
                    <input type="email" name="correo" required autoComplete="username" value={correo} onChange={(evento) => setCorreo(evento.target.value)} />
                  </label>
                )}
                {modo !== "recuperar" && (
                  <div className="acceso__grupo-clave">
                    <label>
                      {modo === "cambiar" ? "Nueva contraseña" : "Contraseña"}
                      <input
                        type={claveVisible ? "text" : "password"}
                        name="clave"
                        required
                        minLength={modo === "entrar" ? undefined : 6}
                        autoComplete={modo === "entrar" ? "current-password" : "new-password"}
                        value={clave}
                        onChange={(evento) => setClave(evento.target.value)}
                      />
                    </label>
                    <button type="button" className="acceso__mostrar" onClick={() => setClaveVisible((visible) => !visible)}>
                      {claveVisible ? "Ocultar" : "Mostrar"}
                    </button>
                  </div>
                )}
                {modo === "cambiar" && (
                  <label>
                    Confirmar nueva contraseña
                    <input type="password" name="confirmar-clave" autoComplete="new-password" required minLength={6} value={confirmacion} onChange={(evento) => setConfirmacion(evento.target.value)} />
                  </label>
                )}
                <button className="boton-solido-lima" type="submit" disabled={enviando}>{enviando ? "Un momento…" : accion}</button>
              </form>
              {error && <p className="aviso aviso--malo" role="alert">{error}</p>}
              {aviso && <p className="aviso" role="status">{aviso}</p>}
              <div className="acceso__enlaces">
                {modo === "entrar" ? (
                  <>
                    <button type="button" className="acceso__cambiar" disabled={enviando} onClick={() => seleccionarModo("recuperar")}>¿Olvidaste tu contraseña?</button>
                    <button type="button" className="acceso__cambiar" disabled={enviando} onClick={() => seleccionarModo("registrar")}>Crear una cuenta</button>
                  </>
                ) : modo === "cambiar" ? (
                  <a className="acceso__cambiar" href="#/panel">Volver al panel</a>
                ) : (
                  <button type="button" className="acceso__cambiar" disabled={enviando} onClick={() => seleccionarModo("entrar")}>Volver a iniciar sesión</button>
                )}
              </div>
            </>
          )}
        </div>
      </div>
    </section>
  );
}
