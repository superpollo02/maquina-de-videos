# Máquina de Videos · EducAI

Estudio y motor generador de videos pedagógicos y explicativos en código impulsado por **Lemo-Opuscar** y **Antigravity**.

## Proyectos

### 1. La Estructura Tripartita del Aula (EducAI)
- **Tema:** Modelo instruccional estandarizado en Moodle (Clase → Lectura → Práctica).
- **Estilo:** Whiteboard Explainer (`whiteboard`).
- **Narración:** Voz femenina rioplatense (`es-AR-ElenaNeural`).
- **Música:** Minimalista a 120 BPM sintetizada.
- **Resolución:** Full HD 1080p (1920x1080) @ 24 fps.
- **Salida:** `films/estructura-tripartita/Estructura_Tripartita_EducAI_Final.mp4`.

## Pipeline de Generación
1. Tratamiento y guion (`TREATMENT.md` y `script.txt`).
2. Generación de locución y subtítulos con `edge-tts`.
3. Renderizado de lienzos canvas HTML5 sincronizados cuadro a cuadro con Chrome headless.
4. Mezcla sonora y masterización con `ffmpeg`.
