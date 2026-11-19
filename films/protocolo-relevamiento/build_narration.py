import json
import subprocess

with open('films/protocolo-relevamiento/timing.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

inputs = []
filter_parts = []
n = len(data['segments'])

for i, s in enumerate(data['segments']):
    inputs.extend(['-i', s['file']])
    delay_ms = int(s['start'] * 1000)
    filter_parts.append(f'[{i}:a]adelay={delay_ms}|{delay_ms}[a{i}];')

mix_inputs = ''.join([f'[a{i}]' for i in range(n)])
filter_str = ''.join(filter_parts) + f'{mix_inputs}amix=inputs={n}:dropout_transition=0,volume={n},loudnorm=I=-16:TP=-1.5:LRA=11[outa]'

cmd = ['ffmpeg', '-y'] + inputs + ['-filter_complex', filter_str, '-map', '[outa]', 'films/protocolo-relevamiento/narration.wav']
subprocess.run(cmd, check=True)
print("narration.wav for protocol generated successfully!")
