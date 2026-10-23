# state.md — revista-express

## Estado atual
<!-- sobrescrever a cada atualização -->
Passo 9 de 9 concluído: preenchimento manual (passo, cores por projeto, planilhas .xlsx) pronto na branch `feat/preenchimento-manual` (13 commits sobre `redesign-shadcn` 1ac55aa, último b958283). Cada task revisada por subagente; revisão final da branch (opus) liberou com correções, já feitas e re-revisadas.
Funcionando: API 135 testes + tsc; editor 71 testes + typecheck + lint; régua ok; extrator 8 ok. Passo + "Gerar linhas vazias"; cores no diálogo, na revista e herdadas ao copiar; `planilhas.zip`, planilhas dentro do `pacote.zip` e botão "Exportar planilhas".
Quebrado/pendente: conferência visual não feita (navegador do Playwright ocupado por outra sessão): layout do campo "Intervalo mínimo", diálogo de cores e planilha gerada vs `revista/modelo/`. Sem push/merge. Pendências pós-merge: `overrides` do uuid (aviso moderado via exceljs, não explorável); minors adiados (testes extras, variante não destrutiva do `Confirmacao`, hex salvo em maiúsculas, `montarPlanilhas` no service).

## Próxima ação
Selos de corte sem sobreposição feitos (D-042, `revista/` sem commit, API reconstruída): abrir o preview real do 2º EF e conferir a olho o 500 e o 400. Pendente de antes: rebuild (`docker compose up -d --build api editor`), anexar um PNG e um PDF a duas linhas no editor, gerar a revista e clicar em "Ver item" nas duas. Commits feitos na `dev` (sem push): 81e0c6f demo-escala, 59f2450 item com imagem, 90446dc legenda, 163c31e CSS/rótulos.

## Plano
<!-- plano completo: ~/.claude/plans/pasted-content-id-aef3-proponha-5-federated-castle.md -->
1. [x] Task 1 — contrato do passo (`niveisDoPasso`, `linhasVaziasDoPasso`, limite 200)
2. [x] Task 2 — API: gravar passo e `POST …/gerar-linhas`
3. [x] Task 3 — editor: "Intervalo mínimo" + "Gerar linhas vazias"
4. [x] Task 4 — contrato das cores (`Cores`, `CORES_PADRAO`)
5. [x] Task 5 — API: gravar, devolver e copiar cores
6. [x] Task 6 — revista: `<style>` com as cores do projeto
7. [x] Task 7 — editor: diálogo "Cores dos padrões"
8. [x] Task 8 — gerador de planilha (`exceljs`)
9. [x] Task 9 — planilhas no zip, `planilhas.zip` e botão no editor
10. [ ] Conferência visual (passos 8–10 de `docs/e2e.md`) e decidir merge/PR  ← agora

## Decisões

### D-001 — Um JSON por disciplina (2026-10-07)
- **Contexto:** a revista tem LP e MT (2º e 5º EF); descritores.json só tem nível de ano.
- **Decisão:** gerar `lingua-portuguesa.json` e `matematica.json`, cada um `{ "2ef": ..., "5ef": ... }`.
- **Motivo:** mantém o formato do descritores.json; um projeto do editor por disciplina.
- **Descartadas:** JSON único com disciplina no topo — foge do formato.
- **Arquivos afetados:** `scripts/extrair-descritores.mjs`
- **Status:** ativa

### D-002 — topic vazio (2026-10-07)
- **Contexto:** o PDF não tem "TÓPICO".
- **Decisão:** `topic = ""`.
- **Motivo:** schema aceita; não inventar dado.
- **Descartadas:** unidade temática/objeto — duplicaria bncc.knowledge.
- **Arquivos afetados:** `scripts/extrair-descritores.mjs`
- **Status:** ~~substituída por D-015~~

### D-003 — Coordenadas (pdftotext -bbox) em vez de texto -layout (2026-10-07)
- **Contexto:** prerrequisitos em 2 colunas, ticks × cortes em colunas diferentes, rótulos BNCC centralizados (MT D06 sai trocado no -layout).
- **Decisão:** ler palavras com x/y via `pdftotext -bbox` (poppler), Node sem dependências.
- **Motivo:** posição resolve colunas e associação rótulo↔valor.
- **Descartadas:** `-layout` + regex — frágil; pdfplumber/pdfjs — dependência nova.
- **Arquivos afetados:** `scripts/extrair-descritores.mjs`
- **Status:** ativa

### D-004 — Script em Python, stdlib + pdftotext (2026-10-07)
- **Contexto:** usuário pediu Python em vez de JS.
- **Decisão:** `scripts/extrair_descritores.py`, só stdlib, chamando `pdftotext -bbox` via subprocess; teste em unittest.
- **Motivo:** pedido do usuário; pypdf/pdfplumber não instalados.
- **Descartadas:** versão .mjs (removida); pdfplumber — dependência nova.
- **Arquivos afetados:** `scripts/extrair_descritores.py`, `scripts/test_extrair_descritores.py`
- **Status:** ativa

### D-005 — Texto da régua pertence ao tick logo abaixo (2026-10-07)
- **Contexto:** posição do texto em relação aos ticks varia por página (ex.: LP 2ef D04).
- **Decisão:** cada linha de texto vai para o primeiro tick abaixo dela (= base da faixa, como `montarFaixasRegua`); abaixo do último tick vai para o mínimo; "–" vira "---".
- **Motivo:** confere com as linhas cinzas da página renderizada.
- **Descartadas:** tick acima — erra D01.
- **Arquivos afetados:** `scripts/extrair_descritores.py`
- **Status:** ativa

### D-006 — Cortes do 5º ano por tabela (2026-10-07)
- **Contexto:** páginas do 5º ano não imprimem números de corte; 2º ano imprime (LP 350/400/500, MT 400/500/625).
- **Decisão:** `CORTES_SEM_NUMERO` com valores Saeb (LP 150/200/250, MT 175/225/275), usada só quando o PDF não traz os 3 cortes.
- **Motivo:** rótulos Básico/Proficiente da página ficam nesses ticks.
- **Descartadas:** ler linhas vetoriais (pdftocairo -svg) — linhas de corte não são caminhos consistentes.
- **Arquivos afetados:** `scripts/extrair_descritores.py`
- **Status:** ~~substituída por D-016~~

### D-007 — Etapa livre no formato <n><ef|em> (2026-10-07)
- **Contexto:** usuário pediu que o editor aceite qualquer etapa; ANOS fixo (5ef/9ef/3em) rejeita "2ef" do extrator.
- **Decisão:** `Ano` = regex `^[1-9](ef|em)$` (EM até 3); rótulos curto/longo e ordem gerados por funções no contrato; `ANOS_PADRAO` só como default/sugestão.
- **Motivo:** chaves curtas, rótulos atuais preservados exatamente, ordem igual à atual.
- **Descartadas:** texto livre — sem rótulo/ordem previsíveis; ampliar a lista fixa — volta a travar na próxima etapa.
- **Arquivos afetados:** `contrato/schemas.ts`, `contrato/revista.ts`, `api/src/modules/projetos/*`, `editor/src/projetos/*`, `revista/escala.hbs`, `revista/script.js`, `api/src/modules/revista/render.ts`
- **Status:** ativa

### D-008 — Projeto com cadernos por disciplina (2026-10-07)
- **Contexto:** a revista de um estado é dividida em LP, Matemática e Alfabetização (Alfa = PDF com LP + MT juntos).
- **Decisão:** `Projeto.cadernos[] = {id, anos}`, ids fixos `lingua-portuguesa`, `matematica`, `alfabetizacao-lp`, `alfabetizacao-mat`; `DISCIPLINAS` mapeia checkbox → cadernos. Rotas `/:slug/cadernos/:caderno/anos/...`.
- **Motivo:** escolha do usuário (1 projeto, N disciplinas); lista plana evita um nível a mais de aninhamento.
- **Descartadas:** 1 projeto por disciplina — usuário preferiu 1 projeto; disciplinas→componentes→anos aninhados — mais código para o mesmo resultado.
- **Arquivos afetados:** `contrato/schemas.ts`, `api/src/modules/projetos/*`, `editor/src/projetos/*`
- **Status:** parcialmente substituída por D-020 (Alfabetização removida)

### D-009 — Extração de PDF por rota síncrona (2026-10-07)
- **Contexto:** "Importar PDF" deve preencher os Anos antes de criar o projeto.
- **Decisão:** `POST /api/extracao` roda `extrair_descritores.py --stdout` e devolve as revistas por disciplina; o editor envia o resultado em `origem: {tipo: "importar", cadernos}`. Origem "Importar .json" sai da UI.
- **Motivo:** reusa a importação existente (Revista + anosDaRevista); API sem estado entre upload e criação.
- **Descartadas:** guardar o PDF e extrair na criação — anos não apareceriam antes de criar.
- **Arquivos afetados:** `scripts/extrair_descritores.py`, `api/src/modules/extracao/*`, `api/Dockerfile`, `editor/src/projetos/NovoProjeto.tsx`
- **Status:** ativa

### D-010 — Publicação: uma pasta por caderno; projetos antigos apagados (2026-10-07)
- **Contexto:** como publicar várias disciplinas e o que fazer com projetos só com `anos`.
- **Decisão:** zip/preview com `<caderno>/index.html` + índice raiz; página (textos/imagens) compartilhada. Projetos antigos são apagados (com confirmação antes do comando). Copiar copia só as disciplinas marcadas.
- **Motivo:** escolhas do usuário; template da revista intacto.
- **Descartadas:** página única com seletor — mexe em template/CSS/JS; migrar antigos para LP — usuário disse que são dados de teste.
- **Arquivos afetados:** `api/src/modules/geracao/service.ts`
- **Status:** ativa

### D-011 — Detalhes da API de cadernos/extração (2026-10-07)
- **Contexto:** pontos decididos na implementação dos passos 1–2.
- **Decisão:** `cadernosDasDisciplinas()` no contrato; exportar JSON vira `GET /:slug/cadernos/:caderno/revista`; extração devolve 422 para PDF ilegível/vazio/timeout e 500 se faltar python3; script configurável por `EXTRATOR_PDF`; `express.json` 10mb; índice raiz do zip usa o nome do projeto.
- **Motivo:** reuso no editor; erro do PDF ≠ erro do servidor; payload de importação com até 4 revistas.
- **Descartadas:** manter `/:slug/revista` — ambíguo com N cadernos.
- **Arquivos afetados:** `contrato/schemas.ts`, `api/src/modules/extracao/*`, `api/src/app.ts`, `api/src/modules/geracao/service.ts`
- **Status:** ativa

### D-012 — Detalhes do editor com cadernos (2026-10-07)
- **Contexto:** pontos decididos na implementação dos passos 3–4.
- **Decisão:** disciplinas começam desmarcadas (erro se nenhuma); rotas `/projetos/:slug/:caderno/ano/:ano[/:codigo]`; exportar JSON baixa um arquivo `{[caderno]: Revista}`; "+ Ano" por caderno; PDF > 50 MB recusado no cliente.
- **Motivo:** evitar criar disciplina por engano; formato do export igual a `origem.cadernos`.
- **Descartadas:** LP marcada por padrão — risco de criar LP ao importar só Matemática; um download por caderno — vários arquivos.
- **Arquivos afetados:** `editor/src/projetos/*`, `editor/src/mocks/*`
- **Status:** ativa

### D-013 — Abas do projeto em dois níveis (2026-10-07)
- **Contexto:** usuário achou confusa a fila única "Página | caderno 2º EF 5º EF + Ano | caderno ...".
- **Decisão:** 1º nível = Página + uma aba por caderno (leva ao 1º ano); 2º nível, só com caderno aberto = seletor segmentado dos anos + um "+ Ano". Caderno ativo via `useMatch` no layout.
- **Motivo:** o rótulo do caderno deixa de parecer aba; "+ Ano" aparece uma vez; hierarquia caderno → ano explícita.
- **Descartadas:** grupos com separador na mesma fila — era o layout confuso; select de caderno — esconde as opções.
- **Arquivos afetados:** `editor/src/projetos/ProjetoLayout.tsx`, `editor/src/projetos/projetos.test.tsx`
- **Status:** ativa

### D-014 — Preview abre o caderno da aba (2026-10-07)
- **Contexto:** o botão Preview abria o índice raiz com links por caderno; usuário quer o preview da aba aberta.
- **Decisão:** `urlPreview(slug, caderno)` → `preview/<caderno>/index.html`; na aba Página usa o primeiro caderno. Índice raiz fica só para o zip offline.
- **Motivo:** um clique até a revista certa.
- **Descartadas:** remover o índice raiz — o zip offline ainda precisa dele.
- **Arquivos afetados:** `editor/src/projetos/api.ts`, `editor/src/projetos/ProjetoLayout.tsx`
- **Status:** ativa

### D-015 — topic = rótulo longo da etapa em maiúsculas (2026-10-13)
- **Contexto:** tópico ficava vazio (D-002); usuário quer "2º ANO DO ENSINO FUNDAMENTAL" para 2ef, idem para todas as etapas.
- **Decisão:** extrator gera `topic` como `rotuloAnoLongo` em maiúsculas (EF: "Nº ANO DO ENSINO FUNDAMENTAL"; EM: "Nª SÉRIE DO ENSINO MÉDIO"). Substitui D-002.
- **Motivo:** pedido do usuário; mesmo texto do cabeçalho da página.
- **Descartadas:** default no schema — afetaria dados digitados à mão.
- **Arquivos afetados:** `scripts/extrair_descritores.py`
- **Status:** ativa

### D-016 — Cortes sempre impressos; sem tabela de fallback (2026-10-13)
- **Contexto:** usuário corrigiu: todas as revistas imprimem os números de corte; o 5º EF do PDF de exemplo foi exceção.
- **Decisão:** remover `CORTES_SEM_NUMERO`; faltando corte, a extração falha com erro. Substitui D-006.
- **Motivo:** não inventar dado; erro explícito em vez de valor Saeb silencioso.
- **Descartadas:** manter fallback — esconderia PDF fora do padrão.
- **Arquivos afetados:** `scripts/extrair_descritores.py`, `scripts/test_extrair_descritores.py`
- **Status:** ativa

### D-017 — Linha da escala com início (level), fim e item opcionais (2026-10-13)
- **Contexto:** habilidades tinham só âncora; várias habilidades da mesma faixa saíam concatenadas; "Ver item" precisa de PDF.
- **Decisão:** `LinhaEscala = {level, fim?, content, item?}`; `level` continua sendo o início; extrator gera uma linha por habilidade (nova habilidade = linha anterior termina em "." e atual começa com maiúscula), `fim` = tick acima (ou máximo). `item = {id, nome, tamanho}` aponta para PDF no GridFS (≤ 5 MB).
- **Motivo:** campos opcionais mantêm dados antigos válidos; manter `level` evita reescrever API/editor/revista.
- **Descartadas:** renomear para inicio/fim — diff grande sem ganho; juntar por faixa — era o bug.
- **Arquivos afetados:** `contrato/schemas.ts`, `scripts/extrair_descritores.py`, editor, API, revista
- **Status:** ativa

### D-018 — UX: ≥/< nos cortes, hover no lugar de "Ver mais", "Ver item" só com PDF (2026-10-13)
- **Contexto:** pedido do usuário (itens 2, 5, 6).
- **Decisão:** cards de padrão com dois campos de operador fixo (≥ início, < fim; Padrão 04 ≤ máximo), mesmo corte ligado entre cards vizinhos; revista expande o texto no hover/foco reaproveitando a animação existente; "Ver item" abre o PDF num iframe no modal.
- **Motivo:** mostra onde o padrão começa e termina; menos cliques; `<object>` é bloqueado pelo CSP do helmet.
- **Descartadas:** operador selecionável — mudaria a semântica dos cortes; link em nova aba — usuário quer ver na revista.
- **Arquivos afetados:** `editor/src/projetos/ano/*`, `revista/*`, `api/src/modules/*`
- **Status:** ativa

### D-019 — Cortes em negrito na coluna dos ticks (2026-10-13)
- **Contexto:** PDF de LP (9º EF/3ª EM) recusado com "esperados 3 cortes impressos, achados []". Os cortes estão impressos, em negrito, na mesma coluna dos ticks (não à esquerda como no 2º EF Alfa). O 5º EF do PDF Alfa é igual — D-006 partiu de premissa errada.
- **Decisão:** número na coluna dos ticks com caixa mais alta que a mediana dos ticks (+0,1 pt; negrito = 9,918 vs 9,747 pt) também é corte (continua sendo tick/base de faixa).
- **Motivo:** pdftotext -bbox não informa a fonte; a altura da caixa difere de forma consistente nos dois PDFs.
- **Descartadas:** ler fonte com pdfplumber — dependência nova; tabela de cortes — dado inventado (LP 5º EF real é 125/175/225, não 150/200/250).
- **Arquivos afetados:** `scripts/extrair_descritores.py`, `scripts/test_extrair_descritores.py`, `api/test/extracao.test.ts`
- **Status:** ativa

### D-020 — Só dois cadernos: LP e MT (2026-10-13)
- **Contexto:** usuário decidiu remover a disciplina Alfabetização; cortes variam por projeto (já lidos do PDF, D-019).
- **Decisão:** `CADERNOS = ["lingua-portuguesa", "matematica"]`, `DISCIPLINAS` sem `alfabetizacao`. PDF de Alfabetização (LP + MT) pode ser enviado nos dois campos. 3 projetos antigos com cadernos Alfa (todos na lixeira, sem imagens) apagados com confirmação.
- **Motivo:** pedido do usuário; `cadernosDaExtracao` já filtra a disciplina do campo, sem código novo.
- **Descartadas:** migrar alfabetizacao-* → LP/MT — usuário escolheu apagar.
- **Arquivos afetados:** `contrato/schemas.ts`, `editor/src/projetos/NovoProjeto.tsx`, testes da API/editor, `README.md`, `docs/contrato.md`
- **Status:** ativa

### D-021 — BNCC: valores por bloco e coluna detectada; skills até 2000 (2026-10-13)
- **Contexto:** PDF LP recusado: "3em.D05.bncc.skills.1: Too big (<=500)". Causas: (1) linha a linha, a 1ª linha de um valor longo ia para o rótulo de cima ("relacionadas"); (2) no 9º D03 a coluna de valores começa em x=154 (< 165 fixo) e o valor virava rótulo; (3) habilidades do EM chegam a ~1000 caracteres.
- **Decisão:** agrupar linhas de valor em blocos (entrelinha < 13pt) e ligar cada bloco ao rótulo mais próximo do centro; coluna de valores = 1ª palavra após "Rótulo:" (fallback 165); `Bncc.skills` com até 2000 caracteres.
- **Motivo:** rótulos ficam centralizados no bloco; layout varia por revista.
- **Descartadas:** só aumentar o limite — skills continuariam erradas.
- **Arquivos afetados:** `scripts/extrair_descritores.py`, `scripts/test_extrair_descritores.py`, `contrato/schemas.ts`
- **Status:** ativa

### D-022 — Botões de criar com ícone Plus e verbo (2026-10-13 17:15)
- **Contexto:** polish da UI dos projetos; "+ Descritor", "+ Ano", "+ parágrafo" usavam "+" digitado, enquanto "Novo projeto" e "Adicionar linha" usam ícone lucide.
- **Decisão:** ícone `Plus` + "Novo descritor", "Novo ano" (aria "Novo ano em {caderno}"), "Adicionar parágrafo". "Excluir ano" vira destructive com Trash2. Lista: "Atualizado" sem a palavra repetida; Situação "Livre" sem bloqueio. Favicon vazio (data:). Escala no celular: textarea em linha própria.
- **Motivo:** um padrão só para criar/excluir; glifo no lugar de ícone foge do sistema.
- **Descartadas:** manter "+" com aria-label antigo — nome acessível diferente do visível; mudar placeholder "sem item" — convenção da revista, fixado em teste.
- **Arquivos afetados:** `editor/src/projetos/**`, `editor/index.html`, testes.
- **Status:** ativa

### D-023 — CSP da API sem upgrade-insecure-requests (2026-10-15)
- **Contexto:** no acesso por http://192.168.5.39:8080 o preview não carregava CSS/JS/SVG: o `helmet()` padrão envia `upgrade-insecure-requests`, e o navegador troca as requisições para https. Em localhost isso não aparece porque o navegador ignora a diretiva.
- **Decisão:** `helmet({ contentSecurityPolicy: { directives: { upgradeInsecureRequests: null } } })`.
- **Motivo:** o sistema é servido em http na rede local; o resto do CSP continua igual.
- **Descartadas:** HTTPS com certificado próprio — exige confiar no certificado em cada máquina; desligar o CSP inteiro — perde proteção sem motivo.
- **Arquivos afetados:** `api/src/app.ts`
- **Status:** ativa

### D-024 — Régua pelos níveis; cortes posicionados dentro da faixa (2026-10-16 10:40)
- **Contexto:** a régua quebrava as faixas por padrão; corte fora de um nível (500 ≠ 503, 400 ≠ 446/390) gerava faixas vazias de altura cheia e a proporção ficava diferente da revista impressa.
- **Decisão:** `montarFaixasRegua` monta as faixas só pelos níveis de todas as linhas e retorna `{faixas, cortes, padroes}` com y em alturas de linha. Cortes fora de um nível ficam dentro da faixa que os contém, na fração (topo − corte)/(topo − base) limitada a 25–75%. Preenchimento tem meia altura. Rótulos dos padrões, barra de cor e selos dos cortes ficam numa camada absoluta (`.escala-rotulos`, `.escala-barra`, `.escala-corte`). Padrão sem linhas continua com faixa "---".
- **Motivo:** a revista mede 500 a ~23% e 400 a ~72% das faixas; o limite também impede o selo de colar no tick vizinho.
- **Descartadas:** proporção linear pura — selo do 500 cola no 503; manter blocos por padrão — uma faixa não atravessa dois blocos.
- **Arquivos afetados:** `revista/script.js`, `revista/styles.css`, `revista/regua.test.mjs`
- **Status:** ativa

### D-025 — Faixa sem habilidade aparece vazia, sem "---" (2026-10-16)
- **Contexto:** usuário prefere a faixa vazia aos tracinhos "---" na revista.
- **Decisão:** só a exibição muda (`faixaHTML` em `revista/script.js`): "---" e `null` viram texto vazio. O dado e `montarFaixasRegua` continuam com "---", que marca faixa de altura cheia (preenchimento `null` tem meia altura).
- **Motivo:** uma linha; não mexe no extrator, no editor nem nos testes da régua.
- **Descartadas:** remover "---" do extrator/dados — muda D-005 e o editor sem necessidade.
- **Arquivos afetados:** `revista/script.js`
- **Status:** ativa

### D-026 — Ajustes do UX portados à mão, não copiados (2026-10-16 11:00)
- **Contexto:** o UX designer editou `~/Documentos/{escala.html,script.js,styles.css}` a partir de um protótipo antigo (fetch do JSON, régua fixa 125/250/375, modal com texto).
- **Decisão:** portar só botão "Ver item" (círculo 44px fora da linha, SVG, tooltip, anel amarelo; ≤1040px dentro da linha; ≤500px 36px) e hover (120ms abrir / 140ms fechar, uma aberta por vez, `.fechando`, transição 0.3s, padding 1.5rem).
- **Motivo:** copiar os arquivos quebraria a régua (D-024/D-025), o PDF do item e o `escala.hbs`.
- **Descartadas:** substituir os arquivos — perde régua, PDF e `escapeHtml`.
- **Arquivos afetados:** `revista/script.js`, `revista/styles.css`
- **Status:** ativa

### D-027 — Truncamento por CSS em vez de por caracteres (2026-10-16 11:00)
- **Contexto:** o JS cortava o texto em 56/40 caracteres; o designer passou a usar `text-overflow: ellipsis`.
- **Decisão:** texto completo no `<p>`, "..." pelo CSS (classe `tem-texto`, vale também para linhas sem PDF); `atualizarTruncamentos` marca `.tem-ver-mais` só onde o texto estoura, refeito em resize (150ms) e `document.fonts.ready`.
- **Motivo:** o corte acompanha a largura real; some o texto truncado guardado em `data-*`.
- **Descartadas:** manter o limite de caracteres — corta cedo em telas largas e tarde em estreitas.
- **Arquivos afetados:** `revista/script.js`, `revista/styles.css`
- **Status:** ativa

### D-028 — Demo das 5 opções da escala em `demo-escala/`, sem tocar `revista/` (2026-10-20 14:15)
- **Contexto:** pedido de 5 UIs sutis para a régua, mantendo a identidade (branco, amarelo `#ffeb00`, 4 cores de padrão, selos, "Ver item"); depois, uma página por opção reaproveitando estilos e comportamentos atuais.
- **Decisão:** `gerar.mjs` renderiza o `revista/escala.hbs` real (handlebars de `api/node_modules`) com `saida/lingua-portuguesa.json` (2ef e 5ef; 1 em cada 4 habilidades ganha `item` de exemplo) e gera `atual.html` + `opcao-1..5.html`, todas carregando `../revista/styles.css` e `../revista/script.js` sem alteração. Uma folha `opcoes.css` com as 5 opções escopadas por `body[data-opcao="N"]` (CSS nesting) e um `opcoes.js` para o que o CSS não alcança: `--p` (cor do padrão) por linha (1 e 5), `.escala-zona`/`.escala-divisa` (3), intervalo no rótulo lendo `cortes` (4) e `DescriptorManager.prototype.atualizarTruncamentos` por altura em vez de largura (5). Todos reagem ao re-render por `MutationObserver` em `.escala-content`.
- **Motivo:** a revista real fica intacta até a escolha; a linha da régua não carrega o padrão no DOM, então a demo o deduz das barras `.escala-barra`; na implementação, o padrão virar classe em `faixaHTML` (1 linha) evita o JS.
- **Descartadas:** copiar `styles.css`/`script.js` para a demo — divergiria da revista; 5 CSS/JS separados — mais arquivos e mais portões, mesmo resultado; `--escala-cor-width` 10px na opção 2 — deslocaria toda a geometria; divisa de 1.5px na opção 3 — o navegador arredonda a borda do rótulo para 1px e ela sai mais clara que a da linha (virou 2px).
- **Arquivos afetados:** `demo-escala/gerar.mjs`, `demo-escala/opcoes.css`, `demo-escala/opcoes.js`, `demo-escala/*.html` (gerados), `demo-escala/arquivos/itens/demo.pdf`
- **Status:** ativa (demo; nada escolhido nem implementado em `revista/`)

### D-029 — Passo por ano gera linhas vazias gravadas no banco (2026-10-20)
- **Contexto:** a equipe pedagógica quer preencher no sistema antes da revista impressa existir; hoje as linhas vazias da régua só vêm do PDF importado. Planilhas modelo: 3EM/5EF de 25 em 25; 2º EF (MT e LP) com níveis irregulares (390, 446, 503…).
- **Decisão:** `AnoProjeto.passo` opcional; `POST …/anos/:ano/gerar-linhas` cria os níveis `min + k·passo < max` que não existem em nenhum padrão (`content: "---"`, padrão por `padraoDoNivel`), sem mexer em linhas existentes; descritor novo em ano com passo já nasce com as linhas; `LinhasPadrao.max` 50 → 200; passo que gera mais de 200 níveis é recusado.
- **Motivo:** escolha do usuário (gravar no banco); dado igual ao do PDF importado, então régua, JSON e planilha não mudam de lógica.
- **Descartadas:** só derivar na saída — o JSON deixaria de bater com o importado e a régua dependeria do passo; passo obrigatório — não descreve o 2º EF.
- **Arquivos afetados:** `contrato/schemas.ts`, `contrato/revista.ts`, `api/src/modules/projetos/*`, `editor/src/projetos/ano/*`, mocks do editor
- **Status:** aprovada, não implementada

### D-030 — Cores dos 4 padrões por projeto; herdar copia os valores (2026-10-20)
- **Contexto:** cores fixas em `revista/styles.css:28-37`; a impressa usa outro esquema (verdes); usuário quer personalizar e reaproveitar esquemas de outros projetos.
- **Decisão:** `Projeto.cores: Cores | null` (null = padrão atual); herdar = escolher um esquema já usado e copiar os 4 hex; "Copiar projeto" leva as cores; a revista recebe `<style>:root{--color-padrao-N…;-bg a 10%}</style>` só quando difere do padrão, com hex revalidado no render.
- **Motivo:** escolha do usuário (copiar valores); revistas publicadas não mudam quando o projeto de origem muda.
- **Descartadas:** vínculo vivo com o projeto de origem — exige resolver o vínculo na geração e tratar origem apagada; cor como campo de página — `CAMPOS_PAGINA` não tem tipo cor.
- **Arquivos afetados:** `contrato/schemas.ts`, `api/src/modules/projetos/*`, `api/src/modules/revista/render.ts`, `revista/escala.hbs`, `editor/src/projetos/*`, `PRODUCT.md`, `DESIGN.md`
- **Status:** aprovada, não implementada

### D-031 — Planilhas .xlsx por caderno e etapa, com aba "Escala", via exceljs (2026-10-20)
- **Contexto:** o núcleo de impressão recebe hoje planilhas (`revista/modelo/`, 1 por disciplina e etapa) sem cortes, cores nem nomes de padrão.
- **Decisão:** 1 `.xlsx` por caderno × etapa: aba "Níveis" no layout dos modelos 3EM/5EF (LP e MT com suas colunas; itens do mesmo nível unidos por `#`; vazio `–` em LP e `...` em MT) + aba "Escala" (mín., máx., passo, cortes, cores). Saem em `planilhas.zip`, no `pacote.zip` e no preview. Gerado na API com `exceljs@4.4.0`.
- **Motivo:** escolha do usuário; dado já está em memória na API; sem processo filho nem Python novo.
- **Descartadas:** idêntico aos modelos sem aba extra — cortes continuariam por outro meio; 1 arquivo por projeto — foge do que a impressão usa; openpyxl via Python — dependência nova no container e processo filho.
- **Arquivos afetados:** `api/package.json`, `api/src/modules/planilhas/*`, `api/src/modules/geracao/*`, `editor/src/projetos/ProjetoLayout.tsx`, `docs/contrato.md`, `docs/e2e.md`
- **Status:** aprovada, não implementada

### D-032 — Opção 1 escolhida; linha cresce no hover, números de início e fim preenchidos (2026-10-20)
- **Contexto:** usuário escolheu a opção 1 (foco na linha) e pediu: destacar o número de início e o de fim da habilidade; hover sem cartão flutuante (a linha cresce e mostra o texto das reticências); tirar a "dupla borda" (pílula branca com anel de cor).
- **Decisão:** só na demo (`opcao-1.html`). Anel removido; número de início (base da linha) e de fim (base da linha de cima, via `:has(+ .linha:hover)`) ganham fundo na cor do padrão (`--p` e `--p-prox`) e `scale(1.15)`. `.linha-conteudo.expandido` deixa de ser `absolute` (fica no fluxo, sem sombra/raio) e a `.linha` aberta passa a `height: auto`. `opcoes.js` (`reposicionar`, via ResizeObserver) recalcula top/height de `.escala-barra`, `.padrao-label` e `.escala-corte` pela altura real das linhas.
- **Motivo:** barra, rótulos e cortes são posicionados em múltiplos de 80px; sem recalcular, desalinham quando a linha cresce.
- **Descartadas:** manter o cartão só com outro estilo — usuário quer a linha crescendo; anel + preenchimento — mantém a dupla borda.
- **Arquivos afetados:** `demo-escala/opcoes.css`, `demo-escala/opcoes.js`
- **Status:** ativa (demo; `revista/` intacto; conferido por estilos computados, sem print)

### D-033 — Opção 1 portada para `revista/` (2026-10-20)
- **Contexto:** usuário pediu para levar a opção 1 (D-032) para a revista, com ponytail.
- **Decisão:** `faixaHTML` põe `--p` e `--p-prox` (cor do padrão da linha e da de baixo) no `style` da `.linha` (sem classe `padrao-N`, que já pinta fundo); barras, rótulos e cortes ganham `data-y`; `seguirLinhas`/`reposicionarCamadas` (ResizeObserver) recalculam top/height pela altura real das linhas. CSS: `.expandido` deixa de ser cartão `absolute` e a linha cresce (`.linha:has(.linha-conteudo.expandido){height:auto}`); hover tinge a linha, barra +3px, número de início e de fim preenchidos. Removidos o `left/right` inline do mobile e as regras de sombra/`fechando`.
- **Motivo:** o JS só existe porque barra/rótulos/cortes são posicionados em múltiplos de 80px; o resto é CSS.
- **Descartadas:** reaproveitar `opcoes.js` da demo — deduz o padrão das barras, a revista já sabe; classe `padrao-N` na linha — colide com `.padrao-N{background}`.
- **Arquivos afetados:** `revista/styles.css`, `revista/script.js`
- **Status:** ativa, sem commit. Efeito colateral: `demo-escala/` (atual e opções 2–5) passa a usar o novo hover, pois carrega os arquivos da revista.

### D-034 — Hover/clique da escala: transição única, foco só de teclado, clique abre item, sem "dente" (2026-10-21)
- **Contexto:** usuário viu fundos com tempos diferentes no hover, habilidade "ativa" após clique+sair do mouse, clique que não abre o item, "dente" na barra e número de corte menor que os demais no hover.
- **Decisão:** `.linha-conteudo` ganha `transition: background-color .2s` (antes só `.tem-ver-mais`); tinta/destaque por `:has(:focus-visible)` em vez de `:focus-within`, `focusin` de `initDestaqueNumeros` só com `:focus-visible`; clique de mouse em `.linha-conteudo.tem-ver-item` chama `abrirModal` (linha sem item: nada), `fecharModal` devolve o foco ao abridor; `.linha::before` removido (a barra já tem a cor, o +3px criava o degrau); `.destaque` anula fonte, altura e anel de `.eh-corte` e o selo `.escala-corte` só amplia.
- **Motivo:** causas lidas no código (sem transition, foco de mouse mantendo `:focus-within`, único handler de clique no botão, `::before` 10px vs barra 7px, `.eh-corte` com fonte menor e anel).
- **Descartadas:** manter o `::before` e engrossar a barra toda — desloca a geometria; expandir texto no clique sem item — o hover já faz isso (decisão do usuário).
- **Arquivos afetados:** `revista/styles.css`, `revista/script.js`
- **Status:** ativa, sem commit. `demo-escala/opcoes.css` ainda tem `:focus-within` próprio (demo, não mexido).

### D-035 — Varredura de UX da escala aplicada (itens 1 a 5) (2026-10-21)
- **Contexto:** `impeccable critique` (A design + B detector/navegador) deu 22/36; usuário escolheu aplicar os 5 itens.
- **Decisão:** (1) modal: `closeBtn.focus()` ao abrir, `inert` nos filhos do `body` exceto o modal, fechar 44px; (2) habilidades truncadas com `role="button"` + `aria-expanded` (atualizado em `abrirHabilidade`/`finalizar`), Enter/Espaço abre o item ou alterna, `aria-label` do "Ver item" com o nível; (3) `@media (prefers-reduced-motion)` zera as transições da escala; (4) legenda "Cada habilidade vale a partir do nível indicado…" (`escala.hbs`), início do padrão ("≥ 500") sob o nome no rótulo, linhas acima da que está em foco com tinta de 6% (leitura cumulativa); (5) texto do filtro inativo `#4b5563`, outline preto no "Ver item", borda escura de 1px nas barras dos padrões.
- **Motivo:** achados medidos no navegador (foco não entrava no modal, 0 regras de reduced-motion, `tem-ver-mais` sem role) e contraste (barra 1.6–2.3:1, filtro 4.0:1, outline ~1.8:1).
- **Descartadas:** faixa completa "≥ a e < b" no rótulo — quebrava linha e cortava nos padrões baixos; remover `tabindex` das habilidades — keyboard perderia a expansão; focus trap manual — `inert` nativo basta.
- **Arquivos afetados:** `revista/styles.css`, `revista/script.js`, `revista/escala.hbs`, `demo-escala/*.html` (regerados)
- **Correção (2026-10-21, pós-commit a0f6d73):** a tinta da leitura cumulativa foi aplicada nas linhas de CIMA, o contrário do correto. Quem chegou à habilidade em foco já domina as de BAIXO: seletor passou para `.linha:is(:hover, :has(:focus-visible)) ~ .linha .linha-conteudo` e a legenda virou "Quem alcança uma habilidade já domina todas as que estão abaixo dela." (a legenda anterior também descrevia o sentido errado).
- **Correção 2 (2026-10-21):** o selo de corte solto (`.escala-corte`, z-index 3) cobria o número de ancoragem de baixo da habilidade em hover (503 sob o 500). `.proficiencia-valor-numero.destaque` ganhou `z-index: 4`; medido: início e fim em hover ficam por cima do corte.
- **Migração para a revista real (2026-10-21):** o gerador real é `revista/` (a API renderiza `revista/escala.hbs`; `demo-escala/` só carrega esses arquivos) e já tinha tudo. O container `revista-api` guarda cópia da pasta no build (`COPY revista`), então estava com a versão antiga; `docker compose up -d --build api` refez a imagem. Conferido dentro do container: legenda, reduced-motion, `fundoInerte`, `z-index: 4` e o seletor `~ .linha`. `escala.html`/`script.js`/`styles.css` da raiz são o protótipo antigo, não tocados. Preview autenticado não aberto no navegador.
- **Correção 3 (2026-10-21, substitui a parte da D-034 "clique de mouse na habilidade com item abre o modal"):** o item abre só pelo botão "Ver item"; clicar na habilidade não faz nada, `cursor: pointer` removido, Enter/Espaço só alterna a expansão. Tinta das linhas de baixo passou a cobrir também `.proficiencia-valor` e `.linha-marcador` (antes sobrava uma faixa branca na coluna dos números). Medido no navegador; API reconstruída.
- **Correção 4 (2026-10-21):** texto dos números em destaque (início/fim) passa a ser branco quando o preto não contrasta com a cor do padrão. `corTextoSobre(hex)` em `revista/script.js` (exportada, testada em `regua.test.mjs`) usa APCA e não a razão WCAG 2: no vermelho `#f72628` o WCAG aprova o preto (5,3:1) mas APCA dá |Lc| 72 para branco contra 45 para preto, o que bate com a leitura do usuário. `initDestaqueNumeros` lê `--color-padrao-N` da raiz (cores do projeto) e põe `--destaque-texto`; `color` entra na transição. Cores padrão: só o vermelho vira branco; cores de projeto conferidas (escuras → branco, amarelo → preto). API reconstruída.
- **Acesso pela rede (2026-10-21):** `ufw status` do usuário mostra `8080/tcp ALLOW 192.168.5.0/24`, então a pendência de 2026-10-15 ("falta liberar a 8080 no ufw") está resolvida; só o editor publica porta (8080), API e Mongo ficam internos. Vale só para a sub-rede 192.168.5.0/24 (outra VLAN/sub-rede não entra). Falta o teste de verdade a partir de outro computador e fixar o IP 192.168.5.39 (hoje DHCP).
- **Status:** ativa, correções sem commit. Limite: com o foco dentro do iframe do PDF o Esc não chega à página (fechar pelo botão); não conferido em 420px reais nem no leitor de tela.

### D-036 — Linhas sem habilidade ("---") têm meia altura (2026-10-21)
- **Contexto:** intervalos mínimos sem habilidade ocupavam 80px, igual aos preenchidos; o texto agora quebra linha (sem `nowrap`), então a diferença ficou visível.
- **Decisão:** `ehVazia(conteudo)` (null ou "---") dá `altura` 0.5 em `montarFaixasRegua` e a classe `preenchimento` (40px) na linha. Todos os intervalos continuam visíveis, com ticks 40px afastados.
- **Motivo:** reusa a meia altura que já existia para preenchimento; `reposicionarCamadas` e o CSS já tratam a classe.
- **Descartadas:** altura nova só para "---" — duplicaria regra; esconder intervalos vazios — a equipe pedagógica quer todos visíveis.
- **Arquivos afetados:** `revista/script.js`, `revista/regua.test.mjs`
- **Status:** ativa

### D-037 — Altura da habilidade acompanha o texto (2026-10-21)
- **Contexto:** a equipe pedagógica aceitou que a escala não seja 100% proporcional; linhas fixas em 80px deixavam habilidades de 1 linha com muito vazio. Sem `nowrap`, o texto já não trunca.
- **Decisão:** `.linha` e `.linha-conteudo` sem `height` fixo, com `min-height: var(--escala-linha-min)` (3.5rem = 24px de texto + 16px de respiro em cima e embaixo). Texto maior cresce a linha. `.linha-cor` passa a `align-self: stretch`.
- **Motivo:** `reposicionarCamadas` já mapeia barra, rótulos e cortes pela altura real de cada linha; nada mais mudou no JS.
- **Descartadas:** manter 80px — vazio desnecessário; altura por contagem de linhas no JS — o CSS resolve.
- **Arquivos afetados:** `revista/styles.css`
- **Status:** ativa

### D-038 — `demo-escala/` apagada; trabalho só em `revista/` (2026-10-21)
- **Contexto:** a demo só carregava os arquivos de `revista/`; o usuário pediu para trabalhar direto na revista real.
- **Decisão:** pasta `demo-escala/` removida (10 arquivos versionados, recuperáveis pelo git). Nenhuma outra referência fora do `state.md`.
- **Motivo:** pedido do usuário.
- **Descartadas:** manter a demo — duplicava caminho de conferência.
- **Arquivos afetados:** `demo-escala/`
- **Status:** ativa. Menções antigas a `demo-escala/` neste arquivo são histórico.

### D-039 — CSS da escala em recursos nativos: tokens `clamp()`, `cqi`, propriedades lógicas, `hover: hover` (2026-10-21)
- **Contexto:** a escala tinha 4 blocos `@media` redeclarando `--escala-*`, fontes por breakpoint, regras duplicadas e `--escala-gap-linha` morto. Plano em `~/.claude/plans/utilize-as-skills-dispon-veis-atomic-gem.md`.
- **Decisão:** passos 1–7 do plano feitos. Larguras (`--escala-padrao/valor/marcador/cor-width`) e fontes (`--escala-texto-size`, `--escala-numero-size`, `--escala-extremo-size`) viram `clamp()` no `:root`; `.escala-proficiencia` é `container: escala / inline-size` e paddings internos usam `cqi`; `inset-inline`/`padding-inline`/`aspect-ratio` no lugar de left/right e width+height; hover só em `@media (hover: hover)`; botão "Ver item" fica com 44px em qualquer largura. Corrige a regressão em que o número ignorava o breakpoint.
- **Motivo:** menos CSS, comportamento contínuo entre larguras, sem saltos nos breakpoints.
- **Descartadas:** `@container` para o botão "Ver item" — ele fica fora da escala (`left: 100%`), então depende do espaço da janela; o `@media (max-width: 1040px)` dele permanece. Remover `.tem-ver-mais`/`max-height` — o JS ainda liga a classe se uma palavra estourar a largura. Passo 8 (`color-mix` nos fundos e `cssDasCores` na API) — depende de aprovação para mexer na API.
- **Arquivos afetados:** `revista/styles.css`
- **Status:** ativa, sem commit. Falta rebuild da API para ver na revista real. `.hero-image` (fora da escala) estoura 9px em 320px.

### D-040 — Polimento da escala: tabular-nums, text-wrap, transições explícitas, easing (2026-10-21)
- **Contexto:** revisão `make-interfaces-feel-better` propôs 10 ajustes; o usuário aprovou 1, 2, 5 e 6.
- **Decisão:** `font-variant-numeric: tabular-nums` em `.proficiencia-valor`; `text-wrap: pretty` em `.linha-conteudo p` e `.escala-legenda`; `.descritor-btn`, `.descritor-btn-lateral` e `.nav-btn` com propriedades explícitas (sem `all`); token `--ease-out: cubic-bezier(0.16, 1, 0.3, 1)` nas transições da escala; fechar habilidade em 0.2s (`.tem-ver-mais.fechando`) e abrir em 0.3s. `prefers-reduced-motion` dos botões movido para o fim do arquivo.
- **Motivo:** o bloco antigo de reduced-motion vinha antes das regras base de `.nav-btn` e `.modal-close`, que o sobrescreviam (mesma especificidade): a transição não desligava.
- **Descartadas:** nenhuma.
- **Arquivos afetados:** `revista/styles.css`
- **Status:** ativa, sem commit.

### D-041 — Item da escala aceita PDF, PNG e JPG (2026-10-21)
- **Contexto:** o "Ver item" só aceitava PDF; pedido de aceitar também PNG, JPG e JPEG.
- **Decisão:** `ItemPdf` ganha `tipo?: "pdf"|"png"|"jpg"` (ausente = pdf); JPG e JPEG viram "jpg" (image/jpeg). Pacote guarda `arquivos/itens/<id>.<tipo>`; GET serve o mime guardado no GridFS; modal da revista usa iframe (pdf) ou img (imagem). Limite segue 5 MB.
- **Motivo:** campo opcional mantém itens e projetos antigos válidos, sem migração.
- **Descartadas:** renomear `ItemPdf` — toca contrato, API, editor e testes sem ganho; WebP — não pedido.
- **Arquivos afetados:** `contrato/schemas.ts` (+ cópias), `api/src/modules/itens/routes.ts`, `api/src/modules/imagens/{routes,service}.ts`, `api/src/modules/projetos/model.ts` (Mongoose descartava `tipo`), `api/src/modules/geracao/service.ts`, `editor/src/projetos/ano/EditorEscala.tsx` (mime pela extensão quando o navegador não informa), `editor/src/mocks/handlers.ts`, `revista/{script.js,escala.hbs,styles.css}`, `docs/contrato.md`
- **Status:** ativa (implementada; testes: API 140, editor 74, régua ok; conferência visual pendente)

### D-042 — Selos de corte soltos em slots, faixa com altura mínima (2026-10-21)
- **Contexto:** corte 500 perto do nível 503 gerava selo amarelo cobrindo o número vizinho; dois cortes na mesma faixa caíam no mesmo y.
- **Decisão:** `montarFaixasRegua` põe os n cortes soltos de uma faixa em k/(n+1) da altura (maior em cima) e devolve `cortesDentro` por faixa; `faixaHTML` marca `.tem-corte` + `--cortes:n`; CSS dá `--escala-linha-min: (n+1) × 1,75rem` (inclui faixa "---" de meia altura). Substitui a regra 25–75% da D-024.
- **Motivo:** a folga era fração da faixa, e selo + número exigem ~26px entre centros; com altura mínima por vão o selo nunca encosta. Usuário escolheu "um acima do outro" (não lado a lado).
- **Descartadas:** selo deslocado na horizontal — alargaria a coluna e a geometria das barras; clamp em px no `reposicionarCamadas` — não testável em Node e não resolve faixa de 40px.
- **Arquivos afetados:** `revista/script.js`, `revista/styles.css`, `revista/regua.test.mjs`
- **Status:** ativa. Medido no navegador com o 2º EF real (500/503, 400/446): folga 21px em 1440px e 34px em 420px; 502+500 na mesma faixa: 6px entre selos. API reconstruída. Sem commit.

### D-043 — Título do modal do item mostra as duas âncoras (2026-10-21)
- **Contexto:** o modal dizia "Imagem do item — nível 556" mesmo com a habilidade ocupando 556 a 616; o usuário quer os dois valores.
- **Decisão:** `rotuloNiveis(inicio, fim)` (exportada, testada): "níveis 556 a 616", ou "nível 300" quando fim = início ou ausente. O botão "Ver item" ganha `data-nivel-fim` (= `topo` da faixa, que é o número de fim destacado no hover; na habilidade mais alta é o máximo da escala) e `abrirModal(nivel, fim, …)` monta título, `alt` e `title` do iframe; `aria-label` do botão vira "Ver item, níveis X a Y".
- **Motivo:** `topo` já é o fim da habilidade em `montarFaixasRegua`; sem dado novo no contrato.
- **Descartadas:** ler o fim do DOM (número destacado) — falha na habilidade mais alta, cujo fim (máximo) fica fora da régua.
- **Arquivos afetados:** `revista/script.js`, `revista/regua.test.mjs`
- **Status:** ativa. Medido no navegador (556 → "níveis 556 a 616", 782 → "níveis 782 a 1000"). API reconstruída. Sem commit; `styles.css` ainda tem a legenda centralizada e as edições manuais do usuário.

### D-044 — Habilidade que cruza um corte usa a cor do padrão da âncora maior (2026-10-23)
- **Contexto:** linha 390→446 (cruza o corte 400) acendia a cor do P02 (padrão da âncora menor); o usuário quer a cor do padrão mais alto.
- **Decisão:** em `montarFaixasRegua`, a linha com conteúdo recebe o padrão do `topo` (âncora maior). O `topo` é limite aberto: padrão = o mais alto cujo corte de início é `< topo`.
- **Motivo:** `topo` já é a âncora maior (D-043); um topo exatamente no corte (350→400) é só o início da próxima linha, então não sobe de padrão.
- **Descartadas:** topo inclusivo — pintaria de P03 toda linha logo abaixo de uma linha que começa no corte.
- **Arquivos afetados:** `revista/script.js`, `revista/regua.test.mjs`
- **Status:** ativa. Teste da régua ok; conferência visual pendente. Sem commit. Na linha mais alta o topo é o máximo da escala (P04 se o máximo passa do corte do P04).

## Perguntas em aberto
- [x] Propostas 1, 2, 5, 6 da revisão `make-interfaces-feel-better` aplicadas (D-040). Pendentes: 3 (`:active` do botão), 4 (feedback de toque), 7–10 — depende de: usuário
- [ ] Alternativa de exibição (régua proporcional ou lista por padrão) — só se a equipe pedagógica quiser; recomendação foi manter a régua.
- [ ] Modo de execução do plano: subagentes ou nativo? — depende de: usuário
- [ ] `skills[]` → "relacionadas" vs "correspondente" na planilha: heurística pelo "(" serve à impressão? — depende de: equipe de impressão
- [ ] Levar a opção 1 ajustada (D-032) para `revista/`? — depende de: usuário ver `demo-escala/opcao-1.html`
- [x] Cortes do 5º ano corretos? — confirmados pelo usuário

## Sessões
### 2026-10-07
- PDF base trocado para SAEGO_2025_RE_Alfa_2EF_5EF Web.pdf; plano aprovado.
- Script reescrito em Python; 84 descritores extraídos; 4 testes OK.
- Etapa livre implementada (D-007) em contrato, API, editor e revista; todas as suítes verdes.
- Novo projeto oferece todas as etapas (ETAPAS: 1º–9º EF, 1ª–3ª EM), padrão continua 5ef/9ef/3em.
- Diálogo "+ Ano" aprovado pelo usuário como está (atalhos padrão + "Outra etapa").
- Cortes do 5º ano confirmados; commit da etapa livre.

### 2026-10-07 (sessão 2)
- Plano aprovado: disciplinas + Importar PDF (D-008, D-009, D-010).
- Passos 1–2 + geração concluídos (API 98 testes verdes).
- Passos 3–4 concluídos (editor 51 testes verdes).
- Abas reorganizadas em dois níveis (D-013), conferido em desktop e 390px.
- Banco limpo: 4 projetos antigos (1 ativo `teste`, 3 na lixeira) e 2 imagens GridFS apagados com confirmação do usuário.
- Bug: "Erro 413" ao importar PDF de 11,7 MB. Causa: nginx do editor com client_max_body_size 6m. Correção: location /api/extracao com 51m e timeout 90s; 413 sem JSON vira mensagem legível no client.
- Preview passa a abrir o caderno da aba (D-014).
- Bug: "Não foi possível verificar a sessão" ao abrir pelo IP da rede (http://192.168.5.39:8080). Causa: crypto.randomUUID só existe em contexto seguro (HTTPS/localhost); sessaoEdicao() lançava antes do fetch. Correção: fallback com getRandomValues + teste. Aviso de CSP 'eval' era a sonda do zod: z.config({jitless}) movido para src/zodConfig.ts, importado primeiro.
- Copiar (não salvos) pela rede em http: navigator.clipboard não existe fora de contexto seguro; copiarTexto() cai em execCommand("copy") e o botão mostra "Copiado"/erro. Teste em projetos.test.tsx.
- Bug: "crypto.randomUUID is not a function" ao abrir ano/escala pelo IP. Causa: outros 5 usos de randomUUID (AbaPagina, EditorEscala, ListaTextos, mocks). Correção: novoId() único em src/lib/utils.ts + regra ESLint no-restricted-properties proibindo crypto.randomUUID.

### 2026-10-08
- README.md criado na raiz (conceitos, arquitetura, Docker, dev sem Docker, fluxo, contrato, extrator, testes). Comandos de teste conferidos: régua OK, extrator OK.
- Pendência: CLAUDE.md do projeto descreve só o protótipo escala.html (desatualizado).

### 2026-10-13
- Plano aprovado: 6 correções (D-015 a D-018); D-002 e D-006 substituídas.
- Passos 1–2 concluídos. Extrator: habilidade sem ponto final antes de outra na mesma faixa seria fundida (não ocorre no PDF atual); "–." vira "---".
- Passos 3–5 concluídos; bug achado: linhaSchema do Mongoose descartava campos novos (corrigido). Todas as suítes verdes.
- Bug: PDF LP recusado (cortes 9ef). Causa: cortes em negrito na coluna dos ticks. Correção D-019; LP 5º EF corrigido para 125/175/225.
- D-020: Alfabetização removida; 3 projetos Alfa apagados do Mongo (confirmado pelo usuário).
- Bug: PDF LP recusado (skills > 500). Causa: BNCC linha a linha + coluna fixa. Correção D-021.

### 2026-10-13 17:15 (polish)
- Plano de polish aprovado (5 itens, D-022).
- Polish aplicado e verificado (mocks, 1440px e celular); 58 testes verdes.

### 2026-10-15
- Acesso pela rede local: editor já publica em 0.0.0.0:8080; cookie secure "auto" funciona em http; falta liberar a 8080 no ufw (ativo).
- Bug: preview quebrava via IP (CSP do helmet com upgrade-insecure-requests forçava https). Correção: diretiva desligada em api/src/app.ts (D-023).
- Pergunta: stack para reconstruir o app. Resposta: não reescrever; candidatos ranqueados = monorepo com pacote de contrato, API tipada ponta a ponta (Hono/ts-rest), revista em Astro. Nada decidido.
- Restrição do usuário: prefere Python a TypeScript na reconstrução. Proposta: Django + Django Ninja + HTMX + PostgreSQL (alternativa: FastAPI + Beanie mantendo o editor React). Aguardando escolha.
- Escolhido: reconstrução em Django no modo mentor (usuário escreve o código). Projeto novo em ~/dev/revista-django; progresso em ~/dev/revista-django/JORNADA.md. Concorrência: trava com expiração + versão otimista (D-002 da jornada).

### 2026-10-16 10:00
- Bug: régua com linhas vazias quando o corte não coincide com um nível. Causa: faixas quebradas por padrão em montarFaixasRegua. Correção: D-024 (teste ok, navegador ok).
- Faixa sem habilidade aparece vazia em vez de "---" (D-025).
- Bug: traço solto entre 325 e 300 (5º EF). Causa: duas habilidades no mesmo nível; a primeira faixa ficava sem número, mas desenhava o tick. Correção: `mesmoNivel` em montarFaixasRegua + classe `.mesmo-nivel` sem tick (teste e navegador ok).

### 2026-10-16 11:00
- Ajustes do UX (~/Documentos) mapeados e portados: botão "Ver item" circular + hover com delays (D-026), "..." por CSS (D-027). Teste da régua ok; DOM conferido em 3 larguras.

### 2026-10-20 14:15
- 5 opções de UI da escala propostas (foco na linha, trilho com nós, zonas tingidas, rótulo com faixa, leitura em 2 linhas).
- Demo montada em `demo-escala/` (D-028) e conferida no Playwright em 1440 e 420px; servidor estático local usado só para isso e desligado.
- Aprendizados: Playwright bloqueia `file:`; a barra de navegação da demo, fixa embaixo, cobria as últimas linhas e foi para a lateral esquerda (≥1360px); prints do elemento `.escala-proficiencia` saem certos.

### 2026-10-20 (retomada)
- Sessão retomada; usuário pergunta como abrir as demos.
- Demo pausada; nova frente: preenchimento manual (passo, cores por projeto, planilhas .xlsx). 6 planilhas modelo lidas (2º EF com níveis irregulares; 3EM/5EF de 25 em 25).
- Decisões do usuário: linhas vazias no banco, 1 planilha por caderno e etapa + aba Escala, herdar cores copiando valores (D-029 a D-031). Plano de 9 tasks (writing-plans) aprovado.
- Achado: `main` está 10+ commits atrás de `redesign-shadcn`; a branch da implementação sai de `redesign-shadcn`.
- Execução por subagentes: 9 tasks + revisão final; decisões R1–R9 no relatório final da sessão. Correção relevante achada na revisão: texto inválido no campo numérico apagava o passo salvo (corrigido em 1b9f6f0).
- Bug: "interface não atualizou". Causa: containers reiniciados sem `--build`, com imagens de 2026-10-19 14:10. Correção: `docker compose up -d --build api editor` (imagens 2026-10-20 16:04); conferido: `planilhas.zip` responde 401 (rota existe), JS do editor tem "Intervalo mínimo"/"Cores dos padrões"/"Exportar planilhas", exceljs 4.4.0 na imagem.
- Ajuste pedido: botão "Gerar linhas vazias" só aparece com inteiro > 0 no campo (contagem usa o valor digitado); com passo salvo e grade completa, o botão dá lugar a "Intervalo mínimo já definido" (substitui "Nenhuma linha a criar"). Testes: ano.test.tsx 20/20, editor 71, typecheck e lint ok; container do editor reconstruído. Sem commit.
- Ajuste pedido: rótulos "Padrão 0X" da régua espremidos nas faixas estreitas (ex.: Padrão 01). `revista/styles.css` `.padrao-label`: nome `clamp(0.75rem, 0.62rem + 0.5vw, 0.9375rem)` (antes `--escala-texto-size`, até 1.1rem), `small` 0.75rem/1rem, padding-block 0.125rem, line-height do nome 1.25. Conferência visual pendente. Sem commit.
- Ajuste pedido: dica "Quem alcança uma habilidade..." virou callout (`.escala-legenda` em `revista/styles.css` + ícone de seta e `<strong>` em `revista/escala.hbs`): fundo branco, borda cinza, barra amarela `--color-primary` à esquerda, raio 0.5rem. Texto inalterado. Conferência visual pendente. Sem commit.
- Ajuste pedido: cor da linha que cruza um corte = padrão da âncora maior (D-044). `montarFaixasRegua` + 2 asserts; sem commit.
