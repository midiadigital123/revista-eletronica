# Preenchimento manual completo — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Permitir que a equipe pedagógica preencha a revista do zero no sistema: passo (intervalo mínimo) por etapa que gera as linhas vazias da régua, cores dos 4 padrões por projeto (herdáveis de outro projeto) e exportação em planilhas `.xlsx` no formato que o núcleo de impressão já recebe.

**Architecture:** Regras puras novas no contrato (`contrato/schemas.ts`), usadas pela API e pelo editor. A API grava `passo` no ano e `cores` no projeto, gera as linhas vazias numa rota com bloqueio, injeta as cores como `<style>` no `index.html` da revista e gera os `.xlsx` com `exceljs` (no preview, no zip e em `planilhas.zip`). O editor ganha o campo "Intervalo mínimo" com o botão "Gerar linhas vazias", o diálogo "Cores dos padrões" e o botão "Exportar planilhas".

**Tech Stack:** TypeScript, zod 4 (contrato), Express + Mongoose + vitest/supertest/mongodb-memory-server (API), React + shadcn + TanStack Query + MSW/vitest (editor), Handlebars (revista), `exceljs@4.4.0` (novo, só na API).

**Spec:** a conversa de 2026-10-20 (pedido do usuário + respostas): linhas vazias gravadas no banco; 1 planilha por caderno e etapa + aba "Escala"; herdar cores copiando os valores. Modelos de referência em `revista/modelo/*.xlsx`; escalas impressas como referência visual.

**Divisão em 3 partes:** A (passo), B (cores), C (planilhas). Cada parte entrega software funcionando e testado por conta própria. Ao iniciar a execução, salvar como `docs/superpowers/plans/2026-10-20-{passo,cores,planilhas}.md`. Ordem: A → B → C (C usa `passo` e `cores` na aba "Escala"); A e B podem andar em paralelo depois da Task 1.

## Global Constraints

- Contrato só em `contrato/`; depois de cada mudança, `node scripts/sync-contrato.mjs` (o `pretest` de API e editor roda `--check` e falha se as cópias divergirem).
- Todo campo novo do contrato entra também em `api/src/modules/projetos/model.ts` (o Mongoose descarta campo desconhecido em silêncio) e nos mocks do editor (`editor/src/mocks/handlers.ts`, `editor/src/mocks/db.ts`).
- Dados antigos continuam válidos: projeto sem `cores` → `cores: null`; ano sem `passo` → campo ausente; JSON de revista sem `passo` importa como hoje.
- Única dependência nova: `exceljs@4.4.0` em `api/package.json` (MIT). Nada no editor.
- Textos de UI em PT-BR; botões com ícone + verbo (D-022); campos com `aria-label` ou `FieldLabel`.
- Cores no formato `#rrggbb`; padrão atual: `#f72628`, `#ff8d43`, `#b3ccff`, `#0ed3ff` (`revista/styles.css:28-31`).
- Limite de linhas por padrão sobe de 50 para 200 (`LinhasPadrao`).
- Git: branch nova `feat/preenchimento-manual` a partir de `redesign-shadcn` (não de `main`, que está 10+ commits atrás), em worktree (superpowers:using-git-worktrees); `revista/modelo/*.xlsx` (hoje fora do git) entra no primeiro commit da Task 8 porque o teste lê os modelos; commits em PT-BR no estilo do repositório (`feat: …`); nenhum push sem pedido.
- `state.md`: registrar D-029 (passo materializado), D-030 (cores copiadas), D-031 (planilhas + `exceljs`) no turno em que cada parte for concluída.

## Review Focus

1. **Linha já existente com o mesmo nível em outro padrão**: gerar linhas não pode duplicar o nível nem mover a linha (teste na Task 2).
2. **Passo pequeno demais** (ex.: 0–1000 com passo 1 = 1000 níveis): resposta 400 com mensagem no campo `passo`, não 500 nem documento gigante (teste na Task 1).
3. **Cor maliciosa** (`"red;}</style><script>"`): rejeitada com 400 na API e nunca escrita no HTML (testes nas Tasks 5 e 6).
4. **Projeto antigo sem `cores`/`passo`** já gravado no Mongo: `GET` devolve `cores: null`, sem erro de schema (teste na Task 5).
5. **Níveis irregulares (2º EF) ou manuais fora da grade**: viram colunas próprias na planilha, com cabeçalho `"a a b"` correto (teste na Task 8).

## Skills por tarefa (todas já instaladas)

| Quando | Skill |
|---|---|
| Executar o plano | `superpowers:subagent-driven-development`, `superpowers:using-git-worktrees` |
| Cada task | `superpowers:test-driven-development`, `superpowers:verification-before-completion` |
| Tasks 3 e 7 (UI) | `shadcn` (Dialog, Field, NativeSelect, Input), `ecc:frontend-a11y` (rótulos, foco, contraste das cores escolhidas) |
| Task 8 (planilhas) | `anthropic-skills:xlsx` para abrir os `.xlsx` gerados e compará-los aos modelos |
| Task 6 (CSS injetado) | `ecc:security-review` |
| Fechamento | `ecc:e2e-testing` (roteiro de `docs/e2e.md` com Playwright), `superpowers:requesting-code-review`, `superpowers:finishing-a-development-branch`, `/impeccable document` (DESIGN.md muda na Task 7) |

---

## Parte A — Passo e linhas vazias

### Task 1: Contrato do passo

**Files:**
- Modify: `contrato/schemas.ts` (`LinhasPadrao` l.177, `AnoProjeto` l.209, `problemasDoAno` l.264, `CriarAnoEntrada` l.434, `AtualizarAnoEntrada` l.440, `RevistaAno` l.347-376)
- Modify: `contrato/revista.ts` (`CHAVES_DO_ANO` l.16, `anosDaRevista`, `revistaDosAnos`)
- Test: `api/test/contrato.test.ts`

**Interfaces:**
- Produces:
  - `Passo = z.int().min(1)`; `AnoProjeto.passo?: number`; `CriarAnoEntrada.passo?: number`; `AtualizarAnoEntrada.passo?: number | null` (null remove).
  - `MAX_LINHAS_PADRAO = 200` (usado em `LinhasPadrao.max`).
  - `niveisDoPasso(faixa: { min: number; max: number }, passo: number): number[]` — crescente, `min + k·passo < max`.
  - `problemasDoPasso(passo: number | undefined, faixa: { min: number; max: number }): Problema[]` — campo `"passo"`; erro se `niveisDoPasso(...).length > MAX_LINHAS_PADRAO` ("Intervalo pequeno demais: geraria N linhas"); chamado por `problemasDoAno`.
  - `linhasVaziasDoPasso(ano: Pick<AnoProjeto, "scaleRange" | "cortes" | "passo">, escala: Escala): Escala` — devolve escala nova: para cada nível de `niveisDoPasso` que **não existe em nenhum padrão**, adiciona `{ level, fim: Math.min(level + passo, max), content: CONTEUDO_VAZIO }` no padrão de `padraoDoNivel(level, cortes)`; linhas existentes intactas; cada padrão em ordem decrescente; sem `passo`, devolve a escala igual.
  - JSON da revista: chave opcional `passo` no ano (ida e volta).

- [ ] **Step 1: Testes que falham** em `api/test/contrato.test.ts`:

```ts
it("niveisDoPasso: 0–500 de 25 em 25 dá 20 níveis (0…475)", () => {
  const n = niveisDoPasso({ min: 0, max: 500 }, 25);
  expect(n).toHaveLength(20);
  expect(n[0]).toBe(0);
  expect(n.at(-1)).toBe(475);
});
it("linhasVaziasDoPasso distribui pelos cortes e não duplica nível existente", () => {
  const ano = { scaleRange: { min: 0, max: 500 }, cortes: { "padrao-1": 150, "padrao-2": 200, "padrao-3": 250 }, passo: 25 };
  const escala = Escala.parse({ "padrao-3": [{ level: 150, content: "manual" }] }); // 150 em outro padrão
  const r = linhasVaziasDoPasso(ano, escala);
  expect(r["padrao-1"].map((l) => l.level)).toEqual([125, 100, 75, 50, 25, 0]);
  expect(r["padrao-2"].map((l) => l.level)).toEqual([175]);          // 150 já existe
  expect(r["padrao-3"].map((l) => l.level)).toEqual([225, 200, 150]);
  expect(r["padrao-4"]).toHaveLength(10);
  expect(r["padrao-4"][0]).toEqual({ level: 475, fim: 500, content: "---" });
});
it("problemasDoAno recusa passo que gera mais de 200 linhas", () => {
  const p = problemasDoAno({ ano: "2ef", scaleRange: { min: 0, max: 1000 }, cortes: { "padrao-1": 350, "padrao-2": 400, "padrao-3": 500 }, passo: 1, descritores: [] });
  expect(p).toContainEqual(expect.objectContaining({ campo: "passo" }));
});
it("revista: passo vai e volta no JSON; sem passo continua válido", () => {
  const anos = anosDaRevista(Revista.parse({ "5ef": { scaleRange: { min: 0, max: 500 }, passo: 25 } }));
  expect(anos[0].passo).toBe(25);
  expect(revistaDosAnos(anos, {})["5ef"]).toMatchObject({ passo: 25 });
  expect(anosDaRevista(Revista.parse({ "5ef": { scaleRange: { min: 0, max: 500 } } }))[0]).not.toHaveProperty("passo");
});
```

- [ ] **Step 2:** `cd api && npx vitest run test/contrato.test.ts` → FAIL (funções não existem).
- [ ] **Step 3:** Implementar as interfaces acima em `contrato/schemas.ts` e `contrato/revista.ts` (`RevistaAno`: incluir `passo: Passo.optional()` no objeto `base` para não cair em "Código de descritor inválido"); rodar `node scripts/sync-contrato.mjs`.
- [ ] **Step 4:** `cd api && npm test` e `cd editor && npm test` → PASS.
- [ ] **Step 5:** `git commit -m "feat: passo (intervalo mínimo) por ano no contrato"`

### Task 2: API — gravar passo e gerar linhas vazias

**Files:**
- Modify: `api/src/modules/projetos/model.ts` (`anoSchema` l.70: `passo: Number`)
- Modify: `api/src/modules/projetos/service.ts` (`atualizarAno` l.211, `criarDescritor` l.242; nova `gerarLinhas`)
- Modify: `api/src/modules/projetos/routes.ts` (nova rota depois de `PATCH rotaAno`)
- Test: `api/test/projetos.test.ts`

**Interfaces:**
- Consumes: `linhasVaziasDoPasso`, `AtualizarAnoEntrada.passo` (Task 1).
- Produces:
  - `gerarLinhas(slug: string, caderno: Caderno, ano: Ano): Promise<AnoProjeto>` via `editarAno` (uma gravação); sem `passo` → `requisicaoInvalida("Defina o intervalo mínimo antes de gerar as linhas", { campo: "passo" })`.
  - Rota `POST /api/projetos/:slug/cadernos/:caderno/anos/:ano/gerar-linhas` com `exigirBloqueio`, `params: ParamsAno`, resposta 200 com o `AnoProjeto`.
  - `atualizarAno`: `passo: null` remove o campo; número grava.
  - `criarDescritor`: ano com `passo` → `descritor.scale = linhasVaziasDoPasso(alvo, descritor.scale)`.

- [ ] **Step 1: Testes que falham** em `api/test/projetos.test.ts` (usar `comProjeto()`/`comDescritor()` já existentes):
  - `"PATCH passo e gerar-linhas: 20 linhas no 5ef, texto preservado, idempotente"`: `PATCH ${LP}/anos/5ef {passo:25}` → 200; com `comDescritor()` (linha `level 50, content "a"` no padrão 1), `POST .../anos/5ef/gerar-linhas` → 200; contar as linhas do D01 = 20; a de nível 50 continua com `content "a"`; chamar de novo → mesmas 20.
  - `"descritor novo em ano com passo já nasce com as linhas vazias"`: depois de `passo: 25`, `POST descritores {codigo:"D02"}` → resposta com 20 linhas `---`.
  - `"gerar-linhas sem passo → 400 no campo passo; sem bloqueio → 423"`.
  - `"passo: null remove o passo"`.
- [ ] **Step 2:** `cd api && npx vitest run test/projetos.test.ts` → FAIL (404 na rota).
- [ ] **Step 3:** Implementar as interfaces acima.
- [ ] **Step 4:** `cd api && npm test` → PASS.
- [ ] **Step 5:** `git commit -m "feat: gerar linhas vazias pelo passo do ano"`

### Task 3: Editor — campo "Intervalo mínimo" e "Gerar linhas vazias"

**Files:**
- Create: `editor/src/projetos/ano/IntervaloMinimo.tsx`
- Modify: `editor/src/projetos/ano/TelaAno.tsx` (renderizar abaixo de `<FaixaCortes>`, l.70, dentro de `FieldsetEdicao`)
- Modify: `editor/src/projetos/api.ts` (`gerarLinhas`)
- Modify: `editor/src/mocks/handlers.ts` (PATCH de ano aceita `passo`; nova rota `gerar-linhas` usando `linhasVaziasDoPasso`)
- Test: `editor/src/projetos/ano/ano.test.tsx`

**Interfaces:**
- Consumes: `linhasVaziasDoPasso`, `niveisDoPasso`, `problemasDoPasso` (Task 1); rota da Task 2.
- Produces:
  - `projetosApi.gerarLinhas(slug: string, caderno: Caderno, ano: Ano): Promise<AnoProjeto>` → `POST ${pa(...)}/gerar-linhas`.
  - `IntervaloMinimo({ caderno, ano }: { caderno: Caderno; ano: AnoProjeto })`: input inteiro "Intervalo mínimo" (vazio = sem passo → envia `passo: null`), salvo no blur por `salvar({ … executar: projetosApi.atualizarAno(…{passo}), aplicar: trocarAno })` como em `FaixaCortes.confirmar`; erro inline de `problemasDoPasso`; botão "Gerar linhas vazias" (ícone `Plus`) desabilitado sem passo; `Confirmacao` com o texto "Criar N linhas vazias em M descritores?" (N e M contados com `linhasVaziasDoPasso` sobre `ano.descritores`; com N = 0, mostra "Nenhuma linha a criar").

- [ ] **Step 1: Testes que falham** em `ano.test.tsx`:
  - `"salva o intervalo mínimo ao sair do campo"`: digitar 25, blur → corpo do PATCH = `{ passo: 25 }` (capturar com `servidorMock.events.on("request:start", …)` como em `projetos.test.tsx:21`).
  - `"Gerar linhas vazias confirma com a contagem e atualiza a escala"`: ano do mock com 1 descritor vazio, passo 25, faixa 0–500 → diálogo mostra "Criar 20 linhas vazias em 1 descritor"; confirmar → escala do descritor com 20 linhas.
  - `"intervalo que gera mais de 200 linhas mostra erro e não salva"`.
- [ ] **Step 2:** `cd editor && npx vitest run src/projetos/ano/ano.test.tsx` → FAIL.
- [ ] **Step 3:** Implementar.
- [ ] **Step 4:** `cd editor && npm test && npm run typecheck && npm run lint` → PASS.
- [ ] **Step 5:** `git commit -m "feat: intervalo mínimo e geração de linhas no editor"`

---

## Parte B — Cores por projeto

### Task 4: Contrato das cores

**Files:**
- Modify: `contrato/schemas.ts` (constantes l.27-35; `ProjetoResumo` l.483; `Projeto` l.491; `AtualizarProjetoEntrada` l.430)
- Test: `api/test/contrato.test.ts`

**Interfaces:**
- Produces:
  - `CorHex = z.string().regex(/^#[0-9a-fA-F]{6}$/, { error: "Use uma cor no formato #rrggbb" })`.
  - `Cores = z.strictObject({ "padrao-1": CorHex, "padrao-2": CorHex, "padrao-3": CorHex, "padrao-4": CorHex })`.
  - `CORES_PADRAO = { "padrao-1": "#f72628", "padrao-2": "#ff8d43", "padrao-3": "#b3ccff", "padrao-4": "#0ed3ff" } as const`.
  - `Projeto.cores: Cores | null` e `ProjetoResumo.cores: Cores | null` (null = cores padrão).
  - `AtualizarProjetoEntrada.cores?: Cores | null` (null restaura o padrão).
  - `mesmasCores(a: Cores | null, b: Cores | null): boolean` (null equivale a `CORES_PADRAO`; compara sem diferenciar maiúsculas).

- [ ] **Step 1: Testes que falham**: `Cores.safeParse` aceita `#0A3d2F`, recusa `"red"`, `"#fff"` e `"red;}</style>"`; `AtualizarProjetoEntrada.parse({ cores: null })` passa; `mesmasCores(null, CORES_PADRAO) === true`.
- [ ] **Step 2:** `cd api && npx vitest run test/contrato.test.ts` → FAIL.
- [ ] **Step 3:** Implementar; `node scripts/sync-contrato.mjs`.
- [ ] **Step 4:** Para manter a suíte verde até a Task 5, `paraProjeto`/`paraResumo` (`api/src/modules/projetos/repository.ts`) devolvem `cores: null` provisoriamente e `editor/src/mocks/db.ts` ganha `cores: null`; `cd api && npm test` e `cd editor && npm test` → PASS.
- [ ] **Step 5:** `git commit -m "feat: cores dos padrões no contrato"`

### Task 5: API — gravar, devolver e copiar cores

**Files:**
- Modify: `api/src/modules/projetos/model.ts` (`ProjetoDb.cores: Cores | null`; `projetoSchema.cores` com subdocumento de 4 strings, `default: null`)
- Modify: `api/src/modules/projetos/repository.ts` (`paraProjeto` l.89, `paraResumo` l.101: `cores: projeto.cores ?? null`)
- Modify: `api/src/modules/projetos/service.ts` (`atualizar` l.132; `conteudoDaOrigem` l.71: retorno inclui `cores`; `copiar` usa `fonte.cores ?? null`; `vazio`/`importar` → `null`)
- Test: `api/test/projetos.test.ts`

**Interfaces:**
- Consumes: `Cores`, `AtualizarProjetoEntrada.cores` (Task 4).
- Produces: `PATCH /api/projetos/:slug { cores }` grava/restaura; `GET /api/projetos` e `GET /api/projetos/:slug` trazem `cores`; `POST /api/projetos` com origem `copiar` herda as 4 cores por valor.

- [ ] **Step 1: Testes que falham**:
  - `"PATCH cores grava, GET devolve, null restaura"`.
  - `"copiar projeto herda as cores por valor"`: criar `sp` com cores verdes, copiar para `rj`, depois mudar `sp` → `rj` segue verde.
  - `"projeto gravado sem o campo cores devolve cores null"`: inserir direto com `ProjetoModel.collection.insertOne` sem `cores` → `GET` 200 com `cores: null`.
  - `"PATCH com cor inválida → 400"`.
- [ ] **Step 2:** `cd api && npx vitest run test/projetos.test.ts` → FAIL.
- [ ] **Step 3:** Implementar.
- [ ] **Step 4:** `cd api && npm test` → PASS.
- [ ] **Step 5:** `git commit -m "feat: cores por projeto na API, herdadas ao copiar"`

### Task 6: Revista — cores do projeto no HTML

**Files:**
- Modify: `api/src/modules/revista/render.ts` (`EntradaRender` ganha `cores: Cores | null`; `renderRevista` l.65)
- Modify: `revista/escala.hbs` (no `<head>`, depois do `<link>` de `styles.css`: `{{#if cssCores}}<style>{{{cssCores}}}</style>{{/if}}`)
- Modify: `api/src/modules/geracao/service.ts` (`montarPacote` l.69: `renderRevista({ anos, pagina, cores: projeto.cores ?? null })`)
- Test: `api/test/revista.test.ts`, `api/test/geracao.test.ts`

**Interfaces:**
- Consumes: `Cores`, `CORES_PADRAO`, `mesmasCores` (Task 4).
- Produces: `cssDasCores(cores: Cores | null): string` (exportada de `render.ts`): `""` quando `mesmasCores(cores, null)`; senão `Cores.parse(cores)` (revalida) e devolve `:root{--color-padrao-1:#xxxxxx;--color-padrao-1-bg:rgba(r, g, b, 0.1);…}` para os 4 padrões (o `-bg` a 10% substitui os `rgba` fixos de `styles.css:34-37`).

- [ ] **Step 1: Testes que falham**:
  - `revista.test.ts`: `"sem cores ou com as cores padrão não há <style>"`; `"cores verdes viram variáveis em :root com -bg a 10%"` (espera `--color-padrao-4:#0b6b3a` e `--color-padrao-4-bg:rgba(11, 107, 58, 0.1)`); `"cssDasCores lança com valor malicioso"`.
  - `geracao.test.ts`: o `index.html` do preview de um projeto com cores contém o `<style>`, e o header `content-security-policy` tem `style-src` com `'unsafe-inline'`.
- [ ] **Step 2:** `cd api && npx vitest run test/revista.test.ts test/geracao.test.ts` → FAIL.
- [ ] **Step 3:** Implementar.
- [ ] **Step 4:** `cd api && npm test && node ../revista/regua.test.mjs` → PASS.
- [ ] **Step 5:** `git commit -m "feat: revista usa as cores do projeto"`

### Task 7: Editor — diálogo "Cores dos padrões"

**Files:**
- Create: `editor/src/projetos/CoresPadroes.tsx`
- Modify: `editor/src/projetos/ProjetoLayout.tsx` (botão "Cores" com ícone `Palette` no `Cabecalho`, l.~257; wrapper do layout com `style={estiloCores(projeto.cores)}`)
- Modify: `editor/src/mocks/handlers.ts` (PATCH de projeto aceita `cores`; cópia leva `cores`), `editor/src/mocks/db.ts`
- Modify: `PRODUCT.md:33`, `DESIGN.md:112` (as cores passam a ser do projeto)
- Test: `editor/src/projetos/projetos.test.tsx`

**Interfaces:**
- Consumes: `Cores`, `CORES_PADRAO`, `mesmasCores` (Task 4); `PATCH` com `cores` (Task 5); `useProjetos()` (`consultas.ts`), `Dialogo` e `NativeSelect` (padrão do `Renomear`, `ProjetoLayout.tsx:469`).
- Produces:
  - `esquemasDeCores(projetos: ProjetoResumo[], slugAtual: string): { rotulo: string; cores: Cores }[]` — esquemas distintos (por `mesmasCores`) dos outros projetos com `cores` não nulo; `rotulo` = nomes dos projetos que usam o esquema, separados por vírgula.
  - `estiloCores(cores: Cores | null): React.CSSProperties` — define `--color-padrao-N` e `--color-padrao-N-bg` (as tarjas `bg-padrao-N` do editor passam a mostrar as cores do projeto).
  - `CoresPadroes({ projeto }: { projeto: Projeto })`: 4 pares `<Input type="color">` + campo hex por padrão (rótulo "Padrão 01"…), `NativeSelect` "Usar esquema de…" (preenche os 4 campos), "Restaurar padrão" (envia `cores: null`), "Salvar" via `salvar({ descricao: "Cores dos padrões", executar: projetosApi.atualizar(slug, { cores }), aplicar: (_, r) => r })`.

- [ ] **Step 1: Testes que falham**:
  - `"salva as 4 cores do diálogo"` (corpo do PATCH = `{ cores: {...} }`).
  - `"Usar esquema de outro projeto preenche as 4 cores"` (mock com projeto `rj` verde).
  - `"Restaurar padrão envia cores null"`.
  - `"hex inválido mostra erro e não salva"`.
- [ ] **Step 2:** `cd editor && npx vitest run src/projetos/projetos.test.tsx` → FAIL.
- [ ] **Step 3:** Implementar.
- [ ] **Step 4:** `cd editor && npm test && npm run typecheck && npm run lint` → PASS.
- [ ] **Step 5:** `git commit -m "feat: diálogo de cores dos padrões com esquemas de outros projetos"`

---

## Parte C — Planilhas .xlsx

### Task 8: Gerador de planilha

**Files:**
- Modify: `api/package.json`, `api/package-lock.json` (`exceljs@4.4.0`)
- Create: `api/src/modules/planilhas/layout.ts` (colunas fixas por caderno)
- Create: `api/src/modules/planilhas/service.ts`
- Test: `api/test/planilhas.test.ts`

**Interfaces:**
- Consumes: `AnoProjeto` (com `passo`), `Cores`, `CORES_PADRAO`, `CONTEUDO_VAZIO`, `rotuloPadrao`-equivalente do contrato.
- Produces:
  - `niveisDaPlanilha(ano: AnoProjeto): { level: number; fim: number }[]` — níveis distintos de todas as linhas do ano ∪ `{ scaleRange.min }`, crescente; `fim` = próximo nível ou `max`.
  - `celulaDoNivel(linhas: LinhaEscala[], vazio: "–" | "..."): string` — `content` das linhas daquele nível sem os `---`, unidos por `"#"`; nada → `vazio`.
  - `separarHabilidades(skills: string[]): { relacionadas: string; correspondente: string }` — itens que começam com `(` → `correspondente`; os outros → `relacionadas`; cada grupo unido por `"\n"`.
  - `nomePlanilha(nomeProjeto: string, caderno: Caderno, ano: Ano): string` → ex.: `"São Paulo - LP 5EF.xlsx"` (MT para matemática; sem `/\\:*?"<>|`).
  - `gerarPlanilha(projeto: { nome: string; cores: Cores | null }, caderno: Caderno, ano: AnoProjeto): Promise<Buffer>`.
  - Layout (`layout.ts`), igual aos modelos 3EM/5EF:
    - LP, aba "Níveis": `Etapa | Descritor | Descrição da habilidade | Pre requisito | <níveis> | Praticas de linguagem: | Objeto de conhecimento: | Habilidades relacionadas | Habilidade correspondente`; vazio `–`.
    - MT, aba "Níveis": `Etapa | Cód. Descritor | Descritor | Pre requisito | <níveis> | Eixo cognitivo (Saeb): | Unidade temática: | Habilidades relacionadas: | Habilidade correspondente:`; vazio `...`.
    - `Etapa` = chave em maiúsculas (`5EF`); `Pre requisito` = `prerequisites` unidos por `"#"`; `practices` → 1ª coluna BNCC, `knowledge` → 2ª.
    - Cabeçalho em negrito, linha 1 congelada, colunas de nível com fundo `FFFF00`.
    - Aba "Escala": linhas `Etapa`, `Mínimo`, `Máximo`, `Intervalo mínimo` (vazio sem passo) e uma tabela `Padrão | Início (≥) | Fim (< / ≤ no 04) | Cor` com as 4 cores (projeto ou `CORES_PADRAO`).
  - `planilhasDoCaderno(projeto: { nome: string; cores: Cores | null }, caderno: CadernoProjeto): ArquivoPacote[]` — uma entrada por ano (`caminho` = `nomePlanilha(...)`, `tipo` xlsx, `abrir` devolve um `Readable` que recebe o buffer de `gerarPlanilha` quando ele fica pronto). `ArquivoPacote` importado só como tipo de `geracao/service.ts`.

- [ ] **Step 1: Testes que falham** em `api/test/planilhas.test.ts` (ler o buffer com `new ExcelJS.Workbook().xlsx.load(buf)`):
  - `"5º EF com passo 25: 20 colunas de nível de '0 a 25' a '475 a 500'"`.
  - `"2º EF irregular: colunas '0 a 390', '390 a 446', …, '782 a 1000'"` (dados de `saida/lingua-portuguesa.json`, `2ef`).
  - `"duas habilidades no mesmo nível viram 'a#b'; nível vazio vira '–' (LP) e '...' (MT)"`.
  - `"separarHabilidades divide códigos e habilidade correspondente"` com `["EF15LP02, EF15LP04", "(EF15LP03) Localizar informações explícitas em textos."]`.
  - `"cabeçalhos iguais aos do modelo"`: ler `revista/modelo/NÍVEIS - LP 5EF.xlsx` e `GO - MT_5EF.xlsx` e comparar os cabeçalhos das colunas fixas e o formato `"a a b"` dos de nível (ignorando espaços no fim).
  - `"aba Escala traz faixa, passo, cortes e cores"`.
- [ ] **Step 2:** `cd api && npx vitest run test/planilhas.test.ts` → FAIL.
- [ ] **Step 3:** `cd api && npm install exceljs@4.4.0`, depois implementar.
- [ ] **Step 4:** `cd api && npm test` → PASS; abrir um `.xlsx` gerado com `anthropic-skills:xlsx` e comparar com o modelo.
- [ ] **Step 5:** `git commit -m "feat: planilhas xlsx no formato do núcleo de impressão"`

### Task 9: Planilhas no zip, em `planilhas.zip` e no editor

**Files:**
- Modify: `api/src/modules/geracao/service.ts` (`TIPOS` ganha `xlsx`; `montarPacote` adiciona `planilhasDoCaderno` com prefixo `${id}/planilhas/`)
- Modify: `api/src/modules/geracao/routes.ts` (extrair `enviarZip(res: Response, nome: string, arquivos: ArquivoPacote[], next: NextFunction): Promise<void>` do `pacote.zip` atual; nova rota `GET /planilhas.zip`)
- Modify: `editor/src/projetos/api.ts` (`urlPlanilhas`), `editor/src/projetos/ProjetoLayout.tsx` (botão "Exportar planilhas", ícone `Download`, `<a download>` ao lado de "Exportar JSON", l.~272)
- Modify: `docs/contrato.md`, `docs/e2e.md`
- Test: `api/test/geracao.test.ts`, `editor/src/projetos/projetos.test.tsx`

**Interfaces:**
- Consumes: `planilhasDoCaderno` (Task 8).
- Produces: `GET /api/projetos/:slug/planilhas.zip` (leitura, sem bloqueio, `Content-Disposition: attachment; filename="<slug>-planilhas.zip"`, caminhos `<caderno>/<nomePlanilha>`); `pacote.zip` e preview com `<caderno>/planilhas/<nomePlanilha>`; `projetosApi.urlPlanilhas(slug: string): string`.

- [ ] **Step 1: Testes que falham**:
  - `geracao.test.ts`: `"planilhas.zip tem um xlsx por caderno e etapa"` (listar com o `python("-l", …)` já usado no teste do `pacote.zip`, l.113-130); `"pacote.zip inclui <caderno>/planilhas/*.xlsx"`; `"planilhas.zip exige login (401) e 404 para projeto inexistente"`.
  - `projetos.test.tsx`: `"botão Exportar planilhas aponta para planilhas.zip"`.
- [ ] **Step 2:** rodar os dois arquivos → FAIL.
- [ ] **Step 3:** Implementar; atualizar `docs/contrato.md` (passo, cores, `gerar-linhas`, `planilhas.zip`) e `docs/e2e.md` (passo de planilhas e cores).
- [ ] **Step 4:** `cd api && npm test`, `cd editor && npm test && npm run typecheck && npm run lint` → PASS.
- [ ] **Step 5:** `git commit -m "feat: exportar planilhas no zip e no editor"`

---

## Verificação ponta a ponta (depois da Task 9)

1. `cd api && npm test`; `cd editor && npm test && npm run typecheck && npm run lint`; `node revista/regua.test.mjs`; `python3 scripts/test_extrair_descritores.py`.
2. `docker compose up --build` (recria a imagem da API com `exceljs`) e roteiro de `docs/e2e.md` com Playwright, por `http://` (o Playwright bloqueia `file:`), prints do elemento `.escala-proficiencia`:
   - projeto vazio, LP 5º EF 0–500, intervalo 25, "Gerar linhas vazias" → 20 linhas por descritor; preview com régua de 25 em 25;
   - LP 2º EF sem intervalo continua com níveis manuais;
   - cores verdes → barra e rótulos verdes no preview e no zip; copiar o projeto herda as cores;
   - "Exportar planilhas" → abrir os `.xlsx` (skill `anthropic-skills:xlsx`) e comparar com `revista/modelo/`.
3. Importar o PDF de exemplo continua funcionando (JSON sem `passo`/`cores`).

## Fora de escopo (próximos pedidos prováveis)

- Nomes dos padrões editáveis ("Abaixo do básico/Básico/Proficiente/Avançado").
- Coluna "Eixo do conhecimento" (LP 2EF): o `topic` hoje guarda o rótulo da etapa (D-015), não o eixo.
- Importar `.xlsx` de volta; incluir o JSON no zip; "limpar linhas vazias fora do passo"; vínculo vivo de cores.
- Rótulos BNCC da revista (`escala.hbs`) são de LP também para MT (já é assim hoje).

## Execução recomendada

**Subagent-driven** (`superpowers:subagent-driven-development`): são 9 tasks encadeadas por interfaces do contrato (Tasks 1 e 4 alimentam todas as outras), e um erro que chegue à revista publicada ou à planilha da impressão custa caro; um revisor novo por task pega divergência de nome/tipo antes da task seguinte. Alternativa mais barata: **Native** (`superpowers:executing-plans`), eu executo tudo nesta sessão e um revisor confere a branch no fim.

## Estimativas (para quem executa)

Parte A ~2h (Tasks 1–3); Parte B ~2h (Tasks 4–7); Parte C ~2h30 (Tasks 8–9; o risco é o mapeamento BNCC); verificação ponta a ponta ~40 min. Total ~7h, ou ~5h com A e B em paralelo depois da Task 1.
