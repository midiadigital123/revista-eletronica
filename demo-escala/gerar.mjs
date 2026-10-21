// Gera as páginas da demo da escala: renderiza o revista/escala.hbs real com dados reais
// e aponta para o styles.css e o script.js reais. Uso: node demo-escala/gerar.mjs
import { createRequire } from "node:module";
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const aqui = dirname(fileURLToPath(import.meta.url));
const raiz = join(aqui, "..");
const Handlebars = createRequire(join(raiz, "api/package.json"))("handlebars");

const PAGINAS = [
  ["atual", "Atual"],
  ["1", "1 · Foco na linha"],
  ["2", "2 · Trilho com nós"],
  ["3", "3 · Zonas tingidas"],
  ["4", "4 · Rótulo com faixa"],
  ["5", "5 · Leitura em 2 linhas"],
];

// LP 2º EF (cortes fora dos níveis, selo no meio da faixa) e LP 5º EF (cortes sobre níveis).
const lp = JSON.parse(readFileSync(join(raiz, "saida/lingua-portuguesa.json"), "utf8"));
const dados = { "2ef": lp["2ef"], "5ef": lp["5ef"] };

// Os dados extraídos ainda não têm PDF de item: uma habilidade em cada quatro ganha o
// botão "Ver item", apontando para um PDF de exemplo.
let n = 0;
for (const ano of Object.values(dados))
  for (const [chave, descritor] of Object.entries(ano)) {
    if (!/^D\d{2}$/.test(chave)) continue;
    for (const linhas of Object.values(descritor.scale))
      for (const linha of linhas)
        if (linha.content !== "---" && n++ % 4 === 0)
          linha.item = { id: "demo", nome: "Item de exemplo", tamanho: 1 };
  }

const jsonSeguro = (v) =>
  JSON.stringify(v).replaceAll("<", "\\u003c").replaceAll("\u2028", "\\u2028").replaceAll("\u2029", "\\u2029");

const template = Handlebars.compile(readFileSync(join(raiz, "revista/escala.hbs"), "utf8"));
const base = template({
  anos: [
    { chave: "2ef", rotulo: "2º EF" },
    { chave: "5ef", rotulo: "5º EF" },
  ],
  pagina: {},
  dadosRevista: jsonSeguro(dados),
})
  .replace('href="styles.css"', 'href="../revista/styles.css"')
  .replace('src="script.js"', 'src="../revista/script.js"></script>\n    <script src="opcoes.js"')
  .replaceAll('src="assets/', 'src="../revista/assets/')
  .replace("</head>", '    <link rel="stylesheet" href="opcoes.css">\n</head>');

for (const [id, titulo] of PAGINAS) {
  const arquivo = id === "atual" ? "atual.html" : `opcao-${id}.html`;
  const nav = PAGINAS.map(([i, t]) => {
    const href = i === "atual" ? "atual.html" : `opcao-${i}.html`;
    return `<a href="${href}"${i === id ? ' aria-current="page"' : ""}>${t}</a>`;
  }).join("");
  const html = base
    .replace("<body>", `<body data-opcao="${id}">`)
    .replace("<title>", `<title>${titulo} — `)
    .replace("</body>", `    <nav class="demo-nav" aria-label="Opções da demo">${nav}</nav>\n</body>`);
  writeFileSync(join(aqui, arquivo), html);
}

// PDF mínimo para o modal do "Ver item" (o script abre arquivos/itens/<id>.pdf).
const fluxo = "BT /F1 22 Tf 40 150 Td (Item de exemplo - demo) Tj ET";
const objetos = [
  "<</Type/Catalog/Pages 2 0 R>>",
  "<</Type/Pages/Kids[3 0 R]/Count 1>>",
  "<</Type/Page/Parent 2 0 R/MediaBox[0 0 420 300]/Contents 4 0 R/Resources<</Font<</F1 5 0 R>>>>>>",
  `<</Length ${fluxo.length}>>\nstream\n${fluxo}\nendstream`,
  "<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>",
];
let pdf = "%PDF-1.4\n";
const posicoes = objetos.map((o, i) => {
  const p = pdf.length;
  pdf += `${i + 1} 0 obj\n${o}\nendobj\n`;
  return p;
});
const xref = pdf.length;
pdf += `xref\n0 ${objetos.length + 1}\n0000000000 65535 f \n`;
pdf += posicoes.map((p) => `${String(p).padStart(10, "0")} 00000 n \n`).join("");
pdf += `trailer\n<</Size ${objetos.length + 1}/Root 1 0 R>>\nstartxref\n${xref}\n%%EOF\n`;
mkdirSync(join(aqui, "arquivos/itens"), { recursive: true });
writeFileSync(join(aqui, "arquivos/itens/demo.pdf"), pdf, "latin1");

console.log(`${PAGINAS.length} páginas em demo-escala/ (abra atual.html)`);
