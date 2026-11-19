"""
Modular Frame Renderer for 'Cuando el trabajo deja de ser necesario' (~404.6s, 24fps = 9710 frames).
Renders frames to disk in batches, allowing safe resumes, and encodes to video_raw.mp4 with FFmpeg.
"""

import os
import sys
import subprocess
from pathlib import Path

JS_SCRIPT = """
const { chromium } = require('playwright-core');
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

async function main() {
  const fps = 24;
  const dur = 404.60;
  const totalFrames = Math.floor(dur * fps);
  const framesDir = path.join(__dirname, 'frames');
  const outVideo = path.join(__dirname, 'video_raw.mp4');

  if (!fs.existsSync(framesDir)) {
    fs.mkdirSync(framesDir, { recursive: true });
  }

  console.log(`Iniciando renderizado modular: ${totalFrames} fotogramas a ${fps} fps (~${dur}s)...`);

  const browser = await chromium.launch({
    executablePath: 'C:\\\\Program Files\\\\Google\\\\Chrome\\\\Application\\\\chrome.exe',
    headless: true
  });
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
  const htmlPath = 'file:///' + path.join(__dirname, 'index.html').replace(/\\\\/g, '/');
  await page.goto(htmlPath);

  const startTime = Date.now();
  for (let f = 0; f < totalFrames; f++) {
    const framePath = path.join(framesDir, `frame_${String(f).padStart(5, '0')}.png`);
    if (!fs.existsSync(framePath)) {
      const t = f / fps;
      await page.evaluate((currT) => window.render(currT), t);
      await page.screenshot({ path: framePath });
    }

    if (f % 500 === 0 || f === totalFrames - 1) {
      const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
      const pct = ((f / totalFrames) * 100).toFixed(1);
      console.log(`Fotograma guardado ${f}/${totalFrames} (${pct}%) - ${elapsed}s transcurridos`);
    }
  }

  await browser.close();
  console.log('Todos los fotogramas guardados en disco. Codificando video MP4...');

  await new Promise((resolve, reject) => {
    const ff = spawn('ffmpeg', [
      '-y',
      '-r', fps.toString(),
      '-i', path.join(framesDir, 'frame_%05d.png'),
      '-c:v', 'libx264',
      '-pix_fmt', 'yuv420p',
      '-preset', 'fast',
      '-crf', '18',
      outVideo
    ]);
    ff.on('close', (code) => {
      if (code === 0) resolve();
      else reject(new Error('ffmpeg failed with code ' + code));
    });
  });

  console.log(`Video base generado exitosamente: ${outVideo}`);
}

main().catch(console.error);
"""

with open("films/cuando-el-trabajo-deja-de-ser-necesario/render_frames.js", "w", encoding="utf-8") as f:
    f.write(JS_SCRIPT)

print("render_frames.js escrito exitosamente.")
