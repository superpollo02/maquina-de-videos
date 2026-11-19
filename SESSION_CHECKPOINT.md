# Estado de la Sesión - Continuación Próxima Vez

**Fecha:** 18 de Noviembre de 2026
**Proyecto:** Máquina de Videos · EducAI (`F:\proyectos antigrtavity\maquina de videos`)
**Repositorio GitHub:** [https://github.com/superpollo02/maquina-de-videos](https://github.com/superpollo02/maquina-de-videos)

---

## 1. Video 1: La Estructura Tripartita del Aula (Completado y Mapeado)
- **Archivo final:** `films/estructura-tripartita/Estructura_Tripartita_EducAI_Final.mp4` (80.3s, 1080p, Whiteboard Explainer + Outro EducAI).
- **Código y assets:** Sincronizados y commiteados en rama `main`.

---

## 2. Video 2: Protocolo de Relevamiento y Diagnóstico (En Progreso)
- **Tema:** Guía de inicio y protocolo de relevamiento para docentes (Zoom 67-80%, Capturas representativas, Voice Memo 3-5 min, Checklist de Diagnóstico).
- **Duración estimada:** ~166 segundos de contenido + 10s outro institucional (total ~176s).
- **Audio narración:** `films/protocolo-relevamiento/narration.wav` (Voz femenina rioplatense `es-AR-ElenaNeural`).
- **Música de fondo:** `films/protocolo-relevamiento/music.wav` sintetizada a 116 BPM.
- **Audio mezclado:** `films/protocolo-relevamiento/audio_mixed.m4a` (165.8s).
- **Lienzo Whiteboard interactivo:** `films/protocolo-relevamiento/index.html`.
- **Renderizado cuadro a cuadro:** `films/protocolo-relevamiento/render_video.js` (generando `video_raw.mp4`, 3980 fotogramas).

---

## 3. Próximos Pasos al Retomar
1. Verificar finalización de `video_raw.mp4` en `films/protocolo-relevamiento/`.
2. Muxear video y audio:
   ```powershell
   ffmpeg -y -i films/protocolo-relevamiento/video_raw.mp4 -i films/protocolo-relevamiento/audio_mixed.m4a -c:v copy -c:a aac -b:a 192k -shortest films/protocolo-relevamiento/whiteboard_with_audio.mp4
   ```
3. Concatenar con `ending_norm.mp4` para generar `films/protocolo-relevamiento/Protocolo_Relevamiento_EducAI_Final.mp4`.
4. Hacer commit y push a GitHub (`git add . && git commit -m "..." && git push`).
