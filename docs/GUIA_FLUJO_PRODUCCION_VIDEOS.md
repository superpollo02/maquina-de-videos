# Guía Operativa de Producción de Videos · EducAI
## Flujo de Trabajo con Agentes: Video Común vs. Video-Cuestionario SCORM

Esta guía describe cómo interactuar con el ecosistema de agentes inteligentes de **Máquina de Videos · EducAI** para producir dos tipos de entregables educativos:

1. **Video Común (Lineal):** Video explicativo continuo en formato `.mp4` (Full HD 1080p), con locución neuronal sincronizada, subtítulos dinámicos estilo CapCut y outro institucional, ideal para YouTube, WhatsApp, clases invertidas o streaming.
2. **Video-Cuestionario SCORM (Interactivo):** Recurso didáctico interactivo empaquetado bajo el estándar **SCORM 1.2** para **Moodle LMS**. El video se pausa automáticamente al finalizar conceptos clave para plantear preguntas evaluativas que califican directamente en el libro de calificaciones del campus virtual.

---

## 1. El Elenco de Agentes y Cómo Interactúan

El sistema opera bajo una arquitectura de **Agente Principal y Subagentes Especialistas**:

```
                              [Docente / Usuario]
                                      │
                                      ▼
                        ┌───────────────────────────┐
                        │  Antigravity Coordinator  │  <-- Interfaz en lenguaje natural
                        └─────────────┬─────────────┘
                                      │
       ┌──────────────────────────────┼──────────────────────────────┐
       ▼                              ▼                              ▼
┌──────────────┐              ┌──────────────┐              ┌────────────────┐
│ Doc Parser & │              │ Brand & Theme│              │ Voice & Timings│
│ Scriptwriter │              │  Architect   │              │   Specialist   │
└──────┬───────┘              └──────┬───────┘              └───────┬────────┘
       │                             │                              │
       └─────────────────────────────┼──────────────────────────────┘
                                     ▼
                        ┌───────────────────────────┐
                        │  Pre-Render QA Gatekeeper │  <-- Invariante 1 (No cortar voz)
                        └─────────────┬─────────────┘
                                      ▼
                        ┌───────────────────────────┐
                        │ Visual Render & Stitcher  │  <-- Invariante 3 (Reanudación)
                        └─────────────┬─────────────┘
                                      ▼
                        ┌───────────────────────────┐
                        │ Post-Render QA Gatekeeper │  <-- Invariante 4 (ffprobe / visual)
                        └─────────────┬─────────────┘
                                      │
       ┌──────────────────────────────┴──────────────────────────────┐
       ▼ (Si es Video Común)                                        ▼ (Si es Video SCORM)
┌───────────────────────────┐                        ┌───────────────────────────┐
│     Entrega Final MP4     │                        │  SCORM Packager Specialist│
│    (*_EducAI_Final.mp4)   │                        └─────────────┬─────────────┘
└───────────────────────────┘                                      ▼
                                                     ┌───────────────────────────┐
                                                     │ Empaquetado Dual ZIP SCORM│
                                                     │ (Completo + Zero-Weight)  │
                                                     └───────────────────────────┘
```

---

## 2. Política de Subtítulos Dinámicos Estilo CapCut (Por Defecto)

### ¿Qué son y cómo se ven?
Inspirados en el estándar visual de CapCut, TikTok e Instagram Reels, los subtítulos dinámicos de EducAI se generan a través de la habilidad `tiktok-word-captions`:
* **Agrupación ágil:** Bloques cortos de 3 a 5 palabras para no saturar la pantalla.
* **Resaltado activo palabra por palabra:** Cada palabra se ilumina en el color de acento de la institución (ej. amarillo `#facc15` o cian `#38bdf8`) con un ligero rebote de escala (`1.08x`) en el milisegundo exacto en que la voz en off la pronuncia.
* **Tipografía de alto impacto:** Fuente gruesa (Black/ExtraBold) con contorno oscuro (`stroke`) y sombra para garantizar lectura perfecta sobre cualquier fondo visual.
* **Zona segura:** Ubicados en el tercio inferior, respetando los controles del reproductor.

### Regla de Inclusión por Defecto (Opt-Out)
> [!IMPORTANT]
> **Los subtítulos estilo CapCut están ACTIVADOS POR DEFECTO.**  
> Se generarán automáticamente en todo video (común o SCORM).  
> **Para desactivarlos**, el usuario debe manifestarlo expresamente en el chat (*"sin subtítulos"*, *"no pongas subtítulos"*, *"desactiva los subtítulos"*) o mediante el flag CLI `--no-captions`.

---

## 3. Flujo 1: Creación de un "Video Común" (Lineal MP4)

### Objetivo
Generar un video MP4 tradicional que se reproduce de principio a fin sin interrupciones, listo para proyectar en aula, subir a YouTube o compartir por mensajería.

### Paso 1: Iniciar la Conversación
Hablas directamente con el **Antigravity Coordinator**.

**Ejemplo de Prompt:**
> *"Hola. Quiero crear un video explicativo común a partir de este archivo `presentacion_ia.pptx`. Usá el logo adjunto `sello educai.jpg` para los colores institucionales y una voz en español argentino. El video debe ser continuo y directo."*

*(Nota: Como no dijiste "sin subtítulos", el video incluirá automáticamente los subtítulos estilo CapCut).*

### Paso 2: Ejecución del Flujo por los Agentes
1. **Doc Parser & Scriptwriter:** Extrae diapositivas y **notas del orador** del PPTX para construir el guion y estructurar `scenes.json`.
2. **Brand & Theme Architect:** Cuantiza el logo, extrayendo 8 colores armónicos en `theme_config.json` y generando las variables CSS en `DESIGN.md`.
3. **Voice & Timings Specialist:** Convierte el guion a voz argentina (`es-AR-ElenaNeural` a `-2%` de velocidad) usando EdgeTTS con `boundary="WordBoundary"`. Genera `audio_timeline.json` y `word_timings.json` (marcas por palabra para los subtítulos).
4. **Pre-Render QA Gatekeeper:** Abre la composición en Chromium headless y verifica que no existan errores de consola ni desajustes entre audio y gráficos.
5. **Visual Render & Stitcher:** Renderiza los fotogramas deterministas a 24 fps con los subtítulos dinámicos integrados, mezcla el audio estéreo con retardos milimétricos (`adelay`) y concatena el cierre institucional `ending_norm.mp4`.
6. **Post-Render QA Gatekeeper:** Audita con `ffprobe` que el video final tenga stream de video H.264 (1080p), audio AAC estéreo a 44.1 kHz y que `silencedetect` no arroje cortes abruptos.

### Resultado Entregado
* Archivo final: `films/mi-leccion/Introduccion_EducAI_Final.mp4`.

### Ejecución equivalente por CLI:
```powershell
# Con subtítulos CapCut por defecto
python -m core.orchestrator `
  --project-dir "films/mi-leccion" `
  --doc "presentacion_ia.pptx" `
  --theme-image "sello educai.jpg" `
  --voice "es-AR-ElenaNeural" `
  --title "Introduccion a la IA"

# Si el usuario pidiera expresamente SIN subtítulos:
python -m core.orchestrator `
  --project-dir "films/mi-leccion" `
  --doc "presentacion_ia.pptx" `
  --no-captions `
  --title "Introduccion a la IA"
```

---

## 4. Flujo 2: Creación de un "Video-Cuestionario SCORM" (Interactivo para Moodle)

### Objetivo
Generar un recurso de aprendizaje activo para Moodle LMS. El video se detiene automáticamente en momentos pedagógicos estratégicos y muestra preguntas en pantalla. El estudiante no puede saltear la pregunta sin responder, y su calificación se reporta automáticamente al libro de calificaciones de Moodle.

### Paso 1: Iniciar la Conversación
Hablas directamente con el **Antigravity Coordinator**, solicitando explícitamente la interactividad o evaluación.

**Ejemplo de Prompt:**
> *"Hola. Quiero transformar este documento `modulo1_didactica.docx` en un video-cuestionario interactivo SCORM para Moodle. Necesito que al final de cada sección importante haga una pregunta formativa de opción múltiple para verificar que el alumno comprendió el tema antes de continuar."*

### Paso 2: Detección y Sincronía de Preguntas (Invariante 1)
El subagente **Doc Parser & Scriptwriter** detecta los cierres temáticos y formula las preguntas (`checkpoints`).
* **Regla Invariante No Negociable:**  
  La pausa de la pregunta se posiciona en:
  $$\text{timestamp} = \text{fin de la alocución de la escena} + 0.05\text{s}$$
  **Está estrictamente prohibido cortar la voz del docente a mitad de una frase o concepto.**

### Paso 3: Renderizado y Post-QA
Se produce el video base MP4 (`*_EducAI_Final.mp4`) siguiendo las mismas fases de calidad del video común (incluyendo los subtítulos estilo CapCut).

### Paso 4: Empaquetado Dual SCORM 1.2 (Invariante 2)
El subagente **SCORM Packager Specialist** toma el video auditado y la lista de checkpoints (`scorm_checkpoints.json`) y construye el paquete web SCORM:
1. **Seguridad en Pantalla Completa:** Bloquea la pantalla completa nativa del reproductor (`controlsList="nofullscreen"`) y la redirecciona al contenedor `#player-container`. Esto garantiza que los formularios de preguntas se vean siempre por encima del video.
2. **Generación Dual ZIP:**
   * **`*_SCORM_Completo.zip` (Autocontenido):** Contiene el reproductor HTML, el archivo `imsmanifest.xml` y el archivo `.mp4` adentro. Ideal para plataformas Moodle que permiten subir archivos de 50 a 100 MB.
   * **`*_SCORM.zip` (Zero-Weight Shell < 400 KB):** Contiene el reproductor inteligente y la lógica de preguntas, pero apunta a una URL directa del video alojada en un servidor o CDN. Supera cualquier restricción de cuota de subida (ej. límites estrictos de 10 MB en campus universitarios).

### Paso 5: Despliegue en Moodle LMS por el Docente
1. En el curso de Moodle, hacer clic en **Activar edición**.
2. Seleccionar **Añadir una actividad o un recurso** $\to$ **Paquete SCORM**.
3. Arrastrar el archivo `*_SCORM_Completo.zip` (o `*_SCORM.zip`).
4. En la sección **Calificación**:
   * *Método de calificación:* **Calificación más alta** o **Promedio de intentos**.
   * *Calificación para aprobar:* Ej. `70` (o `7` según la escala).
5. En la sección **Ajustes de visualización**:
   * Abrir en: **Ventana actual** o **Nueva ventana**.
6. Guardar cambios. Al reproducir, Moodle registrará el avance y la nota obtenida en el intento (`cmi.core.lesson_status` y `cmi.core.score.raw`).

### Ejecución equivalente por CLI:
```powershell
python -m core.orchestrator `
  --project-dir "films/modulo1-didactica" `
  --doc "modulo1_didactica.docx" `
  --theme-image "sello educai.jpg" `
  --title "Modulo 1 Didactica" `
  --voice "es-AR-ElenaNeural"
```

---

## 5. Cuadro Comparativo: Video Común vs. Video-Cuestionario SCORM

| Dimensión | Video Común (Lineal) | Video-Cuestionario SCORM |
| :--- | :--- | :--- |
| **Formato de Entrega** | Archivo único `.mp4` (H.264/AAC). | Paquetes comprimidos `.zip` (SCORM 1.2 Dual). |
| **Interactividad** | Pasiva (reproducción continua de principio a fin). | Activa (pausas obligatorias con preguntas formativas). |
| **Evaluación de Estudiantes** | Sin evaluación ni registro. | Califica automáticamente en el libro de calificaciones de Moodle. |
| **Subtítulos CapCut** | **Sí, por defecto** (Opt-out con `--no-captions`). | **Sí, por defecto** (Opt-out con `--no-captions`). |
| **Outro Institucional** | Concatenado al final (`ending_norm.mp4`). | Concatenado al final (`ending_norm.mp4`). |
| **Reproductor Utilizado** | Cualquier reproductor estándar (VLC, web, móvil). | Reproductor HTML5 seguro con wrapper SCORM 1.2. |
| **Canales de Publicación** | YouTube, WhatsApp, Google Drive, televisión, web. | Moodle, Blackboard, Canvas LMS, Chamilo. |
| **Agente Final Involucrado** | Visual Render & Outro Stitcher. | SCORM Packager Specialist. |

---

## 6. Buenas Prácticas y Resolución de Problemas

1. **Reanudación de Renders (Invariante 3):**
   Si el proceso de render se interrumpió y la carpeta `frames/` ya contiene los cuadros PNG, no vuelvas a renderizar desde cero. Ejecuta el pipeline con `--skip-render` o directamente el multiplexado para ahorrar tiempo y cómputo.
2. **Audio con pausas limpias:**
   Nunca concatenes archivos de audio en bruto; el sistema utiliza `adelay` estéreo para insertar `0.55s` de silencio natural entre escenas, permitiendo que el cerebro del estudiante asimile cada idea.
3. **Validación Previa Obligatoria:**
   Antes de renderizar un video extenso, asegúrate de que el gate `pre_render.py` reporte `passed: true`. Esto evita sorpresas de tipografías faltantes o preguntas superpuestas a la voz.
