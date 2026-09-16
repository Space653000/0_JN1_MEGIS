"""Run inside FreeCADCmd to generate a fixed-template TechDraw SVG."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import xml.etree.ElementTree as ET

import FreeCAD as App
import Part


ROOT = Path(__file__).resolve().parents[2]
RUNTIME = ROOT / "tools" / "freecad" / "FreeCAD_1.1.3-Windows-x86_64-py311"
INPUT_STEP = ROOT / "artifacts" / "g0-cad" / "reference_case.step"
OUTPUT_DIR = ROOT / "artifacts" / "g0-freecad"
FREECAD_TEMPLATE = RUNTIME / "data" / "Mod" / "TechDraw" / "Templates" / "ISO" / "A4_Landscape_TD.svg"
FALLBACK_TEMPLATE = Path(__file__).resolve().parent / "templates" / "a4_landscape_megis.svg"
NOTICE = "DRAFT - ENGINEERING REVIEW REQUIRED"


def file_evidence(path: Path) -> dict[str, object]:
    content = path.read_bytes()
    return {"path": path.name, "bytes": len(content), "sha256": sha256(content).hexdigest()}


def render_fallback_svg(view: object) -> tuple[str, int]:
    """Render FreeCAD TechDraw visible edges into the versioned A4 SVG template."""

    geometry: list[str] = []
    edges = view.getVisibleEdges()
    for edge in edges:
        points = edge.discretize(Deflection=0.1)
        coordinates = " ".join(f"{145 + point.x:.4f},{100 - point.y:.4f}" for point in points)
        geometry.append(f'    <polyline points="{coordinates}"/>')
    if not geometry:
        raise RuntimeError("TechDraw produced no visible edges")
    template = FALLBACK_TEMPLATE.read_text(encoding="utf-8")
    return template.replace("{{GEOMETRY}}", "\n".join(geometry)), len(edges)


def main() -> None:
    for required in (INPUT_STEP, FREECAD_TEMPLATE, FALLBACK_TEMPLATE):
        if not required.is_file():
            raise FileNotFoundError(required)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    document = App.newDocument("MEGIS_G0_TechDraw")
    source = document.addObject("Part::Feature", "ReferenceCase")
    source.Label = "MEGIS G0 Reference Case"
    source.Shape = Part.read(str(INPUT_STEP))

    page = document.addObject("TechDraw::DrawPage", "Page")
    template = document.addObject("TechDraw::DrawSVGTemplate", "Template")
    template.Template = str(FREECAD_TEMPLATE)
    page.Template = template

    editable = dict(template.EditableTexts)
    replacements = {
        "Title": "MEGIS G0 REFERENCE CASE",
        "Subtitle": NOTICE,
        "DrawingTitle1": "MEGIS G0 REFERENCE CASE",
        "DrawingTitle2": NOTICE,
        "Comment1": "FEASIBILITY SPIKE",
        "Comment2": "NOT FOR MANUFACTURING",
        "FC-SH_FORMAT_NAME": "A4 LANDSCAPE",
    }
    for key, value in replacements.items():
        if key in editable:
            editable[key] = value
    template.EditableTexts = editable

    view = document.addObject("TechDraw::DrawViewPart", "TopView")
    view.Source = [source]
    view.Direction = (0.0, 0.0, 1.0)
    view.X = 145.0
    view.Y = 120.0
    view.ScaleType = "Custom"
    view.Scale = 1.0
    page.addView(view)

    annotation = document.addObject("TechDraw::DrawViewAnnotation", "ReviewNotice")
    annotation.Text = [NOTICE, "FEASIBILITY SPIKE - NOT FOR MANUFACTURING"]
    annotation.X = 145.0
    annotation.Y = 35.0
    annotation.Scale = 1.0
    page.addView(annotation)

    document.recompute()
    if "Up-to-date" not in view.State:
        raise RuntimeError(f"TechDraw view state is {view.State}")

    fcstd_path = OUTPUT_DIR / "reference_case_techdraw.FCStd"
    svg_path = OUTPUT_DIR / "reference_case_techdraw_fallback.svg"
    document.saveAs(str(fcstd_path))
    svg_content, visible_edge_count = render_fallback_svg(view)
    svg_path.write_text(svg_content, encoding="utf-8")

    root = ET.fromstring(svg_content)
    polylines = root.findall(".//{http://www.w3.org/2000/svg}polyline")
    texts = [element.text or "" for element in root.findall(".//{http://www.w3.org/2000/svg}text")]
    if len(polylines) != visible_edge_count:
        raise RuntimeError("Fallback SVG did not preserve every TechDraw visible edge")
    if not any(NOTICE in text for text in texts):
        raise RuntimeError("Generated TechDraw SVG is missing the review notice")

    evidence = {
        "schemaVersion": "1.0.0",
        "workItem": "G0-DRW-001",
        "decision": "fallback",
        "freeCadVersion": ".".join(str(value) for value in App.Version()[:3]),
        "executionMode": "FreeCADCmd headless",
        "freeCadTemplate": "ISO/A4_Landscape_TD.svg",
        "fallbackTemplate": "spikes/g0_freecad/templates/a4_landscape_megis.svg",
        "source": "artifacts/g0-cad/reference_case.step",
        "sourceEvidence": file_evidence(INPUT_STEP),
        "runtimeEvidence": {
            "freecadcmd": file_evidence(RUNTIME / "bin" / "freecadcmd.exe"),
            "freeCadTemplate": file_evidence(FREECAD_TEMPLATE),
            "fallbackTemplate": file_evidence(FALLBACK_TEMPLATE),
        },
        "techDraw": {
            "viewState": list(view.State),
            "visibleEdges": visible_edge_count,
            "drawPageSvgApiAvailable": hasattr(page, "getPageSVG"),
            "techDrawGuiAvailableInConsole": False,
        },
        "svg": {
            "validXml": True,
            "polylineElements": len(polylines),
            "reviewNoticePresent": True,
        },
        "artifacts": {
            "fcstd": file_evidence(fcstd_path),
            "svg": file_evidence(svg_path),
        },
        "boundary": {
            "headlessTechDrawProjection": "pass",
            "headlessTechDrawNativeSvg": "unavailable",
            "fixedTemplateSvgFallback": "pass",
            "headlessPdf": "fallback",
            "pdfFallback": "Use the verified SVG as the fixed-template draft source; PDF conversion and manual QA remain required in G5-DRW-001.",
            "engineeringReviewRequired": True,
            "manufacturingRelease": False,
        },
    }
    evidence_path = OUTPUT_DIR / "verification.json"
    evidence_path.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(evidence, ensure_ascii=False))
    App.closeDocument(document.Name)


if __name__ == "__main__":
    main()
