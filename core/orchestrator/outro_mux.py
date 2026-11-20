"""Multiplexing and outro concatenation with audio normalization for EducAI."""

from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

_REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTRO_PATH = _REPO_ROOT / "films" / "estructura-tripartita" / "ending_norm.mp4"


def mux_audio_video(
    video_path: str | Path,
    audio_path: str | Path,
    output_path: str | Path,
    *,
    force_stereo: bool = True,
) -> Path:
    """Mux video and audio into a single MP4, enforcing AAC 44.1kHz stereo audio."""
    v_path = Path(video_path).resolve()
    a_path = Path(audio_path).resolve()
    out_path = Path(output_path).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        "ffmpeg", "-y",
        "-i", str(v_path),
        "-i", str(a_path),
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "192k",
    ]
    if force_stereo:
        cmd.extend(["-ac", "2", "-ar", "44100"])

    cmd.extend(["-shortest", str(out_path)])

    subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=True,
    )
    return out_path


def concat_with_outro(
    main_video_path: str | Path,
    output_final_path: str | Path,
    outro_path: Optional[str | Path] = None,
) -> Path:
    """Concatenate main video with ending outro, using copy mode or filter fallback."""
    main_path = Path(main_video_path).resolve()
    final_path = Path(output_final_path).resolve()
    final_path.parent.mkdir(parents=True, exist_ok=True)

    if outro_path is None:
        if DEFAULT_OUTRO_PATH.is_file():
            outro_resolved = DEFAULT_OUTRO_PATH.resolve()
        else:
            outro_resolved = None
    else:
        candidate = Path(outro_path).resolve()
        outro_resolved = candidate if candidate.is_file() else None

    if outro_resolved is None:
        # No outro available, copy or move main video to target
        if main_path != final_path:
            import shutil
            shutil.copy2(main_path, final_path)
        return final_path

    # Concat using list
    concat_list_path = final_path.parent / f"concat_{final_path.stem}.txt"
    try:
        main_entry = str(main_path).replace("\\", "/")
        outro_entry = str(outro_resolved).replace("\\", "/")
        concat_list_path.write_text(
            f"file '{main_entry}'\nfile '{outro_entry}'\n", encoding="utf-8"
        )

        copy_cmd = [
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_list_path),
            "-c", "copy",
            str(final_path),
        ]
        res = subprocess.run(
            copy_cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

        if res.returncode != 0:
            # Fallback to filter_complex re-encode if stream copy fails
            reencode_cmd = [
                "ffmpeg", "-y",
                "-i", str(main_path),
                "-i", str(outro_resolved),
                "-filter_complex",
                "[0:v][0:a][1:v][1:a]concat=n=2:v=1:a=1[v][a]",
                "-map", "[v]",
                "-map", "[a]",
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                "-r", "24",
                "-c:a", "aac",
                "-ac", "2",
                "-ar", "44100",
                str(final_path),
            ]
            subprocess.run(
                reencode_cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=True,
            )
    finally:
        if concat_list_path.exists():
            try:
                concat_list_path.unlink()
            except OSError:
                pass

    return final_path
