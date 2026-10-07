#!/usr/bin/env node
// Copia /contrato para api/src/contrato e editor/src/contrato.
// Uso: node scripts/sync-contrato.mjs          (copia)
//      node scripts/sync-contrato.mjs --check  (falha se alguma cópia divergir)
import { readFileSync, writeFileSync, mkdirSync, readdirSync, existsSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const raiz = join(dirname(fileURLToPath(import.meta.url)), "..");
const origem = join(raiz, "contrato");
const destinos = [join(raiz, "api/src/contrato"), join(raiz, "editor/src/contrato")];
// Fixture compartilhada (testes da API e mocks do editor).
const fixture = join(raiz, "docs/fixtures/revista.json");
const destinosFixture = [join(raiz, "api/test/fixtures/revista.json"), join(raiz, "editor/src/mocks/revista.json")];
const cabecalho = "// GERADO por scripts/sync-contrato.mjs — edite em /contrato, não aqui.\n";
const verificar = process.argv.includes("--check");

const arquivos = readdirSync(origem).filter((f) => f.endsWith(".ts"));
const divergentes = [];

for (const destino of destinos) {
  mkdirSync(destino, { recursive: true });
  for (const arquivo of arquivos) {
    const esperado = cabecalho + readFileSync(join(origem, arquivo), "utf8");
    const alvo = join(destino, arquivo);
    if (verificar) {
      if (!existsSync(alvo) || readFileSync(alvo, "utf8") !== esperado) divergentes.push(alvo);
    } else {
      writeFileSync(alvo, esperado);
    }
  }
}

for (const alvo of destinosFixture) {
  const esperado = readFileSync(fixture, "utf8");
  if (verificar) {
    if (!existsSync(alvo) || readFileSync(alvo, "utf8") !== esperado) divergentes.push(alvo);
  } else {
    mkdirSync(dirname(alvo), { recursive: true });
    writeFileSync(alvo, esperado);
  }
}

if (verificar && divergentes.length) {
  console.error("Contrato divergente. Rode `node scripts/sync-contrato.mjs`:\n" + divergentes.join("\n"));
  process.exit(1);
}
console.log(verificar ? "Contrato sincronizado." : `Contrato copiado para ${destinos.length} destinos.`);
