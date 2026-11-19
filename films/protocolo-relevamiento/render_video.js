const { chromium } = require('playwright-core');
const { spawn } = require('child_process');
const path = require('path');

async function main() {
  const fps = 24;
  const dur = 165.87;
  const totalFrames = Math.floor(dur * fps);
  const width = 1920;
  const height = 1080;
  const outVideo = path.join(__dirname, 'video_raw.mp4');

  console.log(`Starting render: ${totalFrames} frames at ${fps} fps (~${dur}s)...`);

  const browser = await chromium.launch({
    executablePath: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
    headless: true
  });
  const page = await browser.newPage({ viewport: { width, height } });
  const htmlPath = 'file:///' + path.join(__dirname, 'index.html').replace(/\\/g, '/');
  await page.goto(htmlPath);

  const ffmpeg = spawn('ffmpeg', [
    '-y',
    '-f', 'image2pipe',
    '-vcodec', 'png',
    '-r', fps.toString(),
    '-i', '-',
    '-c:v', 'libx264',
    '-pix_fmt', 'yuv420p',
    '-preset', 'fast',
    '-crf', '18',
    outVideo
  ]);

  const startTime = Date.now();
  for (let f = 0; f < totalFrames; f++) {
    const t = f / fps;
    await page.evaluate((currT) => window.render(currT), t);
    const buf = await page.screenshot({ type: 'png' });
    ffmpeg.stdin.write(buf);

    if (f % 200 === 0 || f === totalFrames - 1) {
      const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
      const pct = ((f / totalFrames) * 100).toFixed(1);
      console.log(`Frame ${f}/${totalFrames} (${pct}%) - ${elapsed}s elapsed`);
    }
  }

  ffmpeg.stdin.end();
  await new Promise((resolve) => ffmpeg.on('close', resolve));
  await browser.close();
  console.log(`Raw video rendered successfully to ${outVideo}`);
}

main().catch(console.error);
