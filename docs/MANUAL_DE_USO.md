# Manual de Uso · Máquina de Videos EducAI

Manual técnico y operativo para la creación automatizada de videos educativos, interactivos y explicativos en código determinista (**HyperFrames / Canvas 2D / Three.js / FFmpeg + EdgeTTS y Evaluación SCORM 1.2 para Moodle**).

---

## 📑 Tabla de Contenidos

1. [Visión General y Principio de Funcionamiento](#1-visión-general-y-principio-de-funcionamiento)
2. [Requisitos del Entorno e Instalación Rápida (< 5 minutos)](#2-requisitos-del-entorno-e-instalación-rápida--5-minutos)
3. [Los Dos Modos de Producción: Caso A vs. Caso B](#3-los-dos-modos-de-producción-caso-a-vs-caso-b)
4. [Las 6 Reglas e Invariantes de Producción (AGENTS.md)](#4-las-6-reglas-e-invariantes-de-producción-agentsmd)
5. [Menú Interactivo de Estilos Gráficos](#5-menú-interactivo-de-estilos-gráficos)
6. [Instructivo de Operación Paso a Paso](#6-instructivo-de-operación-paso-a-paso)
   - [Flujo Caso A: Video Común (Lineal MP4)](#flujo-caso-a-video-común-lineal-mp4)
   - [Flujo Caso B: Video-Cuestionario SCORM para Moodle](#flujo-caso-b-video-cuestionario-scorm-para-moodle)
7. [Referencia Completa de Comandos por Consola (CLI)](#7-referencia-completa-de-comandos-por-consola-cli)
8. [Subida y Configuración en Moodle LMS](#8-subida-y-configuración-en-moodle-lms)
9. [Estructura de Archivos de un Proyecto](#9-estructura-de-archivos-de-un-proyecto)
10. [Resolución de Problemas Frecuentes (Troubleshooting)](#10-resolución-de-problemas-frecuentes-troubleshooting)

---

## 1. Visión General y Principio de Funcionamiento

A diferencia de las herramientas de inteligencia artificial generativa de difusión que alucinan fondos cambiantes, rostros deformes y texto ilegible, la **Máquina de Videos · EducAI** opera bajo el principio de **composición determinista en código**:

$$\text{Video}(t) = \text{LienzoGráfico}(t) \quad \oplus \quad \text{AudioSincronizado}(t)$$

* **Precisión Tipográfica Milimétrica:** Los títulos, esquemas, logotipos institucionales y tablas se renderizan vectorialmente en resolución Full HD (1920x1080) a 24 cuadros por segundo.
* **Sincronía Palabra por Palabra:** Cada elemento visual y cada subtítulo dinámico estilo CapCut se activa en el milisegundo exacto en que la voz en off lo pronuncia (`WordBoundary`).
* **Interactividad Pedagógica Real:** En lugar de ser un simple reproductor pasivo, el motor es capaz de pausar la clase en hitos didácticos para evaluar formativamente al alumno y calificarlo en Moodle LMS vía el protocolo SCORM 1.2.

---

## 2. Requisitos del Entorno e Instalación Rápida (< 5 minutos)

### Requisitos del Sistema
* **Sistema Operativo:** Windows 10/11, macOS o Linux.
* **Python:** Versión `3.10` o superior (probado en Python `3.14.3`).
* **FFmpeg y FFprobe:** Instalados y registrados en el `PATH` del sistema (con soporte `--enable-libass` para quemado de subtítulos).
* **Node.js (Opcional):** Versión `18+` (requerido únicamente si se utiliza el motor de renderizado Canvas basado en scripts Node/Playwright).
* **Google Chrome:** Navegador instalado para las pruebas automatizadas del gate Pre-Render en modo *headless*.

### Instalación de Dependencias

1. **Clonar el repositorio:**
   ```powershell
   git clone https://github.com/superpollo02/maquina-de-videos.git
   cd maquina-de-videos
   ```

2. **Instalar paquetes de Python requeridos:**
   ```powershell
   pip install edge-tts pydub pypdf pymupdf pdfplumber python-docx python-pptx pytest pytest-asyncio playwright
   ```

3. **Verificar la suite de pruebas (100% verde):**
   ```powershell
   python -m pytest tests -v
   ```
   *(Deberás ver `15 passed in ~35s`, lo que confirma que el entorno está listo para producir videos sin fallos).*

---

## 3. Los Dos Modos de Producción: Caso A vs. Caso B

El sistema está diseñado para resolver dos necesidades pedagógicas concretas:

| Dimensión | Caso A: Video Común (Lineal) | Caso B: Video-Cuestionario SCORM |
| :--- | :--- | :--- |
| **Objetivo** | Explicación continua sin interrupciones. | Clase interactiva con pausas evaluativas. |
| **Entregable Principal** | Archivo `.mp4` Full HD 1080p con audio estéreo. | Paquetes `.zip` bajo norma SCORM 1.2. |
| **Subtítulos Dinámicos** | **Activos por defecto** (estilo CapCut karaoke). | **Activos por defecto** (estilo CapCut karaoke). |
| **Calificación en LMS** | No registra calificaciones. | Califica y registra intentos en Moodle LMS. |
| **Plataformas de Uso** | YouTube, WhatsApp, Google Drive, Proyector en clase. | Campus Virtual Moodle, Canvas LMS, Blackboard. |
| **Outro Institucional** | Concatenado al final (`ending_norm.mp4`). | Concatenado al final (`ending_norm.mp4`). |

---

## 4. Las 6 Reglas e Invariantes de Producción (AGENTS.md)

Todo video producido en este estudio respeta obligatoriamente las 6 invariantes de calidad del archivo [AGENTS.md](file:///f:/proyectos%20antigrtavity/maquina%20de%20videos/AGENTS.md):

1. **Sincronía de Preguntas Interactivas (Invariante 1):**  
   Todo bloque de preguntas (`checkpoint`) en un video SCORM debe pausar en:
   $$\text{timestamp} = \text{fin de la alocución de la escena} + 0.05\text{s}$$
   **Está estrictamente prohibido cortar la voz del docente en medio de una frase o discurso.** La ventana de detección en el reproductor es tolerante (`curT >= cp.timestamp && curT <= cp.timestamp + 1.2`) para evitar saltos accidentales.

2. **Pantalla Completa Segura para Moodle (Invariante 2):**  
   En HTML5, maximizar directamente el elemento `<video>` oculta los formularios de preguntas detrás del video. Por eso, el reproductor bloquea la pantalla completa nativa (`controlsList="nofullscreen"`) y la redirecciona al contenedor `#player-container`.

3. **Reanudación de Renders Inconclusos (Invariante 3):**  
   Si una renderización se interrumpe, el orquestador detecta los fotogramas existentes en `frames/` o `video_raw.mp4` y retoma directamente desde el multiplexado con FFmpeg, evitando horas de reprocesamiento.

4. **Gates de Calidad Obligatorios (Invariante 4):**  
   Ningún archivo se entrega sin superar:
   * **Pre-Render (`core.qa.pre_render`):** Valida que no haya errores JavaScript en Chromium headless, que las duraciones de audio coincidan y que los checkpoints no colisionen con la voz.
   * **Post-Render (`core.qa.post_render`):** Audita con `ffprobe` que el MP4 final tenga video H.264, audio AAC 44.1 kHz estéreo a $-16\text{ LUFS}$ y descarta pantallas negras con `blackdetect`.

5. **Subtítulos Dinámicos Estilo CapCut por Defecto (Invariante 5 - Opt-Out):**  
   Todo video incluye automáticamente subtítulos animados palabra por palabra a partir de `word_timings.json`. **Solo se desactivan si el usuario solicita expresamente:** *"sin subtítulos"* o mediante `--no-captions`.

6. **Menú de Preferencias de Estilo Visual (Invariante 6):**  
   Si el usuario no especifica el estilo gráfico en su pedido inicial, el agente coordinador debe consultar interactivamente ofreciendo las 5 familias gráficas estándar.

---

## 5. Menú Interactivo de Estilos Gráficos

El motor cuenta con 5 opciones preconfiguradas:

1. ⭐ **(Recomendado) Pizarra Didáctica / Whiteboard Explainer (`canvas`):**  
   Trazos progresivos a mano alzada, notas visuales y diagramas limpios sobre fondo de pizarra con textura. Ideal para matemáticas, ciencias y clases paso a paso.
2. 🎴 **Motion Graphics & Tarjetas Modernas (`hyperframes`):**  
   Tarjetas informativas dinámicas, tipografía editorial moderna, diseño oscuro o claro y transiciones fluidas. Ideal para tecnología, gestión y cursos ejecutivos.
3. 📐 **Infografía Técnica & Blueprint (`blueprint`):**  
   Esquemas en azul técnico o milimetrado, diagramas de flujo y despiece de procesos. Ideal para ingeniería, sistemas y protocolos.
4. 🎨 **Visual Sketchnote & Ilustración Editorial (`sketchnote`):**  
   Estilo cuaderno de notas con marcadores, texturas orgánicas y viñetas ilustradas. Ideal para humanidades, historia y storytelling.
5. 🎭 **Títeres Vectoriales Mocap (`ink_theater`):**  
   Personajes vectoriales expresivos animados con 12 clips de captura de movimiento de CMU. Ideal para dramatizaciones pedagógicas y resolución de casos.

---

## 6. Instructivo de Operación Paso a Paso

### Flujo Caso A: Video Común (Lineal MP4)

#### Paso 1: Iniciar la Conversación con el Agente
Envía tu documento y las instrucciones generales:
> *"Hola. Quiero crear un **video común explicativo** a partir de la presentación adjunta `clase_historia.pptx`. Usá el logo `sello educai.jpg` para los colores institucionales y voz argentina."*

*(Al no indicar "sin subtítulos", el sistema activará automáticamente los subtítulos estilo CapCut).*

#### Paso 2: Revisión de Guion
El agente genera `scenes.json` dividiendo la clase en escenas de 40 a 90 segundos. Puedes pedir ajustes:
> *"El guion está bien, pero en la escena 2 agregá énfasis en la fecha 1816."*

#### Paso 3: Renderizado y Entrega
El motor sintetiza la voz con EdgeTTS (`es-AR-ElenaNeural` a `-2%`), ejecuta el gate Pre-Render, genera los cuadros a 24 fps, mezcla el audio estéreo con pausas de `0.55s` (`adelay`), concatena el outro institucional y entrega:
* `films/clase_historia/Clase_Historia_EducAI_Final.mp4`

---

### Flujo Caso B: Video-Cuestionario SCORM para Moodle

#### Paso 1: Iniciar la Conversación con el Agente
Solicita explícitamente la interactividad o evaluación:
> *"Hola. Necesito transformar este documento `modulo1_didactica.docx` en un **video interactivo SCORM para Moodle**. Incluí 3 preguntas de opción múltiple con retroalimentación al finalizar cada sección principal."*

#### Paso 2: Aprobación de Preguntas y Sincronía
El subagente pedagógico formula las preguntas y las sitúa estrictamente en el silencio posterior a la voz docente ($\text{fin de frase} + 0.05\text{s}$):
> *"Revisá las 3 preguntas:  
> 1. En el segundo 19.37s: [Pregunta...]  
> 2. En el segundo 37.34s: [Pregunta...]  
> 3. En el segundo 53.13s: [Pregunta...]"*

#### Paso 3: Empaquetado Dual SCORM
El sistema produce el video base y emite dos archivos comprimidos:
1. `*_SCORM_Completo.zip` (Autocontenido: reproductor + XML + video MP4 adentro).
2. `*_SCORM.zip` (Zero-Weight: $< 400\text{ KB}$, reproductor que lee el video desde un enlace HTTP externo).

---

## 7. Referencia Completa de Comandos por Consola (CLI)

### Orquestador Unificado (`core.orchestrator`)

```powershell
python -m core.orchestrator [OPCIONES]
```

| Parámetro | Abreviatura | Valor por Defecto | Descripción |
| :--- | :--- | :--- | :--- |
| `--project-dir` | `-p` | `.` | Carpeta de trabajo donde se guardarán los artefactos. |
| `--doc` | `-d` | *(Ninguno)* | Archivo fuente (`.pptx`, `.docx` o `.pdf`). |
| `--theme-image` | `-t` | *(Ninguno)* | Imagen del logo institucional para extraer 8 colores. |
| `--title` | *(Ninguno)* | Nombre de carpeta | Título de la video-clase y del paquete SCORM. |
| `--voice` | *(Ninguno)* | `es-AR-ElenaNeural` | Voz neuronal de Microsoft EdgeTTS. |
| `--render-mode` | `-m` | `hyperframes` | Motor de render (`hyperframes`, `canvas`, `blueprint`, `sketchnote`, `ink_theater`). |
| `--no-captions` | *(Ninguno)* | *(Inactivo)* | **Desactiva** los subtítulos estilo CapCut (por defecto vienen activos). |
| `--skip-render` | *(Ninguno)* | *(Inactivo)* | Omite renderizar cuadros si `video_raw.mp4` ya existe (Invariante 3). |
| `--no-dual-scorm` | *(Ninguno)* | *(Inactivo)* | Genera únicamente el video MP4 sin empaquetar en SCORM. |
| `--outro` | *(Ninguno)* | `ending_norm.mp4` | Ruta alternativa a un video MP4 de cierre institucional. |

#### Ejemplos de Uso Práctico:

```powershell
# 1. Crear un video común con subtítulos CapCut activos por defecto:
python -m core.orchestrator `
  --project-dir "films/leccion-ia" `
  --doc "leccion_ia.docx" `
  --theme-image "sello educai.jpg" `
  --title "Introduccion a la IA"

# 2. Crear un video SIN subtítulos en pantalla (Opt-Out):
python -m core.orchestrator `
  --project-dir "films/leccion-ia" `
  --doc "leccion_ia.docx" `
  --no-captions `
  --title "Introduccion a la IA"

# 3. Reanudar un render interrumpido sin recalcular cuadros:
python -m core.orchestrator `
  --project-dir "films/leccion-ia" `
  --skip-render `
  --title "Introduccion a la IA"
```

---

### Empaquetador SCORM Independiente (`core.scorm.scorm_packager`)

Si ya dispones de un video `.mp4` y un archivo `checkpoints.json`, puedes empaquetarlo directamente en SCORM 1.2:

```powershell
python -m core.scorm.scorm_packager `
  --title "Evaluacion de Seguridad" `
  --video-url "Seguridad_EducAI_Final.mp4" `
  --include-video "films/seguridad/Seguridad_EducAI_Final.mp4" `
  --checkpoints-json "films/seguridad/checkpoints.json" `
  --audio-timeline "films/seguridad/audio_timeline.json" `
  --strict-sync `
  --dual-zip `
  --output "films/seguridad/Seguridad_SCORM_Completo.zip"
```

---

## 8. Subida y Configuración en Moodle LMS

Sigue este procedimiento para instalar el video-cuestionario en tu campus virtual:

```
[Curso en Moodle] ──► [Activar edición] ──► [Añadir una actividad: Paquete SCORM]
                                                        │
                      ┌─────────────────────────────────┴─────────────────────────────────┐
                      ▼                                                                   ▼
       Si la cuota de subida es > 50 MB                                    Si la cuota de subida es < 20 MB
  (Arrastrar *_SCORM_Completo.zip)                                        (Arrastrar *_SCORM.zip Zero-Weight)
```

1. **Crear Actividad:** En la sección deseada del curso, haz clic en **Añadir una actividad o recurso** $\to$ **Paquete SCORM**.
2. **Nombre:** Ingresa el título de la lección (ej. *"Unidad 1: Video Interactivo con Evaluación"*).
3. **Subir Archivo:**
   * Si el servidor permite subir archivos grandes: arrastra `*_SCORM_Completo.zip` (pesa $\sim 4-20\text{ MB}$).
   * Si el campus tiene límite estricto de 10 MB: arrastra `*_SCORM.zip` (pesa menos de $5\text{ KB}$).
4. **Sección Calificación:**
   * *Método de calificación:* Selecciona **Calificación más alta** (o **Promedio de intentos**).
   * *Calificación máxima:* `100` (o `10` según la escala institucional).
5. **Ajustes de Visualización:**
   * *Mostrar paquete:* **Ventana actual** (recomendado para diseño responsivo).
6. **Guardar cambios y mostrar:**
   * Al reproducirse, el video se pausará en cada checkpoint y reportará la nota del alumno a `cmi.core.score.raw` y el estado a `passed`.

---

## 9. Estructura de Archivos de un Proyecto

Cada carpeta en `films/<nombre-del-proyecto>/` contiene:

```
films/mi-proyecto/
├── documento.docx / .pptx       # Material fuente original del docente
├── theme_config.json            # Paleta de 8 colores extraída del logo
├── DESIGN.md                    # Variables CSS :root y guía tipográfica
├── scenes.json                  # Guion segmentado en escenas con checkpoints
├── audio_timeline.json          # Cronograma exacto de locución con pausas
├── word_timings.json            # Marcas de tiempo al milisegundo por palabra
├── captions.ass                 # Archivo de subtítulos dinámicos estilo CapCut
├── scene_01.mp3, scene_02.mp3   # Pistas de audio individuales por escena
├── audio_mixed.m4a              # Audio estéreo normalizado (-16 LUFS)
├── video_raw.mp4                # Video 1080p generado por el motor
├── Mi_Video_EducAI_Final.mp4    # Video final ensamblado con el outro institucional
├── Mi_Video_SCORM_Completo.zip  # Paquete SCORM autocontenido con video adentro
└── Mi_Video_SCORM.zip           # Paquete SCORM Zero-Weight (< 400 KB)
```

---

## 10. Resolución de Problemas Frecuentes (Troubleshooting)

### A. "Audio duration mismatch warning" en Pre-Render QA
* **Causa:** La duración real del audio mezclado difiere en más de $0.5\text{s}$ del cronograma de escenas.
* **Solución:** Ocurre si se editaron los MP3 manualmente sin regenerar `audio_timeline.json`. Ejecuta nuevamente la etapa de síntesis de voz con `python -m core.orchestrator` para alinear los archivos.

### B. Error en Windows con FFmpeg libass (`ass=C:\...`)
* **Causa:** Los dos puntos de la unidad de disco (`C:`) en Windows rompen la sintaxis de filtros de FFmpeg.
* **Solución:** La herramienta `core.captions.capcut_ass` normaliza automáticamente las rutas:
  ```python
  ass_escaped = str(ass_file).replace("\\", "/").replace(":", "\\:")
  # Produce: ass='C\:/ruta/al/archivo.ass'
  ```

### C. El video en Moodle se corta al abrir en pantalla completa
* **Causa:** Se presionó la pantalla completa nativa del elemento video en lugar del contenedor.
* **Solución:** Verifica que el reproductor tenga el atributo `controlsList="nofullscreen"` y utiliza el botón de pantalla completa provisto por la barra superior de EducAI.

### D. En Moodle el paquete Zero-Weight no reproduce el video
* **Causa:** El servidor donde está alojado el archivo `.mp4` no tiene habilitado CORS o no admite solicitudes de rango de bytes (*HTTP Byte-Range requests*).
* **Solución:** Asegúrate de alojar el video en un servidor HTTP estándar con cabecera `Access-Control-Allow-Origin: *` o sube directamente el paquete `*_SCORM_Completo.zip`.
