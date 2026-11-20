const { chromium } = require('playwright-core');
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

async function test() {
  const dir = path.resolve('films/cuando-el-trabajo-deja-de-ser-necesario');
  const zipPath = path.join(dir, 'Cuando_El_Trabajo_Deja_De_Ser_Necesario_SCORM_Completo.zip');
  const tempHtml = path.join(dir, 'test_scorm_runner.html');

  // Extraer index.html
  const content = execSync(`tar -xf "${zipPath}" -O index.html`).toString('utf-8');
  fs.writeFileSync(tempHtml, content, 'utf-8');

  const browser = await chromium.launch({
    executablePath: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
    headless: true
  });
  const page = await browser.newPage({ viewport: { width: 1280, height: 720 } });
  
  page.on('console', msg => console.log('PAGE LOG:', msg.text()));
  page.on('pageerror', err => console.log('PAGE ERROR:', err.message));

  await page.goto('file:///' + tempHtml.replace(/\\/g, '/'));
  console.log('Cargado con exito');

  // Comprobar estado inicial
  const scoreText = await page.textContent('#score-display');
  console.log('Score inicial:', scoreText);

  // Probar disparar timeupdate en 96.6
  await page.evaluate(() => {
    const v = document.getElementById('video-elem');
    v.currentTime = 96.6;
    v.dispatchEvent(new Event('timeupdate'));
  });

  await new Promise(r => setTimeout(r, 500));

  const display = await page.evaluate(() => {
    return window.getComputedStyle(document.getElementById('overlay')).display;
  });
  console.log('Estado display de overlay:', display);

  const title = await page.textContent('#q-title');
  console.log('Titulo pregunta:', title);

  const optsCount = await page.evaluate(() => document.querySelectorAll('.option-btn').length);
  console.log('Cantidad de opciones:', optsCount);

  // Simular clic en la opcion correcta (indice 1)
  await page.click('.option-btn:nth-child(2)');
  const feedbackText = await page.textContent('#feedback');
  console.log('Feedback:', feedbackText);

  const isContinueVisible = await page.evaluate(() => {
    return window.getComputedStyle(document.getElementById('btn-continue')).display;
  });
  console.log('Boton continuar visible:', isContinueVisible);

  await browser.close();
  fs.unlinkSync(tempHtml);
}

test().catch(console.error);
