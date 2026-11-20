"""Scene generation, brand theming, and SCORM checkpoint alignment for EducAI."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from core.brand_theme import extract_brand_theme
from core.orchestrator._openmontage_env import ensure_openmontage_env
from core.parsers.doc_parser import parse_document


def build_scenes_from_document(
    doc_path: str | Path,
    brand_theme: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Parse a PPTX, DOCX, or PDF document and map it into structured EducAI scenes."""
    doc_data = parse_document(str(doc_path))
    sections = doc_data.get("sections", [])

    scenes: list[dict[str, Any]] = []
    for idx, sec in enumerate(sections, 1):
        sid = f"scene_{idx:02d}"
        title = sec.get("title") or f"Escena {idx}"
        paragraphs = sec.get("paragraphs") or []
        bullets = sec.get("bullets") or []

        # Script creation: prefer paragraphs or bullets, or fallback to title
        if paragraphs:
            voiceover_script = " ".join(paragraphs)
        elif bullets:
            voiceover_script = f"{title}. " + ". ".join(bullets)
        else:
            voiceover_script = title

        # Build basic screen elements
        screen_elements = {
            "title": title,
            "bullets": bullets or paragraphs[:3],
            "theme": brand_theme.get("palette") if brand_theme else {},
        }

        # Checkpoint placeholder at scene boundary (to be aligned with audio_timeline)
        checkpoints = []
        if sec.get("checkpoints"):
            checkpoints = sec["checkpoints"]

        scenes.append({
            "scene_id": sid,
            "order": idx,
            "title": title,
            "voiceover_script": voiceover_script,
            "screen_elements": screen_elements,
            "checkpoints": checkpoints,
        })

    return scenes


def build_playbook_and_decisions(
    brand_theme: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Construct OpenMontage playbook and edit_decisions from an EducAI brand theme."""
    palette = (brand_theme or {}).get("palette", {})
    typography = (brand_theme or {}).get("typography", {})

    primary = palette.get("primary", "#0284c7")
    secondary = palette.get("secondary", "#1e293b")
    alert = palette.get("alert", "#ea580c")
    dark_neutral = palette.get("dark_neutral", "#0f172a")
    bg = palette.get("background", "#0B0F1A")
    font_family = typography.get("font_family", "Inter")

    playbook = {
        "name": "educai_brand",
        "visual_language": {
            "color_palette": {
                "primary": primary,
                "secondary": secondary,
                "accent": alert,
                "surface": dark_neutral,
                "background": bg,
                "text": "#F8FAFC",
                "muted_text": "#94A3B8",
            },
            "palette": {
                "primary": primary,
                "secondary": secondary,
                "accent": alert,
                "surface": dark_neutral,
                "bg": bg,
                "fg": "#F8FAFC",
                "muted": "#94A3B8",
            },
            "typography": {
                "heading": font_family,
                "body": font_family,
                "code": "JetBrains Mono",
            },
            "motion": {
                "ease": "cubic-bezier(0.16, 1, 0.3, 1)",
                "duration": "0.6s",
            },
        },
    }

    edit_decisions = {
        "metadata": {
            "title": "EducAI Video Class",
            "primary_color": primary,
            "accent_color": alert,
            "background_color": bg,
            "text_color": "#F8FAFC",
            "render_runtime": "hyperframes",
        },
        "audio": {
            "voice": "es-AR-ElenaNeural",
            "rate": "-2%",
            "normalize": True,
            "loudnorm_target": -16.0,
        },
    }

    return playbook, edit_decisions


def generate_style_artifacts(
    brand_theme: dict[str, Any] | None = None,
) -> tuple[dict[str, str], str]:
    """Generate CSS custom properties and DESIGN.md using OpenMontage style_bridge."""
    ensure_openmontage_env()
    from lib.hyperframes_style_bridge import style_bridge

    playbook, edit_decisions = build_playbook_and_decisions(brand_theme)
    css_vars, design_md = style_bridge(playbook, edit_decisions)
    return css_vars, design_md


def align_checkpoints_to_timeline(
    checkpoints: list[dict[str, Any]],
    timeline_scenes: list[dict[str, Any]],
    margin: float = 0.05,
) -> list[dict[str, Any]]:
    """Align SCORM checkpoints strictly to the end of speech for their associated scenes."""
    aligned: list[dict[str, Any]] = []
    scenes_by_id = {s["scene_id"]: s for s in timeline_scenes}
    scenes_by_order = {s["order"]: s for s in timeline_scenes}

    for idx, cp in enumerate(checkpoints):
        cp_copy = dict(cp)
        matched_scene = None

        if "scene_id" in cp and cp["scene_id"] in scenes_by_id:
            matched_scene = scenes_by_id[cp["scene_id"]]
        elif "scene_order" in cp and cp["scene_order"] in scenes_by_order:
            matched_scene = scenes_by_order[cp["scene_order"]]
        elif idx < len(timeline_scenes):
            matched_scene = timeline_scenes[idx]

        if matched_scene:
            scene_end = matched_scene["end"]
            cp_copy["timestamp"] = round(scene_end + margin, 3)
            cp_copy["scene_id"] = matched_scene["scene_id"]
            if not cp_copy.get("section_title"):
                cp_copy["section_title"] = matched_scene.get("title", f"Sección {idx + 1}")
        aligned.append(cp_copy)

    return aligned
