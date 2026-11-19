const { chromium } = require('playwright-core');
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

async function main() {
  const fps = 24;
  const dur = 165.87;
  const totalFrames = Math.floor(dur * fps);
  const width = 1920;
  const height = 1080;
  const framesDir = path.join(__dirname, 'frames');
  const outVideo = path.join(__dirname, 'video_raw.mp4');

  if (!fs.existsSync(framesDir)) {
    fs.mkdirSync(framesDir, { recursive: true });
  }

  console.log(`Starting render: ${totalFrames} frames at ${fps} fps (~${dur}s)...`);

  const browser = await chromium.launch({
    executablePath: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
    headless: true
  });
  const page = await browser.newPage({ viewport: { width, height } });
  const htmlPath = 'file:///' + path.join(__dirname, 'index.html').replace(/\\/g, '/');
  await page.goto(htmlPath);

  const startTime = Date.now();
  for (let f = 0; f < totalFrames; f++) {
    const framePath = path.join(framesDir, `frame_${String(f).padStart(5, '0')}.png`);
    if (!fs.existsSync(framePath)) {
      const t = f / fps;
      await page.evaluate((currT) => window.render(currT), t);
      await page.screenshot({ path: framePath });
    }

    if (f % 250 === 0 || f === totalFrames - 1) {
      const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
      const pct = ((f / totalFrames) * 100).toFixed(1);
      console.log(`Saved frame ${f}/${totalFrames} (${pct}%) - ${elapsed}s elapsed`);
    }
  }

  await browser.close();
  console.log('All frames saved. Encoding video with ffmpeg...');

  // Encode frames to mp4
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

  console.log(`Raw video created successfully at ${outVideo}`);
}

main().catch(console.error);
