from pathlib import Path
import sys
import types

from starsvg import StarSVGCanvas


def test_render_svg_embeds_multiple_svgs(tmp_path: Path) -> None:
    first_svg = tmp_path / "first.svg"
    second_svg = tmp_path / "second.svg"

    first_svg.write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20"><circle cx="10" cy="10" r="8"/></svg>', encoding="utf-8")
    second_svg.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12"><rect width="12" height="12"/></svg>', encoding="utf-8")

    canvas = StarSVGCanvas(width=800, height=600, background="white")
    canvas.add_svg_file(first_svg, x=10, y=20, width=120, height=140)
    canvas.add_svg_file(second_svg, x=30, y=40, width=220, height=240)

    output = canvas.render_svg()

    assert output.startswith("<svg")
    assert output.endswith("</svg>")
    assert output.count("<g transform=") == 2
    assert "data:image/svg+xml;base64" not in output
    assert 'fill="white"' in output
    assert "circle" in output
    assert "rect" in output


def test_save_svg_creates_output_file(tmp_path: Path) -> None:
    canvas = StarSVGCanvas(width=100, height=100)
    canvas.add_svg_content('<svg xmlns="http://www.w3.org/2000/svg"><rect width="10" height="10"/></svg>')

    out = canvas.save_svg(tmp_path / "result.svg")

    assert out.exists()
    assert out.read_text(encoding="utf-8").startswith("<svg")


def test_save_pdf_uses_svglib_and_reportlab(tmp_path: Path, monkeypatch) -> None:
    called = {}

    def fake_svg2rlg(svg_path: str):
        called["svg_path"] = svg_path
        return object()

    def fake_draw_to_file(drawing, output_path: str) -> None:
        called["drawing"] = drawing
        called["output_path"] = output_path
        Path(output_path).write_bytes(b"%PDF-FAKE")

    fake_svglib_module = types.SimpleNamespace(svg2rlg=fake_svg2rlg)
    fake_render_pdf_module = types.SimpleNamespace(drawToFile=fake_draw_to_file)

    monkeypatch.setitem(sys.modules, "svglib", types.SimpleNamespace())
    monkeypatch.setitem(sys.modules, "svglib.svglib", fake_svglib_module)
    monkeypatch.setitem(sys.modules, "reportlab", types.SimpleNamespace())
    monkeypatch.setitem(sys.modules, "reportlab.graphics", types.SimpleNamespace(renderPDF=fake_render_pdf_module))
    monkeypatch.setitem(sys.modules, "reportlab.graphics.renderPDF", fake_render_pdf_module)

    canvas = StarSVGCanvas(width=100, height=100)
    canvas.add_svg_content('<svg xmlns="http://www.w3.org/2000/svg"><circle cx="4" cy="4" r="2"/></svg>')

    out = canvas.save_pdf(tmp_path / "result.pdf")

    assert out.exists()
    assert called["output_path"].endswith("result.pdf")
    assert called["svg_path"].endswith(".svg")
    assert called["drawing"] is not None


def test_save_pdf_raises_without_pdf_dependencies(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setitem(sys.modules, "svglib", None)
    monkeypatch.setitem(sys.modules, "reportlab", None)

    original_import = __import__

    def fake_import(name, *args, **kwargs):
        if name.startswith("svglib") or name.startswith("reportlab"):
            raise ImportError("missing")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr("builtins.__import__", fake_import)

    canvas = StarSVGCanvas(width=100, height=100)

    try:
        canvas.save_pdf(tmp_path / "result.pdf")
        assert False, "Expected RuntimeError"
    except RuntimeError as exc:
        assert "requires svglib and reportlab" in str(exc)


def test_render_svg_invalid_input_raises_value_error() -> None:
    canvas = StarSVGCanvas(width=100, height=100)
    canvas.add_svg_content("not-valid-svg")

    try:
        canvas.render_svg()
        assert False, "Expected ValueError"
    except ValueError as exc:
        assert "Invalid SVG content" in str(exc)
