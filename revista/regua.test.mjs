// Teste da régua da escala: `node revista/regua.test.mjs`
import assert from "node:assert/strict";
import { createRequire } from "node:module";

const { montarFaixasRegua } = createRequire(import.meta.url)("./script.js");

const cortes = { "padrao-1": 125, "padrao-2": 250, "padrao-3": 375 };
const L = (level, content = "Lorem") => ({ level, content });
// [padrão, topo, base, rótulo, ehCorte, conteúdo] para comparar compacto
const resumo = (faixas) =>
  faixas.map((f) => [f.padrao.slice(-1), f.topo, f.base, f.rotuloBase, f.ehCorte, f.conteudo]);

// Referência 8.png
assert.deepEqual(
  resumo(
    montarFaixasRegua({
      min: 0,
      max: 500,
      cortes,
      escala: {
        "padrao-4": [L(375, "---")],
        "padrao-3": [L(300), L(275, "---"), L(250, "---")],
        "padrao-2": [L(225), L(150), L(125, "---")],
        "padrao-1": [L(100, "---"), L(75)],
      },
    }),
  ),
  [
    ["4", 500, 375, 375, true, "---"],
    ["3", 375, 300, 300, false, "Lorem"],
    ["3", 300, 275, 275, false, "---"],
    ["3", 275, 250, 250, true, "---"],
    ["2", 250, 225, 225, false, "Lorem"],
    ["2", 225, 150, 150, false, "Lorem"],
    ["2", 150, 125, 125, true, "---"],
    ["1", 125, 100, 100, false, "---"],
    ["1", 100, 75, 75, false, "Lorem"],
    ["1", 75, 0, null, false, null], // preenchimento até o mínimo, sem tick
  ],
);

// Captura 7.png: níveis repetidos e nível = mínimo
assert.deepEqual(
  resumo(
    montarFaixasRegua({
      min: 0,
      max: 500,
      cortes,
      escala: {
        "padrao-4": [L(383, "fhghfg"), L(383, "fgjfghj"), L(375, "dfsdfdf")],
        "padrao-3": [L(250, "sdfsdf")],
        "padrao-2": [L(125, "dfd")],
        "padrao-1": [L(0, "dfd")],
      },
    }),
  ),
  [
    ["4", 500, 383, null, false, "fhghfg"], // 383 aparece uma vez só, na faixa seguinte
    ["4", 383, 383, 383, false, "fgjfghj"],
    ["4", 383, 375, 375, true, "dfsdfdf"],
    ["3", 375, 250, 250, true, "sdfsdf"],
    ["2", 250, 125, 125, true, "dfd"],
    ["1", 125, 0, null, false, "dfd"], // 0 = mínimo: rótulo fora da régua
  ],
);

// Padrões vazios: uma faixa "---" entre os limites de cada um
assert.deepEqual(
  resumo(montarFaixasRegua({ min: 0, max: 500, cortes, escala: { "padrao-3": [L(300)] } })),
  [
    ["4", 500, 375, 375, true, "---"],
    ["3", 375, 300, 300, false, "Lorem"],
    ["3", 300, 250, 250, true, null],
    ["2", 250, 125, 125, true, "---"],
    ["1", 125, 0, null, false, "---"],
  ],
);

// Nível igual ao máximo: o 500 já aparece fora da régua, sem tick repetido
assert.deepEqual(
  resumo(montarFaixasRegua({ min: 0, max: 500, cortes, escala: { "padrao-4": [L(500, "topo")] } }))[0],
  ["4", 500, 500, null, false, "topo"],
);

console.log("regua.test.mjs: ok");
