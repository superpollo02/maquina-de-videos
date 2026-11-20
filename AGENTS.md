# Reglas de Producción — Máquina de Videos · EducAI

## 1. Sincronía de Preguntas Interactivas y Locución (Invariante)
- **Prohibido cortar la narración:** Todo bloque de preguntas (`checkpoint`) en un video interactivo SCORM debe ubicarse **al finalizar la alocución de la escena** (usando el tiempo `end` de `audio_timeline.json` o el silencio entre escenas, con un margen de `+0.05s` a `+0.1s`), nunca en medio de una frase o discurso.
- **Tolerancia de disparo:** En el reproductor (`timeupdate`), usar una ventana de captura amplia (ej. `curT >= cp.timestamp && curT <= cp.timestamp + 1.2`) para evitar que saltos de fotogramas o adelantos omitan la pausa.

## 2. Empaquetado SCORM Interactivo para Moodle
- **Coincidencia exacta de archivo:** Verificar siempre que `<source src="...">` en `index.html` coincida exactamente con el nombre del `.mp4` final (ej. `*_EducAI_Final.mp4`) o con una URL HTTP directa con soporte de *byte-range*.
- **Pantalla completa segura:** Deshabilitar el botón nativo de pantalla completa del `<video>` (`controlsList="nofullscreen"`) y proveer un botón de pantalla completa sobre `#player-container`. En HTML5, maximizar `<video>` directamente oculta los overlays de preguntas detrás del video.
- **Indicador de interactividad:** Mostrar en la barra superior un indicador permanente del próximo checkpoint (`Próxima Pregunta: <Sección> (en MM:SS)`) para que docentes y estudiantes sepan de inmediato que el recurso contiene pausas evaluativas.
- **Empaquetado Dual:**
  - **Autocontenido (`*_SCORM_Completo.zip`):** Incluye `index.html`, `imsmanifest.xml` (declarando el `.mp4` como `<file href="..."/>`) y el `.mp4` adentro, cuando el tamaño entra en la cuota de Moodle.
  - **Zero-Weight (`*_SCORM.zip`):** Solo `index.html` e `imsmanifest.xml` (< 10 KB) apuntando a un servidor HTTP/CDN directo (no YouTube en `<video src>` por CORS).

## 3. Reanudación de Renders Inconclusos
- Antes de re-renderizar desde cero un proyecto en `films/<nombre>/`, verificar `frames/` y `video_raw.mp4`.
- Si los fotogramas PNG están completos en `frames/` pero `video_raw.mp4` quedó en 0 bytes o corrupto, retomar directamente desde la codificación FFmpeg, el multiplexado con `audio_mixed.m4a` y la concatenación con `ending_norm.mp4`.

## 4. Gates de Calidad Obligatorios (Pre-Render y Post-Render)
- **Pre-Render (`pre-render-composition-validator`):** Antes de renderizar fotogramas, validar existencia de assets, coincidencia de duración entre `audio_mixed.m4a` / `audio_timeline.json` y `render_frames.js`, cero errores JS en headless Chrome y sincronía de checkpoints SCORM al fin de locución.
- **Post-Render (`post-render-video-qa`):** Después de generar el MP4 final y antes de entregar, extraer fotogramas clave con FFmpeg e inspeccionarlos visualmente (fondos, subtítulos, márgenes) junto con verificación `ffprobe` de audio/video sin cortes abruptos.

