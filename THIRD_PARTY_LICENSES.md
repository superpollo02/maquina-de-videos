# Third-Party Licenses & Attributions

## 1. OpenMontage
- **Origin Repository:** `https://github.com/OpenMontageInc/OpenMontage.git`
- **Commit:** `2e003e65fa99a0f329478a2c1cdcf26bc481933a`
- **License:** GNU Affero General Public License v3.0 (AGPLv3)
- **Location:** `vendor/openmontage/`
- **Full License Text:** See `vendor/openmontage/LICENSE`
- **Modifications (2026-11-20):**
  - Added `vendor/openmontage/tools/audio/edge_tts.py`: `EdgeTTS(BaseTool)` adapter supporting `WordBoundary` timestamps and EducAI `audio_timeline.json` compatibility.
  - Patched `vendor/openmontage/tools/video/hyperframes_compose.py`: Windows `cp1252` fallback, resilient timeout for `npx hyperframes` probe, explicit `encoding="utf-8", errors="replace"`.
  - Patched `vendor/openmontage/tools/analysis/composition_validator.py`: Respect `ffprobe` binary dependency.
  - Patched `vendor/openmontage/lib/config_model.py` and `vendor/openmontage/tools/cost_tracker.py`: Explicit UTF-8 on file reads/writes.
  - Patched `vendor/openmontage/tools/video/video_compose.py`: Graceful degradation when `remotion-composer` is omitted.

## 2. Patrick Hand Font (in `vendor/openmontage/ink-theater/mocap/patrickhand.ttf`)
- **Author:** Patrick Wagesreiter
- **License:** SIL Open Font License, Version 1.1 (OFL-1.1)

## 3. CMU Graphics Lab Motion Capture Database
- **Clips:** Stored in `vendor/openmontage/ink-theater/mocap/`
- **Source:** Carnegie Mellon University Motion Capture Database (`mocap.cs.cmu.edu`)
- **Terms:** Free for research and educational purposes.
