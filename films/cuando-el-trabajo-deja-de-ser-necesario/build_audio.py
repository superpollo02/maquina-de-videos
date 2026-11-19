"""
Audio Generation and Timing Pipeline for 'Cuando el trabajo deja de ser necesario'.
Generates speech for all 7 scenes using edge-tts (es-AR-ElenaNeural),
computes precise durations with ffprobe, synthesizes a matching zero-copyright
ambient music track, mixes the master audio, and exports checkpoints with exact timestamps.
"""

import os
import sys
import json
import math
import wave
import struct
import asyncio
import subprocess
from pathlib import Path
import edge_tts

PROJECT_DIR = Path("films/cuando-el-trabajo-deja-de-ser-necesario")
SCENES_FILE = PROJECT_DIR / "scenes.json"

async def generate_speech_and_timing():
    with open(SCENES_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    scenes = data["scenes"]
    timeline = []
    total_time = 0.0

    print(f"Generando locuciones para {len(scenes)} escenas...")
    for idx, sc in enumerate(scenes):
        sid = sc["scene_id"]
        text = sc["voiceover_script"]
        mp3_path = PROJECT_DIR / f"{sid}.mp3"
        
        # Edge TTS Argentine Spanish Female
        comm = edge_tts.Communicate(text, "es-AR-ElenaNeural", rate="-2%")
        await comm.save(str(mp3_path))

        # Measure exact duration
        cmd = [
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", str(mp3_path)
        ]
        dur = float(subprocess.check_output(cmd).decode().strip())
        
        entry = {
            "scene_id": sid,
            "order": sc.get("order", idx + 1),
            "title": sc["title"],
            "mp3_file": str(mp3_path),
            "start": round(total_time, 3),
            "duration": round(dur, 3),
            "end": round(total_time + dur, 3),
            "voiceover_script": text,
            "screen_elements": sc.get("screen_elements", {}),
            "checkpoints": sc.get("checkpoints", [])
        }
        timeline.append(entry)
        total_time += dur + 0.55  # clear scene transition breath

    total_time = round(total_time, 3)
    print(f"[OK] Audio speech completado. Duración total: {total_time}s (~{total_time/60:.2f} min)")

    with open(PROJECT_DIR / "audio_timeline.json", "w", encoding="utf-8") as f:
        json.dump({"total_duration": total_time, "scenes": timeline}, f, indent=2, ensure_ascii=False)

    return total_time, timeline

def assemble_narration_wav(timeline):
    inputs = []
    filter_parts = []
    n = len(timeline)

    for i, sc in enumerate(timeline):
        inputs.extend(["-i", sc["mp3_file"]])
        delay_ms = int(sc["start"] * 1000)
        filter_parts.append(f"[{i}:a]adelay={delay_ms}|{delay_ms}[a{i}];")

    mix_inputs = "".join([f"[a{i}]" for i in range(n)])
    filter_str = "".join(filter_parts) + f"{mix_inputs}amix=inputs={n}:dropout_transition=0,volume={n},loudnorm=I=-16:TP=-1.5:LRA=11[outa]"

    out_wav = str(PROJECT_DIR / "narration.wav")
    cmd = ["ffmpeg", "-y"] + inputs + ["-filter_complex", filter_str, "-map", "[outa]", out_wav]
    subprocess.run(cmd, check=True)
    print(f"[OK] narration.wav generado exitosamente en {out_wav}")

def generate_ambient_music(total_duration):
    sr = 44100
    dur = math.ceil(total_duration) + 3
    num_samples = int(sr * dur)
    samples = [0.0] * num_samples

    bpm = 112
    beat_len = 60.0 / bpm

    # Thoughtful, philosophical harmonic progression: Dm - Bb - F - C
    progression = [
        [293.66, 349.23, 440.00, 587.33],  # Dm
        [233.08, 293.66, 349.23, 466.16],  # Bb
        [174.61, 220.00, 261.63, 349.23],  # F
        [196.00, 246.94, 293.66, 392.00]   # C
    ]

    cycle_dur = beat_len * 8
    cur_t = 0.0
    while cur_t < dur:
        for chord in progression:
            chord_end = min(dur, cur_t + cycle_dur)
            idx = 0
            t_note = cur_t
            step = beat_len / 2.0
            while t_note < chord_end:
                freq = chord[idx % len(chord)]
                start_idx = int(t_note * sr)
                note_len = int(0.38 * sr)
                for i in range(note_len):
                    if start_idx + i < num_samples:
                        local_t = i / sr
                        env = math.exp(-5.5 * local_t)
                        # Warm electric piano / marimba sine overtones
                        val = (math.sin(2 * math.pi * freq * local_t) + 0.22 * math.sin(4 * math.pi * freq * local_t)) * env * 0.13
                        samples[start_idx + i] += val
                t_note += step
                idx += 1
            cur_t += cycle_dur
            if cur_t >= dur:
                break

    max_val = max(abs(s) for s in samples) or 1.0
    out_music = PROJECT_DIR / "music.wav"
    with wave.open(str(out_music), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sr)
        for s in samples:
            norm = (s / max_val) * 0.18
            val = int(max(min(norm * 32767, 32767), -32768))
            wav.writeframes(struct.pack("<h", val))

    print(f"[OK] music.wav (Zero-Copyright) generado exitosamente en {out_music}")

def mix_master_audio():
    narration_wav = str(PROJECT_DIR / "narration.wav")
    music_wav = str(PROJECT_DIR / "music.wav")
    audio_mixed = str(PROJECT_DIR / "audio_mixed.m4a")

    cmd = [
        "ffmpeg", "-y",
        "-i", narration_wav,
        "-i", music_wav,
        "-filter_complex", "[1:a]volume=0.18[bg];[0:a][bg]amix=inputs=2:duration=first[out]",
        "-map", "[out]",
        "-c:a", "aac",
        "-b:a", "192k",
        audio_mixed
    ]
    subprocess.run(cmd, check=True)
    print(f"[OK] Master audio_mixed.m4a generado exitosamente en {audio_mixed}")

def export_scorm_checkpoints(timeline):
    checkpoints = []
    for sc in timeline:
        cps = sc.get("checkpoints", [])
        if cps:
            # Place checkpoint near the middle-end of the scene
            for cp in cps:
                timestamp = round(sc["start"] + sc["duration"] * 0.75, 1)
                checkpoints.append({
                    "scene_id": sc["scene_id"],
                    "timestamp": timestamp,
                    "question": cp["question"],
                    "options": cp["options"],
                    "correct_index": cp["correct_index"],
                    "feedback_ok": cp.get("feedback_ok", "¡Excelente!"),
                    "feedback_error": cp.get("feedback_error", "Respuesta incorrecta.")
                })

    out_file = PROJECT_DIR / "scorm_checkpoints.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(checkpoints, f, indent=2, ensure_ascii=False)
    print(f"[OK] {len(checkpoints)} checkpoints SCORM exportados con timestamps exactos en {out_file}")

async def main():
    total_time, timeline = await generate_speech_and_timing()
    assemble_narration_wav(timeline)
    generate_ambient_music(total_time)
    mix_master_audio()
    export_scorm_checkpoints(timeline)
    print(">>> PIPELINE DE AUDIO Y TIMELINE COMPLETADO EXITOSAMENTE <<<")

if __name__ == "__main__":
    asyncio.run(main())
