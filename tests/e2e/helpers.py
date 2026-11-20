"""Opaque-box E2E helpers: decorators, synthetic media/doc builders, ffprobe, SCORM & Chrome verifiers."""

from __future__ import annotations

import importlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.parse
import xml.etree.ElementTree as ET
import zipfile
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from typing import Any

from tests.conftest import CHROME_EXECUTABLE, REPO_ROOT, ensure_openmontage_on_path, find_openmontage_root


def baseline(fn):
    """Mark a test method as runnable against the current baseline repository."""
    fn._e2e_baseline = True
    return fn


def is_baseline_test(test_case) -> bool:
    method_name = getattr(test_case, "_testMethodName", "")
    method = getattr(test_case, method_name, None)
    return bool(getattr(method, "_e2e_baseline", False))


def get_python_exe() -> str:
    return sys.executable


def clean_cp1252_env(extra: dict[str, str] | None = None) -> dict[str, str]:
    """Return a subprocess environment simulating Windows default cp1252 console (no PYTHONUTF8)."""
    env = os.environ.copy()
    env.pop("PYTHONUTF8", None)
    env["PYTHONIOENCODING"] = "cp1252"
    if extra:
        env.update(extra)
    return env


def run_cmd(
    cmd: list[str],
    cwd: Path | str | None = None,
    env: dict[str, str] | None = None,
    timeout: int = 120,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=str(cwd or REPO_ROOT),
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )


# ---------------------------------------------------------------------------
# Synthetic Fixture Builders (always write into caller's temp Path)
# ---------------------------------------------------------------------------

def build_synthetic_pptx(
    path: Path,
    slides: list[dict[str, Any]] | None = None,
) -> Path:
    from pptx import Presentation

    prs = Presentation()
    layout = prs.slide_layouts[1]
    blank_layout = prs.slide_layouts[6]
    if slides is None:
        slides = [
            {
                "title": "Introducción a la IA Educativa",
                "bullets": ["Diseño instruccional modular", "Evaluación formativa continua"],
                "notes": "Bienvenidos a esta clase sobre diseño educativo con inteligencia artificial.",
            },
            {
                "title": "Sincronía Pedagógica",
                "bullets": ["Pausas al cierre de escena", "Retroalimentación inmediata"],
                "notes": "Cada pregunta aparece exactamente al terminar la locución docente.",
            },
        ]

    for item in slides:
        if item.get("empty"):
            slide = prs.slides.add_slide(blank_layout)
        else:
            slide = prs.slides.add_slide(layout)
            if item.get("title") is not None and slide.shapes.title:
                slide.shapes.title.text = item["title"]
            body_shapes = [s for s in slide.shapes if s.has_text_frame and s != slide.shapes.title]
            if body_shapes and item.get("bullets"):
                tf = body_shapes[0].text_frame
                tf.clear()
                for idx, bullet in enumerate(item["bullets"]):
                    p = tf.paragraphs[0] if idx == 0 else tf.add_paragraph()
                    p.text = bullet
        if item.get("notes"):
            slide.notes_slide.notes_text_frame.text = item["notes"]

    path.parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(path))
    return path


def build_synthetic_docx(
    path: Path,
    sections: list[dict[str, Any]] | None = None,
) -> Path:
    from docx import Document

    doc = Document()
    if sections is None:
        sections = [
            {
                "heading": "Unidad 1: Fundamentos",
                "style": "Heading 1",
                "paragraphs": [
                    "La educación digital requiere claridad narrativa y ritmo visual.",
                    "Integrar recursos multimedia mejora la retención conceptual.",
                ],
            },
            {
                "heading": "Unidad 2: Evaluación SCORM",
                "style": "Heading 2",
                "paragraphs": [
                    "Las preguntas formativas deben ubicarse al cierre de cada explicación.",
                ],
            },
        ]

    for sec in sections:
        if sec.get("heading"):
            p = doc.add_paragraph(sec["heading"])
            style_name = sec.get("style", "Heading 1")
            if style_name in [s.name for s in doc.styles]:
                p.style = doc.styles[style_name]
            else:
                doc.add_heading(sec["heading"], level=1)
        for para in sec.get("paragraphs", []):
            doc.add_paragraph(para)

    path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(path))
    return path


def build_synthetic_pdf(path: Path, pages: list[list[str]] | None = None) -> Path:
    import pymupdf

    if pages is None:
        pages = [
            [
                "Módulo 1: Pedagogía Digital",
                "La enseñanza multimedia combina voz, imagen y texto.",
                "Contenido en español con acentos: áéíóúüñ¿¡.",
            ],
            [
                "Módulo 2: Evaluación Continua",
                "Validación automática en Moodle 4.5 con SCORM 1.2.",
            ],
        ]

    doc = pymupdf.open()
    for page_lines in pages:
        page = doc.new_page(width=595, height=842)
        y = 72
        for line in page_lines:
            if line:
                page.insert_text((72, y), line, fontsize=12)
            y += 22
    path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(path))
    doc.close()
    return path


def build_synthetic_image(
    path: Path,
    size: tuple[int, int] = (240, 160),
    blocks: list[tuple[tuple[int, int, int, int], tuple[int, int, int] | tuple[int, int, int, int]]] | None = None,
    mode: str = "RGB",
    bg: tuple[int, ...] = (255, 255, 255),
) -> Path:
    from PIL import Image, ImageDraw

    img = Image.new(mode, size, bg)
    draw = ImageDraw.Draw(img)
    if blocks is None:
        w, h = size
        blocks = [
            ((0, 0, w // 2, h // 2), (10, 120, 220)),     # primary blue
            ((w // 2, 0, w, h // 2), (230, 55, 20)),     # warm coral/red alert
            ((0, h // 2, w // 2, h), (15, 23, 42)),      # dark neutral navy
            ((w // 2, h // 2, w, h), (30, 160, 110)),    # secondary teal
        ]
    for box, color in blocks:
        draw.rectangle(box, fill=color)
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(str(path))
    return path


def build_synthetic_wav(
    path: Path,
    duration: float = 1.5,
    freq: int = 440,
    sample_rate: int = 44100,
    channels: int = 1,
) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg", "-y", "-v", "error",
        "-f", "lavfi", "-i", f"sine=frequency={freq}:duration={duration}:sample_rate={sample_rate}",
        "-ac", str(channels),
        str(path),
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if res.returncode != 0:
        raise RuntimeError(f"ffmpeg wav generation failed: {res.stderr}")
    return path


def build_synthetic_mp4(
    path: Path,
    duration: float = 2.0,
    width: int = 1920,
    height: int = 1080,
    fps: int = 24,
    with_audio: bool = True,
    trailing_silence: float = 0.0,
) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    if with_audio:
        audio_dur = max(0.2, duration - trailing_silence)
        if trailing_silence > 0:
            cmd = [
                "ffmpeg", "-y", "-v", "error",
                "-f", "lavfi", "-i", f"testsrc=size={width}x{height}:rate={fps}:duration={duration}",
                "-f", "lavfi", "-i", f"sine=frequency=440:duration={audio_dur}:sample_rate=44100",
                "-f", "lavfi", "-i", f"anullsrc=r=44100:cl=mono:d={trailing_silence}",
                "-filter_complex", "[1:a][2:a]concat=n=2:v=0:a=1[aout]",
                "-map", "0:v", "-map", "[aout]",
                "-c:v", "libx264", "-pix_fmt", "yuv420p",
                "-c:a", "aac", "-ar", "44100", "-ac", "1",
                "-shortest", str(path),
            ]
        else:
            cmd = [
                "ffmpeg", "-y", "-v", "error",
                "-f", "lavfi", "-i", f"testsrc=size={width}x{height}:rate={fps}:duration={duration}",
                "-f", "lavfi", "-i", f"sine=frequency=440:duration={duration}:sample_rate=44100",
                "-c:v", "libx264", "-pix_fmt", "yuv420p",
                "-c:a", "aac", "-ar", "44100", "-ac", "1",
                "-shortest", str(path),
            ]
    else:
        cmd = [
            "ffmpeg", "-y", "-v", "error",
            "-f", "lavfi", "-i", f"testsrc=size={width}x{height}:rate={fps}:duration={duration}",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-an",
            str(path),
        ]
    res = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if res.returncode != 0:
        raise RuntimeError(f"ffmpeg mp4 generation failed: {res.stderr}")
    return path


def ffprobe_json(media_path: Path) -> dict[str, Any]:
    cmd = [
        "ffprobe", "-v", "error",
        "-show_format", "-show_streams",
        "-of", "json", str(media_path),
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if res.returncode != 0:
        raise AssertionError(f"ffprobe failed on {media_path}: {res.stderr}")
    return json.loads(res.stdout)


def assert_valid_educai_mp4(
    mp4_path: Path,
    expected_width: int = 1920,
    expected_height: int = 1080,
    expected_fps: str | None = "24/1",
    min_duration: float = 0.5,
    expected_duration: float | None = None,
    duration_tolerance: float = 0.6,
) -> dict[str, Any]:
    assert mp4_path.is_file(), f"MP4 not found: {mp4_path}"
    assert mp4_path.stat().st_size > 0, f"MP4 is empty: {mp4_path}"
    info = ffprobe_json(mp4_path)
    streams = info.get("streams", [])
    v_streams = [s for s in streams if s.get("codec_type") == "video"]
    a_streams = [s for s in streams if s.get("codec_type") == "audio"]
    assert len(v_streams) == 1, f"Expected 1 video stream in {mp4_path}, got {len(v_streams)}"
    assert len(a_streams) == 1, f"Expected 1 audio stream in {mp4_path}, got {len(a_streams)}"
    vs = v_streams[0]
    as_ = a_streams[0]
    assert vs.get("codec_name") == "h264", f"Expected h264, got {vs.get('codec_name')}"
    assert vs.get("pix_fmt") == "yuv420p", f"Expected yuv420p, got {vs.get('pix_fmt')}"
    assert vs.get("width") == expected_width, f"Expected width {expected_width}, got {vs.get('width')}"
    assert vs.get("height") == expected_height, f"Expected height {expected_height}, got {vs.get('height')}"
    if expected_fps is not None:
        assert vs.get("r_frame_rate") == expected_fps, f"Expected fps {expected_fps}, got {vs.get('r_frame_rate')}"
    assert as_.get("codec_name") == "aac", f"Expected aac, got {as_.get('codec_name')}"
    dur = float(info["format"]["duration"])
    assert dur >= min_duration, f"Duration {dur}s < {min_duration}s"
    if expected_duration is not None:
        assert abs(dur - expected_duration) <= duration_tolerance, (
            f"Duration {dur:.2f}s differs from expected {expected_duration:.2f}s by > {duration_tolerance}s"
        )
    return info


# ---------------------------------------------------------------------------
# OpenMontage ToolRegistry / Orchestrator / QA Discovery Helpers
# ---------------------------------------------------------------------------

def get_tool_registry():
    ensure_openmontage_on_path()
    mod = importlib.import_module("tools.tool_registry")
    registry = mod.ToolRegistry()
    if hasattr(registry, "discover"):
        registry.discover()
    return registry


def execute_tool(tool, inputs: dict[str, Any]):
    """Invoke BaseTool.execute using dict signature (fallback to kwargs only if TypeError)."""
    try:
        return tool.execute(inputs)
    except TypeError:
        return tool.execute(**inputs)


def resolve_orchestrator_module():
    orch_dir = REPO_ROOT / "core" / "orchestrator"
    assert orch_dir.is_dir(), "core/orchestrator/ directory missing"
    py_files = [p for p in orch_dir.glob("*.py") if p.name != "__pycache__"]
    assert py_files, "core/orchestrator/ has no Python modules yet (M3 deliverable)"
    for mod_name in (
        "core.orchestrator",
        "core.orchestrator.pipeline",
        "core.orchestrator.orchestrator",
        "core.orchestrator.cli",
    ):
        try:
            return importlib.import_module(mod_name)
        except ImportError:
            continue
    raise AssertionError(f"Could not import orchestrator entrypoint from {py_files}")


def resolve_orchestrator_cli_cmd() -> list[str]:
    orch_dir = REPO_ROOT / "core" / "orchestrator"
    assert orch_dir.is_dir(), "core/orchestrator/ missing"
    if (orch_dir / "__main__.py").is_file():
        return [get_python_exe(), "-m", "core.orchestrator"]
    for cand in ("cli.py", "pipeline.py", "orchestrator.py", "run.py"):
        p = orch_dir / cand
        if p.is_file():
            return [get_python_exe(), str(p)]
    py_files = list(orch_dir.glob("*.py"))
    if py_files:
        return [get_python_exe(), str(py_files[0])]
    raise AssertionError("core/orchestrator/ has no CLI script yet (M3 deliverable)")


def resolve_qa_module():
    qa_dir = REPO_ROOT / "core" / "qa"
    assert qa_dir.is_dir(), "core/qa/ directory does not exist yet (M3 deliverable)"
    py_files = list(qa_dir.glob("*.py"))
    assert py_files, "core/qa/ has no Python modules yet (M3 deliverable)"
    for mod_name in ("core.qa", "core.qa.validators", "core.qa.qa_runner", "core.qa.gate"):
        try:
            return importlib.import_module(mod_name)
        except ImportError:
            continue
    raise AssertionError(f"Could not import core/qa entrypoint from {py_files}")


# ---------------------------------------------------------------------------
# SCORM ZIP & Playwright Headless Chrome Verification Helpers
# ---------------------------------------------------------------------------

def inspect_scorm_zip(zip_path: Path) -> dict[str, Any]:
    assert zip_path.is_file(), f"SCORM ZIP missing: {zip_path}"
    assert zip_path.stat().st_size > 100, f"SCORM ZIP looks empty/stub ({zip_path.stat().st_size} B): {zip_path}"
    with zipfile.ZipFile(zip_path, "r") as zf:
        bad = zf.testzip()
        assert bad is None, f"Corrupt ZIP entry {bad} in {zip_path}"
        names = zf.namelist()
        assert "index.html" in names, f"index.html missing from {zip_path}"
        assert "imsmanifest.xml" in names, f"imsmanifest.xml missing from {zip_path}"
        html = zf.read("index.html").decode("utf-8")
        manifest = zf.read("imsmanifest.xml").decode("utf-8")

    root = ET.fromstring(manifest)
    ns = {
        "imscp": "http://www.imsproject.org/xsd/imscp_rootv1p1p2",
        "adlcp": "http://www.adlnet.org/xsd/adlcp_rootv1p2",
    }
    schema_ver = root.find(".//imscp:schemaversion", ns)
    assert schema_ver is not None and schema_ver.text == "1.2", "SCORM 1.2 <schemaversion>1.2</schemaversion> missing"
    files = [el.attrib.get("href", "") for el in root.findall(".//imscp:resource/imscp:file", ns)]
    assert "index.html" in files, "Manifest missing <file href='index.html'/>"
    src_match = re.search(r'<source\s+src="([^"]+)"', html)
    video_src = src_match.group(1) if src_match else None
    return {
        "names": names,
        "html": html,
        "manifest": manifest,
        "manifest_files": files,
        "video_src": video_src,
        "size_bytes": zip_path.stat().st_size,
    }


def run_scorm_in_chrome(
    zip_path: Path,
    checkpoints_expected: list[dict[str, Any]] | None = None,
    require_agents_md_invariants: bool = False,
    verify_media_loaded: bool = False,
    answer_sequence: list[int] | None = None,
    probe_early_offset: float | None = None,
    probe_trigger_offset: float = 0.25,
) -> dict[str, Any]:
    """Extract SCORM ZIP into TemporaryDirectory and verify DOM, fullscreen, checkpoints & SCORM API in Chrome."""
    from playwright.sync_api import sync_playwright

    with tempfile.TemporaryDirectory(prefix="scorm_chrome_") as tmp:
        tmp_dir = Path(tmp)
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(tmp_dir)
        index_path = tmp_dir / "index.html"
        assert index_path.is_file(), "Extracted SCORM ZIP missing index.html"

        blocked_urls: list[str] = []
        page_errors: list[str] = []

        class QuietHandler(SimpleHTTPRequestHandler):
            def log_message(self, format, *args):
                pass

        handler = partial(QuietHandler, directory=str(tmp_dir))
        server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        port = server.server_address[1]
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()

        try:
            with sync_playwright() as p:
                launch_kwargs: dict[str, Any] = {"headless": True}
                if CHROME_EXECUTABLE.is_file():
                    launch_kwargs["executable_path"] = str(CHROME_EXECUTABLE)
                browser = p.chromium.launch(**launch_kwargs)
                context = browser.new_context(viewport={"width": 1280, "height": 800})

                def _route_guard(route):
                    url = route.request.url
                    if url.startswith(("http://127.0.0.1", "http://localhost", "file://", "data:", "blob:")):
                        route.continue_()
                    else:
                        blocked_urls.append(url)
                        route.abort()

                context.route("**/*", _route_guard)
                page = context.new_page()
                page.on("pageerror", lambda err: page_errors.append(str(err)))

                page.add_init_script("""
                    window.__scormCalls = [];
                    window.__scormStore = {};
                    window.__fullscreenTargetId = null;
                    window.API = {
                        LMSInitialize: function(arg) { window.__scormCalls.push(['LMSInitialize', arg]); return "true"; },
                        LMSGetValue: function(k) { return window.__scormStore[k] || ""; },
                        LMSSetValue: function(k, v) { window.__scormStore[k] = String(v); window.__scormCalls.push(['LMSSetValue', k, String(v)]); return "true"; },
                        LMSCommit: function(arg) { window.__scormCalls.push(['LMSCommit', arg]); return "true"; },
                        LMSFinish: function(arg) { window.__scormCalls.push(['LMSFinish', arg]); return "true"; },
                        LMSGetLastError: function() { return "0"; },
                        LMSGetErrorString: function() { return ""; },
                        LMSGetDiagnostic: function() { return ""; }
                    };
                    Element.prototype.requestFullscreen = function() {
                        window.__fullscreenTargetId = this.id || this.tagName;
                        return Promise.resolve();
                    };
                    if (!Element.prototype.webkitRequestFullscreen) {
                        Element.prototype.webkitRequestFullscreen = Element.prototype.requestFullscreen;
                    }
                """)

                page.goto(f"http://127.0.0.1:{port}/index.html", wait_until="domcontentloaded")
                page.wait_for_timeout(300)

                if verify_media_loaded:
                    page.wait_for_function("document.getElementById('video-elem').readyState >= 1", timeout=10000)

                media_meta = page.evaluate("""() => {
                    const v = document.getElementById('video-elem');
                    return {
                        controlsList: v ? (v.getAttribute('controlsList') || '') : '',
                        readyState: v ? v.readyState : 0,
                        videoWidth: v ? v.videoWidth : 0,
                        videoHeight: v ? v.videoHeight : 0,
                        duration: v ? (Number.isFinite(v.duration) ? v.duration : 0) : 0,
                        hasHeaderBar: !!document.getElementById('header-bar'),
                        headerText: (document.getElementById('header-bar') || document.getElementById('next-checkpoint-info') || {}).textContent || '',
                        hasBtnFullscreen: !!document.getElementById('btn-fullscreen'),
                        scoreText: (document.getElementById('score-display') || {}).textContent || '',
                        checkpoints: typeof checkpoints !== 'undefined' ? checkpoints : []
                    };
                }""")

                if require_agents_md_invariants:
                    assert "nofullscreen" in media_meta["controlsList"].lower(), (
                        f"Missing controlsList='nofullscreen' on <video>: {media_meta['controlsList']!r}"
                    )
                    assert media_meta["hasHeaderBar"], "Missing #header-bar next-checkpoint bar"
                    assert "Próxima Pregunta" in media_meta["headerText"], (
                        f"Expected 'Próxima Pregunta' in header bar, got: {media_meta['headerText']!r}"
                    )
                    assert media_meta["hasBtnFullscreen"], "Missing #btn-fullscreen button"
                    page.click("#btn-fullscreen")
                    fs_target = page.evaluate("window.__fullscreenTargetId")
                    assert fs_target == "player-container", (
                        f"Fullscreen button must target #player-container, got {fs_target!r}"
                    )

                cps = checkpoints_expected if checkpoints_expected is not None else media_meta["checkpoints"]
                early_triggered = False
                if probe_early_offset is not None and cps:
                    early_t = max(0.0, float(cps[0]["timestamp"]) + probe_early_offset)
                    page.evaluate(f"""() => {{
                        const v = document.getElementById('video-elem');
                        Object.defineProperty(v, 'currentTime', {{ value: {early_t}, configurable: true }});
                        v.dispatchEvent(new Event('timeupdate'));
                    }}""")
                    page.wait_for_timeout(100)
                    early_triggered = page.evaluate("getComputedStyle(document.getElementById('overlay')).display !== 'none'")

                triggered_results: list[dict[str, Any]] = []
                for idx, cp in enumerate(cps):
                    ts = float(cp["timestamp"]) + probe_trigger_offset
                    page.evaluate(f"""() => {{
                        const v = document.getElementById('video-elem');
                        Object.defineProperty(v, 'currentTime', {{ value: {ts}, configurable: true }});
                        v.dispatchEvent(new Event('timeupdate'));
                    }}""")
                    page.wait_for_timeout(150)
                    overlay_open = page.evaluate("getComputedStyle(document.getElementById('overlay')).display !== 'none'")
                    assert overlay_open, f"Checkpoint {idx} at {ts}s did not open #overlay"

                    q_text = page.locator("#q-title").text_content() or ""
                    opts_count = page.locator("#opts-container .option-btn").count()
                    assert opts_count >= 2, f"Expected >=2 option buttons, got {opts_count}"

                    chosen = answer_sequence[idx] if answer_sequence and idx < len(answer_sequence) else int(cp.get("correct_index", 0))
                    page.locator("#opts-container .option-btn").nth(chosen).click()
                    page.wait_for_timeout(100)
                    assert page.locator("#btn-continue").is_visible(), "#btn-continue not visible after answering"
                    fb_text = page.locator("#feedback").text_content() or ""
                    score_now = page.locator("#score-display").text_content() or ""
                    page.locator("#btn-continue").click()
                    page.wait_for_timeout(100)
                    overlay_after = page.evaluate("getComputedStyle(document.getElementById('overlay')).display")
                    assert overlay_after == "none", "#overlay did not close on #btn-continue click"
                    triggered_results.append({
                        "idx": idx,
                        "question": q_text,
                        "options_count": opts_count,
                        "feedback": fb_text,
                        "score_after": score_now,
                    })

                # Trigger ended event
                page.evaluate("""() => {
                    const v = document.getElementById('video-elem');
                    v.dispatchEvent(new Event('ended'));
                }""")
                page.wait_for_timeout(150)
                scorm_calls = page.evaluate("window.__scormCalls")
                scorm_store = page.evaluate("window.__scormStore")
                browser.close()
        finally:
            server.shutdown()
            server.server_close()

        assert not page_errors, f"Uncaught JS errors in Chrome SCORM playback: {page_errors}"
        assert not blocked_urls, f"External network requests attempted during SCORM playback: {blocked_urls}"

        return {
            "media_meta": media_meta,
            "early_triggered": early_triggered,
            "triggered_results": triggered_results,
            "scorm_calls": scorm_calls,
            "scorm_store": scorm_store,
        }


def run_html_render_in_chrome(html_path: Path, timestamps: list[float]) -> list[str]:
    """Open composition index.html read-only in headless Chrome and call window.render(t) at timestamps."""
    from playwright.sync_api import sync_playwright

    page_errors: list[str] = []
    with sync_playwright() as p:
        launch_kwargs: dict[str, Any] = {"headless": True}
        if CHROME_EXECUTABLE.is_file():
            launch_kwargs["executable_path"] = str(CHROME_EXECUTABLE)
        browser = p.chromium.launch(**launch_kwargs)
        context = browser.new_context(viewport={"width": 1920, "height": 1080})
        context.route(
            "**/*",
            lambda r: r.continue_() if r.request.url.startswith(("file://", "http://127.0.0.1", "data:", "blob:")) else r.abort(),
        )
        page = context.new_page()
        page.on("pageerror", lambda err: page_errors.append(str(err)))
        page.goto(html_path.resolve().as_uri(), wait_until="domcontentloaded")
        page.wait_for_timeout(200)
        has_render = page.evaluate("typeof window.render === 'function'")
        assert has_render, f"{html_path} does not expose window.render(t)"
        for t in timestamps:
            page.evaluate(f"window.render({float(t)})")
        browser.close()
    return page_errors
