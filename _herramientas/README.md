# Herramientas del visor 3D (El Laboratorio SG)

Cómo se hizo `hair-transplant/`, para repetirlo con cada cliente:

1. **Vectores**: exportar el PDF de Corel del logo y convertirlo a SVG (`pdftocairo -svg`). `vec.py` toma las formas (relleno o clip-paths) y las guarda en `piezas.json`, cada letra con su grupo (`arriba` = separada con snaps y retroiluminada, `design` = pegada a la pared) y su material. Ajustar la selección de formas para cada logo.
2. **Modelo**: `build3d.py` lee `piezas.json` y genera `modelo.glb` a tamaño real (ancho total en pulgadas), el halo de luz cálida y los PNG del modo foto (`logo-encendido.png`, `logo-apagado.png`). Ajustar ancho, grosor (`T`), separación (`GAP`), colores y qué grupo lleva luz.
3. **Revisión**: `test.html` + `poster.js` renderizan el GLB con three.js para revisar y sacar `poster.jpg` / `og.jpg`.
4. **Página**: copiar `hair-transplant/index.html` a la carpeta del nuevo cliente y cambiar nombre, medidas, textos y enlace de WhatsApp.
5. Subir la carpeta a este repositorio: queda en `https://ellaboratoriosg-bot.github.io/visor/<cliente>/`.


**Variante con base blanca por sección** (Hair Transplant v2): `vec_bases.py` saca del SVG las bases blancas (unidas y limpias), las letras verdes y las piezas doradas; `build3d_bases.py` las monta así: base blanca separada de la pared con la luz detrás y las letras encima. El dibujo de Corel ya viene a escala 1:1 (1 pt = 1/72"). Al actualizar un visor, súbele el `?v=` a los archivos en el `index.html` para que el teléfono no muestre la versión vieja.
