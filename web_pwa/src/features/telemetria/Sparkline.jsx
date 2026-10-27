// Mini gráfico de línea en SVG puro (sin librerías de gráficos): ligero y sin trabajo de CPU continuo.

// useMemo evita recalcular el dibujo si los valores no cambiaron.
import { useMemo } from "react";

// Tamaño interno del dibujo (viewBox) y margen.
const ANCHO = 120;
const ALTO = 36;
const MARGEN = 3;

// Props: valores (lista de números o null, de más antiguo a más nuevo) y etiqueta (texto accesible).
export default function Sparkline({ valores, etiqueta }) {
  // Calcula los puntos solo cuando cambian los valores.
  const dibujo = useMemo(() => {
    // Descarta los datos ausentes: no se dibujan como cero.
    const numeros = valores.filter((v) => typeof v === "number");
    // Con menos de 2 puntos no hay línea que mostrar.
    if (numeros.length < 2) return null;
    // Rango de los valores para escalar el eje vertical.
    const minimo = Math.min(...numeros);
    const maximo = Math.max(...numeros);
    // Si todos los valores son iguales, se usa 1 para no dividir por cero.
    const rango = maximo - minimo || 1;
    // Convierte cada valor en una coordenada (x, y) dentro del recuadro.
    const puntos = numeros.map((v, i) => {
      // x avanza de izquierda a derecha según la posición.
      const x = MARGEN + (i / (numeros.length - 1)) * (ANCHO - 2 * MARGEN);
      // y: los valores altos van arriba (el eje y del SVG crece hacia abajo).
      const y = ALTO - MARGEN - ((v - minimo) / rango) * (ALTO - 2 * MARGEN);
      // Redondea a un decimal para un texto más corto.
      return [Number(x.toFixed(1)), Number(y.toFixed(1))];
    });
    // Texto de la línea: "x,y x,y ...".
    const linea = puntos.map(([x, y]) => `${x},${y}`).join(" ");
    // Área bajo la línea: la línea más dos esquinas inferiores.
    const area = `${linea} ${puntos[puntos.length - 1][0]},${ALTO} ${puntos[0][0]},${ALTO}`;
    // Último punto, que se resalta.
    const ultimo = puntos[puntos.length - 1];
    // Devuelve lo necesario para dibujar.
    return { linea, area, ultimo };
  }, [valores]);

  // Sin suficientes datos, se muestra un espacio vacío con una línea punteada.
  if (!dibujo) {
    return <div className="spark spark--vacio" role="img" aria-label={`${etiqueta}: aún no hay suficientes datos para graficar`} />;
  }

  // Devuelve el gráfico.
  return (
    // role="img" + aria-label describen el gráfico a los lectores de pantalla.
    <svg className="spark" viewBox={`0 0 ${ANCHO} ${ALTO}`} preserveAspectRatio="none" role="img" aria-label={`Tendencia de ${etiqueta}`}>
      {/* Área suave bajo la línea. */}
      <polygon className="spark__area" points={dibujo.area} />
      {/* Línea de tendencia. */}
      <polyline className="spark__linea" points={dibujo.linea} />
      {/* Punto del último valor. */}
      <circle className="spark__punto" cx={dibujo.ultimo[0]} cy={dibujo.ultimo[1]} r="2.4" />
    </svg>
  );
}
