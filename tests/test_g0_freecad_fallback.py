from hashlib import sha256
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_DIR = ROOT / "artifacts" / "g0-freecad"


def digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def test_freecad_fallback_artifacts_match_the_recorded_decision() -> None:
    evidence = json.loads((ARTIFACT_DIR / "verification.json").read_text(encoding="utf-8"))
    svg_path = ARTIFACT_DIR / evidence["artifacts"]["svg"]["path"]
    fcstd_path = ARTIFACT_DIR / evidence["artifacts"]["fcstd"]["path"]

    assert evidence["decision"] == "fallback"
    assert evidence["freeCadVersion"] == "1.1.3"
    assert evidence["techDraw"]["viewState"] == ["Up-to-date"]
    assert evidence["techDraw"]["visibleEdges"] == 12
    assert evidence["techDraw"]["drawPageSvgApiAvailable"] is False
    assert evidence["boundary"]["headlessTechDrawProjection"] == "pass"
    assert evidence["boundary"]["fixedTemplateSvgFallback"] == "pass"
    assert evidence["boundary"]["headlessPdf"] == "fallback"
    assert evidence["boundary"]["engineeringReviewRequired"] is True
    assert evidence["boundary"]["manufacturingRelease"] is False

    assert digest(svg_path) == evidence["artifacts"]["svg"]["sha256"]
    assert digest(fcstd_path) == evidence["artifacts"]["fcstd"]["sha256"]
    svg = ET.parse(svg_path).getroot()
    namespace = {"svg": "http://www.w3.org/2000/svg"}
    assert len(svg.findall(".//svg:polyline", namespace)) == 12
    text = " ".join(element.text or "" for element in svg.findall(".//svg:text", namespace))
    assert "DRAFT - ENGINEERING REVIEW REQUIRED" in text
    assert "NOT FOR MANUFACTURING" in text

    with zipfile.ZipFile(fcstd_path) as archive:
        document_xml = archive.read("Document.xml").decode("utf-8")
    assert "TechDraw::DrawPage" in document_xml
    assert "TechDraw::DrawViewPart" in document_xml
    assert "TechDraw::DrawSVGTemplate" in document_xml
