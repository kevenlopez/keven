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
    monkeypatch.setitem(sys.modules, "reportlab.graphics", types.SimpleNamespace())
    monkeypatch.setitem(sys.modules, "reportlab.graphics.renderPDF", fake_render_pdf_module)

    canvas = StarSVGCanvas(width=100, height=100)
    canvas.add_svg_content('<svg xmlns="http://www.w3.org/2000/svg"><circle cx="4" cy="4" r="2"/></svg>')

    out = canvas.save_pdf(tmp_path / "result.pdf")

    assert out.exists()
    assert called["output_path"].endswith("result.pdf")
    assert called["svg_path"].endswith(".svg")
    assert called["drawing"] is not None


def test_save_png_and_resolutions(tmp_path: Path, monkeypatch) -> None:
    calls = []

    def fake_svg2rlg(_svg_path: str):
        return object()

    def fake_draw_to_file(_drawing, output_path: str, **kwargs) -> None:
        calls.append((output_path, kwargs.get("dpi")))
        Path(output_path).write_bytes(b"PNG")

    fake_svglib_module = types.SimpleNamespace(svg2rlg=fake_svg2rlg)
    fake_render_pm_module = types.SimpleNamespace(drawToFile=fake_draw_to_file)

    monkeypatch.setitem(sys.modules, "svglib", types.SimpleNamespace())
    monkeypatch.setitem(sys.modules, "svglib.svglib", fake_svglib_module)
    monkeypatch.setitem(sys.modules, "reportlab", types.SimpleNamespace())
    monkeypatch.setitem(sys.modules, "reportlab.graphics", types.SimpleNamespace())
    monkeypatch.setitem(sys.modules, "reportlab.graphics.renderPM", fake_render_pm_module)

    canvas = StarSVGCanvas(width=200, height=200)
    canvas.add_svg_content('<svg xmlns="http://www.w3.org/2000/svg"><circle cx="50" cy="50" r="10"/></svg>')

    png = canvas.save_png(tmp_path / "single.png", scale=2)
    generated = canvas.save_png_resolutions(tmp_path / "multi", "mapa", scales=[1, 3])

    assert png.exists()
    assert len(generated) == 2
    assert generated[0].name == "mapa@1x.png"
    assert generated[1].name == "mapa@3x.png"
    assert calls[0][1] == 144
    assert calls[1][1] == 72
    assert calls[2][1] == 216


def test_save_png_raises_without_png_dependencies(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setitem(sys.modules, "svglib", None)
    monkeypatch.setitem(sys.modules, "reportlab", None)

    canvas = StarSVGCanvas(width=100, height=100)

    try:
        canvas.save_png(tmp_path / "result.png")
        assert False, "Expected RuntimeError"
    except RuntimeError as exc:
        assert "PNG export requires" in str(exc)


def test_save_pdf_raises_without_pdf_dependencies(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setitem(sys.modules, "svglib", None)
    monkeypatch.setitem(sys.modules, "reportlab", None)

    canvas = StarSVGCanvas(width=100, height=100)

    try:
        canvas.save_pdf(tmp_path / "result.pdf")
        assert False, "Expected RuntimeError"
    except RuntimeError as exc:
        assert "PDF export requires" in str(exc)


def test_render_svg_invalid_input_raises_value_error() -> None:
    canvas = StarSVGCanvas(width=100, height=100)
    canvas.add_svg_content("not-valid-svg")

    try:
        canvas.render_svg()
        assert False, "Expected ValueError"
    except ValueError as exc:
        assert "Invalid SVG content" in str(exc)
