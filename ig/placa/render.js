// Render de la placa: carga plantilla.html (que lee data.js + screen.png) y
// saca UN screenshot 1080x1350. Adaptado de ig/reel/render.js.
//
//   node render.js [salida.png]
const { chromium } = require('playwright');
const path = require('path');

const OUT = process.argv[2] || path.join(__dirname, 'out.png');
const W = 1080, H = 1350, SCALE = 2;

(async () => {
  const browser = await chromium.launch({
    args: ['--allow-file-access-from-files', '--font-render-hinting=none'],
  });
  const page = await browser.newPage({
    viewport: { width: W, height: H },
    deviceScaleFactor: SCALE,
  });
  const errs = [];
  page.on('pageerror', e => errs.push(e.message));

  await page.goto('file:///' + path.resolve(__dirname, 'plantilla.html').replace(/\\/g, '/'));
  await page.waitForFunction(() => document.fonts.ready.then(() => true));
  await page.waitForFunction(() => window.__placaReady === true, { timeout: 15000 });
  await page.waitForTimeout(400);

  if (errs.length) { console.error('ERRORES JS:\n' + errs.join('\n')); process.exit(1); }

  await page.screenshot({ path: OUT, clip: { x: 0, y: 0, width: W, height: H } });
  await browser.close();
  console.log('placa lista:', OUT);
})();
