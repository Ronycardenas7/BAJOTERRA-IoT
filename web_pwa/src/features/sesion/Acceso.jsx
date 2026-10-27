// Formulario de inicio de sesión y registro (modo nube). Usa Supabase Auth con correo y contraseña.

// useState guarda los campos y mensajes.
import { useState } from "react";
// Cliente de Supabase.
import { supabase } from "../../services/supabase.js";

// Traduce los errores más comunes de Supabase Auth al español.
function traducir(mensaje) {
  // Credenciales incorrectas.
  if (/invalid login credentials/i.test(mensaje)) return "Correo o contraseña incorrectos.";
  // Correo sin confirmar.
  if (/email not confirmed/i.test(mensaje)) return "Primero confirma tu correo con el enlace que te enviamos.";
  // Usuario ya registrado.
  if (/already registered/i.test(mensaje)) return "Ese correo ya tiene cuenta: usa 'Entrar'.";
  // Contraseña corta.
  if (/password should be at least/i.test(mensaje)) return "La contraseña debe tener al menos 6 caracteres.";
  // Demasiados intentos o correos.
  if (/rate limit/i.test(mensaje)) return "Demasiados intentos. Espera unos minutos y vuelve a probar.";
  // Otro error: se muestra tal cual.
  return mensaje;
}

// Componente sin props.
export default function Acceso() {
  // "entrar" o "registrar".
  const [modo, setModo] = useState("entrar");
  // Campos del formulario.
  const [correo, setCorreo] = useState("");
  const [clave, setClave] = useState("");
  // Mensajes para el usuario.
  const [error, setError] = useState(null);
  const [aviso, setAviso] = useState(null);
  // true mientras se espera a Supabase.
  const [enviando, setEnviando] = useState(false);

  // Envía el formulario.
  async function alEnviar(evento) {
    // Evita que el navegador recargue la página.
    evento.preventDefault();
    // Limpia mensajes y marca "enviando".
    setError(null);
    setAviso(null);
    setEnviando(true);
    // Inicia sesión o crea la cuenta según el modo.
    const { data, error: fallo } =
      modo === "entrar"
        ? await supabase.auth.signInWithPassword({ email: correo, password: clave })
        : await supabase.auth.signUp({ email: correo, password: clave, options: { emailRedirectTo: window.location.origin } });
    // Termina el envío.
    setEnviando(false);
    // Error: se muestra traducido.
    if (fallo) return setError(traducir(fallo.message));
    // Registro sin sesión inmediata: falta confirmar el correo.
    if (modo === "registrar" && !data.session) setAviso("Cuenta creada. Revisa tu correo y pulsa el enlace de confirmación; luego vuelve aquí y entra.");
  }

  // Devuelve el formulario.
  return (
    // Tarjeta centrada.
    <section className="acceso" aria-labelledby="titulo-acceso">
      {/* Título. */}
      <h1 id="titulo-acceso">{modo === "entrar" ? "Entrar al Panel de Control" : "Crear una cuenta"}</h1>
      {/* Explicación. */}
      <p className="acceso__texto">Los datos del invernadero solo se muestran a personas con cuenta. Para enviar órdenes, además, tu cuenta debe estar marcada como operador.</p>
      {/* Formulario. */}
      <form onSubmit={alEnviar} className="acceso__formulario">
        {/* Correo. */}
        <label>
          Correo
          <input type="email" required autoComplete="email" value={correo} onChange={(e) => setCorreo(e.target.value)} />
        </label>
        {/* Contraseña. */}
        <label>
          Contraseña
          <input type="password" required minLength={6} autoComplete={modo === "entrar" ? "current-password" : "new-password"} value={clave} onChange={(e) => setClave(e.target.value)} />
        </label>
        {/* Botón principal. */}
        <button className="boton boton--primario" type="submit" disabled={enviando}>
          {enviando ? "Un momento…" : modo === "entrar" ? "Entrar" : "Crear cuenta"}
        </button>
      </form>
      {/* Mensajes. */}
      {error && (
        <p className="aviso aviso--malo" role="alert">
          {error}
        </p>
      )}
      {aviso && (
        <p className="aviso aviso--simulado" role="status">
          {aviso}
        </p>
      )}
      {/* Cambiar entre entrar y registrarse. */}
      <button type="button" className="enlace-sutil acceso__cambiar" onClick={() => setModo(modo === "entrar" ? "registrar" : "entrar")}>
        {modo === "entrar" ? "¿No tienes cuenta? Crear una" : "¿Ya tienes cuenta? Entrar"}
      </button>
    </section>
  );
}
