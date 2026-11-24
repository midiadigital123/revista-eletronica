// Verificação do protótipo F2 gerado: abre index.html e index-sem-habilidades.html por file://,
// percorre o tour, minimapa, zoom livre e modais, salva PNGs e imprime critério | resultado.
//   NODE_PATH=/home/otavio.peres/dev/revista-express/app/e2e/node_modules node verificar.cjs
"use strict";
const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright");

const SAIDA = "/tmp/claude-1001/-home-otavio-peres-dev-revista-express/927f0962-2c8b-4e49-9bea-284f09be9a0d/scratchpad/f2-fase0";
const ESPERA = 900; // > duration (700 ms) do svg-tour
const PAGINAS = [
  { nome: "index", passos: 4, bloco: "habilidades" },
  { nome: "index-sem-habilidades", passos: 3, bloco: "progressao" },
];
const linhas = [];
let falhas = 0;

function registra(criterio, ok, detalhe) {
  if (!ok) falhas++;
  linhas.push([criterio, (ok ? "OK" : "FALHA") + (detalhe ? ` (${detalhe})` : "")]);
}

async function verificar(browser, { nome, passos, bloco }) {
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  const erros = [];
  page.on("console", (m) => m.type() === "error" && erros.push(m.text()));
  page.on("pageerror", (e) => erros.push(String(e)));
  const png = (sufixo) => path.join(SAIDA, `${nome}-${sufixo}.png`);
  const tour = (fn, ...args) => page.evaluate(({ fn, args }) => { window.f2Tour[fn](...args); }, { fn, args });

  await page.goto("file://" + path.resolve(__dirname, nome + ".html"));
  await page.waitForSelector(".svg-tour__panel");
  await page.waitForFunction(() => !!window.f2Tour);
  await page.waitForTimeout(ESPERA);
  await page.screenshot({ path: png("00-visao-geral") });

  // passos
  const n = await page.evaluate(() => window.f2Tour.steps.length);
  registra(`${nome}: tour com ${passos} passos`, n === passos, `steps=${n}`);
  for (let i = 0; i < n; i++) {
    await tour("go", i);
    await page.waitForTimeout(ESPERA);
    await page.screenshot({ path: png(`passo-${i + 1}`) });
  }
  const blocoSumiu = await page.evaluate(() => !document.querySelector("#f2-habilidades, #dlg-habilidades"));
  if (nome !== "index") registra(`${nome}: f2-habilidades e dlg-habilidades ausentes`, blocoSumiu);

  // minimapa (fica visível após sair da visão geral; captura o <img> gerado do SVG)
  const mm = page.locator(".svg-tour__minimap");
  const temMinimapa = (await mm.count()) === 1;
  const img = mm.locator("img");
  const imgOk = temMinimapa && (await img.count()) === 1 &&
    (await img.evaluate((el) => el.complete && el.naturalWidth > 0));
  registra(`${nome}: minimapa com <img> renderizado`, imgOk);
  if (temMinimapa) await ((await img.count()) ? img : mm).screenshot({ path: png("minimapa") });

  // texto do foreignObject selecionável
  const sel = await page.evaluate(() => {
    const div = document.querySelector("#revista foreignObject div");
    const s = window.getSelection(); s.selectAllChildren(div);
    const len = s.toString().length; s.removeAllRanges(); return len;
  });
  registra(`${nome}: texto do foreignObject selecionável`, sel > 0, `${sel} caracteres`);

  // zoom livre até o máximo sobre o bloco
  await tour("setMode", "free");
  await page.waitForTimeout(300);
  const centro = await page.evaluate((id) => {
    const b = document.getElementById(id).getBoundingClientRect();
    const s = document.querySelector(".svg-tour__stage").getBoundingClientRect();
    return { x: b.x + b.width / 2 - s.x, y: b.y + b.height / 2 - s.y };
  }, "f2-" + bloco);
  let zoomAnterior = "";
  for (let i = 0; i < 12; i++) { // zoomBy para no freeMaxZoom; o rótulo deixa de mudar
    await tour("zoomBy", 1.6, centro.x, centro.y);
    await page.waitForTimeout(350);
    const z = await page.locator(".svg-tour__zoomlabel").innerText();
    if (z === zoomAnterior) break;
    zoomAnterior = z;
  }
  const modo = await page.evaluate(() => window.f2Tour.mode);
  registra(`${nome}: modo explorar + zoom máximo sobre ${bloco}`, modo === "free", `zoom ${zoomAnterior}`);
  await page.screenshot({ path: png("zoom-livre") });

  // modal por clique
  const idBotao = "f2-btn-action-" + bloco;
  const passoBloco = await page.evaluate((alvo) => window.f2Tour.steps.findIndex((s) => s.target === alvo), "f2-" + bloco);
  await tour("go", passoBloco);
  await page.waitForTimeout(ESPERA);
  await page.click("#" + idBotao);
  let aberto = await page.waitForSelector("dialog[open]", { timeout: 3000 }).then(() => true, () => false);
  registra(`${nome}: clique em #${idBotao} abre dialog`, aberto);
  await page.screenshot({ path: png("modal-clique") });
  await page.keyboard.press("Escape");
  await page.waitForSelector("dialog[open]", { state: "detached", timeout: 3000 }).catch(() => {});

  // modal por teclado (focus + Enter), Escape devolve o foco ao botão
  await page.evaluate((id) => document.getElementById(id).focus(), idBotao);
  await page.keyboard.press("Enter");
  aberto = await page.waitForSelector("dialog[open]", { timeout: 3000 }).then(() => true, () => false);
  const idDialog = aberto ? await page.evaluate(() => document.querySelector("dialog[open]").id) : "";
  registra(`${nome}: Enter em #${idBotao} abre dlg-${bloco}`, aberto && idDialog === "dlg-" + bloco, idDialog);
  await page.screenshot({ path: png("modal-teclado") });
  await page.keyboard.press("Escape");
  await page.waitForTimeout(200);
  const focoVoltou = await page.evaluate(() => document.activeElement && document.activeElement.id);
  registra(`${nome}: Escape devolve o foco ao botão`, focoVoltou === idBotao, `activeElement=${focoVoltou}`);

  registra(`${nome}: sem erro de console/pageerror`, erros.length === 0, erros.join(" | ").slice(0, 200));
  await page.close();
}

(async () => {
  fs.mkdirSync(SAIDA, { recursive: true });
  const browser = await chromium.launch();
  try {
    for (const p of PAGINAS) await verificar(browser, p);
  } finally {
    await browser.close();
  }
  const larg = Math.max(...linhas.map((l) => l[0].length));
  console.log("critério".padEnd(larg) + " | resultado");
  console.log("-".repeat(larg) + "-|-" + "-".repeat(30));
  for (const [c, r] of linhas) console.log(c.padEnd(larg) + " | " + r);
  console.log(`\nPNGs em ${SAIDA}`);
  process.exit(falhas ? 1 : 0);
})().catch((e) => { console.error(e); process.exit(1); });
