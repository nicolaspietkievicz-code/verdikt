// Captura real de la app para el mockup de teléfono de la placa.
//
//   node capturar.js "?a=AAPL&c=stock"   -> el análisis de un activo
//   node capturar.js "/"                 -> la home (ranking del día)
//
// Espera a que la pantalla real esté dibujada (no el cold-start ni el
// esqueleto) antes de disparar el screenshot a screen.png.
//
// Best effort: si algo falla, sale con código != 0 y el orquestador sigue (la
// plantilla renderiza el mockup con un placeholder).
const { chromium } = require('playwright');
const path = require('path');

const ruta = process.argv[2] || '/';
const URL = 'https://app.verdikt.finance/' + ruta.replace(/^\//, '');
const OUT = path.join(__dirname, 'screen.png');
const esDetalle = ruta.includes('a=');

(async () => {
  const browser = await chromium.launch({ args: ['--font-render-hinting=none'] });
  const page = await browser.newPage({
    viewport: { width: 390, height: 900 },
    deviceScaleFactor: 3,
  });
  page.setDefaultTimeout(90000);
  await page.goto(URL, { waitUntil: 'domcontentloaded' });

  try {
    await page.waitForFunction((detalle) => {
      const t = document.body ? document.body.innerText : '';
      return detalle
        ? (/\/100/.test(t) && /EVITAR/.test(t))                 // pantalla de análisis
        : (/\/100/.test(t) || /Ánimo|MERCADO|RANKING/i.test(t)); // home
    }, esDetalle, { timeout: 80000 });
  } catch (e) {
    console.error('no apareció el contenido a tiempo:', e.message);
    await browser.close();
    process.exit(1);
  }

  await page.waitForFunction(() => document.fonts.ready.then(() => true));
  await page.waitForFunction(() =>
    [...document.images].every(i => i.complete && i.naturalWidth > 0));
  await page.waitForTimeout(1200);

  await page.screenshot({ path: OUT });
  await browser.close();
  console.log('captura lista:', OUT);
})();
