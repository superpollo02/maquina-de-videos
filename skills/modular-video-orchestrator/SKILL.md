---
name: modular-video-orchestrator
description: Orquestador y compilador de videos largos por lotes de escenas. Renderiza cada escena de 40 a 90 segundos con caché de fotogramas en disco y realiza el stitching y ensamble final sin desbordes de memoria.
---

# Modular Video Orchestrator

Esta habilidad resuelve el cuello de botella técnico del renderizado de videos extensos (más de 5 a 20 minutos). En lugar de renderizar decenas de miles de fotogramas continuos en un solo proceso (lo cual provoca saturación de RAM y cuelgues), la orquestación se realiza de forma **modular por escenas**.

## 📌 Principios de Arquitectura

1. **Partición en Escenas Autónomas:**
   - La lección se divide en $N$ escenas de 40 a 90 segundos a partir de `scenes.json`.
   - Cada escena genera su locución (`scene_XX_audio.mp3`) y su video (`scene_XX.mp4`).

2. **Caché en Disco (Disk-Frame Cache):**
   - Los fotogramas PNG se escriben secuencialmente en carpetas temporales (`frames/scene_XX/`).
   - Si el proceso se interrumpe o la máquina se reinicia, el renderizador retoma desde el último fotograma guardado sin perder el trabajo anterior.

3. **Stitcher & Multiplexer con FFmpeg:**
   - Ensambla todas las escenas con el filtro concat de FFmpeg sin recodificación innecesaria (`-c copy`).
   - Integra automáticamente el video de cierre institucional (`ending. educai.mp4`).

## 🚀 Flujo de Ejecución

```
scenes.json 
   ├── Escena 1 (00:00 - 01:15) ──► scene_01.mp4
   ├── Escena 2 (01:15 - 02:30) ──► scene_02.mp4
   └── Escena 3 (02:30 - 04:00) ──► scene_03.mp4
                                       │
                                       ▼ Concat Stitcher
                            Leccion_Completa_Final.mp4
```
