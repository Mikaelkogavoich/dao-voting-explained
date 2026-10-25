// Exports every diagrams/*.svg to a 2x PNG with the brand fonts loaded,
// then prints index.html to guide.pdf in the light theme.
// Usage: node tools/render.js            (needs Playwright with Chromium)
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const ROOT = path.join(__dirname, '..');
const FONTS = 'https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=block';

(async () => {
  const browser = await chromium.launch();

  const dir = path.join(ROOT, 'diagrams');
  for (const file of fs.readdirSync(dir).filter(f => f.endsWith('.svg')).sort()) {
    const svg = fs.readFileSync(path.join(dir, file), 'utf8');
    const w = Number(svg.match(/width="(\d+)"/)[1]);
    const h = Number(svg.match(/height="(\d+)"/)[1]);
    const page = await browser.newPage({ viewport: { width: w, height: h }, deviceScaleFactor: 2 });
    await page.setContent(`<!doctype html><html><head><link rel="stylesheet" href="${FONTS}">
      <style>html,body{margin:0;background:transparent}</style></head><body>${svg}</body></html>`);
    await page.evaluate(() => document.fonts.ready);
    const ok = await page.evaluate(() => document.fonts.check('600 18px "Be Vietnam Pro"') && document.fonts.check('500 14px "JetBrains Mono"'));
    if (!ok) throw new Error('Brand fonts did not load for ' + file);
    await page.locator('svg').screenshot({ path: path.join(dir, file.replace('.svg', '.png')), omitBackground: true });
    await page.close();
    console.log('diagram', file.replace('.svg', '.png'));
  }

  const index = path.join(ROOT, 'index.html');
  if (fs.existsSync(index)) {
    const page = await browser.newPage();
    await page.goto('file://' + index + '?print');
    await page.evaluate(() => document.fonts.ready);
    await page.waitForTimeout(300);
    await page.emulateMedia({ media: 'print' });
    await page.pdf({
      path: path.join(ROOT, 'guide.pdf'), format: 'A4', printBackground: true,
      margin: { top: '16mm', bottom: '16mm', left: '16mm', right: '16mm' },
    });
    console.log('guide.pdf');
  }
  await browser.close();
})();
