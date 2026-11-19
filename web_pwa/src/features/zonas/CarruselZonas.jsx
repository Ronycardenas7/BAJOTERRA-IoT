// El desplazamiento nativo conserva los gestos táctiles.
import { useEffect, useLayoutEffect, useRef, useState } from "react";
// Anime.js anima la descripción al pasar el ratón.
import { animate } from "animejs";
// Usa las fotos originales de los tres microclimas.
import { FOTOS_ZONAS } from "../../config/fotos.js";

// Mantiene el mismo orden que las tarjetas de la portada.
const ZONAS = Object.entries(FOTOS_ZONAS);
const TOTAL = ZONAS.length;
const VELOCIDAD = 30;
const COPIAS = ["anterior", "original", "siguiente"];

// Devuelve la posición que centra la tarjeta en la ventana.
function posicionDe(lista, indice) {
  const tarjeta = lista.children[indice];
  return tarjeta.offsetLeft - (lista.clientWidth - tarjeta.offsetWidth) / 2;
}

function indiceCentrado(lista) {
  // Las tarjetas mantienen un ancho uniforme, incluso al cambiar el tamaño de pantalla.
  const paso = posicionDe(lista, 1) - posicionDe(lista, 0);
  return Math.round((lista.scrollLeft - posicionDe(lista, 0)) / paso);
}

function FotoZona({ id, zona, copia }) {
  // Guarda la animación actual para limpiar sus estilos al reiniciar o desmontar.
  const detalle = useRef(null);
  const animacion = useRef(null);
  useEffect(() => () => animacion.current?.revert(), []);

  function destacar(evento) {
    // En dispositivos táctiles se muestra la descripción directamente.
    if (evento.pointerType !== "mouse" || matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    animacion.current?.revert();
    animacion.current = animate(detalle.current, {
      y: [10, 0],
      opacity: [0, 1],
      duration: 360,
      ease: "outCubic",
    });
  }

  return (
    // El acento identifica el microclima; la foto y el nombre lo explican sin depender del color.
    <li className={`carrusel-zonas__diapositiva zona--${id}`} aria-hidden={copia || undefined} onPointerEnter={destacar}>
      <figure className="carrusel-zonas__foto">
        <img {...zona.imagen} loading="lazy" decoding="async" />
        <figcaption className="carrusel-zonas__pie">
          <span>{zona.titulo}</span>
          <strong>{zona.planta}</strong>
          <p ref={detalle}>{zona.descripcion}</p>
        </figcaption>
      </figure>
    </li>
  );
}

export default function CarruselZonas() {
  // Sincroniza los selectores con el movimiento automático y manual.
  const pista = useRef(null);
  const destino = useRef(null);
  const manualHasta = useRef(0);
  const [activa, setActiva] = useState(0);
  const [visible, setVisible] = useState(false);
  const [interactuando, setInteractuando] = useState(false);

  useLayoutEffect(() => {
    // Empieza por Árida, con una copia a cada lado para cerrar el ciclo.
    const lista = pista.current;
    lista.scrollLeft = posicionDe(lista, TOTAL);
    const observador = new IntersectionObserver(([entrada]) => setVisible(entrada.isIntersecting));
    observador.observe(lista);
    return () => observador.disconnect();
  }, []);

  useEffect(() => {
    if (!visible || interactuando) return undefined;
    const lista = pista.current;
    const reducirMovimiento = matchMedia("(prefers-reduced-motion: reduce)");
    let cuadro;
    let anterior;
    let posicion = lista.scrollLeft;

    function avanzar(ahora) {
      // Da tiempo para leer una foto elegida o terminar un gesto táctil.
      if (ahora >= manualHasta.current) {
        destino.current = null;
        const origen = posicionDe(lista, TOTAL);
        const vuelta = posicionDe(lista, TOTAL * 2) - origen;
        const transcurrido = anterior === undefined ? 0 : Math.min(50, ahora - anterior);
        // Conserva la fracción de píxel y corrige cambios manuales o de tamaño.
        if (Math.abs(posicion - lista.scrollLeft) > 1) posicion = lista.scrollLeft;
        const avance = posicion - origen + transcurrido * VELOCIDAD / 1000;
        posicion = origen + ((avance % vuelta) + vuelta) % vuelta;
        lista.scrollLeft = posicion;
      }
      anterior = ahora;
      cuadro = requestAnimationFrame(avanzar);
    }

    function ajustarMovimiento() {
      cancelAnimationFrame(cuadro);
      anterior = undefined;
      if (!reducirMovimiento.matches) cuadro = requestAnimationFrame(avanzar);
    }

    ajustarMovimiento();
    reducirMovimiento.addEventListener("change", ajustarMovimiento);
    return () => {
      cancelAnimationFrame(cuadro);
      reducirMovimiento.removeEventListener("change", ajustarMovimiento);
    };
  }, [interactuando, visible]);

  function darTiempoParaLeer() {
    manualHasta.current = performance.now() + 2400;
  }

  function desplazar(indice) {
    const lista = pista.current;
    const izquierda = posicionDe(lista, indice);
    // Centra una tarjeta próxima y permite seleccionar con el movimiento reducido.
    destino.current = Math.abs(lista.scrollLeft - izquierda) > 1 ? indice : null;
    darTiempoParaLeer();
    lista.scrollTo({
      left: izquierda,
      behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "instant" : "smooth",
    });
  }

  function paso(direccion) {
    const lista = pista.current;
    let actual = destino.current ?? indiceCentrado(lista);
    // Reubica un extremo en su copia idéntica antes de seguir en esa dirección.
    if (actual + direccion < 0 || actual + direccion >= lista.children.length) {
      actual = TOTAL + actual % TOTAL;
      lista.scrollLeft = posicionDe(lista, actual);
    }
    desplazar(actual + direccion);
  }

  function alDesplazar() {
    const lista = pista.current;
    // Las copias no cambian el indicador de la zona.
    setActiva(indiceCentrado(lista) % TOTAL);
  }

  function alTeclado(evento) {
    // También permite usar las flechas cuando la galería tiene el foco.
    if (evento.key !== "ArrowLeft" && evento.key !== "ArrowRight") return;
    evento.preventDefault();
    paso(evento.key === "ArrowLeft" ? -1 : 1);
  }

  return (
    <section className="carrusel-zonas" aria-label="Fotos de los microclimas" onKeyDown={alTeclado}>
      {/* La lista muestra parte de la siguiente foto como pista visual del desplazamiento. */}
      <ul
        className="carrusel-zonas__pista"
        ref={pista}
        tabIndex={0}
        aria-label="Desliza para ver las zonas"
        onScroll={alDesplazar}
        onScrollEnd={() => { destino.current = null; }}
        onPointerEnter={(evento) => { if (evento.pointerType === "mouse") setInteractuando(true); }}
        onPointerLeave={() => setInteractuando(false)}
        onPointerDown={() => {
          destino.current = null;
          darTiempoParaLeer();
        }}
        onTouchMove={darTiempoParaLeer}
        onWheel={darTiempoParaLeer}
      >
        {COPIAS.map((grupo) => ZONAS.map(([id, zona]) => (
          <FotoZona key={`${grupo}-${id}`} id={id} zona={zona} copia={grupo !== "original"} />
        )))}
      </ul>
      {/* Flechas y selectores directos funcionan con ratón, teclado y tacto. */}
      <div className="carrusel-zonas__controles">
        <button type="button" className="carrusel-zonas__flecha" aria-label="Zona anterior" onClick={() => paso(-1)}>‹</button>
        <div className="carrusel-zonas__puntos">
          {ZONAS.map(([id, zona], indice) => (
            <button
              key={id}
              className="carrusel-zonas__punto"
              type="button"
              aria-label={`Mostrar ${zona.titulo}`}
              aria-current={indice === activa ? "true" : undefined}
              onClick={() => {
                // Elige la copia más próxima para evitar recorrer una vuelta innecesaria.
                const actual = destino.current ?? indiceCentrado(pista.current);
                const candidatos = [indice, TOTAL + indice, TOTAL * 2 + indice];
                desplazar(candidatos.reduce((cerca, opcion) => (
                  Math.abs(opcion - actual) < Math.abs(cerca - actual) ? opcion : cerca
                )));
              }}
            />
          ))}
        </div>
        <button type="button" className="carrusel-zonas__flecha" aria-label="Zona siguiente" onClick={() => paso(1)}>›</button>
      </div>
    </section>
  );
}
