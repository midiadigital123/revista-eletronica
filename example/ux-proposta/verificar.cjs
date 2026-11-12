// Captura as páginas da demo em 1440 e 390 px, aponta erro de console e rolagem horizontal da página.
//   NODE_PATH=/home/otavio.peres/dev/revista-express/app/e2e/node_modules node verificar.cjs <pasta> [pagina.html ...] [--perfil imp]
// Os PNGs vão para <pasta>/_shots/<pagina>-d.png (1440) e -m.png (390). Uma rodada por vez; não vire laço.
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

(async () => {
  const args = process.argv.slice(2);
  const iperfil = args.indexOf('--perfil');
  const perfil = iperfil >= 0 ? args.splice(iperfil, 2)[1] : 'ped';
  const pasta = path.resolve(args.shift() || '.');
  let paginas = args.length ? args : fs.readdirSync(pasta).filter((f) => f.endsWith('.html') && !f.startsWith('_'));
  const saida = path.join(pasta, '_shots');
  fs.mkdirSync(saida, { recursive: true });
  const b = await chromium.launch();
  let problemas = 0;
  for (const [w, h, sufixo] of [[1440, 900, 'd'], [390, 844, 'm']]) {
    const ctx = await b.newContext({ viewport: { width: w, height: h } });
    await ctx.addInitScript((p) => { try { localStorage.setItem('perfil', p); } catch (e) {} }, perfil);
    for (const pg of paginas) {
      const p = await ctx.newPage();
      const erros = [];
      p.on('console', (m) => { if (m.type() === 'error') erros.push('console: ' + m.text()); });
      p.on('pageerror', (e) => erros.push('pageerror: ' + e.message));
      await p.goto('file://' + path.join(pasta, pg));
      await p.waitForTimeout(150);
      const larg = await p.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
      if (larg > 1) erros.push(`rolagem horizontal da página: +${larg}px`);
      await p.screenshot({ path: path.join(saida, pg.replace('.html', '') + '-' + sufixo + '.png'), fullPage: true });
      if (erros.length) { problemas += erros.length; console.log(`${pg} (${sufixo}):\n  ` + erros.join('\n  ')); }
      await p.close();
    }
    await ctx.close();
  }
  await b.close();
  console.log(problemas ? `PROBLEMAS: ${problemas}` : `OK: ${paginas.length} páginas × 2 larguras em ${saida}`);
})();
