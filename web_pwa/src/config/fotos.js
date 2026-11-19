// Las tarjetas y el carrusel comparten las fotos individuales y sus alternativas textuales.
export const FOTOS_ZONAS = {
  arida: {
    titulo: "Zona Árida",
    planta: "Cactus",
    descripcion: "Microclima seco con riego espaciado.",
    imagen: { src: "/assets/fotos/cactus.webp", alt: "Cactus dentro del módulo color arena" },
  },
  humeda: {
    titulo: "Zona Húmeda",
    planta: "Oreja de Oso",
    descripcion: "Ambiente húmedo con riego por pulsos.",
    imagen: { src: "/assets/fotos/oreja-de-oso-y-tagete.webp", alt: "Oreja de Oso en el módulo verde lima" },
  },
  selvatica: {
    titulo: "Zona Selvática",
    planta: "Schefflera",
    descripcion: "Follaje denso en un ambiente de alta humedad.",
    imagen: { src: "/assets/fotos/schefflera.webp", alt: "Schefflera dentro del módulo verde bosque" },
  },
};
// Fondo fotográfico de la portada y del acceso (Brands&People, Unsplash).
export const FOTO_FONDO = {
  src: "/assets/fotos/fondo-invernadero-1600.webp",
  srcSet: "/assets/fotos/fondo-invernadero-800.webp 800w, /assets/fotos/fondo-invernadero-1600.webp 1600w",
  sizes: "100vw",
  width: 1600,
  height: 1067,
  alt: "",
};

