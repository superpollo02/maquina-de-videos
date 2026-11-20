"""Level 3 & 4: E2E Pipeline and Live Chrome SCORM Verification."""

import json
from pathlib import Path

import pytest
from core.orchestrator.pipeline import EducAIPipeline
from tests.conftest import REPO_ROOT
from tests.e2e.helpers import (
    assert_valid_educai_mp4,
    build_synthetic_docx,
    inspect_scorm_zip,
    run_scorm_in_chrome,
)


def test_pipeline_e2e_and_scorm_browser(tmp_path: Path):
    # 1. Prepare synthetic document
    doc_path = tmp_path / "clase_demo.docx"
    build_synthetic_docx(
        doc_path,
        [
            {
                "heading": "Introducción",
                "paragraphs": ["Bienvenidos a la clase sobre IA educativa y pedagogía."],
            },
            {
                "heading": "Evaluación Formativa",
                "paragraphs": ["Las evaluaciones SCORM deben verificar la comprensión sin interrumpir la voz."],
            },
        ],
    )

    logo_path = REPO_ROOT / "sello educai.jpg"

    # 2. Run Pipeline
    pipeline = EducAIPipeline(tmp_path)
    result = pipeline.run(
        doc_path=doc_path,
        theme_image=logo_path,
        render_mode="hyperframes",
        scorm_title="Clase Demostrativa",
        dual_scorm=True,
    )

    assert result["success"] is True

    # 3. Verify final MP4
    final_video = Path(result["final_video"])
    assert final_video.is_file()
    assert_valid_educai_mp4(final_video, min_duration=2.0)

    # 4. Verify SCORM packages
    scorm_full = Path(result["scorm_full"])
    scorm_zero = Path(result["scorm_zero"])
    assert scorm_full.is_file()
    assert scorm_zero.is_file()

    full_info = inspect_scorm_zip(scorm_full)
    assert 'controlsList="nofullscreen"' in full_info["html"]
    assert "btn-fullscreen" in full_info["html"]

    # 5. Level 4: Live Chrome SCORM execution
    chrome_report = run_scorm_in_chrome(
        scorm_full,
        require_agents_md_invariants=True,
        verify_media_loaded=False,
    )
    assert chrome_report["scorm_calls"] != []
    call_names = [c[0] for c in chrome_report["scorm_calls"]]
    assert "LMSInitialize" in call_names
    assert "LMSSetValue" in call_names
    assert chrome_report["media_meta"]["controlsList"] == "nofullscreen"
