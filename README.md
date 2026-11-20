# Máquina de Videos · EducAI

Estudio y motor generador de videos educativos, interactivos y explicativos en código determinista (**HyperFrames / Canvas 2D / Three.js / SVG Mocap / FFmpeg** + **Síntesis TTS y Evaluación SCORM 1.2 para Moodle**).

Desarrollado bajo la integración de **OpenMontage** y la arquitectura de agentes de **Google Antigravity**.

---

## 📚 Índice de Contenidos

1. [Visión General y Principio de Determinismo](#1-visión-general-y-principio-de-determinismo)
2. [Arquitectura de Agentes y Habilidades](#2-arquitectura-de-agentes-y-habilidades)
3. [Tipos de Videos que se Producen](#3-tipos-de-videos-que-se-producen)
4. [Flujo de Trabajo de Producción (Workflow E2E)](#4-flujo-de-trabajo-de-producción-workflow-e2e)
   * 📘 [Guía Operativa Detallada: Video Común vs. SCORM](docs/GUIA_FLUJO_PRODUCCION_VIDEOS.md)
5. [Invariantes de Producción y Gates de Calidad (AGENTS.md)](#5-invariantes-de-producción-y-gates-de-calidad-agentsmd)
6. [Empaquetado SCORM 1.2 Interactivo para Moodle](#6-empaquetado-scorm-12-interactivo-para-moodle)
7. [Uso del Orquestador Unificado (CLI & Python)](#7-uso-del-orquestador-unificado-cli--python)
8. [Estructura del Proyecto](#8-estructura-del-proyecto)
9. [Suite de Verificación y Pruebas E2E (Cero Mocks)](#9-suite-de-verificación-y-pruebas-e2e-cero-mocks)

---

## 1. Visión General y Principio de Determinismo

A diferencia de las herramientas tradicionales de IA generativa de video que alucinan píxeles impredecibles y texto ilegible, esta máquina de video opera bajo el principio:

$$\text{Video}(t) = \text{LienzoCódigo}(t) \quad \oplus \quad \text{AudioSincronizado}(t)$$

* **100% Determinista:** Cualquier cuadro al segundo `t = 28.5s` se reproduce idéntico en cualquier computadora.
* **Tipografía y Gráficos Nítidos:** Los textos, diagramas vectoriales, logotipos institucionales y tablas conservan precisión vectorial milimétrica.
* **Sincronía Palabra por Palabra:** Cada elemento visual se anima exactamente en el segundo y milisegundo en que la voz en off lo pronuncia.

---

## 2. Arquitectura de Agentes y Habilidades

El proyecto está diseñado como un equipo de especialistas coordinados por el **Agente Principal Antigravity**:

```
[Usuario / Docente]
        │
        ▼ (Prompt en lenguaje natural o CLI)
[Antigravity Coordinator] ──────────────────────────────────────────┐
        │                                                           │
        ├──► Document Ingestion (`core.parsers.doc_parser`)         │
        ├──► Brand & Theme Architect (`core.brand_theme`)           ▼
        ├──► Voice & Timings (`vendor.openmontage.tools.audio`) ── [ToolRegistry]
        ├──► Pre-Render QA Gate (`core.qa.pre_render`)             (165 herramientas)
        ├──► Multi-Engine Visual Render (`hyperframes`/`canvas`)    │
        ├──► Audio Mix & Outro Stitcher (`core.orchestrator`)       │
        ├──► Post-Render QA Gate (`core.qa.post_render`)            │
        └──► Interactive SCORM Packager (`core.scorm`) ─────────────┘
```

### 2.1. Matriz de Agentes y Subagentes del Ecosistema (Tabla de Doble Entrada)

| Entidad / Actor | Nivel / Rol | Función Principal (¿Qué hace?) | Entradas (Insumos) | Salidas (Entregables) | Módulo / Habilidad Vinculada | Control Crítico / Invariante |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Antigravity Coordinator** | **Agente Principal** | Interfaz con el usuario, interpretación pedagógica, planificación global, delegación de tareas y supervisión general del ciclo de vida. | Prompt del usuario, documentos de cátedra, imágenes de marca. | Plan de producción, reportes de estado, entregables finales al usuario. | Orquestador central Antigravity | Supervisa el cumplimiento estricto de `AGENTS.md`. |
| **Doc Parser & Scriptwriter** | **Subagente Especialista** | Extrae contenidos crudos (incluyendo notas del orador) y los convierte en un guion estructurado escena por escena. | `.pptx`, `.docx`, `.pdf`. | `scenes.json`, guion de locución y lista de checkpoints evaluativos. | `raw-document-video-parser` | No omite conceptos didácticos clave; segmenta en escenas de 40 a 90 segundos. |
| **Brand & Theme Architect** | **Subagente Especialista** | Cuantiza logotipos institucionales y extrae paletas armónicas con reglas de estilo editorial y variables CSS. | Imagen del logo institucional (`.jpg`, `.png`). | `theme_config.json`, `DESIGN.md`, variables `:root` CSS (8 colores). | `core.brand_theme` | Asegura contraste accesible (WCAG AA) y armonía cromática coherente. |
| **Voice & Timings Specialist** | **Subagente Especialista** | Sintetiza la narración oral con entonación natural y captura eventos temporales palabra por palabra. | Guion textual de `scenes.json`, configuración de voz (`es-AR-ElenaNeural`). | `scene_XX.mp3`, `audio_timeline.json`, `word_timings.json`. | `tiktok-word-captions` y adaptador EdgeTTS | Velocidad calibrada a `-2%`; desfase temporal $\le 0.05\text{s}$ respecto a `ffprobe`. |
| **Pre-Render QA Gatekeeper** | **Subagente de Calidad** | Audita la composición técnica antes de gastar recursos de render, bloqueando la ejecución ante inconsistencias. | `scenes.json`, audios, `audio_timeline.json`, plantilla HTML. | Reporte JSON de validación Pre-Render (`valid: true/false`). | `pre-render-composition-validator` | **Invariante 1:** Ningún checkpoint evaluativo puede cortar la alocución de la escena. |
| **Visual Render & Outro Stitcher** | **Subagente de Producción** | Renderiza fotogramas deterministas a 24 fps, mezcla el audio estéreo con retardos exactos y ensambla el outro institucional. | Plantilla HTML/JS, fotogramas en disco, `ending_norm.mp4`, `adelay`. | Cuadros PNG en `frames/`, `audio_mixed.m4a`, `video_raw.mp4`, `*_Final.mp4`. | `modular-video-orchestrator` y `core.orchestrator` | **Invariante 3:** Reanudación desde `frames/` si un render se interrumpió; audio estéreo AAC 44.1 kHz. |
| **Post-Render QA Gatekeeper** | **Subagente de Calidad** | Inspecciona el video final compilado mediante análisis de flujos y verificación visual de fotogramas clave. | Video final `.mp4`. | Reporte de integridad técnica, fotogramas clave extraídos. | `post-render-video-qa` | Detecta fotogramas negros, cortes de audio con `silencedetect` y desincronías. |
| **SCORM Packager Specialist** | **Subagente de Entrega** | Empaqueta el video interactivo con listeners de tiempo, interfaz de preguntas formativas y comunicación LMS. | Video `.mp4`, lista de preguntas (`checkpoints`), metadatos de cátedra. | `*_SCORM_Completo.zip` y `*_SCORM.zip` (Zero-Weight). | `interactive-scorm-video-packager` | **Invariante 2:** Pantalla completa sobre `#player-container` (`controlsList="nofullscreen"`). |

### 2.2. Matriz de Habilidades Operativas (`skills/`) (Tabla de Doble Entrada)

| Habilidad (`Skill`) | Propósito Técnico | Herramientas / Librerías | Cuándo se Activa | Resultado Técnico Garantizado |
| :--- | :--- | :--- | :--- | :--- |
| **`raw-document-video-parser`** | Ingesta robusta de archivos docentes multiformato con extracción de notas de orador y metadatos. | `pypdf`, `pymupdf`, `pdfplumber`, `python-docx`, `python-pptx`. | Al recibir un archivo fuente (.pptx, .docx, .pdf) en la fase inicial. | Estructura JSON normalizada con títulos, conceptos y notas orales sin pérdida de texto. |
| **`tiktok-word-captions`** | Generación de subtítulos dinámicos estilo karaoke con resaltado palabra por palabra. | `edge-tts` (eventos `WordBoundary`), formato `.ass` o inyección en DOM/Canvas. | Durante la síntesis de voz y preparación visual de la composición. | Archivo `word_timings.json` sincronizado milimétricamente con el audio final. |
| **`modular-video-orchestrator`** | Renderizado modular por lotes de escenas para evitar saturación de memoria en videos largos. | Node.js, Puppeteer/Playwright, FFmpeg, manejo de hilos. | Al disparar el renderizado visual de la lección (HyperFrames o Canvas). | Fotogramas PNG a 24 fps cacheados en disco listos para multiplexado determinista. |
| **`pre-render-composition-validator`** | Gate de control previo al render para detectar errores JS/CSS y sincronía de preguntas. | Headless Chromium, Playwright, analizador de árboles JSON. | Obligatoriamente antes de ejecutar el render de fotogramas. | Aprobación formal (`0` errores de consola, duraciones alineadas, checkpoints al cierre de alocución). |
| **`post-render-video-qa`** | Auditoría posterior al ensamble del video final MP4. | `ffprobe`, `ffmpeg` (`silencedetect`, `blackdetect`, filtros de extracción). | Inmediatamente después de ensamblar el `.mp4` y antes del SCORM. | Confirmación de stream de video H.264 + audio AAC estéreo sin caídas abruptas ni pantallas negras. |
| **`interactive-scorm-video-packager`** | Generación de paquetes SCORM 1.2 interactivos para Moodle con arquitectura Dual ZIP. | SCORM 1.2 API Wrapper, HTML5 Player seguro, generador de `imsmanifest.xml`. | Al finalizar con éxito el gate Post-Render para entrega en Moodle. | Emisión de paquete autocontenido (`_SCORM_Completo.zip`) y paquete liviano (`_SCORM.zip` < 400 KB). |

---

## 3. Tipos de Videos que se Producen

1. **Whiteboard / Pizarra Explicativa:** Dibujo progresivo de diagramas, conceptos clave, subrayados y notas visuales sincronizadas con la voz en off.
2. **Kinetic Typography & Motion Graphics (HyperFrames):** Composiciones HTML/CSS/GSAP con entradas, tarjetas interactivas y subtítulos con resaltado activo palabra por palabra.
3. **Animación con Títeres SVG (Ink Theater):** Personajes vectoriales expresivos animados mediante 12 clips de captura de movimiento (mocap CMU) y tipografía de trazo a mano.
4. **Infografías 3D e Ilustración Espacial (Three.js):** Diagramas dimensionales y rotaciones espaciales sobre WebGL.
5. **Video-Clases Interactivas SCORM 1.2:** Videos que pausan en puntos clave para plantear preguntas formativas que califican al estudiante en Moodle LMS.

---

## 4. Flujo de Trabajo de Producción (Workflow E2E)

### 4.1. Pasos del Flujo Operativo

1. **Briefing e Ingesta:** El usuario provee un documento pedagógico (`.docx`, `.pptx`, `.pdf`) y opcionalmente un logo/sello.
2. **Estructuración:** Se generan `scenes.json`, `theme_config.json` y `DESIGN.md`.
3. **Locución y Cronograma:** Se sintetizan los audios de escena (`scene_XX.mp3`), `audio_timeline.json` y las marcas por palabra (`word_timings.json`).
4. **Mezcla Estéreo:** Se aplica `adelay` milimétrico para respetar los silencios entre escenas y se normaliza el audio estéreo (`audio_mixed.m4a`).
5. **Gate Pre-Render:** Validación automática antes de renderizar (bloquea la ejecución ante inconsistencias).
6. **Renderizado de Cuadros:** Renderizado acelerado mediante HyperFrames o motor Canvas determinista a 24 fps con reanudación desde `frames/`.
7. **Multiplexado y Cierre:** Unión de video con audio estéreo y concatenación con `ending_norm.mp4`.
8. **Gate Post-Render:** Auditoría técnica de streams y descarte de pantallas negras.
9. **Empaquetado Dual SCORM:** Emisión de `*_SCORM_Completo.zip` y `*_SCORM.zip`.

### 4.2. Matriz de Flujo de Trabajo: Fases vs. Agentes y Habilidades (Tabla de Doble Entrada)

| Fase del Pipeline | Agente Responsable | Habilidad Utilizada | Insumo Principal | Artefacto de Salida | Invariante Aplicada |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **1. Ingesta Didáctica** | Scriptwriter Subagent | `raw-document-video-parser` | Documento docente (`.docx`, `.pptx`, `.pdf`) | `scenes.json` | Extracción prioritaria de notas de orador |
| **2. Identidad Visual** | Brand Architect | `core.brand_theme` | Logotipo / Isotipo | `theme_config.json`, `DESIGN.md` | Paleta de 8 colores armónicos y legibles |
| **3. Síntesis y Marcas** | Voice Specialist | `tiktok-word-captions` | Guion de locución | `scene_XX.mp3`, `word_timings.json` | Velocidad `-2%` y eventos `WordBoundary` |
| **4. Gate Pre-Render** | Pre-Render QA Gatekeeper | `pre-render-composition-validator` | Assets + `audio_timeline.json` | Reporte Pre-QA (`PASS`/`FAIL`) | **Invariante 1:** Checkpoints a `fin_alocucion + 0.05s` |
| **5. Render Cuadro a Cuadro** | Engine Render | `modular-video-orchestrator` | Escenas HTML/Canvas | `frames/frame_*.png` (24 fps) | **Invariante 3:** Reanudación si `frames/` ya existe |
| **6. Mezcla y Outro** | Outro Stitcher | `core.orchestrator` | `ending_norm.mp4`, `adelay` | `*_EducAI_Final.mp4` | Audio normalizado AAC 44.1 kHz 2ch |
| **7. Gate Post-Render** | Post-Render QA Gatekeeper | `post-render-video-qa` | `*_EducAI_Final.mp4` | Reporte Post-QA (`PASS`/`FAIL`) | **Invariante 4:** Cero pantallas negras ni cortes de voz |
| **8. Empaque SCORM** | SCORM Packager | `interactive-scorm-video-packager`| MP4 auditado + Checkpoints | Paquetes Dual ZIP (`.zip`) | **Invariante 2:** Fullscreen seguro sobre contenedor |

---

## 5. Invariantes de Producción y Gates de Calidad (AGENTS.md)

El archivo `AGENTS.md` define 5 invariantes no negociables en todo el repositorio:

1. **Sincronía de Preguntas Interactivas:** Todo bloque de preguntas (`checkpoint`) debe ubicarse al terminar la alocución de la escena (`end + 0.05s` a `+0.1s`), **nunca en medio de una frase o discurso**. La ventana de captura en el reproductor es tolerante (`curT >= cp.timestamp && curT <= cp.timestamp + 1.2`).
2. **Pantalla Completa Segura para Moodle:** El reproductor usa `controlsList="nofullscreen"` en `<video>` y maximiza `#player-container`. Maximizar `<video>` directamente en HTML5 oculta los overlays de preguntas detrás del video.
3. **Reanudación de Renders Inconclusos:** Si un render se interrumpe y los fotogramas PNG están en `frames/`, el sistema retoma directamente desde la codificación FFmpeg sin renderizar de nuevo los cuadros existentes.
4. **Gates Pre-Render y Post-Render Obligatorios:** Ningún video se entrega ni se empaqueta sin pasar las validaciones de `core.qa.pre_render` y `core.qa.post_render`.
5. **Subtítulos Dinámicos Estilo CapCut por Defecto (Opt-Out):** Todo video incluye subtítulos animados palabra por palabra a partir de `word_timings.json` con la habilidad `tiktok-word-captions`, a menos que el usuario solicite explícitamente desactivarlos (`--no-captions` o *"sin subtítulos"*).

---

## 6. Empaquetado SCORM 1.2 Interactivo para Moodle

El empaquetador genera una arquitectura **Dual ZIP**:

* **Autocontenido (`*_SCORM_Completo.zip`):** Incluye `index.html`, `imsmanifest.xml` declarando `<file href="video.mp4"/>` y el archivo `.mp4` adentro, para servidores Moodle con cuota de subida suficiente.
* **Zero-Weight (`*_SCORM.zip`):** Paquete ultraliviano ($< 400\text{ KB}$) que apunta a un servidor HTTP/CDN externo con soporte de *byte-range*, ideal para superar límites de subida de 10-20 MB en campus universitarios.

---

## 7. Uso del Orquestador Unificado (CLI & Python)

### Invocación por Línea de Comandos:

```powershell
# Ejecutar el pipeline completo hacia video final y SCORM Dual (con subtítulos CapCut por defecto)
python -m core.orchestrator `
  --project-dir "films/mi-leccion" `
  --doc "documento.docx" `
  --theme-image "sello educai.jpg" `
  --render-mode hyperframes `
  --title "Introducción a la IA" `
  --voice "es-AR-ElenaNeural"

# Si el usuario solicita explícitamente desactivar los subtítulos:
python -m core.orchestrator `
  --project-dir "films/mi-leccion" `
  --doc "documento.docx" `
  --no-captions `
  --title "Introducción a la IA"
```

### Empaquetado SCORM independiente:

```powershell
python -m core.scorm.scorm_packager `
  --title "Protocolo de Relevamiento EducAI" `
  --video-url "Protocolo_EducAI_Final.mp4" `
  --include-video "films/protocolo/Protocolo_EducAI_Final.mp4" `
  --checkpoints-json "checkpoints.json" `
  --audio-timeline "audio_timeline.json" `
  --strict-sync `
  --dual-zip `
  --output "Protocolo_SCORM_Completo.zip"
```

---

## 8. Estructura del Proyecto

```
maquina-de-videos/
├── AGENTS.md                  # Reglas e invariantes estrictas de producción
├── THIRD_PARTY_LICENSES.md    # Licencias de OpenMontage (AGPLv3), Patrick Hand, etc.
├── pyproject.toml             # Configuración de dependencias y suite de pytest
├── core/
│   ├── brand_theme.py         # Extracción de paleta de 8 colores desde logos
│   ├── captions/              # Generador de subtítulos CapCut (.ass karaoke)
│   ├── parsers/doc_parser.py  # Ingesta de PPTX, DOCX y PDF
│   ├── qa/
│   │   ├── pre_render.py      # Gate de calidad previo al renderizado
│   │   └── post_render.py     # Gate de calidad posterior al renderizado
│   ├── orchestrator/
│   │   ├── pipeline.py        # EducAIPipeline (orquestador de 8 fases)
│   │   ├── scene_builder.py   # Constructor de escenas y alineador SCORM
│   │   ├── video_render.py    # Renderizador motion graphics con tarjetas y subtítulos
│   │   └── outro_mux.py       # Multiplexado estéreo y ensamble con ending_norm.mp4
│   └── scorm/
│       └── scorm_packager.py  # Generador Dual ZIP SCORM 1.2 para Moodle
├── docs/                      # Guías operativas e instructivos paso a paso
│   └── GUIA_FLUJO_PRODUCCION_VIDEOS.md
├── films/                     # Producciones y video-clases generadas
│   ├── cuando-el-trabajo-deja-de-ser-necesario/
│   ├── estructura-tripartita/
│   ├── instructivo-caso-a-video-comun/
│   ├── instructivo-caso-b-video-scorm/
│   └── protocolo-relevamiento/
├── skills/                    # Especificaciones operativas de habilidades
├── tests/                     # Suite de pruebas E2E (Unit, Contratos, Chrome)
│   ├── unit/                  # Tests unitarios y de ToolRegistry
│   └── e2e/                   # Pipeline E2E real, regresión y navegador Chrome
└── vendor/
    └── openmontage/           # Runtime aislado de OpenMontage (165 herramientas)
```

---

## 9. Suite de Verificación y Pruebas E2E (Cero Mocks)

El proyecto incluye 15 pruebas automatizadas que cubren 5 niveles de verificación técnica:

```powershell
# Ejecutar la suite completa de pruebas
python -m pytest tests -v
```

* **Nivel 1:** Tests unitarios y contratos de parseo (`.pptx`, `.docx`, `.pdf`), paleta y SCORM.
* **Nivel 2:** Descubrimiento de `edge_tts` y más de 38 herramientas locales en `ToolRegistry`, disponibilidad de `HyperFramesCompose` en Windows y síntesis real de voz con `WordBoundary`.
* **Nivel 3:** Flujo completo E2E con generación de video final y concatenación con `ending_norm.mp4`.
* **Nivel 4:** Verificación en navegador Chrome real (*headless*) con Playwright de los eventos DOM, listeners y API SCORM 1.2 (`LMSInitialize`, `LMSSetValue`, `LMSCommit`, `LMSFinish`).
* **Nivel 5:** No regresión de interfaces CLI e integridad de los 3 videos finales existentes en `films/`.
