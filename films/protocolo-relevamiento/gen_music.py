import math, wave, struct

sr = 44100
dur = 168.0
num_samples = int(sr * dur)
samples = [0.0] * num_samples

bpm = 116
beat_len = 60.0 / bpm

# Calm academic chord progression: C - G - Am - F
progression = [
    [261.63, 329.63, 392.00, 523.25], # C
    [196.00, 246.94, 293.66, 392.00], # G
    [220.00, 261.63, 329.63, 440.00], # Am
    [174.61, 220.00, 261.63, 349.23]  # F
]

cycle_dur = beat_len * 8 # 8 beats per chord
total_cycles = int(dur / (cycle_dur * len(progression))) + 1

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
            note_len = int(0.35 * sr)
            for i in range(note_len):
                if start_idx + i < num_samples:
                    local_t = i / sr
                    env = math.exp(-6.5 * local_t)
                    # Warm marimba timbre
                    val = (math.sin(2 * math.pi * freq * local_t) + 0.25 * math.sin(4 * math.pi * freq * local_t)) * env * 0.14
                    samples[start_idx + i] += val
            t_note += step
            idx += 1
        cur_t += cycle_dur
        if cur_t >= dur:
            break

max_val = max(abs(s) for s in samples) or 1.0
with wave.open('films/protocolo-relevamiento/music.wav', 'wb') as wav:
    wav.setnchannels(1)
    wav.setsampwidth(2)
    wav.setframerate(sr)
    for s in samples:
        norm = (s / max_val) * 0.20
        val = int(max(min(norm * 32767, 32767), -32768))
        wav.writeframes(struct.pack('<h', val))

print('music.wav for protocol generated successfully!')
