// Captura real de la app para meter dentro del mockup de telefono de la placa.
//
//   node capturar.js AAPL stock
//   node capturar.js BTC crypto
//
// Navega al deep link del analisis en app.verdikt.finance, espera a que el
// detalle este dibujado (no el cold-start ni el esqueleto) y saca un
// screenshot a screen.png. Mismo enfoque que los scripts de la landing:
// esperar contenido EXCLUSIVO del detalle ("/100" del score) antes de disparar.
//
// Best effort: si algo falla, sale con codigo != 0 y el orquestador sigue
// (la plantilla renderiza el mockup con un placeholder oscuro).
const { chromium } = require('playwright');
const path = require('path');

const [sym, clase = 'stock'] = process.argv.slice(2);
if (!sym) { console.error('falta el simbolo'); process.exit(2); }

const URL = `https://app.verdikt.finance/?a=${encodeURIComponent(sym)}&c=${clase}`;
const OUT = path.join(__dirname, 'screen.png');

(async () => {
  const browser = await chromium.launch({ args: ['--font-render-hinting=none'] });
  // Telefono alto: el detalle es una columna larga; despues la plantilla
  // recorta lo que entra en el marco.
  const page = await browser.newPage({
    viewport: { width: 390, height: 900 },
    deviceScaleFactor: 3,
  });

  page.setDefaultTimeout(90000);
  await page.goto(URL, { waitUntil: 'domcontentloaded' });

  // El detalle real trae el score "NN/100" y la escala EVITAR..COMPRA. El
  // cold-start de la app y el intersticial no. Se espera a eso, con margen
  // para que el backend despierte.
  try {
    await page.waitForFunction(() => {
      const t = document.body ? document.body.innerText : '';
      return /\/100/.test(t) && /EVITAR/.test(t);
    }, { timeout: 80000 });
  } catch (e) {
    console.error('no aparecio el detalle a tiempo:', e.message);
    await browser.close();
    process.exit(1);
  }

  await page.waitForFunction(() => document.fonts.ready.then(() => true));
  await page.waitForFunction(() =>
    [...document.images].every(i => i.complete && i.naturalWidth > 0));
  await page.waitForTimeout(1200); // que termine de dibujar el grafico (svg)

  await page.screenshot({ path: OUT });
  await browser.close();
  console.log('captura lista:', OUT);
})();
