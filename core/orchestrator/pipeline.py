"""Unified EducAI Pipeline backing video synthesis with OpenMontage tools and QA gates."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Optional

from core.brand_theme import extract_brand_theme
from core.orchestrator._openmontage_env import ensure_openmontage_env, get_registry
from core.orchestrator.outro_mux import concat_with_outro, mux_audio_video
from core.orchestrator.scene_builder import (
    align_checkpoints_to_timeline,
    build_playbook_and_decisions,
    build_scenes_from_document,
    generate_style_artifacts,
)
from core.qa.post_render import validate_post_render
from core.qa.pre_render import validate_pre_render
from core.scorm.scorm_packager import build_scorm_package


class EducAIPipeline:
    """End-to-end video production pipeline for EducAI."""

    def __init__(self, project_dir: str | Path, registry: Optional[Any] = None) -> None:
        self.project_dir = Path(project_dir).resolve()
        self.project_dir.mkdir(parents=True, exist_ok=True)
        self.registry = registry or get_registry()

    def run(
        self,
        *,
        doc_path: Optional[str | Path] = None,
        scenes: Optional[list[dict[str, Any]]] = None,
        theme_image: Optional[str | Path] = None,
        render_mode: str = "hyperframes",
        scorm_title: Optional[str] = None,
        voice: str = "es-AR-ElenaNeural",
        captions: bool = True,
        outro_path: Optional[str | Path] = None,
        dual_scorm: bool = True,
        skip_render: bool = False,
    ) -> dict[str, Any]:
        """Execute all stages of the EducAI pipeline."""
        start_time = time.time()
        print(f"\n[Pipeline] Starting EducAI pipeline in: {self.project_dir}")
        print(f"[Pipeline] Mode: {render_mode} | Voice: {voice} | Captions: {'ON (CapCut-style)' if captions else 'OFF'}")

        # --- Stage 1: Ingestion & Branding ---
        brand_theme: dict[str, Any] = {}
        if theme_image and Path(theme_image).is_file():
            print(f"[Stage 1] Extracting brand palette from {theme_image}...")
            theme_out = self.project_dir / "theme_config.json"
            brand_theme = extract_brand_theme(str(theme_image), output_json=str(theme_out))

        if not scenes:
            if doc_path and Path(doc_path).is_file():
                print(f"[Stage 1] Ingesting document: {doc_path}...")
                scenes = build_scenes_from_document(doc_path, brand_theme)
            else:
                scenes_json = self.project_dir / "scenes.json"
                if scenes_json.is_file():
                    scenes = json.loads(scenes_json.read_text(encoding="utf-8"))
                else:
                    raise ValueError("No input document, scenes list, or scenes.json provided.")

        scenes_path = self.project_dir / "scenes.json"
        scenes_path.write_text(json.dumps(scenes, indent=2, ensure_ascii=False), encoding="utf-8")

        # Generate style artifacts for HyperFrames if applicable
        css_vars, design_md = generate_style_artifacts(brand_theme)
        (self.project_dir / "DESIGN.md").write_text(design_md, encoding="utf-8")

        # --- Stage 2: Narration & Subtitles (EdgeTTS) ---
        print("[Stage 2] Synthesizing speech narration via EdgeTTS...")
        edge_tts_tool = self.registry.get("edge_tts")
        tts_res = edge_tts_tool.execute({
            "scenes": scenes,
            "output_dir": str(self.project_dir),
            "voice": voice,
            "rate": "-2%",
            "emit_word_boundaries": captions,
        })
        if not tts_res.success:
            raise RuntimeError(f"EdgeTTS narration synthesis failed: {tts_res.error}")

        timeline = tts_res.data.get("scenes", [])
        total_audio_duration = float(tts_res.data.get("total_duration", 0.0))

        # Re-align checkpoints strictly to scene end
        raw_checkpoints = []
        for sc in scenes:
            raw_checkpoints.extend(sc.get("checkpoints", []))
        if not raw_checkpoints:
            local_cp = self.project_dir / "checkpoints.json"
            if local_cp.is_file():
                try:
                    raw_checkpoints = json.loads(local_cp.read_text(encoding="utf-8"))
                except Exception:
                    raw_checkpoints = []
        if raw_checkpoints:
            aligned_cps = align_checkpoints_to_timeline(raw_checkpoints, timeline)
            cp_path = self.project_dir / "scorm_checkpoints.json"
            cp_path.write_text(json.dumps(aligned_cps, indent=2, ensure_ascii=False), encoding="utf-8")

        # --- Stage 3: Stereo Normalized Audio Mix ---
        print("[Stage 3] Mixing audio tracks (voice + music) in normalized stereo...")
        audio_mixed_path = self.project_dir / "audio_mixed.m4a"
        self._build_or_mix_audio(timeline, total_audio_duration, audio_mixed_path)

        # --- Stage 4: Pre-Render QA Gate ---
        print("[Stage 4] Running Pre-Render QA gate...")
        pre_qa = validate_pre_render(
            self.project_dir,
            render_mode=render_mode,
            audio_file="audio_mixed.m4a",
            timeline_file="audio_timeline.json",
        )
        if not pre_qa["passed"]:
            print(f"[QA Gate Warning] Pre-render detected issues: {pre_qa['issues']}")
        else:
            print("[QA Gate] Pre-render checks passed successfully.")

        # --- Stage 5: Visual Render ---
        video_raw_path = self.project_dir / "video_raw.mp4"
        if not skip_render or not video_raw_path.is_file():
            print(f"[Stage 5] Rendering visuals with backend '{render_mode}'...")
            self._render_visuals(render_mode, total_audio_duration, video_raw_path, captions=captions)
        else:
            print(f"[Stage 5] Skipping render; reusing existing {video_raw_path}")

        # --- Stage 6: Mux + Outro Concatenation ---
        print("[Stage 6] Multiplexing video with audio and appending outro...")
        final_video_name = f"{scorm_title or self.project_dir.stem}_EducAI_Final.mp4"
        final_video_path = self.project_dir / final_video_name

        muxed_main_temp = self.project_dir / "main_with_audio.mp4"
        mux_audio_video(video_raw_path, audio_mixed_path, muxed_main_temp, force_stereo=True)
        concat_with_outro(muxed_main_temp, final_video_path, outro_path=outro_path)

        if muxed_main_temp.is_file():
            try:
                muxed_main_temp.unlink()
            except OSError:
                pass

        # --- Stage 7: Post-Render QA Gate ---
        print("[Stage 7] Running Post-Render QA gate...")
        post_qa = validate_post_render(final_video_path)
        if not post_qa["passed"]:
            print(f"[QA Gate Warning] Post-render detected issues: {post_qa['issues']}")
        else:
            print("[QA Gate] Post-render checks passed successfully.")

        # --- Stage 8: Export Bundle & SCORM 1.2 Packaging ---
        print("[Stage 8] Building SCORM 1.2 package for Moodle...")
        checkpoints_for_scorm = []
        cp_file = self.project_dir / "scorm_checkpoints.json"
        if cp_file.is_file():
            checkpoints_for_scorm = json.loads(cp_file.read_text(encoding="utf-8"))

        clean_title = scorm_title or self.project_dir.stem.replace("-", " ").title()
        scorm_full_zip = self.project_dir / f"{scorm_title or self.project_dir.stem}_SCORM_Completo.zip"
        
        build_scorm_package(
            title=clean_title,
            video_url=final_video_name,
            checkpoints=checkpoints_for_scorm,
            output_zip=str(scorm_full_zip),
            include_video_file=str(final_video_path),
            audio_timeline_path=str(self.project_dir / "audio_timeline.json"),
            strict_sync=True,
            also_build_zero_weight=dual_scorm,
        )

        total_elapsed = round(time.time() - start_time, 2)
        print(f"\n[Pipeline] Completed successfully in {total_elapsed}s!")
        print(f"[Pipeline] Final Video: {final_video_path}")
        print(f"[Pipeline] SCORM Package: {scorm_full_zip}")

        return {
            "success": True,
            "final_video": str(final_video_path),
            "scorm_full": str(scorm_full_zip),
            "scorm_zero": str(scorm_full_zip.with_name(f"{scorm_title or self.project_dir.stem}_SCORM.zip")),
            "elapsed_seconds": total_elapsed,
            "pre_qa": pre_qa,
            "post_qa": post_qa,
        }

    def _build_or_mix_audio(
        self,
        timeline: list[dict[str, Any]],
        total_duration: float,
        output_mixed_path: Path,
    ) -> None:
        """Combine scene MP3 files and optional background music into normalized stereo AAC."""
        if output_mixed_path.is_file() and output_mixed_path.stat().st_size > 0:
            return

        if not timeline:
            return

        n = len(timeline)
        inputs: list[str] = []
        filter_parts: list[str] = []

        for i, sc in enumerate(timeline):
            inputs.extend(["-i", str(Path(sc["mp3_file"]).resolve())])
            delay_ms = int(sc.get("start", 0.0) * 1000)
            filter_parts.append(f"[{i}:a]adelay={delay_ms}|{delay_ms}[a{i}];")

        mix_inputs = "".join([f"[a{i}]" for i in range(n)])

        # Check for optional background music
        music_candidates = [self.project_dir / "music.wav", self.project_dir / "music.mp3"]
        music_path = next((m for m in music_candidates if m.is_file()), None)

        if music_path:
            inputs.extend(["-i", str(music_path.resolve())])
            music_idx = n
            filter_str = (
                "".join(filter_parts)
                + f"{mix_inputs}amix=inputs={n}:dropout_transition=0,volume={n}[narr];"
                + f"[{music_idx}:a]volume=0.15[bg];"
                + "[narr][bg]amix=inputs=2:duration=first:dropout_transition=2,loudnorm=I=-16:TP=-1.5:LRA=11[outa]"
            )
        else:
            filter_str = (
                "".join(filter_parts)
                + f"{mix_inputs}amix=inputs={n}:dropout_transition=0,volume={n},loudnorm=I=-16:TP=-1.5:LRA=11[outa]"
            )

        cmd = [
            "ffmpeg", "-y",
            *inputs,
            "-filter_complex", filter_str,
            "-map", "[outa]",
            "-c:a", "aac",
            "-b:a", "192k",
            "-ac", "2",
            "-ar", "44100",
            "-t", str(total_duration),
            str(output_mixed_path),
        ]
        subprocess.run(cmd, capture_output=True, check=True)

    def _render_visuals(
        self,
        render_mode: str,
        total_duration: float,
        output_raw: Path,
        captions: bool = True,
    ) -> None:
        """Dispatch rendering to the chosen backend."""
        if render_mode == "canvas":
            # Reusable canvas render from frames/ or render_frames.js
            frames_dir = self.project_dir / "frames"
            if frames_dir.is_dir() and any(frames_dir.glob("frame_*.png")):
                print("[Render] Found existing frames in frames/, encoding directly to video_raw.mp4...")
                subprocess.run(
                    [
                        "ffmpeg", "-y",
                        "-framerate", "24",
                        "-i", str(frames_dir / "frame_%05d.png"),
                        "-c:v", "libx264",
                        "-pix_fmt", "yuv420p",
                        "-preset", "fast",
                        "-crf", "18",
                        str(output_raw),
                    ],
                    capture_output=True,
                    check=True,
                )
                return

            render_js = self.project_dir / "render_frames.js"
            if render_js.is_file():
                subprocess.run(["node", str(render_js)], cwd=str(self.project_dir), check=True)
                return

        # Motion graphics / HyperFrames renderer with dynamic scene cards & CapCut captions
        try:
            from core.orchestrator.video_render import render_motion_graphics_video
            render_motion_graphics_video(self.project_dir, total_duration, output_raw, captions=captions)
        except Exception as e:
            print(f"[Render Fallback] Motion graphics generator encountered: {e}. Falling back to standard lavfi generator...")
            subprocess.run(
                [
                    "ffmpeg", "-y",
                    "-f", "lavfi",
                    "-i", f"color=c=0x0F172A:s=1920x1080:d={total_duration}:r=24",
                    "-c:v", "libx264",
                    "-pix_fmt", "yuv420p",
                    "-preset", "veryfast",
                    str(output_raw),
                ],
                capture_output=True,
                check=True,
            )


def main() -> None:
    parser = argparse.ArgumentParser(description="EducAI Unified Video Pipeline")
    parser.add_argument("--project-dir", "-p", default=".", help="Project working directory")
    parser.add_argument("--doc", "-d", help="Input document (.pptx, .docx, .pdf)")
    parser.add_argument("--theme-image", "-t", help="Theme logo/image for color extraction")
    parser.add_argument("--render-mode", "-m", default="hyperframes", choices=["hyperframes", "canvas", "ffmpeg", "threejs", "ink_theater"])
    parser.add_argument("--title", help="Title for video and SCORM package")
    parser.add_argument("--voice", default="es-AR-ElenaNeural", help="EdgeTTS voice")
    parser.add_argument("--no-captions", action="store_true", help="Disable default CapCut-style animated captions")
    parser.add_argument("--outro", help="Path to outro MP4 to concatenate")
    parser.add_argument("--skip-render", action="store_true", help="Skip re-rendering video_raw.mp4")
    parser.add_argument("--no-dual-scorm", action="store_true", help="Disable dual SCORM packaging")

    args = parser.parse_args()

    pipeline = EducAIPipeline(args.project_dir)
    pipeline.run(
        doc_path=args.doc,
        theme_image=args.theme_image,
        render_mode=args.render_mode,
        scorm_title=args.title,
        voice=args.voice,
        captions=not args.no_captions,
        outro_path=args.outro,
        dual_scorm=not args.no_dual_scorm,
        skip_render=args.skip_render,
    )


if __name__ == "__main__":
    main()
