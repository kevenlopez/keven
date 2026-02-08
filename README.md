# StarSVG

StarSVG es una librería de Python para:

1. Incrustar varios archivos SVG en un lienzo.
2. Generar un SVG combinado final.
3. Exportar ese SVG final a PDF (**sin CairoSVG**).
4. Exportar PNG en una o varias resoluciones.

## Instalación

```bash
pip install -e .
```

Con soporte para PDF:

```bash
pip install -e .[pdf]
```

Con soporte para PNG:

```bash
pip install -e .[png]
```

## Uso rápido

```python
from starsvg import StarSVGCanvas

canvas = StarSVGCanvas(width=1200, height=800, background="white")
canvas.add_svg_file("mapa_base.svg", x=0, y=0, width=1200, height=800)
canvas.add_svg_file("planeta_marte.svg", x=610, y=310, width=40, height=40)

canvas.save_svg("mapa_general.svg")
canvas.save_pdf("mapa_general.pdf")
canvas.save_png("mapa_general.png", scale=2)
canvas.save_png_resolutions("exports", "mapa_general", scales=[1, 2, 3])
```

## API

- `StarSVGCanvas(width, height, background="transparent")`
- `add_svg_file(svg_path, x=0, y=0, width=100, height=100)`
- `add_svg_content(svg_content, x=0, y=0, width=100, height=100)`
- `render_svg() -> str`
- `save_svg(output_path)`
- `save_pdf(output_path)`
- `save_png(output_path, scale=1.0)`
- `save_png_resolutions(output_dir, base_name, scales)`

## Notas

- StarSVG compone SVG de forma **inline** (inyecta nodos SVG al resultado final), en lugar de usar `<image href="data:...">`, para maximizar compatibilidad de render en SVG y PDF/PNG.
- La exportación a PDF requiere `svglib` y `reportlab` (`pip install starsvg[pdf]`).
- La exportación a PNG requiere `svglib` y `reportlab` (`pip install starsvg[png]`).
- `save_pdf` y `save_png` lanzarán un `RuntimeError` si faltan sus dependencias.
