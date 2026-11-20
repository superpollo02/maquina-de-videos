# Estado de la Sesión - Continuación Próxima Vez

**Fecha:** 20 de Noviembre de 2026
**Proyecto:** Máquina de Videos · EducAI (`F:\proyectos antigrtavity\maquina de videos`)
**Repositorio GitHub:** [https://github.com/superpollo02/maquina-de-videos](https://github.com/superpollo02/maquina-de-videos) (rama `main`)

---

## 1. Integración OpenMontage + EducAI (Hitos M1, M2, M3, M4 Completados y Verificados)
- **Hito M1 (Plan):** Documento maestro arquitectónico en `docs/OPENMONTAGE_INTEGRATION_PLAN.md`.
- **Hito M2 (Runtime Aislado):**
  - Subconjuntos aprobados de OpenMontage integrados en `vendor/openmontage/` bajo AGPLv3 (`lib/`, `tools/`, `schemas/`, `styles/`, `pipeline_defs/`, `ink-theater/`, `backlot/`).
  - `THIRD_PARTY_LICENSES.md` y `vendor/openmontage/NOTICE` incorporados.
  - Parches Windows aplicados (`hyperframes_compose.py`, `composition_validator.py`, `config_model.py`, `cost_tracker.py`, `video_compose.py`).
  - Adaptador `EdgeTTS(BaseTool)` en `vendor/openmontage/tools/audio/edge_tts.py` con soporte de `WordBoundary` y generación de `audio_timeline.json` y `word_timings.json`.
  - Cadena resiliente de extracción PDF en `core/parsers/doc_parser.py` (`pypdf` -> `pymupdf` -> `pdfplumber`).
- **Hito M3 (Orquestador y QA):**
  - Paquete `core/orchestrator/`: `scene_builder.py`, `outro_mux.py`, `pipeline.py` (`EducAIPipeline`), `__main__.py` (`python -m core.orchestrator`).
  - Gates de control de calidad en `core/qa/`: `pre_render.py` (`validate_pre_render`) y `post_render.py` (`validate_post_render`).
  - `core/scorm/scorm_packager.py` actualizado con invariantes de `AGENTS.md` (`controlsList="nofullscreen"`, botón fullscreen `#player-container`, ventana 1.2s, `--strict-sync`, empaquetado Dual ZIP).
  - Documentación técnica operativa en `skills/*/SKILL.md` actualizada.
- **Hito M4 (Verificación E2E Cero Mocks):**
  - Suite completa de 15 pruebas pasando al 100% en `tests/unit/` y `tests/e2e/`.
  - Verificación live en headless Chrome del paquete SCORM generado.
  - Verificación de no-regresión de los 3 videos finales existentes en `films/`.

---

## 2. Videos Existentes en `films/`
1. **Video 1: La Estructura Tripartita del Aula**
   - `films/estructura-tripartita/Estructura_Tripartita_EducAI_Final.mp4` (80.3s, 1080p).
2. **Video 2: Protocolo de Relevamiento y Diagnóstico**
   - `films/protocolo-relevamiento/Protocolo_Relevamiento_EducAI_Final.mp4` (176s, 1080p).
3. **Video 3: Cuando el Trabajo Deja de Ser Necesario**
   - `films/cuando-el-trabajo-deja-de-ser-necesario/Cuando_El_Trabajo_Deja_De_Ser_Necesario_EducAI_Final.mp4` (414s, 1080p).
   - Paquetes SCORM generados: `Cuando_El_Trabajo_Deja_De_Ser_Necesario_SCORM_Completo.zip` y `Cuando_El_Trabajo_Deja_De_Ser_Necesario_SCORM.zip`.

---

## 3. Despliegue en GitHub
- Commit `a90f381` ("feat: integrar OpenMontage en vendor/openmontage, orquestador unificado core/orchestrator, gates QA y verificacion E2E") subido exitosamente a `origin/main`.
