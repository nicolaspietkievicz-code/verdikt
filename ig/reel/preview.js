// Saca frames sueltos de una escena para revisar composicion sin renderizar los
// 600. Uso: node preview.js scene2.html 0.6 3.2 8.0 11.5 14.5 18.5
const { chromium } = require('playwright');
const path = require('path');

(async () => {
  const [file, ...tiempos] = process.argv.slice(2);
  const browser = await chromium.launch({ args: ['--allow-file-access-from-files', '--font-render-hinting=none'] });
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
  const errs = [];
  page.on('pageerror', e => errs.push(e.message));
  await page.goto('file:///' + path.resolve(file).replace(/\\/g, '/'));
  await page.waitForFunction(() => document.fonts.ready.then(() => true));
  await page.waitForTimeout(300);

  for (const t of tiempos) {
    await page.evaluate(x => window.seek(x), Number(t));
    await page.screenshot({ path: `prev-${String(t).replace('.', '_')}.png` });
  }
  if (errs.length) console.log('ERRORES JS:\n' + errs.join('\n'));
  else console.log('sin errores | marcas:', JSON.stringify(await page.evaluate(() => window.MARCAS)));
  await browser.close();
})();
