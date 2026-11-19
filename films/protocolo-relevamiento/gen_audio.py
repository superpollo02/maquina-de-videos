import asyncio
import edge_tts
import json
import subprocess

# 10 comprehensive instructional segments designed to comfortably exceed 120 seconds
segments = [
    ("seg_01", "Estimado docente: para auditar la lógica actual de su aula virtual en Moodle y planificar la renovación bajo la Estructura Tripartita, en EducAI realizamos un diagnóstico exhaustivo mediante un asistente de inteligencia artificial especializado en andragogía."),
    ("seg_02", "Dado que los campus virtuales son entornos cerrados y protegidos a los que las herramientas automatizadas no pueden ingresar directamente, necesitamos que nos proporcione la documentación visual y sonora de su curso siguiendo este protocolo."),
    ("seg_03", "Paso uno: Preparación del Navegador. Abra su aula virtual en Moodle desde la computadora. Ajuste el zoom de la pantalla al mínimo, por ejemplo al sesenta y siete u ochenta por ciento. Esto permitirá registrar la mayor cantidad de elementos y la imagen general de la secuencia vertical en cada captura."),
    ("seg_04", "Paso dos: Registro Visual en Capturas de Pantalla. En primer lugar, tome capturas ordenadas de la vista principal del curso que muestren la secuencia de las secciones, el maquetado gráfico, los banners y el orden de las unidades de arriba a abajo mediante el desplazamiento vertical."),
    ("seg_05", "A continuación, tome una muestra representativa de los recursos. Ingrese a al menos un recurso de cada tipo: haga clic en un video incrustado, un documento PDF, una página de texto y un cuestionario, tomando una captura interna de cada uno."),
    ("seg_06", "Para el envío, agrupe todas las imágenes ordenadas, completas y sin duplicados dentro de una sola carpeta o en un archivo comprimido punto zip."),
    ("seg_07", "Paso tres: Grabación de la Nota de Audio de Observación. Grabe un audio breve, de tres a cinco minutos, desde su teléfono o computadora mientras navega por su aula virtual, detallando tres aspectos esenciales."),
    ("seg_08", "Primero, la disposición: qué elementos siente dispersos o difíciles de encontrar. Segundo, formato y estética: qué imágenes, tamaños de letra o estilos desearía renovar. Y tercero, los puntos de dolor: qué partes del curso actual le generan más consultas o dificultades técnicas a los estudiantes."),
    ("seg_09", "Finalmente, complete el Checklist de Relevamiento de Diagnóstico: nombre de la asignatura, verificación de la carpeta de capturas, el audio de observación y el archivo de respaldo del aula si está disponible."),
    ("seg_10", "Este instrumento audita la identidad visual y define el alcance para La Clase, La Lectura y La Práctica, así como la modalidad de trabajo: entrega de paquetes SCORM o implementación directa por el equipo de EducAI en su plataforma.")
]

async def generate():
    meta = []
    total_t = 0.0
    for name, text in segments:
        mp3_path = f"films/protocolo-relevamiento/{name}.mp3"
        c = edge_tts.Communicate(text, "es-AR-ElenaNeural", rate="-2%")
        await c.save(mp3_path)
        
        # probe duration
        res = subprocess.check_output([
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", mp3_path
        ])
        dur = float(res.decode().strip())
        meta.append({
            "name": name,
            "text": text,
            "file": mp3_path,
            "start": round(total_t, 3),
            "duration": round(dur, 3),
            "end": round(total_t + dur, 3)
        })
        total_t += dur + 0.55  # clear pedagogical pause between steps

    print(f"Total narration duration: {round(total_t, 3)} seconds")
    with open("films/protocolo-relevamiento/timing.json", "w", encoding="utf-8") as f:
        json.dump({"total": round(total_t, 3), "segments": meta}, f, indent=2, ensure_ascii=False)

asyncio.run(generate())
