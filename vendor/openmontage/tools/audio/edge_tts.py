"""Edge TTS text-to-speech provider tool with word-level boundary synchronization."""

from __future__ import annotations

import asyncio
import json
import os
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any, Optional

from tools.base_tool import (
    BaseTool,
    Determinism,
    ExecutionMode,
    ResourceProfile,
    RetryPolicy,
    ToolResult,
    ToolRuntime,
    ToolStability,
    ToolStatus,
    ToolTier,
)


def _run_async(coro):
    """Run an async coroutine safely even if an event loop is already running in current thread."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            return pool.submit(asyncio.run, coro).result()
    else:
        return asyncio.run(coro)


class EdgeTTS(BaseTool):
    name = "edge_tts"
    version = "0.1.0"
    tier = ToolTier.VOICE
    capability = "tts"
    provider = "edge_tts"
    stability = ToolStability.PRODUCTION
    execution_mode = ExecutionMode.SYNC
    determinism = Determinism.DETERMINISTIC
    runtime = ToolRuntime.API

    dependencies = ["python:edge_tts", "cmd:ffprobe"]
    install_instructions = "Install edge-tts via: pip install edge-tts"
    agent_skills = ["text-to-speech", "tiktok-word-captions"]

    capabilities = [
        "text_to_speech",
        "word_timings",
        "audio_timeline",
        "scene_batch_narration",
    ]
    supports = {
        "voice_cloning": False,
        "multilingual": True,
        "offline": False,
        "native_audio": True,
        "word_boundaries": True,
    }
    best_for = [
        "EducAI Argentine and Latin American voice narration (es-AR-ElenaNeural)",
        "synchronous word-level captions and interactive SCORM audio timelines",
    ]
    not_good_for = [
        "completely offline air-gapped environments without network",
    ]

    input_schema = {
        "type": "object",
        "properties": {
            "text": {"type": "string", "description": "Single text to synthesize"},
            "scenes": {
                "type": "array",
                "description": "Batch of scenes for multi-scene educational videos",
                "items": {"type": "object"},
            },
            "voice": {
                "type": "string",
                "default": "es-AR-ElenaNeural",
                "description": "Voice identifier (default: es-AR-ElenaNeural)",
            },
            "rate": {
                "type": "string",
                "default": "-2%",
                "description": "Speech rate adjustment (default: -2%)",
            },
            "pitch": {"type": "string", "default": "+0Hz"},
            "volume": {"type": "string", "default": "+0%"},
            "inter_scene_pause": {
                "type": "number",
                "default": 0.55,
                "description": "Pause between scenes in seconds",
            },
            "emit_word_boundaries": {
                "type": "boolean",
                "default": True,
                "description": "Capture WordBoundary events for word_timings.json",
            },
            "output_path": {
                "type": "string",
                "description": "Destination file for single audio mode",
            },
            "output_dir": {
                "type": "string",
                "description": "Destination directory for batch multi-scene mode",
            },
        },
    }

    resource_profile = ResourceProfile(
        cpu_cores=1, ram_mb=256, vram_mb=0, disk_mb=100, network_required=True
    )
    retry_policy = RetryPolicy(max_retries=2, retryable_errors=["OSError", "Exception"])
    idempotency_key_fields = ["text", "voice", "rate", "pitch"]
    side_effects = ["writes audio file(s) and word timing metadata to disk"]
    user_visible_verification = ["Listen to generated MP3 and verify word_timings.json"]

    def get_status(self) -> ToolStatus:
        if shutil.which("ffprobe") is None:
            return ToolStatus.UNAVAILABLE
        try:
            import edge_tts  # noqa: F401
            return ToolStatus.AVAILABLE
        except ImportError:
            return ToolStatus.UNAVAILABLE

    def _probe_duration(self, path: Path) -> float:
        cmd = [
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", str(path)
        ]
        res = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=True,
        )
        return float(res.stdout.strip())

    async def _synthesize_async(
        self,
        text: str,
        mp3_path: Path,
        voice: str,
        rate: str,
        pitch: str,
        volume: str,
        emit_word_boundaries: bool,
    ) -> list[dict[str, Any]]:
        import edge_tts

        boundary_type = "WordBoundary" if emit_word_boundaries else "SentenceBoundary"
        comm = edge_tts.Communicate(
            text,
            voice=voice,
            rate=rate,
            pitch=pitch,
            volume=volume,
            boundary=boundary_type,
        )

        word_timings: list[dict[str, Any]] = []
        mp3_path.parent.mkdir(parents=True, exist_ok=True)
        with open(mp3_path, "wb") as f_audio:
            async for chunk in comm.stream():
                if chunk["type"] == "audio":
                    f_audio.write(chunk["data"])
                elif chunk["type"] == "WordBoundary":
                    # Offset and duration in 100ns units
                    offset_sec = round(chunk.get("offset", 0) / 10_000_000, 3)
                    duration_sec = round(chunk.get("duration", 0) / 10_000_000, 3)
                    word_timings.append({
                        "text": chunk.get("text", ""),
                        "start": offset_sec,
                        "duration": duration_sec,
                        "end": round(offset_sec + duration_sec, 3),
                    })

        return word_timings

    def execute(self, inputs: dict[str, Any]) -> ToolResult:
        start_time = time.time()
        text = inputs.get("text")
        scenes = inputs.get("scenes")
        voice = inputs.get("voice", "es-AR-ElenaNeural")
        rate = inputs.get("rate", "-2%")
        pitch = inputs.get("pitch", "+0Hz")
        volume = inputs.get("volume", "+0%")
        inter_scene_pause = float(inputs.get("inter_scene_pause", 0.55))
        emit_word_boundaries = bool(inputs.get("emit_word_boundaries", True))

        if not text and not scenes:
            return ToolResult(
                success=False,
                error="Either 'text' or 'scenes' must be provided to edge_tts.",
            )

        artifacts: list[str] = []

        # Single speech mode
        if text and not scenes:
            output_path_str = inputs.get("output_path")
            if not output_path_str:
                out_dir = Path(inputs.get("output_dir") or ".")
                output_path = out_dir / "narration.mp3"
            else:
                output_path = Path(output_path_str)

            try:
                words = _run_async(
                    self._synthesize_async(
                        text, output_path, voice, rate, pitch, volume, emit_word_boundaries
                    )
                )
                dur = self._probe_duration(output_path)
                artifacts.append(str(output_path))

                word_timings_path = output_path.with_name(f"{output_path.stem}_words.json")
                if words:
                    with open(word_timings_path, "w", encoding="utf-8") as f_w:
                        json.dump(words, f_w, indent=2, ensure_ascii=False)
                    artifacts.append(str(word_timings_path))
                else:
                    word_timings_path = None

                return ToolResult(
                    success=True,
                    data={
                        "audio_path": str(output_path),
                        "duration": round(dur, 3),
                        "word_timings": words,
                        "word_timings_path": str(word_timings_path) if word_timings_path else None,
                    },
                    artifacts=artifacts,
                    duration_seconds=round(time.time() - start_time, 2),
                    cost_usd=0.0,
                )
            except Exception as exc:
                return ToolResult(
                    success=False,
                    error=f"EdgeTTS single synthesis failed: {exc}",
                    duration_seconds=round(time.time() - start_time, 2),
                )

        # Multi-scene batch mode
        out_dir = Path(inputs.get("output_dir") or ".")
        out_dir.mkdir(parents=True, exist_ok=True)
        timeline: list[dict[str, Any]] = []
        all_word_timings: dict[str, list[dict[str, Any]]] = {}
        total_time = 0.0

        try:
            for idx, sc in enumerate(scenes):  # type: ignore[union-attr]
                sid = sc.get("scene_id") or f"scene_{idx + 1:02d}"
                script = sc.get("voiceover_script") or sc.get("text", "")
                mp3_path = out_dir / f"{sid}.mp3"

                words = _run_async(
                    self._synthesize_async(
                        script, mp3_path, voice, rate, pitch, volume, emit_word_boundaries
                    )
                )
                dur = self._probe_duration(mp3_path)
                artifacts.append(str(mp3_path))
                all_word_timings[sid] = words

                start_ts = round(total_time, 3)
                end_ts = round(start_ts + dur, 3)

                entry = {
                    "scene_id": sid,
                    "order": sc.get("order", idx + 1),
                    "title": sc.get("title", f"Scene {idx + 1}"),
                    "mp3_file": str(mp3_path),
                    "start": start_ts,
                    "duration": round(dur, 3),
                    "end": end_ts,
                    "voiceover_script": script,
                    "screen_elements": sc.get("screen_elements", {}),
                    "checkpoints": sc.get("checkpoints", []),
                }
                timeline.append(entry)
                total_time += dur + inter_scene_pause

            total_time = round(total_time, 3)

            timeline_path = out_dir / "audio_timeline.json"
            with open(timeline_path, "w", encoding="utf-8") as f_tl:
                json.dump({"total_duration": total_time, "scenes": timeline}, f_tl, indent=2, ensure_ascii=False)
            artifacts.append(str(timeline_path))

            word_timings_path = out_dir / "word_timings.json"
            with open(word_timings_path, "w", encoding="utf-8") as f_wt:
                json.dump(all_word_timings, f_wt, indent=2, ensure_ascii=False)
            artifacts.append(str(word_timings_path))

            return ToolResult(
                success=True,
                data={
                    "total_duration": total_time,
                    "scenes": timeline,
                    "timeline_path": str(timeline_path),
                    "word_timings_path": str(word_timings_path),
                    "scenes_processed": len(timeline),
                },
                artifacts=artifacts,
                duration_seconds=round(time.time() - start_time, 2),
                cost_usd=0.0,
            )
        except Exception as exc:
            return ToolResult(
                success=False,
                error=f"EdgeTTS batch synthesis failed: {exc}",
                duration_seconds=round(time.time() - start_time, 2),
            )
