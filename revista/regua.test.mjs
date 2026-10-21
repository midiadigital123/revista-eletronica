// Teste da régua da escala: `node revista/regua.test.mjs`
import assert from "node:assert/strict";
import { createRequire } from "node:module";

const { montarFaixasRegua: regua, rotuloAno, rotuloAnoLongo, tipoDoItem, urlDoItem } = createRequire(import.meta.url)("./script.js");
const montarFaixasRegua = (args) => regua(args).faixas;

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

// Nível repetido: só a última faixa do nível tem tick
assert.deepEqual(
  montarFaixasRegua({
    min: 0,
    max: 500,
    cortes,
    escala: { "padrao-4": [L(383, "a"), L(383, "b"), L(375, "c")] },
  })
    .slice(0, 3)
    .map((f) => f.mesmoNivel),
  [true, false, false],
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

// Linhas no mesmo nível (habilidades separadas) e item repassado para a faixa
{
  const item = { id: "abc123", nome: "item.pdf", tamanho: 1024 };
  const faixas = montarFaixasRegua({
    min: 0,
    max: 500,
    cortes,
    escala: { "padrao-3": [{ level: 300, content: "A", item }, L(300, "B")] },
  });
  assert.deepEqual(
    resumo(faixas).slice(1, 4),
    [
      ["3", 375, 300, null, false, "A"],
      ["3", 300, 300, 300, false, "B"],
      ["3", 300, 250, 250, true, null],
    ],
  );
  assert.deepEqual(faixas[1].item, item);
  assert.equal(faixas[2].item, undefined);
  assert.equal(faixas[3].item, undefined); // preenchimento não tem item
}

// Rótulos das abas gerados a partir da chave da etapa (mesmo texto do contrato)
assert.equal(rotuloAno("2ef"), "2º EF");
assert.equal(rotuloAno("3em"), "3ª EM");
assert.equal(rotuloAnoLongo("5ef"), "5º Ano do Ensino Fundamental");
assert.equal(rotuloAnoLongo("3em"), "3ª Série do Ensino Médio");
assert.equal(rotuloAno("outro"), "outro");
assert.equal(rotuloAnoLongo("outro"), "outro");

// Revista LP: cortes 500/400 caem entre níveis (503→446, 446→390) e não criam faixa vazia
{
  const r = regua({
    min: 0,
    max: 1000,
    cortes: { "padrao-1": 350, "padrao-2": 400, "padrao-3": 500 },
    escala: {
      "padrao-4": [L(782), L(732), L(675), L(616), L(556), L(503)],
      "padrao-3": [L(446)],
      "padrao-2": [L(390)],
    },
  });
  assert.deepEqual(
    r.faixas.map((f) => [f.topo, f.base, f.conteudo]),
    [
      [1000, 782, "Lorem"],
      [782, 732, "Lorem"],
      [732, 675, "Lorem"],
      [675, 616, "Lorem"],
      [616, 556, "Lorem"],
      [556, 503, "Lorem"],
      [503, 446, "Lorem"], // atravessa o corte 500
      [446, 390, "Lorem"], // atravessa o corte 400
      [390, 350, null], // meia altura até o padrão vazio
      [350, 0, "---"],
    ],
  );
  assert.deepEqual(
    r.cortes.map((c) => [c.valor, c.y, c.exato]),
    [
      [500, 6.5, false], // selo no meio da faixa 503→446: não encosta no 503 nem no 446
      [400, 7.5, false], // idem na faixa 446→390
      [350, 8.5, true],
    ],
  );
  assert.deepEqual(
    r.padroes.map((p) => [p.y0, p.y1]),
    [[0, 6.5], [6.5, 7.5], [7.5, 8.5], [8.5, 9]], // faixa "---" tem meia altura,
  );
  assert.deepEqual(
    r.faixas.filter((f) => f.cortesDentro).map((f) => [f.topo, f.base, f.cortesDentro]),
    [[503, 446, 1], [446, 390, 1]], // só essas ganham altura mínima no CSS
  );
}

// Texto sobre a cor do padrão: branco só onde contrasta mais que o preto
const { corTextoSobre } = createRequire(import.meta.url)("./script.js");
assert.equal(corTextoSobre("#f72628"), "#fff"); // padrão 1 (vermelho)
assert.equal(corTextoSobre("#ff8d43"), "#000"); // padrão 2
assert.equal(corTextoSobre("#b3ccff"), "#000"); // padrão 3
assert.equal(corTextoSobre("#0ed3ff"), "#000"); // padrão 4
assert.equal(corTextoSobre("#000"), "#fff");
assert.equal(corTextoSobre("#FFFFFF"), "#000");
assert.equal(corTextoSobre("#1a237e"), "#fff"); // azul escuro de um projeto
assert.equal(corTextoSobre(""), "#000"); // inválido: preto

// URL do item: tipo validado contra lista fixa, id codificado
assert.equal(urlDoItem("abc", "png"), "arquivos/itens/abc.png");
assert.equal(urlDoItem("abc", "jpg"), "arquivos/itens/abc.jpg");
assert.equal(urlDoItem("abc", undefined), "arquivos/itens/abc.pdf"); // item antigo
assert.equal(urlDoItem("abc", "../x"), "arquivos/itens/abc.pdf"); // tipo inválido
assert.equal(urlDoItem("a/b", "pdf"), "arquivos/itens/a%2Fb.pdf");
assert.equal(tipoDoItem("PNG"), "pdf"); // case-sensitive: só o que o pacote grava

// Selos de corte soltos não encostam no número vizinho: a faixa guarda o selo em k/(n+1)
// da sua altura e o CSS lhe dá (n+1) × 1,75rem de altura mínima
{
  const niveis = (conteudo475 = "Lorem") => ({
    "padrao-4": [L(525)],
    "padrao-3": [L(503)],
    "padrao-2": [L(475, conteudo475)],
    "padrao-1": [L(300)],
  });
  const faixaDe = (r, base) => r.faixas.find((f) => f.base === base);
  const centro = (f, k, n) => f.y0 + (f.altura * k) / (n + 1);

  // 500 (corte) a 3 pontos do 503: selo centrado na faixa 503 → 475, não a 25%
  let r = regua({ min: 0, max: 600, cortes: { "padrao-1": 300, "padrao-2": 400, "padrao-3": 500 }, escala: niveis() });
  assert.equal(faixaDe(r, 475).cortesDentro, 1);
  assert.equal(faixaDe(r, 300).cortesDentro, 1); // 400 também cai solto, na faixa 475 → 300
  assert.equal(faixaDe(r, 503).cortesDentro, 0);
  assert.deepEqual(
    r.cortes.map((c) => [c.valor, c.exato]),
    [[500, false], [400, false], [300, true]],
  );
  assert.equal(r.cortes[0].y, centro(faixaDe(r, 475), 1, 1));

  // 500 e 502 na mesma faixa: dois selos, o maior em cima, em y diferentes
  r = regua({ min: 0, max: 600, cortes: { "padrao-1": 300, "padrao-2": 500, "padrao-3": 502 }, escala: niveis() });
  assert.equal(faixaDe(r, 475).cortesDentro, 2);
  const [c502, c500] = r.cortes;
  assert.equal(c502.valor, 502);
  assert.equal(c502.y, centro(faixaDe(r, 475), 1, 2));
  assert.equal(c500.y, centro(faixaDe(r, 475), 2, 2));
  assert.ok(c502.y < c500.y);

  // faixa "---" (meia altura) também comporta o selo; a altura vem do CSS
  r = regua({ min: 0, max: 600, cortes: { "padrao-1": 300, "padrao-2": 400, "padrao-3": 500 }, escala: niveis("---") });
  assert.equal(faixaDe(r, 475).altura, 0.5);
  assert.equal(faixaDe(r, 475).cortesDentro, 1);
  assert.equal(r.cortes[0].y, faixaDe(r, 475).y0 + 0.25);

  // sem corte solto: cortesDentro é 0 em todas as faixas
  r = regua({ min: 0, max: 600, cortes: { "padrao-1": 300, "padrao-2": 475, "padrao-3": 503 }, escala: niveis() });
  assert.ok(r.faixas.every((f) => f.cortesDentro === 0));
}

console.log("regua.test.mjs: ok");
