# StarSVG

StarSVG es una librería de Python para:

1. Incrustar varios archivos SVG en un lienzo.
2. Generar un SVG combinado final.
3. Exportar ese SVG final a PDF (**sin CairoSVG**).

## Instalación

```bash
pip install -e .
```

Con soporte para PDF:

```bash
pip install -e .[pdf]
```

## Uso rápido

```python
from starsvg import StarSVGCanvas

canvas = StarSVGCanvas(width=1200, height=800, background="white")
canvas.add_svg_file("logo.svg", x=50, y=40, width=200, height=200)
canvas.add_svg_file("icon.svg", x=400, y=200, width=300, height=300)

canvas.save_svg("composicion.svg")
canvas.save_pdf("composicion.pdf")
```

## API

- `StarSVGCanvas(width, height, background="transparent")`
- `add_svg_file(svg_path, x=0, y=0, width=100, height=100)`
- `add_svg_content(svg_content, x=0, y=0, width=100, height=100)`
- `render_svg() -> str`
- `save_svg(output_path)`
- `save_pdf(output_path)`

## Notas

- StarSVG compone SVG de forma **inline** (inyecta nodos SVG al resultado final), en lugar de usar `<image href="data:...">`, para maximizar compatibilidad de render en SVG y PDF.
- La exportación a PDF requiere `svglib` y `reportlab` (`pip install starsvg[pdf]`).
- `save_pdf` lanzará un `RuntimeError` si esas dependencias no están instaladas.
