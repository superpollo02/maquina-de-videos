# Máquina de Videos · EducAI

Estudio y motor generador de videos educativos, interactivos y explicativos en código determinista (**HyperFrames / Canvas 2D / Three.js / SVG Mocap / FFmpeg** + **Síntesis TTS y Evaluación SCORM 1.2 para Moodle**).

Desarrollado bajo la integración de **OpenMontage** y la arquitectura de agentes de **Google Antigravity**.

---

## 📚 Índice de Contenidos

1. [Visión General y Principio de Determinismo](#1-visión-general-y-principio-de-determinismo)
2. [Arquitectura de Agentes y Habilidades](#2-arquitectura-de-agentes-y-habilidades)
3. [Tipos de Videos que se Producen](#3-tipos-de-videos-que-se-producen)
4. [Flujo de Trabajo de Producción (Workflow E2E)](#4-flujo-de-trabajo-de-producción-workflow-e2e)
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

### Funciones de los Componentes:

1. **Document Ingestion (`doc_parser.py`):** Ingesta diapositivas `.pptx` (extrayendo notas del orador), documentos `.docx` y archivos `.pdf` mediante una cadena tolerante de extracción (`pypdf` $\to$ `pymupdf` $\to$ `pdfplumber`).
2. **Brand & Theme Extractor (`brand_theme.py`):** Cuantiza imágenes de logotipos institucionales y extrae una paleta armónica de 8 colores y reglas tipográficas para generar `DESIGN.md` y variables CSS `:root`.
3. **Voice & Word Captions (`edge_tts.py` / `tiktok-word-captions`):** Locución en español argentino (`es-AR-ElenaNeural`) a `-2%` de velocidad. Captura eventos `WordBoundary` para generar `word_timings.json` y subtítulos dinámicos estilo TikTok/karaoke.
4. **Pre-Render QA Validator (`pre_render.py`):** Verifica que no haya errores de consola en 5 puntos de tiempo evaluados en Chromium headless (Playwright), valida coincidencia de duración de audio y bloquea renders si una pregunta corta la voz docente.
5. **Outro Mux (`outro_mux.py`):** Garantiza salida AAC estéreo a 44.1 kHz (2 canales) normalizada a $-16\text{ LUFS}$ y concatena el cierre institucional `ending_norm.mp4`.
6. **Post-Render QA Auditor (`post_render.py`):** Audita con `ffprobe` e inspección visual de fotogramas clave que el MP4 final cumpla con el estándar H.264/AAC y que `silencedetect` no revele cortes abruptos de alocución.
7. **Interactive SCORM Packager (`scorm_packager.py`):** Empaqueta la video-clase en paquetes SCORM 1.2 interactivos para Moodle con soporte **Dual ZIP**.

---

## 3. Tipos de Videos que se Producen

1. **Whiteboard / Pizarra Explicativa:** Dibujo progresivo de diagramas, conceptos clave, subrayados y notas visuales sincronizadas con la voz en off.
2. **Kinetic Typography & Motion Graphics (HyperFrames):** Composiciones HTML/CSS/GSAP con entradas, tarjetas interactivas y subtítulos con resaltado activo palabra por palabra.
3. **Animación con Títeres SVG (Ink Theater):** Personajes vectoriales expresivos animados mediante 12 clips de captura de movimiento (mocap CMU) y tipografía de trazo a mano.
4. **Infografías 3D e Ilustración Espacial (Three.js):** Diagramas dimensionales y rotaciones espaciales sobre WebGL.
5. **Video-Clases Interactivas SCORM 1.2:** Videos que pausan en puntos clave para plantear preguntas formativas que califican al estudiante en Moodle LMS.

---

## 4. Flujo de Trabajo de Producción (Workflow E2E)

1. **Briefing e Ingesta:** El usuario provee un documento pedagógico (`.docx`, `.pptx`, `.pdf`) y opcionalmente un logo/sello.
2. **Estructuración:** Se generan `scenes.json`, `theme_config.json` y `DESIGN.md`.
3. **Locución y Cronograma:** Se sintetizan los audios de escena (`scene_XX.mp3`), `audio_timeline.json` y las marcas por palabra (`word_timings.json`).
4. **Mezcla Estéreo:** Se aplica `adelay` milimétrico para respetar los silencios entre escenas y se normaliza el audio estéreo (`audio_mixed.m4a`).
5. **Gate Pre-Render:** Validación automática antes de renderizar (bloquea la ejecución ante inconsistencias).
6. **Renderizado de Cuadros:** Renderizado acelerado mediante HyperFrames o motor Canvas determinista a 24 fps con reanudación desde `frames/`.
7. **Multiplexado y Cierre:** Unión de video con audio estéreo y concatenación con `ending_norm.mp4`.
8. **Gate Post-Render:** Auditoría técnica de streams y descarte de pantallas negras.
9. **Empaquetado Dual SCORM:** Emisión de `*_SCORM_Completo.zip` y `*_SCORM.zip`.

---

## 5. Invariantes de Producción y Gates de Calidad (AGENTS.md)

El archivo `AGENTS.md` define 4 invariantes no negociables en todo el repositorio:

1. **Sincronía de Preguntas Interactivas:** Todo bloque de preguntas (`checkpoint`) debe ubicarse al terminar la alocución de la escena (`end + 0.05s` a `+0.1s`), **nunca en medio de una frase o discurso**. La ventana de captura en el reproductor es tolerante (`curT >= cp.timestamp && curT <= cp.timestamp + 1.2`).
2. **Pantalla Completa Segura para Moodle:** El reproductor usa `controlsList="nofullscreen"` en `<video>` y maximiza `#player-container`. Maximizar `<video>` directamente en HTML5 oculta los overlays de preguntas detrás del video.
3. **Reanudación de Renders Inconclusos:** Si un render se interrumpe y los fotogramas PNG están en `frames/`, el sistema retoma directamente desde la codificación FFmpeg sin renderizar de nuevo los cuadros existentes.
4. **Gates Pre-Render y Post-Render Obligatorios:** Ningún video se entrega ni se empaqueta sin pasar las validaciones de `core.qa.pre_render` y `core.qa.post_render`.

---

## 6. Empaquetado SCORM 1.2 Interactivo para Moodle

El empaquetador genera una arquitectura **Dual ZIP**:

* **Autocontenido (`*_SCORM_Completo.zip`):** Incluye `index.html`, `imsmanifest.xml` declarando `<file href="video.mp4"/>` y el archivo `.mp4` adentro, para servidores Moodle con cuota de subida suficiente.
* **Zero-Weight (`*_SCORM.zip`):** Paquete ultraliviano ($< 400\text{ KB}$) que apunta a un servidor HTTP/CDN externo con soporte de *byte-range*, ideal para superar límites de subida de 10-20 MB en campus universitarios.

---

## 7. Uso del Orquestador Unificado (CLI & Python)

### Invocación por Línea de Comandos:

```powershell
# Ejecutar el pipeline completo hacia video final y SCORM Dual
python -m core.orchestrator `
  --project-dir "films/mi-leccion" `
  --doc "documento.docx" `
  --theme-image "sello educai.jpg" `
  --render-mode hyperframes `
  --title "Introducción a la IA" `
  --voice "es-AR-ElenaNeural"
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
│   ├── parsers/doc_parser.py  # Ingesta de PPTX, DOCX y PDF
│   ├── qa/
│   │   ├── pre_render.py      # Gate de calidad previo al renderizado
│   │   └── post_render.py     # Gate de calidad posterior al renderizado
│   ├── orchestrator/
│   │   ├── pipeline.py        # EducAIPipeline (orquestador de 8 fases)
│   │   ├── scene_builder.py   # Constructor de escenas y alineador SCORM
│   │   └── outro_mux.py       # Multiplexado estéreo y ensamble con ending_norm.mp4
│   └── scorm/
│       └── scorm_packager.py  # Generador Dual ZIP SCORM 1.2 para Moodle
├── films/                     # Producciones y video-clases generadas
│   ├── cuando-el-trabajo-deja-de-ser-necesario/
│   ├── estructura-tripartita/
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
