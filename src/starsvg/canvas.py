from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import List, Optional, Tuple, Union
from xml.etree import ElementTree as ET

PathLike = Union[str, Path]
SVG_NS = "http://www.w3.org/2000/svg"


@dataclass
class SVGPlacement:
    """Represents an SVG resource to place inside a canvas."""

    content: str
    x: float = 0
    y: float = 0
    width: float = 100
    height: float = 100


class StarSVGCanvas:
    """Compose multiple SVGs in a single SVG output and export to PDF."""

    def __init__(self, width: float, height: float, background: str = "transparent") -> None:
        self.width = width
        self.height = height
        self.background = background
        self._items: List[SVGPlacement] = []

    def add_svg_file(
        self,
        svg_path: PathLike,
        x: float = 0,
        y: float = 0,
        width: float = 100,
        height: float = 100,
    ) -> None:
        """Add an SVG from a file path into the canvas."""
        path = Path(svg_path)
        content = path.read_text(encoding="utf-8")
        self.add_svg_content(content, x=x, y=y, width=width, height=height)

    def add_svg_content(
        self,
        svg_content: str,
        x: float = 0,
        y: float = 0,
        width: float = 100,
        height: float = 100,
    ) -> None:
        """Add raw SVG content into the canvas."""
        self._items.append(SVGPlacement(content=svg_content, x=x, y=y, width=width, height=height))

    @staticmethod
    def _parse_length(value: Optional[str]) -> Optional[float]:
        if not value:
            return None
        value = value.strip()
        filtered = "".join(char for char in value if char.isdigit() or char in ".-+")
        try:
            return float(filtered) if filtered else None
        except ValueError:
            return None

    @classmethod
    def _extract_source_size(cls, svg_root: ET.Element) -> Tuple[float, float, float, float]:
        view_box = svg_root.attrib.get("viewBox")
        if view_box:
            parts = view_box.replace(",", " ").split()
            if len(parts) == 4:
                min_x, min_y, vb_width, vb_height = [float(v) for v in parts]
                if vb_width > 0 and vb_height > 0:
                    return min_x, min_y, vb_width, vb_height

        src_width = cls._parse_length(svg_root.attrib.get("width")) or 100.0
        src_height = cls._parse_length(svg_root.attrib.get("height")) or 100.0
        return 0.0, 0.0, src_width, src_height

    @classmethod
    def _build_placement_group(cls, item: SVGPlacement) -> ET.Element:
        try:
            src_root = ET.fromstring(item.content)
        except ET.ParseError as exc:
            raise ValueError("Invalid SVG content provided to StarSVGCanvas") from exc

        min_x, min_y, src_width, src_height = cls._extract_source_size(src_root)
        scale_x = item.width / src_width if src_width else 1.0
        scale_y = item.height / src_height if src_height else 1.0

        group = ET.Element("g")
        group.set("transform", f"translate({item.x} {item.y}) scale({scale_x} {scale_y}) translate({-min_x} {-min_y})")

        for child in list(src_root):
            group.append(child)

        return group

    def render_svg(self) -> str:
        """Render the composed SVG string."""
        ET.register_namespace("", SVG_NS)
        root = ET.Element(
            f"{{{SVG_NS}}}svg",
            {
                "width": str(self.width),
                "height": str(self.height),
                "viewBox": f"0 0 {self.width} {self.height}",
            },
        )

        ET.SubElement(
            root,
            f"{{{SVG_NS}}}rect",
            {"width": "100%", "height": "100%", "fill": self.background},
        )

        for item in self._items:
            root.append(self._build_placement_group(item))

        return ET.tostring(root, encoding="unicode")

    def save_svg(self, output_path: PathLike) -> Path:
        """Save the composed SVG to a file."""
        destination = Path(output_path)
        destination.write_text(self.render_svg(), encoding="utf-8")
        return destination

    def save_pdf(self, output_path: PathLike) -> Path:
        """Export the composed SVG to PDF using svglib + reportlab."""
        try:
            from reportlab.graphics import renderPDF
            from svglib.svglib import svg2rlg
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError(
                "PDF export requires svglib and reportlab. Install with: pip install starsvg[pdf]"
            ) from exc

        destination = Path(output_path)
        composed_svg = self.render_svg()

        with NamedTemporaryFile("w", suffix=".svg", encoding="utf-8", delete=True) as temp_svg:
            temp_svg.write(composed_svg)
            temp_svg.flush()
            drawing = svg2rlg(temp_svg.name)

        if drawing is None:
            raise RuntimeError("Could not parse composed SVG into a PDF drawing.")

        renderPDF.drawToFile(drawing, str(destination))
        return destination
