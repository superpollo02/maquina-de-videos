---
name: tiktok-word-captions
description: Genera subtítulos dinámicos a nivel de palabra con resaltado activo estilo TikTok/Reels sincronizados con la locución TTS para videos en Canvas 2D/HTML5 o exportación FFmpeg (.ass).
---

# TikTok Word-Level Captions

Esta habilidad genera subtítulos de alto impacto con **sincronía palabra por palabra** y resaltado visual activo (estilo karaoke/TikTok) para el motor determinista `render(t)` o quemado directo con FFmpeg.

## 📌 Principios de Diseño y Sincronía

1. **Extracción de Marcas de Tiempo por Palabra:**
   - Captura eventos `WordBoundary` directamente desde `edge-tts` (o alineación forzada/Whisper cuando el audio es pregrabado) guardando `[{ word, start, end }]` en `word_timings.json`.
   - Escala los tiempos respecto a `audio_dur` real medido con `ffprobe` para evitar desfasajes en videos largos.

2. **Agrupación en Bloques Cortos (Chunks):**
   - Agrupa de **3 a 5 palabras por bloque** (máximo 1–2 líneas, sin cortar frases en conectores débiles).
   - Cada bloque permanece visible únicamente entre `chunk[0].start` y `chunk[-1].end`.

3. **Estilo Visual (Alto Contraste y Legibilidad):**
   - Tipografía sans-serif gruesa (`800`/`900`, mayúsculas o *Title Case*), borde oscuro (`strokeText`) + sombra proyectada o píldora semitransparente detrás del bloque (*scrim*).
   - **Palabra inactiva:** blanco (`#ffffff`) con opacidad alta.
   - **Palabra activa (`t >= w.start && t <= w.end`):** color de acento de marca (ej. Amarillo `#facc15`, Cian `#38bdf8` o Coral `#f97316`) con leve escala (`1.08x`) sin provocar saltos de línea (*layout shift*).

## 🚀 Integración en el Pipeline

### A. Extracción con `edge-tts` (`WordBoundary`) o mediante `ToolRegistry`
> [!IMPORTANT]
> En `edge-tts >= 7.3.1`, el parámetro `boundary` es por defecto `'SentenceBoundary'`. Debe pasarse explícitamente `boundary="WordBoundary"` para emitir marcas de tiempo por palabra, o utilizar el adaptador integrado `EdgeTTS` (`python -m core.orchestrator` / `registry.get("edge_tts")`).

```python
import edge_tts, asyncio, json

async def synthesize_with_words(text, voice, out_mp3, out_json):
    # En edge-tts >= 7.3.1 es mandatorio pasar boundary="WordBoundary"
    communicate = edge_tts.Communicate(text, voice, boundary="WordBoundary")
    words = []
    with open(out_mp3, "wb") as f:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                start = chunk["offset"] / 10_000_000
                dur = chunk["duration"] / 10_000_000
                words.append({"word": chunk["text"], "start": round(start, 3), "end": round(start + dur, 3)})
    with open(out_json, "w", encoding="utf-8") as jf:
        json.dump(words, jf, ensure_ascii=False, indent=2)
```

### B. Renderizado Determinista en Canvas (`window.render(t)`)
- Calcular el ancho total de cada palabra del bloque activo usando `ctx.measureText(w.word + " ")` antes de dibujar, para centrar el bloque de forma fija y evitar vibración horizontal cuando la palabra activa cambia de escala.
- Dibujar primero la sombra/borde (`ctx.strokeText`) y luego el relleno (`ctx.fillText`) con el color de acento si `t >= w.start && t <= w.end`.
- Mantener la zona de subtítulos dentro del tercio inferior seguro (por encima de la barra de controles en 16:9, y evitando el 20% inferior en 9:16).

### C. Alternativa Rápida en FFmpeg (`.ass`)
- Para quemar subtítulos sobre videos ya renderizados, generar un archivo SubStation Alpha (`.ass`) usando etiquetas karaoke `\kf` (duración en centésimas de segundo) y aplicar con:
  ```powershell
  ffmpeg -y -i video.mp4 -vf "ass=captions.ass" -c:a copy video_subtitled.mp4
  ```
