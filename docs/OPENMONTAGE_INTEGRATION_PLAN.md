# Plan de Análisis e Integración: OpenMontage en `maquina de videos` (EducAI)

- **Estado:** Planificado (M1 — Requisito R1 / Criterio de Aceptación AC1)
- **Repositorio origen analizado:** `https://github.com/OpenMontageInc/OpenMontage.git` (commit `2e003e65fa99a0f329478a2c1cdcf26bc481933a`)
- **Proyecto destino:** `e:\proyectos antigrtavity\maquina de videos` (EducAI)
- **Alcance de este documento:** Análisis arquitectónico, matriz real de compatibilidad y especificación técnica ejecutable para las fases M2 (integración de runtime y herramientas), M3 (orquestador unificado, QA y SCORM 1.2) y M4 (verificación E2E sin mocks y no regresión).

---

## 1. Resumen Ejecutivo y Análisis Comparativo de Arquitectura

### 1.1 Comparación de Paradigmas: `maquina de videos` (EducAI) vs. `OpenMontage`

| Dimensión | `maquina de videos` (EducAI) | `OpenMontage` (`2e003e65`) | Sinergia de Integración |
|---|---|---|---|
| **Propósito principal** | Producción de video-clases educativas SCORM 1.2 para Moodle (`films/*/`). | Framework modular multi-pipeline de video por etapas, herramientas y QA automatizado. | EducAI conserva su dominio pedagógico/SCORM e incorpora motores locales de audio, subtítulos, HyperFrames, SVG/mocap, 3D y QA. |
| **Ingesta y branding** | `core/parsers/doc_parser.py` (`.pptx`, `.docx`, `.pdf`) y `core/brand_theme.py` (paleta de 8 colores + tipografía). | `styles/playbook_loader.py` + `lib/hyperframes_style_bridge.py` (`style_bridge` -> CSS vars + `design.md`). | `doc_parser` + `brand_theme` alimentan `scenes.json`, `edit_decisions` y `style_bridge`. |
| **Orquestación** | Scripts por película (`films/*/{build_audio,setup_renderer,render_frames,update_scorm_robust}.py`); `core/orchestrator/` actualmente vacío. | `lib/pipeline_loader.py` (`pipeline_defs/`), `lib/checkpoint.py`, `tools/tool_registry.py` (`BaseTool`, `CostTracker`). | `core/orchestrator/` unifica la ejecución sobre `ToolRegistry` manteniendo compatibilidad con el flujo por proyecto. |
| **Locución y mezcla de audio** | `edge-tts` (`es-AR-ElenaNeural`, `-2%`, pausa `0.55s`), `ffprobe`, música procedural mono `music.wav` + `amix`/`loudnorm`. | `tools/audio/audio_mixer.py` (`mix`, `duck`, `full_mix`, `segmented_music`, `loudnorm`), `tools/audio/tts_selector.py`, `piper_tts.py`. | Nuevo adaptador `EdgeTTS(BaseTool)` registrado en `ToolRegistry` + `AudioMixer` en estéreo (`-ac 2`) para compatibilidad con `ending_norm.mp4`. |
| **Render visual** | HTML5 Canvas determinista (`window.render(t)`) + `playwright-core` + caché en disco `frames/frame_%05d.png` + `video_raw.mp4`. | `HyperFramesCompose` (HTML/GSAP + `npx hyperframes`), `VideoCompose`, `InkTheater` (SVG + 12 clips mocap CMU), `ThreeJSWorld`, `remotion-composer` (diferido). | Soporte dual: modo `canvas` legado (preservando `window.render(t)` y reanudación desde `frames/`) + modos OpenMontage (`hyperframes`, `ink_theater`, `threejs`, `ffmpeg`). |
| **Validación y QA** | Checklists documentales en `skills/pre-render-composition-validator/` y `skills/post-render-video-qa/` + `AGENTS.md`. | `CompositionValidator` (`tools/analysis/composition_validator.py`) y `VisualQA` (`tools/analysis/visual_qa.py`). | `core/qa/pre_render.py` y `core/qa/post_render.py` convierten los checklists de `AGENTS.md`/`skills/` en gates ejecutables respaldados por OpenMontage. |
| **Empaquetado / Salida** | `ending_norm.mp4` concat + `core/scorm/scorm_packager.py` + `update_scorm_robust.py` (SCORM 1.2 Moodle). | `ExportBundle` (`tools/publishers/export_bundle.py`) + `Backlot` (`backlot/` FastAPI + SSE `:4750`). | `outro_mux.py` normaliza y concatena `ending_norm.mp4`; `ExportBundle` genera bundle de metadatos y `scorm_packager.py` emite Dual ZIP SCORM 1.2 alineado a `AGENTS.md`. |

### 1.2 Límites de Colisión y Aislamiento (`lemo-opuscar-antigravity-plugin.zip`, `skills/`, `AGENTS.md`)

Una inspección previa detectó tres vectores críticos de colisión si se extrajeran paquetes externos directamente en la raíz del repositorio:

1. **`lemo-opuscar-antigravity-plugin.zip` (`46,469,611` bytes, `548` entradas):**
   - Contiene en su raíz `core/` (`core/lib.js`, `core/audio/*`, `core/fonts/*`, `core/image/*`, `core/post/*`, `core/render/*`, `core/three/*`, `core/tts/*`), `package.json`, `package-lock.json`, `plugin.json`, `rules/AGENTS.md`, `skills/lemo-opuscar/SKILL.md` y `styles/*` (99 estilos).
   - **Regla de frontera:** Nunca descomprimir este archivo en la raíz de `maquina de videos`, porque sobrescribiría `package.json` (`playwright-core ^1.65.1`), `plugin.json` y se mezclaría con el paquete `core/` de EducAI (`brand_theme.py`, `parsers/`, `scorm/`, `orchestrator/`).
2. **Directorio `skills/` de EducAI (6 skills canónicas) vs. `OpenMontage/skills/` (158 archivos):**
   - `maquina de videos/skills/` contiene las 6 especificaciones operativas de EducAI:
     - `skills/raw-document-video-parser/SKILL.md`
     - `skills/modular-video-orchestrator/SKILL.md`
     - `skills/tiktok-word-captions/SKILL.md`
     - `skills/pre-render-composition-validator/SKILL.md`
     - `skills/post-render-video-qa/SKILL.md`
     - `skills/interactive-scorm-video-packager/SKILL.md`
   - OpenMontage incluye `skills/` (158 archivos), `.agents/` + `.claude/` + `.codex/` + `.cursor/` + `.github/` (1,451 archivos).
   - **Regla de frontera:** Excluir totalmente `skills/`, `.agents/`, `.claude/`, `.codex/`, `.cursor/` y `.github/` de OpenMontage al integrar. Ninguna skill existente de EducAI puede ser sobrescrita.
3. **`AGENTS.md` raíz de EducAI (22 líneas):**
   - Define las 4 invariantes obligatorias de producción EducAI (sincronía SCORM fin de locución + ventana `1.2s`, SCORM 1.2 Moodle `controlsList="nofullscreen"` + `#player-container` + Dual ZIP, reanudación desde `frames/`, y gates pre/post-render).
   - **Regla de frontera:** `AGENTS.md` de raíz permanece intacto; todos los módulos de OpenMontage se aíslan bajo **`vendor/openmontage/`** sin archivos IDE/agente en raíz.

---

## 2. Inventario Real de Módulos, Dependencias y Compatibilidad

### 2.1 Matriz de Runtimes Verificados en Host Windows

| Componente | Versión / Ruta Verificada en Host | Estado | Impacto en Integración |
|---|---|---|---|
| **Sistema Operativo** | Windows (AMD64, consola `cp1252` por defecto) | Activo | Requiere `encoding="utf-8", errors="replace"` explícito en subprocesos y apertura de archivos JSON/YAML. |
| **Python activo** | `3.14.3` (`tags/v3.14.3:323c59a`, MSC v.1944 64-bit, `C:\Users\arifi\AppData\Local\Python\pythoncore-3.14-64\python.exe`) | Activo (respaldos `uv`: `3.13.15` y `3.12.14`) | Todas las dependencias core/dev de OpenMontage resuelven a wheels `win_amd64` / `py3-none-any` sin compilar desde fuente; se mantiene `3.14.3`. |
| **Node.js / npm** | `Node v24.19.0` / `npm 11.17.0` | Activo | Compatible con `hyperframes` (`_NODE_FLOOR_MAJOR = 22`). **Incompatible** con `remotion-composer/package.json` (`^22.23.4 \|\| ^24.22.1 \|\| ^26.12.1`), por lo que Remotion queda diferido. |
| **FFmpeg / FFprobe** | `FFmpeg 9.0.2` y `FFprobe` en `PATH` | Activo | Requeridos por `AudioMixer`, `VideoCompose`, `HyperFramesCompose`, `CompositionValidator`, `VisualQA`, `EdgeTTS` y `outro_mux.py`. |
| **Google Chrome** | `C:\Program Files\Google\Chrome\Application\chrome.exe` | Activo | Usado por `playwright-core` (`render_frames.js` / QA) y por `hyperframes check` / render headless. |
| **Playwright** | `playwright-core ^1.65.1` (`package.json`) | Activo | Reutilizado para modo `canvas` y tests de navegador SCORM. |
| **HyperFrames CLI** | `hyperframes@0.9.71` (`%LOCALAPPDATA%\npm-cache\_npx\702923228c2ce1e6`) | Activo | `npx --yes hyperframes doctor --json` reporta `ok: true` en `Version` (`0.9.71`), `CLI binary`, `Node.js`, `FFmpeg`, `FFprobe` y `Chrome` (reporta `ok: false` en opcionales `whisper-cpp`, `TTS (Kokoro)` y `Docker running`). |

### 2.2 Módulos Actuales de `maquina de videos` (Rutas, Líneas y Hallazgos Reales)

1. **`core/brand_theme.py` (101 líneas):**
   - Firma pública: `extract_brand_theme(image_path, output_json=None)` (`:19`). CLI: posicional `image` y `--output`/`-o` (`default="theme_config.json"`, `:95-101`).
   - Algoritmo: abre imagen RGB, redimensiona a `(200, 200)` (`:22`), cuantiza a `colors=8, method=2` (`:25`), filtra candidatos por luminancia `0.08 < lum < 0.90` (`:39`), ordena por saturación (`:42-48`) y asigna `primary` (`#0284c7`), `secondary` (`#1e293b`), `alert` (`#ea580c` o rojo/naranja dominante) y `dark_neutral` (`#0f172a` o `lum < 0.20`) (`:51-66`).
   - Salida: `{"source_image", "palette": {primary, secondary, alert, dark_neutral, background, board_sheen}, "typography": {font_family, title_weight, body_weight, subtitles_bg, subtitles_text, subtitles_border}}` (`:68-86`). Dependencia: `Pillow 12.3.0`.
2. **`core/parsers/doc_parser.py` (126 líneas):**
   - Funciones: `parse_pptx(file_path)` (`:13-51`), `parse_docx(file_path)` (`:53-79`; nota: inicializa `"tables": []` en `:57,:67` sin extraer `doc.tables`), `parse_pdf(file_path)` (`:81-100`), `parse_document(input_path, output_json=None)` (`:102-118`). CLI: posicional `input` y `--output`/`-o` (`default="raw_extracted.json"`, `:120-126`).
   - **Bloqueante detectado en línea 82:** `parse_pdf()` ejecuta `from pypdf import PdfReader` de forma incondicional, lanzando `ModuleNotFoundError: No module named 'pypdf'` en el entorno Python 3.14.3 actual. Sin embargo, ya están instalados **`PyMuPDF 1.28.2`** (`import pymupdf` limpio; `import fitz` emite warning de deprecación) y **`pdfplumber 0.11.10`**.
3. **`core/scorm/scorm_packager.py` (340 líneas) vs. `films/cuando-el-trabajo-deja-de-ser-necesario/update_scorm_robust.py` (499 líneas) y `AGENTS.md`:**
   - Firma actual: `build_scorm_package(title, video_url, checkpoints, output_zip)` (`:309`), CLI `--title`, `--video-url`, `--checkpoints-json`, `--output`/`-o` (`:331-334`).
   - **6 divergencias respecto a `AGENTS.md` (presentes en `update_scorm_robust.py` y `pack_scorm_complete.py`):**
     1. `:152` usa `<video id="video-elem" controls playsinline>` sin `controlsList="nofullscreen"`.
     2. Carece de `#player-container:fullscreen` / `:-webkit-full-screen` y del botón `#btn-fullscreen` sobre el contenedor.
     3. Solo tiene `#score-bar` (`:151`), sin `#header-bar` ni `#next-checkpoint-info` (`Próxima Pregunta: <Sección> (en MM:SS)`).
     4. `:219` evalúa `Math.abs(curT - cp.timestamp) < 0.6` en lugar de la ventana amplia `curT >= cp.timestamp && curT <= cp.timestamp + 1.2` (`update_scorm_robust.py:390`).
     5. `:58` usa `#overlay { z-index: 50 }` (vs `z-index: 100` en `update_scorm_robust.py:124`) y `:270` `btnContinue.style.display = 'block'` (vs `'inline-block'`).
     6. `:303` declara únicamente `<file href="index.html"/>` en `imsmanifest.xml` y `:321-323` solo genera el ZIP Zero-Weight, sin modo Dual (`*_SCORM.zip` + `*_SCORM_Completo.zip` con `<file href="{video_name}"/>` y el `.mp4` incluido).
4. **`films/cuando-el-trabajo-deja-de-ser-necesario/test_browser_scorm.js` (65 líneas):**
   - Línea `34` fija `v.currentTime = 96.6;` (originado en `build_audio.py:168`: `round(sc["start"] + sc["duration"] * 0.75, 1)` guardado en `scorm_checkpoints.json:4`).
   - `update_scorm_robust.py:9,280,390` trasladó el primer checkpoint al final real de la escena (`110.4` = `110.35s` fin de `scene_02` + `0.05s`) con disparo `curT >= 110.4`. Por ello `96.6` no dispara `#overlay` y provoca timeout en línea `52` (`.option-btn:nth-child(2)`). Además `test_browser_scorm.js:13` escribe/borra `test_scorm_runner.html` dentro de `films/`.
5. **`core/orchestrator/` y estructura `core/`:**
   - `core/orchestrator/` existe pero está vacío; `core/` no tiene archivos `__init__.py`.
6. **Contrato de Media, Timeline y Concatenación con `ending_norm.mp4`:**
   - `films/estructura-tripartita/ending_norm.mp4`: video `h264 High L4.0`, `1920x1080`, `SAR 1:1`, `DAR 16:9`, `yuv420p`, `24/1 fps`, `time_base 1/12288`, `10.000s` (`240` frames); audio `aac LC`, `44100 Hz`, **`channels: 2` (`stereo`)**, `10.005011s`. (Nota: el archivo raíz `ending. educai.mp4` es `1280x720` `48000 Hz` stereo y no es compatible con `-c copy`).
   - `films/cuando-el-trabajo-deja-de-ser-necesario/audio_mixed.m4a`: `aac LC`, `44100 Hz`, **`channels: 1` (`mono`)**, `404.051973s` (porque `build_audio.py:133` genera `music.wav` mono con `setnchannels(1)`). Al concatenar con `-f concat -c copy` contra `ending_norm.mp4` (estéreo), el MP4 resultante queda con streams mixtos mono/estéreo bajo metadata `1 channel (mono)`.
   - `render_frames.js` (67 líneas): `fps = 24`, viewport `1920x1080`, loop reanudable que omite `frames/frame_XXXXX.png` existentes, evalúa `window.render(currT)` y codifica `video_raw.mp4` con `libx264 -pix_fmt yuv420p -preset fast -crf 18`.

### 2.3 Inventario de OpenMontage (`commit 2e003e65`)

| Subdirectorio / Archivo | Cantidad | Contenido clave | Clasificación |
|---|---|---|---|
| `lib/` | 21 | `paths.py`, `asset_cache.py`, `config_model.py`, `checkpoint.py`, `pipeline_loader.py`, `media_profiles.py`, `hyperframes_style_bridge.py`, `events.py`, `scoring.py`. Todos usan imports top-level (`from lib...`, `from schemas...`, `from styles...`). | **Requerido** |
| `tools/` | 236 | `BaseTool`, `ToolRegistry` (`164` herramientas, `38+` locales sin API key), `CostTracker`, `audio_mixer`, `tts_selector`, `piper_tts`, `subtitle_gen`, `video_compose`, `hyperframes_compose`, `composition_validator`, `visual_qa`, `threejs_world` (+ `graphics/templates/threejs_world/`), `export_bundle`, `stock_sources`, `character_animation`. | **Requerido** |
| `schemas/` | 35 | Esquemas JSON validados por `checkpoint.py`, `pipeline_loader.py`, `playbook_loader.py` y `export_bundle.py`. | **Requerido** |
| `styles/` | 7 | `playbook_loader.py` y definiciones de playbooks usados por `checkpoint.py`, `video_compose.py` y `hyperframes_style_bridge.py`. | **Requerido** |
| `pipeline_defs/` | 13 | Manifiestos YAML de pipelines cargados por `lib/pipeline_loader.py`. | **Requerido** |
| `config.yaml`, `LICENSE`, `setup.py`, `requirements.txt` | 4 | Configuración base, licencia AGPLv3, metadata y dependencias. | **Requerido** |
| `ink-theater/` | 30 | `ink-theater.js` (`window.InkTheater`), `ink-puppet.js` (`window.InkPuppet`), `mocap/{bvh2clip.mjs,add-motion.mjs}`, 12 clips CMU (`30 fps`, `520 px`) y fuente `patrickhand.ttf` (OFL 1.1). | **Opcional (Recomendado)** |
| `backlot/` | 11 | Servidor FastAPI + SSE (`127.0.0.1:4750`) para tablero de proyectos, `TrustedHostMiddleware`, `watchfiles.awatch` opcional con fallback manual. | **Opcional** |
| `scripts/` | 10 | Utilidades como `scaffold_atelier_project.py` y `backlot_simulate_run.py`. | **Opcional (Selectivo)** |
| `remotion-composer/` | 50 | Proyecto React/Remotion (`openmontage-remotion-composer@1.0.0`). Requiere Node `^22.23.4 \|\| ^24.22.1 \|\| ^26.12.1` (host actual: `v24.19.0`). | **Diferido** |
| `skills/`, `.agents/`, `.claude/`, `.codex/`, `.cursor/`, `.github/`, raíz IDE (`AGENTS.md`, `CLAUDE.md`, `docs/`, `tests/`, `assets/`, `requirements-gpu.txt`, etc.) | ~1,848 | Packs de agentes IDE, duplicados de skills globales, guías, tests upstream y manifiesto PyTorch GPU. | **Excluido** del repo runtime (tests upstream usables solo como referencia de contratos). |

### 2.4 Auditoría de Dependencias Python 3.14.3

Verificado mediante `importlib.metadata.version()` y `python -B -m pip install --dry-run --quiet --ignore-installed ... --report -` sobre Python 3.14.3 Windows x64:

| Paquete | Requisito | Instalado en Host | Wheel PyPI Windows x64 / Pure-Python | Acción en M2 (`pyproject.toml`) |
|---|---|---|---|---|
| `pyyaml` | `>=6.0` | `6.0.3` | Satisfecho | Fijar `pyyaml>=6.0` |
| `pydantic` | `>=2.0` | `2.13.5` | Satisfecho | Fijar `pydantic>=2.0` |
| `jsonschema` | `>=4.20` | `4.26.0` | Satisfecho | Fijar `jsonschema>=4.20` |
| `python-dotenv` | `>=1.0` | `1.2.3` | Satisfecho | Fijar `python-dotenv>=1.0` |
| `Pillow` | `>=10.0` | `12.3.0` | Satisfecho | Fijar `Pillow>=10.0` |
| `numpy` | `>=1.24` | `2.5.3` | Satisfecho | Fijar `numpy>=1.24` |
| `requests` | `>=2.31` | `2.34.2` | Satisfecho | Fijar `requests>=2.31` |
| `certifi` | `>=2026.10.19` | **`2026.7.22` (desactualizado)** | `certifi==2026.10.23` (`py3-none-any`) | Actualizar a `certifi>=2026.10.19` |
| `google-auth` | `>=2.0` | `2.58.1` | Satisfecho | Fijar `google-auth>=2.0` |
| `google-genai` / `openai` | `>=1.0.0` / `>=2.44.0` | `2.25.0` / `2.54.0` | Satisfecho | Extra `[cloud]` o core |
| `fastapi` / `uvicorn` / `websockets` | `>=0.110` / `>=0.29` / `>=14.0` | `0.141.1` / `0.53.0` / `16.1.1` | Satisfecho | Extra `[backlot]` |
| `watchfiles` | `>=0.21` | **No instalado** | `watchfiles==1.3.0` (`cp310-abi3-win_amd64`) | Instalar (`[backlot]` / core) |
| `pythainlp` | `>=5.0` | **No instalado** | `pythainlp==5.4.0` (`py3-none-any`) | Instalar o aislar en `requirements` |
| `pytest` / `pytest-asyncio` / `httpx` | `>=8.0` / `>=0.23` / `>=0.24` | No / No / `0.28.1` | `pytest==9.2.0`, `pytest-asyncio==1.5.0` (`py3-none-any`) | Instalar en `[dev]` |
| `pypdf` | `doc_parser.py:82` | **No instalado** | `pypdf==7.1.1` (`py3-none-any`) | Instalar `pypdf>=5.0` y además implementar fallback `pymupdf` (`1.28.2`) / `pdfplumber` (`0.11.10`) |
| `edge-tts` / `python-pptx` / `python-docx` / `pydub` | EducAI core | `7.3.1` / `1.0.2` / `1.2.0` / `0.25.1` | Satisfecho | Fijar en `pyproject.toml` |
| `piper-tts` | TTS local opcional | **No instalado** | `piper-tts==1.8.0` (`cp39-abi3-win_amd64` + `onnxruntime==1.32.0`) | Opcional `[local-tts]` |

### 2.5 Bugs y Quirks Exactos Verificados en Windows

1. **`tools/video/hyperframes_compose.py`:**
   - `_probe_cli()` (líneas `361-396`, fallo en línea **`382`**): ejecuta `subprocess.run([npx, "--yes", cls._NPM_PACKAGE, "doctor", "--json"], capture_output=True, text=True, timeout=20)`. En caché `npx` fría el timeout de `20s` expira y `get_status()` marca la herramienta como `UNAVAILABLE`.
   - `_run_hf()` (líneas **`1404-1411`**) y los helpers `_node_major_version()` (`:262`), `_resolve_npm_package()` (`:309`), `_cached_cli_version()` (`:350`) y `_probe_cli()` (`:381`) llaman `subprocess.run(..., text=True)` **sin `encoding="utf-8", errors="replace"`**, provocando `UnicodeDecodeError` bajo `cp1252` ante salida UTF-8 de `hyperframes`.
   - Además, `npx --yes hyperframes doctor --json` retorna `"ok": false` global cuando `whisper-cpp`, `TTS (Kokoro)` o `Docker` opcionales no están instalados aunque `Node.js`, `FFmpeg`, `FFprobe`, `Chrome` y `CLI binary` reporten `"ok": true`. El parser de estado debe evaluar los checks requeridos (`CLI binary`, `Node.js`, `FFmpeg`, `FFprobe`, `Chrome`) y no fallar por opcionales.
2. **`tools/analysis/composition_validator.py` (líneas `89-90`):**
   - `CompositionValidator.get_status()` está sobrescrito para devolver `ToolStatus.AVAILABLE` de forma incondicional, ignorando `dependencies = ["binary:ffprobe"]`. En M2 debe respetar la verificación de `ffprobe` (o delegar en `super().get_status()`).
3. **`lib/config_model.py:81` y `tools/cost_tracker.py:502, 506`:**
   - Usan `open(...)` sin `encoding="utf-8"`, vulnerable a textos en español/acentos en Windows (`cp1252`).
4. **`tools/video/video_compose.py`:**
   - Hardcodea la ruta a `remotion-composer` via `Path(__file__).resolve().parent.parent.parent / "remotion-composer"` en `_remotion_available()`, `_remotion_render()` y `_render_via_atelier()` (líneas **`270, 326, 1022, 2057`**). Al diferirse `remotion-composer`, `VideoCompose` debe degradar limpiamente a `False` sin lanzar excepción cuando el directorio no tenga `node_modules`.
   - `_has_audio_stream()` (`:410`) y `_run_final_review()` (líneas **`2406, 2501, 2542, 2697`**) invocan `ffprobe`/`ffmpeg` directamente sin `self.run_command()` ni `encoding="utf-8", errors="replace"`.
5. **`edge_tts 7.3.1` (`inspect.signature(edge_tts.Communicate.__init__)`):**
   - El parámetro `boundary` tiene valor por defecto **`'SentenceBoundary'`**, no `'WordBoundary'`. Si no se pasa `boundary="WordBoundary"` de forma explícita, no se emiten eventos por palabra para subtítulos/captions sincronizados (actualmente `skills/tiktok-word-captions/SKILL.md:32` también lo omite).

### 2.6 Análisis Legal y de Frontera Técnica: Licencia AGPLv3

OpenMontage se distribuye bajo **GNU Affero General Public License v3 (AGPLv3)** (`LICENSE`, 661 líneas, versión del 19 de noviembre de 2007):

- **Sec. 4 (`LICENSE:183-194`):** La distribución literal requiere mantener intactos los avisos de copyright, licencia y garantía, y entregar copia de `LICENSE`.
- **Sec. 5 (`LICENSE:196-231`):** Toda versión modificada debe portar avisos prominentes de modificación con fecha (`:202-203`), avisos de liberación bajo AGPLv3 (`:205-208`), licenciar el trabajo combinado completo bajo AGPLv3 (`:210-216`) y conservar avisos legales en interfaces de usuario (`:218-221`). El concepto de *aggregate* (`:223-231`) no extiende el copyleft a programas independientes almacenados al lado, pero la importación en proceso desde `core/orchestrator/` hacia `vendor/openmontage/` sí vincula ambos en un mismo programa.
- **Sec. 6 (`LICENSE:233-283`):** Exige acompañar distribuciones no-fuente con el *Corresponding Source*.
- **Sec. 13 (`LICENSE:540-559`):** Si se modifica el software y se permite que usuarios externos interactúen con él remotamente a través de una red (por ejemplo, exponiendo `backlot/` o una API web multiusuario), se debe ofrecer el *Corresponding Source* del conjunto combinado gratuitamente por red.
- **Implicancias prácticas para EducAI:**
  1. **Uso interno de producción:** Ejecutar el pipeline localmente para producir archivos `.mp4` y paquetes SCORM 1.2 (`.zip` con HTML/JS propio de `scorm_packager.py`) no constituye distribución de código fuente/binario ni servicio en red AGPLv3 sobre los videos resultantes.
  2. **Distribución o SaaS en red:** Si en el futuro se distribuye la herramienta completa a terceros o se expone como servicio web/SaaS (`backlot/` o API remota), la combinación `core/orchestrator/` + `vendor/openmontage/` queda sujeta a AGPLv3 (Sec. 5 y Sec. 13).
  3. **Cumplimiento obligatorio en M2:** Conservar `vendor/openmontage/LICENSE` verbatim, crear `vendor/openmontage/NOTICE` y `THIRD_PARTY_LICENSES.md` en raíz registrando el origen (`commit 2e003e65`), la licencia AGPLv3 y cada archivo nuevo o parcheado dentro de `vendor/openmontage/` (`tools/audio/edge_tts.py`, parches UTF-8/timeout Windows) con fecha y descripción.

---

## 3. Arquitectura de Integración para M2 y M3

```
[Entrada: .pptx / .docx / .pdf + logo/imagen]
       │
       ├──► core/parsers/doc_parser.py (pypdf -> pymupdf -> pdfplumber)
       └──► core/brand_theme.py (paleta 8 colores + tipografía)
                     │
                     ▼
        core/orchestrator/scene_builder.py
        ├──► scenes.json (esquema EducAI preservado)
        └──► playbook / edit_decisions ──► lib.hyperframes_style_bridge.style_bridge()
                     │
                     ▼
        core/orchestrator/pipeline.py (EducAIPipeline + _openmontage_env.py)
        ├──► ToolRegistry ("edge_tts") ──► audio_timeline.json + word_timings.json + scene_XX.mp3
        ├──► ToolRegistry ("subtitle_gen") ──► .srt / .vtt / .caption.json
        ├──► ToolRegistry ("audio_mixer": full_mix / loudnorm -16 LUFS, -ac 2 stereo 44.1kHz)
        │
        ├──► core/qa/pre_render.py (CompositionValidator + AGENTS.md + Playwright 5 pts + SCORM sync)
        │
        ├──► Backend Visual (pluggable):
        │      ├── "canvas"       -> Playwright window.render(t) + caché frames/ + video_raw.mp4
        │      ├── "hyperframes"  -> ToolRegistry ("hyperframes_compose")
        │      ├── "ink_theater"  -> ink-theater.js / ink-puppet.js sobre HyperFrames/GSAP
        │      ├── "threejs"      -> ToolRegistry ("threejs_world")
        │      └── "ffmpeg"       -> ToolRegistry ("video_compose")
        │
        ├──► core/orchestrator/outro_mux.py
        │      └── Mux video + audio_mixed.m4a (stereo 44.1kHz) + concat ending_norm.mp4 -> *_EducAI_Final.mp4
        │
        ├──► core/qa/post_render.py (VisualQA + ffprobe + silencedetect + luma keyframes)
        │
        └──► Salida Dual:
               ├── ToolRegistry ("export_bundle") -> video/ + metadata/ + thumbnails/
               └── core/scorm/scorm_packager.py -> *_SCORM.zip + *_SCORM_Completo.zip
```

### 3.1 Ubicación y Resolución de Paquetes (`vendor/openmontage/`)

- **Ubicación:** Todos los artefactos adoptados de OpenMontage se alojan exclusivamente bajo `e:\proyectos antigrtavity\maquina de videos\vendor\openmontage\`:
  - **Incluidos:** `lib/`, `tools/` (incluyendo `tools/graphics/templates/`), `schemas/`, `styles/`, `pipeline_defs/`, `config.yaml`, `LICENSE`, `NOTICE`, `setup.py`, `requirements.txt`.
  - **Opcionales incluidos:** `ink-theater/`, `backlot/`, `scripts/` selectivos (`scaffold_atelier_project.py`, `backlot_simulate_run.py`).
  - **Diferidos:** `remotion-composer/` (no ejecutar `npm install` hasta actualizar Node a `>=24.22.1`).
  - **Excluidos:** `skills/`, `.agents/`, `.claude/`, `.codex/`, `.cursor/`, `.github/`, `AGENTS.md`, `CLAUDE.md`, `CODEX.md`, `COPILOT.md`, `CURSOR.md`, `.windsurfrules`, `AGENT_GUIDE.md`, `PROJECT_CONTEXT.md`, `PROMPT_GALLERY.md`, `README*.md`, `CONTRIBUTING.md`, `Makefile`, `render_demo.py`, `render-demo.sh`, `diagram.png`, `requirements-gpu.txt`, `assets/`, `docs/`, `tests/`.
- **Resolución de imports (`from lib...`, `from tools...`, `from schemas...`, `from styles...`, `from backlot...`):**
  - OpenMontage usa exclusivamente imports absolutos desde su raíz (`lib/__init__.py` y `tools/__init__.py` tienen 0 bytes, y `ToolRegistry.discover()` usa `pkgutil.walk_packages` sobre `tools`).
  - Para evitar reescrituras masivas de 243+ archivos Python:
    1. `core/orchestrator/_openmontage_env.py` inserta `str(Path(__file__).resolve().parents[2] / "vendor" / "openmontage")` al inicio de `sys.path` de forma idempotente antes de importar `lib` o `tools`.
    2. `pyproject.toml` declara `[tool.pytest.ini_options] pythonpath = [".", "vendor/openmontage"]` y, opcionalmente, `.venv` instala `vendor/openmontage` en modo editable (`pip install -e vendor/openmontage --no-deps`).
- **Aislamiento de proyectos y caché:**
  - `lib/paths.py:17` lee `OPENMONTAGE_PROJECTS_DIR` (por defecto `REPO_ROOT / "projects"`). `_openmontage_env.py` fija por defecto `OPENMONTAGE_PROJECTS_DIR` hacia una ruta dedicada de trabajo/film (por ejemplo `films/` o el directorio de trabajo del proyecto activo) para no contaminar `vendor/openmontage/`.
  - `lib/asset_cache.py:93-130` lee `OPENMONTAGE_ASSET_CACHE` y `OPENMONTAGE_ASSET_CACHE_DIR`, permitiendo activar caché determinista compartida sin alterar código upstream.

### 3.2 Adaptador `EdgeTTS(BaseTool)` (`vendor/openmontage/tools/audio/edge_tts.py`)

En `vendor/openmontage/tools/audio/` **no existe** una clase base `AudioTool`; los adaptadores (como `PiperTTS` en `tools/audio/piper_tts.py:26-178`) heredan directamente de `BaseTool` (`tools/base_tool.py`).

- **Contrato de clase:**
  - Archivo: `vendor/openmontage/tools/audio/edge_tts.py`
  - Clase: `EdgeTTS(BaseTool)`
  - Atributos de registro:
    - `name = "edge_tts"`
    - `tier = ToolTier.VOICE`
    - `capability = "tts"`
    - `provider = "edge_tts"`
    - `runtime = ToolRuntime.API`
    - `dependencies = ["python:edge_tts", "cmd:ffprobe"]`
    - `resource_profile = ResourceProfile(network_required=True)`
- **Autodescubrimiento:** `ToolRegistry.discover("tools")` (`tools/tool_registry.py:119-135`) importa todos los submódulos de `tools` y registra toda subclase concreta de `BaseTool`. `TTSSelector._providers()` (`tools/audio/tts_selector.py:176-181`) consulta automáticamente toda herramienta registrada con `capability == "tts"`, por lo que `EdgeTTS` queda disponible tanto en `registry.get("edge_tts")` como en `TTSSelector` **sin modificar `tts_selector.py`**.
- **Comportamiento de síntesis y tiempos:**
  - Parámetros por defecto EducAI: `voice = "es-AR-ElenaNeural"`, `rate = "-2%"`, `inter_scene_pause = 0.55`, `emit_word_boundaries = True`.
  - **Corrección obligatoria para `edge-tts 7.3.1`:** instanciar `edge_tts.Communicate(text, voice, rate=rate, pitch=pitch, volume=volume, boundary="WordBoundary" if emit_word_boundaries else "SentenceBoundary")`.
  - Consumir el stream asíncrono (`async for chunk in communicate.stream()`) capturando chunks `"audio"` hacia `.mp3` y chunks `"WordBoundary"` convirtiendo ticks de 100ns (`chunk["offset"] / 10_000_000`, `chunk["duration"] / 10_000_000`) hacia `word_timings.json`. Usar ejecución `asyncio` segura (hilo dedicado si ya existe un event loop corriendo, como en `pytest-asyncio` o FastAPI).
  - Medir duración real del `.mp3` resultante mediante `ffprobe` (via `self.run_command(...)` para heredar UTF-8 en Windows) y acumular `total_time += duration + inter_scene_pause` (`0.55s`).
  - Soportar modo texto único (`text`, `output_path`) y modo batch multi-escena (`scenes`, `output_dir`) emitiendo `audio_timeline.json` con el esquema exacto heredado de `build_audio.py`:
    `{"total_duration": float, "scenes": [{"scene_id", "order", "title", "mp3_file", "start", "duration", "end", "voiceover_script", "screen_elements", "checkpoints"}]}`.
  - Retornar `ToolResult(success=True, data={"audio_path", "duration", "timeline", "word_timings_path"}, artifacts=[...], cost_usd=0.0)`.

### 3.3 Fix de `core/parsers/doc_parser.py`

Mantener intacta la firma `parse_document(input_path, output_json=None)` (`:102`), el CLI (`input`, `--output`/`-o`) y los esquemas JSON de retorno de `.pptx`, `.docx` y `.pdf`.

En `parse_pdf(file_path)` (`core/parsers/doc_parser.py:81-100`), reemplazar la importación rígida de la línea `82` (`from pypdf import PdfReader`) por una cadena de extracción con fallback manteniendo exactamente la lógica de división por líneas (`:88-93`) y el contrato `{"source_type": "pdf", "file_name": ..., "total_items": ..., "sections": [{"page_number", "title", "paragraphs"}]}`:

1. Intentar `from pypdf import PdfReader` (si está instalado en `.venv`).
2. Si lanza `ImportError`, usar `import pymupdf` (`PyMuPDF 1.28.2`, sin usar `import fitz` para evitar deprecation warning): `with pymupdf.open(file_path) as doc: [page.get_text("text") or "" for page in doc]`.
3. Si no está disponible o falla, usar `import pdfplumber` (`0.11.10`): `with pdfplumber.open(file_path) as pdf: [page.extract_text() or "" for page in pdf.pages]`.

### 3.4 Orquestador Unificado (`core/orchestrator/`)

Agregar `core/__init__.py` y `core/orchestrator/__init__.py` más cuatro módulos acotados:

1. **`core/orchestrator/_openmontage_env.py`:**
   - Inserta `vendor/openmontage` en `sys.path` de manera idempotente.
   - Configura `PYTHONIOENCODING=utf-8`, `OPENMONTAGE_PROJECTS_DIR` y `OPENMONTAGE_ASSET_CACHE`.
   - Expone `get_registry() -> ToolRegistry` llamando `registry.ensure_discovered()`.
2. **`core/orchestrator/scene_builder.py`:**
   - Consume `parse_document()` (`core/parsers/doc_parser.py`) y `extract_brand_theme()` (`core/brand_theme.py`).
   - Construye `scenes.json` compatible con EducAI y un diccionario `playbook` + `edit_decisions` compatible con `lib.hyperframes_style_bridge.style_bridge(playbook, edit_decisions)` (inyectando `primary`, `secondary`, `alert`, `dark_neutral`, `background` y `font_family`).
   - Recalcula cualquier checkpoint SCORM sobre el `end` real de `audio_timeline.json` (`end + 0.05..0.1s`, eliminando la fórmula heredada `start + duration * 0.75` de `build_audio.py:168`).
3. **`core/orchestrator/pipeline.py` (`EducAIPipeline` y CLI `python -m core.orchestrator`):**
   - Ejecuta la secuencia completa mediante `ToolRegistry` y checkpoints de `lib.checkpoint` (opcional por proyecto):
     1. **Ingesta:** `doc_parser` + `brand_theme` -> `scenes.json` + tokens de estilo.
     2. **Locución y Subtítulos:** `registry.get("edge_tts").execute(...)` -> `audio_timeline.json`, `word_timings.json`, `scene_XX.mp3`; opcional `registry.get("subtitle_gen").execute(...)` -> `.srt`/`.vtt`/`.caption.json`.
     3. **Mezcla Estéreo Normalizada:** `registry.get("audio_mixer").execute(operation="full_mix", ...)` con `loudnorm_target=-16` (`normalize=True`), garantizando salida AAC `44100 Hz` **estéreo (`-ac 2`)** para empatar exactamente con `ending_norm.mp4`.
     4. **Gate Pre-Render:** llamada obligatoria a `core/qa/pre_render.py`.
     5. **Render Visual (backend seleccionable):**
        - `canvas` (legado EducAI): `window.render(t)` a 24 fps (`1920x1080`) con `playwright-core`; aplica `AGENTS.md` §3 verificando `frames/frame_%05d.png` existentes antes de re-renderizar o recodificar `video_raw.mp4`.
        - `hyperframes`: `registry.get("hyperframes_compose").execute(...)` alimentado por `style_bridge()`.
        - `ink_theater`: composición HyperFrames/GSAP enlazando `vendor/openmontage/ink-theater/{ink-theater.js,ink-puppet.js}` y clips mocap.
        - `threejs`: `registry.get("threejs_world").execute(...)` para escenas 3D deterministas.
        - `ffmpeg`: `registry.get("video_compose").execute(...)`.
     6. **Mux + Outro (`outro_mux.py`):** multiplexa `video_raw.mp4` + `audio_mixed.m4a` y concatena `films/estructura-tripartita/ending_norm.mp4`.
     7. **Gate Post-Render:** llamada obligatoria a `core/qa/post_render.py`.
     8. **Publicación y SCORM:** `registry.get("export_bundle").execute(...)` + `build_scorm_package(...)` (Dual ZIP).
4. **`core/orchestrator/outro_mux.py`:**
   - Normaliza el video principal al contrato exacto de `films/estructura-tripartita/ending_norm.mp4` (`h264 High L4.0`, `1920x1080`, `SAR 1:1`, `yuv420p`, `24/1 fps`, `aac 44100 Hz stereo 2ch`) antes de ejecutar `ffmpeg -f concat -safe 0 -i concat_list.txt -c copy` (o usa `concat` por filtro si se solicita una resolución distinta, ej. `1080x1920` vertical), garantizando cero streams mixtos mono/estéreo.

### 3.5 Gates Ejecutables (`core/qa/`)

1. **`core/qa/pre_render.py` (`validate_pre_render`):**
   - Ejecuta `registry.get("composition_validator").execute(...)` cuando exista `composition_path`/manifiesto OpenMontage.
   - Ejecuta las reglas programáticas de `skills/pre-render-composition-validator/SKILL.md` y `AGENTS.md` §1/§4:
     - Verifica existencia y tamaño `> 0` de `index.html` (o workspace HyperFrames), `audio_mixed.m4a`, `audio_timeline.json`, `ending_norm.mp4` y assets referenciados.
     - Compara duración real de `audio_mixed.m4a` vía `ffprobe` contra `audio_timeline.json["total_duration"]` (`<= 0.5s`) y contra duración de render (`>= audio_dur - 0.5s`).
     - En modo `canvas`: inspecciona `index.html` buscando usos prohibidos de `Date.now()` / `Math.random()` / `requestAnimationFrame` no deterministas dentro de `window.render`, y abre headless Chrome (`playwright-core`) evaluando 5 timestamps (`0`, `0.25*d`, `0.5*d`, `0.75*d`, `max(0, d-0.1)`) exigiendo `0` `pageerror` y `0` `console.error`.
     - En modo `hyperframes`: ejecuta `HyperFramesCompose` operaciones `lint` y `check`.
     - Si existen `scorm_checkpoints.json`, valida que cada `cp["timestamp"]` caiga en `[scene["end"], scene["end"] + 0.2]` (nunca en medio de una alocución).
2. **`core/qa/post_render.py` (`validate_post_render`):**
   - Ejecuta `registry.get("visual_qa").execute(operation="probe", ...)` + `"review"` + `"audio_levels"` (`tools/analysis/visual_qa.py`).
   - Implementa los checks de `skills/post-render-video-qa/SKILL.md`:
     - `ffprobe`: exactamente 1 stream video (`h264`, `yuv420p`, `1920x1080` o `1080x1920`) y 1 stream audio (`aac`, `44100 Hz`, `2 channels`), duración dentro de `+-1.0s` de `contenido + ending`.
     - `ffmpeg -af silencedetect=noise=-35dB:d=0.4 -f null -`: verifica pausas naturales entre escenas sin cortes abruptos al final.
     - Extracción temporal de keyframes (`fps=1/30` + límites de escena + frame del outro) verificando ausencia de frames negros/vacíos por luma y limpiando la carpeta temporal al finalizar.

### 3.6 Alineación SCORM 1.2 (`core/scorm/scorm_packager.py`)

Actualizar `core/scorm/scorm_packager.py` preservando compatibilidad 100% hacia atrás con los 4 parámetros posicionales actuales (`title, video_url, checkpoints, output_zip`) y los flags CLI actuales (`--title`, `--video-url`, `--checkpoints-json`, `--output`/`-o`):

- **Nueva firma extendida:**
  `build_scorm_package(title, video_url, checkpoints, output_zip, *, include_video_file=None, audio_timeline_path=None, strict_sync=False, theme=None, also_build_zero_weight=False)`
- **Flags CLI opcionales nuevos:** `--include-video`, `--audio-timeline`, `--strict-sync`, `--dual-zip`.
- **Invariantes absorbidas de `AGENTS.md` y `update_scorm_robust.py` en `SCORM_HTML_TEMPLATE` y `MANIFEST_XML`:**
  1. `<video id="video-elem" controls controlsList="nofullscreen" playsinline>` (`AGENTS.md:9`).
  2. `#player-container:fullscreen` / `:-webkit-full-screen` + botón `#btn-fullscreen` llamando `requestFullscreen()` sobre `#player-container` (`#overlay` con `z-index: 100`), evitando que el video nativo tape las preguntas.
  3. Barra superior `#header-bar` permanente con `#next-checkpoint-info` (`Próxima Pregunta: <span id="checkpoint-label">`) actualizado dinámicamente con `section_title` y `MM:SS`, más `#section-badge`.
  4. Listener `timeupdate` con ventana `curT >= cp.timestamp && curT <= cp.timestamp + 1.2` (`AGENTS.md:5`).
  5. Validación opcional `--strict-sync` contra `audio_timeline_path` para rechazar checkpoints que corten una alocución antes de `scene["end"]`.
  6. `imsmanifest.xml`: cuando `include_video_file` se provee, añade `<file href="{basename}"/>` dentro de `<resource>` y empaqueta el `.mp4` con `<source src="{basename}">` (`*_SCORM_Completo.zip`); cuando es `None`, emite paquete Zero-Weight (`*_SCORM.zip`, `< 500 KB`) apuntando a `video_url`. Con `--dual-zip` emite ambos archivos en una sola invocación.

### 3.7 Actualización Documental en `skills/` durante M3

- En M3, actualizar **únicamente** las referencias operativas dentro de `skills/modular-video-orchestrator/SKILL.md`, `skills/tiktok-word-captions/SKILL.md` (documentar `boundary="WordBoundary"` explícito para `edge-tts 7.3.1`), `skills/pre-render-composition-validator/SKILL.md`, `skills/post-render-video-qa/SKILL.md` y `skills/interactive-scorm-video-packager/SKILL.md` para referenciar `python -m core.orchestrator`, `core/qa/{pre_render,post_render}.py` y los nuevos flags de `core/scorm/scorm_packager.py`.
- No importar ni copiar `skills/` de OpenMontage hacia `maquina de videos/skills/`, ni modificar las reglas nucleares de `AGENTS.md`.

---

## 4. Hoja de Ruta (M2–M4), Estrategia de Verificación Reproducible (Cero Mocks) y Plan de Rollback / No Regresión

### 4.1 Hoja de Ruta Trazada a R1, R2 y AC1–AC4

| Hito | Entregables Técnicos Concretos | Trazabilidad |
|---|---|---|
| **M1 (Actual)** | `docs/OPENMONTAGE_INTEGRATION_PLAN.md` validado contra rutas, líneas, versiones y reglas reales. | **R1, AC1** |
| **M2 (Runtime & Core)** | 1. Copiar subconjuntos aprobados de OpenMontage (`2e003e65`) a `vendor/openmontage/` + `LICENSE` + `NOTICE` + `THIRD_PARTY_LICENSES.md`.<br>2. Crear `pyproject.toml` y actualizar/instalar `.venv` (`certifi>=2026.10.19`, `watchfiles`, `pythainlp`, `pypdf`, `pytest`, `pytest-asyncio`).<br>3. Aplicar parches Windows en `vendor/openmontage/` (`hyperframes_compose.py` líneas `262,309,350,381,382,1404-1411`, `composition_validator.py:89-90`, `config_model.py:81`, `cost_tracker.py:502,506`, `video_compose.py` `remotion-composer` fallback + UTF-8).<br>4. Implementar `vendor/openmontage/tools/audio/edge_tts.py` (`EdgeTTS(BaseTool)` con `boundary="WordBoundary"`).<br>5. Corregir `core/parsers/doc_parser.py:82` (`pypdf -> pymupdf -> pdfplumber`). | **R2, AC2** |
| **M3 (Orquestador, QA & SCORM)** | 1. Implementar `core/orchestrator/{_openmontage_env,scene_builder,pipeline,outro_mux}.py`.<br>2. Implementar `core/qa/{pre_render,post_render}.py`.<br>3. Actualizar `core/scorm/scorm_packager.py` manteniendo firma legacy + invariantes `AGENTS.md` + Dual ZIP.<br>4. Actualizar documentación operativa en `skills/*/SKILL.md` sin colisiones. | **R2, AC2** |
| **M4 (Verificación E2E & Hardening)** | 1. Ejecutar suite reproducible de 5 niveles (cero mocks) sobre fixtures reales y runtimes reales (`edge-tts`, `ffmpeg`, `ffprobe`, `npx hyperframes`, `playwright-core` Chrome).<br>2. Verificar no regresión de `core/` y `films/*`.<br>3. Auditoría adversarial Tier 5 de casos borde (rutas con espacios, acentos `cp1252`, checkpoints fuera de sincro, reanudación de `frames/`, caché `npx` fría). | **R2, AC2, AC3, AC4** |

### 4.2 Estrategia de Verificación Reproducible de 5 Niveles (Cero Mocks)

Todos los niveles se ejecutarán con herramientas reales bajo `pytest` y scripts reproducibles en `tests/` (sin escribir archivos temporales dentro de `films/`):

1. **Nivel 1 — Unit & Contract (`python -B -m pytest tests/unit tests/contracts`):**
   - `doc_parser.parse_document()` sobre fixtures reales `.pptx`, `.docx` y `.pdf` (verificando ausencia de `ModuleNotFoundError` y esquema exacto).
   - `brand_theme.extract_brand_theme("sello educai.jpg")` validando las 6 claves de `palette` y 6 de `typography`.
   - `scorm_packager.build_scorm_package()` inspeccionando el ZIP generado (`index.html`, `imsmanifest.xml`, `controlsList="nofullscreen"`, `#player-container`, `#next-checkpoint-info`, ventana `1.2s`, Dual ZIP y `<file href>`).
   - Contratos de `vendor/openmontage/lib/` (`pipeline_loader`, `checkpoint`, `hyperframes_style_bridge`, `media_profiles`).
2. **Nivel 2 — ToolRegistry, `EdgeTTS` y `HyperFramesCompose` en Windows:**
   - `registry.discover("tools")` debe descubrir `edge_tts` y `>=38` herramientas locales en estado `AVAILABLE` sin claves de API pagas.
   - `HyperFramesCompose().get_status()` debe reportar `AVAILABLE` usando el probe tolerante en Windows.
   - `EdgeTTS.execute()` debe sintetizar un audio real con `es-AR-ElenaNeural` y generar `word_timings.json` + `audio_timeline.json` con duración `> 0` medida por `ffprobe`.
3. **Nivel 3 — Flujo End-to-End Integrado (FFmpeg + HyperFrames + Canvas):**
   - Ejecutar `python -m core.orchestrator` sobre un fixture reproducible de 2 escenas en modo **`hyperframes`** (con `style_bridge` + `edge_tts` + `subtitle_gen` + `audio_mixer` stereo + `pre_render` + `hyperframes_compose` + `outro_mux` con `ending_norm.mp4` + `post_render` + `export_bundle` + Dual SCORM ZIP) y en modo **`canvas`** (con `window.render(t)` + reanudación parcial desde `frames/`), validando con `ffprobe` streams `h264`/`yuv420p` `1920x1080` `24fps` + `aac 44100 Hz stereo` sin cortes de audio ni frames negros.
4. **Nivel 4 — Browser SCORM con Playwright (`playwright-core` + Chrome real):**
   - Extraer `index.html` + `.mp4` del `*_SCORM_Completo.zip` generado en un directorio temporal `tests/.tmp_scorm/`, abrir en Chrome headless, verificar `#checkpoint-label`, simular reproducción/avance en el rango `[cp.timestamp, cp.timestamp + 1.2]`, comprobar `#overlay` visible, responder la trivia y validar actualización de `#score-display` y llamadas al mock de `window.API` (único stub DOM estándar de Moodle LMS necesario para emular `LMSInitialize`/`LMSSetValue`, nunca mockeando herramientas de video/audio).
5. **Nivel 5 — No Regresión de `core/` y `films/*`:**
   - Re-verificar ejecución CLI (`--help` y corrida sobre entrada real) de `core/brand_theme.py`, `core/parsers/doc_parser.py` y `core/scorm/scorm_packager.py` con argumentos heredados de 4 parámetros.
   - Ejecutar `ffprobe` de integridad sobre los 3 videos finales existentes en `films/` (`Cuando_El_Trabajo_Deja_De_Ser_Necesario_EducAI_Final.mp4`, `Estructura_Tripartita_EducAI_Final.mp4`, `Protocolo_Relevamiento_EducAI_Final.mp4`) y validar que ninguno haya sido alterado.
   - Nota de saneamiento en M4: el script legado `films/cuando-el-trabajo-deja-de-ser-necesario/test_browser_scorm.js:34` contiene el timestamp obsoleto `96.6` (frente a `110.4` en `update_scorm_robust.py:9`) y escribe en `films/`; en M3/M4 se decidirá dejar `films/` intacto y mantener la suite normalizada en `tests/` (o corregir `96.6 -> 110.4` solo si el usuario solicita actualizar ese film legado).

### 4.3 Plan de Rollback y Criterios de Aceptación Finales

- **Rollback limpio:** Gracias al aislamiento en `vendor/openmontage/` y a la compatibilidad retroactiva de `core/`:
  1. Eliminar `vendor/openmontage/`, `core/orchestrator/`, `core/qa/`, `tests/`, `pyproject.toml` y `THIRD_PARTY_LICENSES.md`.
  2. Restaurar `core/parsers/doc_parser.py`, `core/scorm/scorm_packager.py` y `skills/*/SKILL.md` mediante `git checkout -- <rutas>`.
  3. Los proyectos existentes bajo `films/*/` y los scripts originales de `core/` quedan intactos en todo momento.
- **Criterios de Aceptación globales (R1 + R2):**
  - **AC1:** `docs/OPENMONTAGE_INTEGRATION_PLAN.md` completo y consistente con los artefactos reales (cumplido en M1).
  - **AC2:** OpenMontage invocable desde `core/orchestrator/` y `ToolRegistry` sin simulaciones en herramientas de producción.
  - **AC3:** Al menos un flujo E2E completo de OpenMontage integrado produce video final + QA + bundle/SCORM sin errores.
  - **AC4:** Todas las capacidades y verificaciones previas del proyecto siguen pasando sin regresiones.
