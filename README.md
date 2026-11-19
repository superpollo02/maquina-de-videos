# Máquina de Videos · EducAI

Estudio y motor generador de videos explicativos e instructivos en código (Canvas 2D / WebGL / Three.js / HTML5 + Síntesis de Audio y TTS). Impulsado por la arquitectura **Lemo-Opuscar** y **Google Antigravity**.

---

## 📚 Índice de Contenidos
1. [Requisitos y Configuración del Sistema](#1-requisitos-y-configuración-del-sistema)
2. [Arquitectura y Filosofía del Pipeline](#2-arquitectura-y-filosofía-del-pipeline)
3. [Tutorial Paso a Paso: Cómo Crear un Video](#3-tutorial-paso-a-paso-cómo-crear-un-video)
   - [Paso 1: Guion y Tratamiento (`TREATMENT.md`)](#paso-1-guion-y-tratamiento-treatmentmd)
   - [Paso 2: Generación de Voz en Off y Subtítulos (TTS)](#paso-2-generación-de-voz-en-off-y-subtítulos-tts)
   - [Paso 3: Composición de Música y Foley Acústico](#paso-3-composición-de-música-y-foley-acústico)
   - [Paso 4: Maquetación del Lienzo Dinámico (`index.html`)](#paso-4-maquetación-del-lienzo-dinámico-indexhtml)
   - [Paso 5: Renderizado Cuadro a Cuadro a 24 FPS](#paso-5-renderizado-cuadro-a-cuadro-a-24-fps)
   - [Paso 6: Ensamble, Multiplexado y Outro Institucional](#paso-6-ensamble-multiplexado-y-outro-institucional)
4. [Catálogo de Estilos Visuales Disponibles (99 Estilos)](#4-catálogo-de-estilos-visuales-disponibles)
5. [Buenas Prácticas y Resolución de Problemas](#5-buenas-prácticas-y-resolución-de-problemas)

---

## 1. Requisitos y Configuración del Sistema

Para operar el estudio y renderizar videos en alta resolución (1080p a 24/30/60 fps) se requieren los siguientes componentes:

### Herramientas del Sistema (CLI / Binarios)
- **Node.js (v20+):** Motor de ejecución para automatizar el navegador headless y orquestar las escenas.
- **Google Chrome o Microsoft Edge:** Navegador Chromium utilizado por Playwright / Puppeteer en modo `--headless` para rasterizar cada fotograma.
- **FFmpeg (v7.0+):** Codificador multimedia para componer audio multicanal, compresión de video H.264 (libx264) y multiplexado final.
- **Python (3.11+):** Para síntesis de audio, generación de ondas sonoras y llamado a servicios de TTS.

### Dependencias de Paquetes
- **NPM:**
  ```bash
  npm install playwright-core
  ```
- **Python:**
  ```bash
  pip install edge-tts
  ```

---

## 2. Arquitectura y Filosofía del Pipeline

A diferencia de las herramientas tradicionales de IA generativa de video (que inventan píxeles impredecibles y texto ilegible), esta máquina de video opera bajo el principio:

> **"La imagen es una función matemática determinista del tiempo: `render(t)`"**

```
                     ┌──────────────────┐
                     │ Texto / Contenido│
                     └────────┬─────────┘
                              │
               ┌──────────────┴──────────────┐
               ▼                             ▼
       [Audio & Tiempo]              [Lienzo Visual]
      edge-tts (Locución)           HTML5 Canvas / CSS
               │                             │
    Marcas de tiempo (.json)         window.render(t)
               │                             │
    Pista musical sintetizada                │
               │                             │
       Mezcla (FFmpeg)                       │
               │                             │
               ▼                             ▼
        audio_mixed.m4a              Frames PNG (Playwright)
               │                             │
               └──────────────┬──────────────┘
                              ▼
                  video_raw.mp4 (libx264)
                              │
                              ▼
                + ending. educai.mp4 (Concat)
                              │
                              ▼
                   VIDEO_FINAL_1080P.mp4
```

### Ventajas de este enfoque:
- **100% Determinista:** Cualquier cuadro a los `t = 28.5s` se reproduce idéntico en cualquier máquina.
- **Tipografía y Gráficos Nítidos:** Sin distorsiones; textos, diagramas vectoriales, logos y tablas conservan precisión milimétrica.
- **Sincronización Exacta:** Cada elemento visual se dibuja exactamente en el segundo y milisegundo en que la voz lo pronuncia.

---

## 3. Tutorial Paso a Paso: Cómo Crear un Video

A continuación se detalla el procedimiento estándar utilizado para producir los videos de la plataforma.

### Paso 1: Guion y Tratamiento (`TREATMENT.md`)
Todo proyecto comienza creando una subcarpeta dentro de `films/<nombre-del-proyecto>/`.
1. Redacta el guion estructurado en bloques de ideas claras.
2. Define los colores del marcador, el estilo visual (ej. `whiteboard`, `iso-infographic`, `blueprint`) y el ritmo pedagógico.
3. Ejemplo de archivo: `films/mi-proyecto/TREATMENT.md`.

### Paso 2: Generación de Voz en Off y Subtítulos (TTS)
La voz se genera mediante `edge-tts` dividida en segmentos para extraer su duración exacta con `ffprobe`.

```python
# gen_audio.py
import asyncio, subprocess, json, edge_tts

segments = [
    ("seg_01", "Texto del primer bloque temático..."),
    ("seg_02", "Texto del segundo bloque temático...")
]

async def main():
    total_t = 0.0
    meta = []
    for name, text in segments:
        file = f"{name}.mp3"
        # Voz rioplatense femenina
        c = edge_tts.Communicate(text, "es-AR-ElenaNeural", rate="-2%")
        await c.save(file)
        
        dur = float(subprocess.check_output([
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", file
        ]).decode().strip())
        
        meta.append({"name": name, "start": total_t, "duration": dur, "end": total_t + dur})
        total_t += dur + 0.45 # Pausa pedagógica
        
    with open("timing.json", "w", encoding="utf-8") as f:
        json.dump({"total": total_t, "segments": meta}, f, indent=2)

asyncio.run(main())
```

### Paso 3: Composición de Música y Foley Acústico
Se genera una base instrumental armónica minimalista (marimba / piano suave a 116-120 BPM) calculada a la duración total del video:

```python
# gen_music.py
import math, wave, struct

sr = 44100
dur = 168.0 # Duración en segundos
# Síntesis matemática senoidal con decaimiento exponencial (timbre marimba)
...
```

Luego se combinan la voz y la música con FFmpeg aplicando ducking/volumen balanceado:
```bash
ffmpeg -y -i narration.wav -i music.wav -filter_complex "[1:a]volume=0.18[bg];[0:a][bg]amix=inputs=2:duration=first[out]" -map "[out]" -c:a aac -b:a 192k audio_mixed.m4a
```

### Paso 4: Maquetación del Lienzo Dinámico (`index.html`)
Se crea una página web autónoma de **1920x1080** con una función global `window.render(t)`.

```html
<!DOCTYPE html>
<html>
<head>
  <style>
    * { margin:0; padding:0; box-sizing:border-box; }
    body, canvas { width:1920px; height:1080px; overflow:hidden; background:#ffffff; }
  </style>
</head>
<body>
  <canvas id="stage" width="1920" height="1080"></canvas>
  <script>
    const canvas = document.getElementById('stage');
    const ctx = canvas.getContext('2d');

    // Función de interpolación suave
    function smoothstep(min, max, t) {
      let x = Math.max(0, Math.min(1, (t - min) / (max - min)));
      return x * x * (3 - 2 * x);
    }

    window.render = function(t) {
      ctx.clearRect(0, 0, 1920, 1080);
      
      // Fondo y textura de pizarra
      ...
      
      // Acto 1 (0 a 30s): Dibujar diagramas con t
      let a1 = smoothstep(0.5, 3.0, t);
      ctx.fillStyle = `rgba(2, 132, 199, ${a1})`;
      ctx.fillText("Título del Módulo", 200, 150);
      
      // Subtítulos dinámicos basados en t
      drawSubtitles(t);
    };
  </script>
</body>
</html>
```

### Paso 5: Renderizado Cuadro a Cuadro a 24 FPS
Para evitar problemas de cuelgues o pérdidas de sincronización por pipes de memoria, los fotogramas se capturan en disco y luego se ensamblan con FFmpeg:

```javascript
// render_frames.js
const { chromium } = require('playwright-core');
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

async function main() {
  const fps = 24;
  const dur = 165.87;
  const totalFrames = Math.floor(dur * fps);
  const framesDir = path.join(__dirname, 'frames');
  if (!fs.existsSync(framesDir)) fs.mkdirSync(framesDir);

  const browser = await chromium.launch({
    executablePath: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
    headless: true
  });
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
  await page.goto('file:///' + path.join(__dirname, 'index.html').replace(/\\/g, '/'));

  for (let f = 0; f < totalFrames; f++) {
    const framePath = path.join(framesDir, `frame_${String(f).padStart(5, '0')}.png`);
    if (!fs.existsSync(framePath)) {
      const t = f / fps;
      await page.evaluate((time) => window.render(time), t);
      await page.screenshot({ path: framePath });
    }
  }
  await browser.close();

  // Codificación a video MP4
  spawn('ffmpeg', [
    '-y', '-r', fps.toString(),
    '-i', path.join(framesDir, 'frame_%05d.png'),
    '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-preset', 'fast', '-crf', '18',
    'video_raw.mp4'
  ]);
}
main();
```

### Paso 6: Ensamble, Multiplexado y Outro Institucional
1. **Unir Video y Audio del explicador:**
   ```bash
   ffmpeg -y -i video_raw.mp4 -i audio_mixed.m4a -c:v copy -c:a aac -b:a 192k whiteboard_with_audio.mp4
   ```

2. **Concatenar con el Outro Institucional EducAI:**
   Se crea un archivo `concat_list.txt`:
   ```
   file 'whiteboard_with_audio.mp4'
   file 'ending_norm.mp4'
   ```
   Y se genera la copia final sin pérdida:
   ```bash
   ffmpeg -y -f concat -safe 0 -i concat_list.txt -c copy VIDEO_FINAL_1080P.mp4
   ```

---

## 4. Catálogo de Estilos Visuales Disponibles

El motor cuenta con **99 estilos visuales** en código categorizados en:
- **Sketch & Board:** `whiteboard` (Pizarra blanca explicativa), `chalkboard` (Pizarra tiza), `sketchnote` (Apuntes visuales), `ipad-sketch`.
- **Line Diagrams & Blueprint:** `blueprint` (Plano técnico azul), `iso-infographic` (Infografía isométrica 3D), `exploded-teardown` (Despiece técnico), `instruction-manual` (Manual estilo IKEA).
- **Screens & Interfaces:** `dark-keynote` (Lanzamiento tecnológico estilo Apple), `app-flythrough` (Recorrido de UI de aplicaciones), `spreadsheet-film`.
- **Traditional Crafts & Art:** `chinese-ink` (Aguada oriental), `ukiyo-e` (Grabado japonés), `paper-cut` (Papel calado), `risograph`.
- **Data & Maps:** `data-storytelling` (Gráficos interactivos dinámicos), `transit-map` (Líneas tipo metro).

---

## 5. Buenas Prácticas y Resolución de Problemas

1. **Gestión de Memoria en Renders Largos:**
   - Para videos de más de 60 segundos (>1500 cuadros), guardar cuadros temporales en una subcarpeta `frames/` garantiza que si se interrumpe el proceso, este se reanuda sin perder el avance.
2. **Normalización de Formato para Concat:**
   - Los videos a concatenar deben compartir la misma resolución (`1920x1080`), tasa de cuadros (`24 fps`) y formato de audio (`44100 Hz stereo / mono`).
3. **Subtítulos Quemados e Inclusivos:**
   - Reservar siempre el 12% inferior del fotograma libre de información crítica para que los subtítulos no tapen diagramas ni textos explicativos.
