// Renderiza scene.html frame por frame: en vez de grabar en tiempo real, se le
// pide a la escena que se posicione en t = f/FPS y se saca una captura nativa.
// Ventaja sobre grabar la pantalla: 1080x1920 real y movimiento exacto, sin
// frames perdidos ni depender de la velocidad de la maquina.
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const FPS = 30;

(async () => {
  const dir = 'frames';
  fs.rmSync(dir, { recursive: true, force: true });
  fs.mkdirSync(dir);

  const browser = await chromium.launch({ args: ['--allow-file-access-from-files', '--font-render-hinting=none'] });
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
  await page.goto('file:///' + path.resolve('scene.html').replace(/\\/g, '/'));

  // Sin esto el primer segundo sale con fuente de sistema o sin capturas.
  await page.waitForFunction(() => document.fonts.ready.then(() => true));
  await page.waitForFunction(() =>
    [...document.images].every(i => i.complete && i.naturalWidth > 0));
  await page.waitForTimeout(400);

  const dur = await page.evaluate(() => window.DUR);
  const total = Math.round(dur * FPS);
  for (let f = 0; f < total; f++) {
    await page.evaluate(t => window.seek(t), f / FPS);
    await page.screenshot({ path: path.join(dir, String(f).padStart(4, '0') + '.png') });
    if (f % 60 === 0) console.log(`frame ${f}/${total}`);
  }
  await browser.close();
  console.log(`listo: ${total} frames a ${FPS}fps`);
})();
