"""Level 5: Regression of core tools, existing films integrity and adversarial cases."""

import json
import subprocess
from pathlib import Path

import pytest
from core.qa.pre_render import validate_pre_render
from core.scorm.scorm_packager import build_scorm_package
from tests.conftest import REPO_ROOT
from tests.e2e.helpers import assert_valid_educai_mp4, build_synthetic_pptx, get_python_exe


def test_core_brand_theme_cli_regression(tmp_path: Path):
    logo = REPO_ROOT / "sello educai.jpg"
    out_json = tmp_path / "theme_cli.json"
    res = subprocess.run(
        [get_python_exe(), "-m", "core.brand_theme", str(logo), "-o", str(out_json)],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    assert out_json.is_file()
    data = json.loads(out_json.read_text(encoding="utf-8"))
    assert "palette" in data


def test_core_doc_parser_cli_regression(tmp_path: Path):
    deck = tmp_path / "deck.pptx"
    build_synthetic_pptx(deck)
    out_json = tmp_path / "doc_parsed.json"

    res = subprocess.run(
        [get_python_exe(), "-m", "core.parsers.doc_parser", str(deck), "-o", str(out_json)],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    assert out_json.is_file()
    data = json.loads(out_json.read_text(encoding="utf-8"))
    assert data["source_type"] == "pptx"


def test_core_scorm_packager_cli_legacy_args(tmp_path: Path):
    cps_file = tmp_path / "cps.json"
    cps_file.write_text(json.dumps([{"timestamp": 5.0, "question": "Q?", "options": ["A"], "correct_index": 0}]))
    out_zip = tmp_path / "scorm_legacy.zip"

    res = subprocess.run(
        [
            get_python_exe(),
            "-m", "core.scorm.scorm_packager",
            "--title", "Legacy SCORM",
            "--video-url", "https://cdn.example.com/v.mp4",
            "--checkpoints-json", str(cps_file),
            "--output", str(out_zip),
        ],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    assert out_zip.is_file()


def test_existing_films_mp4_integrity():
    films = [
        REPO_ROOT / "films" / "cuando-el-trabajo-deja-de-ser-necesario" / "Cuando_El_Trabajo_Deja_De_Ser_Necesario_EducAI_Final.mp4",
        REPO_ROOT / "films" / "estructura-tripartita" / "Estructura_Tripartita_EducAI_Final.mp4",
        REPO_ROOT / "films" / "protocolo-relevamiento" / "Protocolo_Relevamiento_EducAI_Final.mp4",
    ]
    for film in films:
        assert film.is_file(), f"Film missing: {film}"
        # Verify valid streams and non-zero duration
        assert_valid_educai_mp4(film, min_duration=10.0, expected_fps=None)


def test_adversarial_checkpoint_sync_violation(tmp_path: Path):
    # Scene ends at 10.0s, but checkpoint placed at 6.0s (in the middle of narration)
    timeline = {
        "total_duration": 12.0,
        "scenes": [
            {"scene_id": "scene_01", "start": 0.0, "duration": 10.0, "end": 10.0, "title": "S1"}
        ]
    }
    tl_path = tmp_path / "audio_timeline.json"
    tl_path.write_text(json.dumps(timeline), encoding="utf-8")

    bad_cps = [{"scene_id": "scene_01", "timestamp": 6.0, "question": "Cutting speech?"}]
    cp_path = tmp_path / "scorm_checkpoints.json"
    cp_path.write_text(json.dumps(bad_cps), encoding="utf-8")

    # validate_pre_render should detect this violation
    qa = validate_pre_render(
        tmp_path,
        render_mode="hyperframes",
        audio_file="dummy.m4a",  # will trigger missing audio warning, but we check checkpoint issue
        timeline_file="audio_timeline.json",
        checkpoints_file="scorm_checkpoints.json",
    )
    assert any("cuts scene 'scene_01' speech" in isue for isue in qa["issues"])

    # scorm_packager with strict_sync=True should raise ValueError
    with pytest.raises(ValueError, match="violates strict_sync"):
        build_scorm_package(
            "Test",
            "v.mp4",
            bad_cps,
            str(tmp_path / "out.zip"),
            audio_timeline_path=str(tl_path),
            strict_sync=True,
        )
