"""Level 1: Unit & Contract Tests for EducAI core and OpenMontage libraries."""

import json
from pathlib import Path

import pytest
from core.brand_theme import extract_brand_theme
from core.parsers.doc_parser import parse_document
from core.scorm.scorm_packager import build_scorm_package
from tests.conftest import REPO_ROOT, ensure_openmontage_on_path
from tests.e2e.helpers import (
    build_synthetic_docx,
    build_synthetic_pdf,
    build_synthetic_pptx,
    inspect_scorm_zip,
)


def test_doc_parser_pptx(tmp_path: Path):
    pptx_path = tmp_path / "test_deck.pptx"
    build_synthetic_pptx(pptx_path)

    res = parse_document(str(pptx_path))
    assert res["source_type"] == "pptx"
    assert res["total_items"] >= 2
    assert len(res["sections"]) >= 2
    sec1 = res["sections"][0]
    assert "title" in sec1
    assert "bullet_points" in sec1 or "paragraphs" in sec1


def test_doc_parser_docx(tmp_path: Path):
    docx_path = tmp_path / "test_doc.docx"
    build_synthetic_docx(docx_path)

    res = parse_document(str(docx_path))
    assert res["source_type"] == "docx"
    assert res["total_items"] >= 2
    assert len(res["sections"]) >= 2
    assert "Fundamentos" in res["sections"][0]["title"]


def test_doc_parser_pdf(tmp_path: Path):
    pdf_path = tmp_path / "test_doc.pdf"
    build_synthetic_pdf(pdf_path)

    res = parse_document(str(pdf_path))
    assert res["source_type"] == "pdf"
    assert res["total_items"] >= 2
    assert len(res["sections"]) >= 2
    assert "Pedagogía Digital" in res["sections"][0]["title"]


def test_brand_theme_extraction(tmp_path: Path):
    logo_path = REPO_ROOT / "sello educai.jpg"
    assert logo_path.is_file(), "sello educai.jpg missing in repo root"

    out_json = tmp_path / "theme.json"
    theme = extract_brand_theme(str(logo_path), output_json=str(out_json))

    assert "palette" in theme
    assert "typography" in theme
    palette = theme["palette"]
    for key in ("primary", "secondary", "alert", "dark_neutral", "background"):
        assert key in palette, f"Missing palette key {key}"
        assert palette[key].startswith("#")

    typo = theme["typography"]
    for key in ("font_family", "subtitles_bg", "subtitles_text"):
        assert key in typo, f"Missing typography key {key}"


def test_scorm_packager_unit_and_dual_zip(tmp_path: Path):
    checkpoints = [
        {
            "timestamp": 10.5,
            "section_title": "Módulo 1",
            "question": "¿Pregunta de prueba?",
            "options": ["Opción A", "Opción B"],
            "correct_index": 0,
            "feedback_ok": "Correcto",
            "feedback_error": "Incorrecto",
        }
    ]

    out_full = tmp_path / "test_SCORM_Completo.zip"
    fake_video = tmp_path / "test_video.mp4"
    fake_video.write_bytes(b"\x00" * 1024)

    # Build dual package
    res_full = build_scorm_package(
        title="Curso de Prueba",
        video_url="https://cdn.educai.com/test_video.mp4",
        checkpoints=checkpoints,
        output_zip=str(out_full),
        include_video_file=str(fake_video),
        also_build_zero_weight=True,
    )
    assert Path(res_full).is_file()

    # Inspect full package
    full_info = inspect_scorm_zip(out_full)
    assert 'controlsList="nofullscreen"' in full_info["html"]
    assert "btn-fullscreen" in full_info["html"]
    assert "checkpoint-label" in full_info["html"]
    assert "test_video.mp4" in full_info["names"]
    assert "test_video.mp4" in full_info["manifest_files"]

    # Inspect zero-weight package
    out_zero = tmp_path / "test_SCORM.zip"
    assert out_zero.is_file()
    zero_info = inspect_scorm_zip(out_zero)
    assert 'controlsList="nofullscreen"' in zero_info["html"]
    assert "test_video.mp4" not in zero_info["names"]
    assert zero_info["size_bytes"] < 50_000


def test_openmontage_lib_contracts():
    om_root = ensure_openmontage_on_path()
    assert (om_root / "lib").is_dir()

    from lib.hyperframes_style_bridge import style_bridge

    playbook = {
        "visual_language": {
            "color_palette": {
                "primary": "#0284c7",
                "accent": "#ea580c",
                "surface": "#0f172a",
                "background": "#ffffff",
                "text": "#0f172a",
            },
            "typography": {"heading": "Inter", "body": "Inter"},
        }
    }
    css_vars, design_md = style_bridge(playbook)
    assert "--color-primary" in css_vars
    assert css_vars["--color-primary"] == "#0284c7"
    assert "# DESIGN" in design_md
