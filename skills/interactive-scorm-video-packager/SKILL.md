---
name: interactive-scorm-video-packager
description: Empaquetador de videos interactivos en paquetes SCORM 1.2 ultra-livianos (< 500 KB) con arquitectura Zero-Weight Shell para Moodle. Integra pausas de video, preguntas formativas en pantalla y calificación automática en el LMS.
---

# Interactive SCORM Video Packager (Zero-Weight Architecture)

Esta habilidad resuelve el problema de las cuotas de subida en Moodle para videos extensos (de 5 a 30+ minutos), encapsulando la interactividad y la calificación en un contenedor ultraliviano.

## 📌 Principio Técnico: Zero-Weight Shell

- **El problema:** Subir un video Full HD de 15 minutos dentro de un ZIP SCORM tradicional pesa >80 MB y falla en la mayoría de los servidores Moodle limitados a 10-20 MB.
- **La solución:** 
  1. El video `.mp4` reside en un servidor de streaming o CDN (o en el repositorio multimedia del campus).
  2. El paquete SCORM (`.zip`) contiene **exclusivamente el reproductor inteligente, el listener de marcas de tiempo y el API Wrapper SCORM 1.2**.
  3. **Peso final del ZIP:** Menor a **400 KB** (subida instantánea garantizada).

## 🚀 Uso del Empaquetador CLI

```powershell
python core/scorm/scorm_packager.py `
  --title "Protocolo de Relevamiento EducAI" `
  --video-url "https://servidor-educai.com/videos/protocolo.mp4" `
  --checkpoints-json "checkpoints.json" `
  --output "Protocolo_Interactivo_SCORM.zip"
```

## Estructura de Checkpoints JSON

```json
[
  {
    "timestamp": 85.0,
    "question": "¿Cuál es el zoom recomendado para capturar la vista vertical del aula?",
    "options": [
      "120% para ver textos grandes",
      "67% u 80% para registrar la panorámica completa",
      "100% estándar"
    ],
    "correct_index": 1,
    "feedback_ok": "¡Correcto! Maximiza el registro de la secuencia vertical.",
    "feedback_error": "Incorrecto. Se recomienda 67% u 80%."
  }
]
```

## Calificación en Moodle
El reproductor reporta automáticamente a la API SCORM de Moodle:
- `cmi.core.score.raw` (porcentaje acumulado de respuestas correctas 0 a 100).
- `cmi.core.lesson_status` (`passed` si el puntaje >= 60%, de lo contrario `completed` o `incomplete`).
