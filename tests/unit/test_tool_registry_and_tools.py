"""Level 2: ToolRegistry discovery, EdgeTTS execution and HyperFramesCompose status."""

from pathlib import Path

import pytest
from tests.conftest import ensure_openmontage_on_path


def test_tool_registry_discovery():
    ensure_openmontage_on_path()
    from tools.base_tool import ToolStatus
    from tools.tool_registry import ToolRegistry

    registry = ToolRegistry()
    registry.ensure_discovered()

    # Discover edge_tts
    edge_tool = registry.get("edge_tts")
    assert edge_tool is not None
    assert edge_tool.name == "edge_tts"
    assert edge_tool.get_status() == ToolStatus.AVAILABLE

    # Check available local tools count
    available_tools = [t for t in registry._tools.values() if t.get_status() == ToolStatus.AVAILABLE]
    assert len(available_tools) >= 38, f"Expected >= 38 available tools, found {len(available_tools)}"


def test_hyperframes_compose_status():
    ensure_openmontage_on_path()
    from tools.base_tool import ToolStatus
    from tools.video.hyperframes_compose import HyperFramesCompose

    hf = HyperFramesCompose()
    status = hf.get_status()
    assert status == ToolStatus.AVAILABLE, f"HyperFramesCompose is {status}, expected AVAILABLE"
    info = hf.get_info()
    runtime = info.get("hyperframes_runtime", {})
    assert runtime.get("runtime_available") is True
    assert runtime.get("ffmpeg_available") is True
    assert runtime.get("npx_available") is True


def test_edge_tts_synthesis_and_timings(tmp_path: Path):
    ensure_openmontage_on_path()
    from tools.audio.edge_tts import EdgeTTS

    tts = EdgeTTS()
    out_mp3 = tmp_path / "test_speech.mp3"

    res = tts.execute({
        "text": "Bienvenidos al curso de inteligencia artificial.",
        "output_path": str(out_mp3),
        "voice": "es-AR-ElenaNeural",
        "emit_word_boundaries": True,
    })

    assert res.success is True, f"EdgeTTS failed: {res.error}"
    assert out_mp3.is_file()
    assert out_mp3.stat().st_size > 5000
    assert res.data["duration"] > 1.0

    # Verify word timings
    words_file = tmp_path / "test_speech_words.json"
    assert words_file.is_file()
    words = res.data.get("word_timings", [])
    assert len(words) >= 3
    assert "start" in words[0]
    assert "end" in words[0]
