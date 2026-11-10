# state.md — revista-express

## Estado atual
<!-- sobrescrever a cada atualização -->
Fase 3 do F2 (K-028) aberta: worktree `/home/otavio.peres/dev/revista-express-f2-f3`, branch `feat/f2-f3` saída da `integ/f2-gerado` (`93c28f5`), com a `main` mergeada (PRs #8 a #11: abrir ano D-246, docs D-233/D-234 da main, kanban D-253). Funcionando: tudo da fase 2 (F2 gerado, páginas separadas, zip) + primeiro ano vazio + kanban. Quebrado/pendente: specs E2E `impacto`, `impresso`, `painel` e `revista-textos` vermelhos até a fase 3 (pendência `infografico`); fases 4 e 5; S17/S18. Tarefas no `kanban.md`.

## Próxima ação
<!-- sobrescrever: UMA ação concreta -->
Rodar a suíte Django na stack `-p f2-f3` para provar o merge da `main`; depois, planejar a T1 da fase 3 (D-252).

## Plano
<!-- plano completo: plans/revista-express-django.md -->
Ver `kanban.md` (skill `kanban`; S01–S18 e fases do F2 migrados para cards em 10/11, D-253).

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

### ~~D-045 — Herança viva entre templates/projetos no redesenho Django + PostgreSQL (2026-10-26)
- **Contexto:** o usuário avalia refazer a API em Django + PostgreSQL por causa de herança entre projetos, templates de escala por parceiro, perfis/auth fortes e auditoria de texto para a equipe do impresso. Faltava definir se o filho acompanha o pai.
- **Decisão:** herança **viva**: mudou algo no template (ou projeto pai) usado por X, X reflete a mudança. Resolução na leitura (sem copiar nem propagar escritas); o filho guarda só o que sobrescreveu.
- **Motivo:** pedido do usuário; evita revista de um parceiro divergir do template sem aviso.
- **Descartadas:** cópia na criação com rastreio de origem — o filho não acompanharia o pai (o D-031 já fazia isso para cores, mas aqui não serve).
- **Arquivos afetados:** nenhum ainda (só desenho). Futuro: modelos Django `TemplateEscala`, `Projeto`, `Descritor`, `LinhaEscala`.
- **Status:** ~~substituída por D-051~~. Em aberto (já sem efeito): o que vale quando X sobrescreveu o campo que o pai mudou (padrão proposto: sobrescrita local vence e a interface avisa "pai mudou").

### D-046 — Ano (edição) é dimensão do modelo, com histórico (2026-10-27)
- **Contexto:** o sistema será reutilizado todo ano; o trabalho atual é 2026.
- **Decisão:** guardar dados por ano e manter o histórico. Matriz, cortes e etapas/CC avaliadas podem mudar de um ano para outro.
- **Motivo:** pedido do usuário; tudo pode mudar entre anos.
- **Descartadas:** só o ano corrente, sobrescrevendo — perde histórico.
- **Arquivos afetados:** nenhum ainda (desenho).
- **Status:** ativa.

### D-047 — Parceiro tem no máximo um projeto; cidades são parceiros independentes (2026-10-27)
- **Contexto:** a planilha mistura UFs e municípios (ex.: SC e JOINVILLE).
- **Decisão:** parceiro ↔ projeto é 1:1 (no máximo um). Município é parceiro próprio, sem vínculo com a UF (matriz e cortes independentes).
- **Motivo:** regra de negócio informada pelo usuário.
- **Descartadas:** hierarquia UF → município — não existe no negócio.
- **Arquivos afetados:** nenhum ainda.
- **Status:** ativa.

### D-048 — Quatro matrizes independentes: comunitária, CE, ES, JOINVILLE (2026-10-27)
- **Contexto:** a maioria dos parceiros usa a mesma matriz (base SAEGO); 3 exceções.
- **Decisão:** cada exceção tem matriz própria e completa, sem relação com a comunitária. Projeto não edita conteúdo (habilidade, descritor, tarefa); só referencia uma matriz.
- **Motivo:** como o impresso já trabalha (4 fontes de dados para todos os parceiros).
- **Descartadas:** exceção como comunitária + sobrescritas (herança) — usuário confirmou que não há relação.
- **Arquivos afetados:** nenhum ainda.
- **Status:** ativa. Efeito na D-045: sem sobrescrita por projeto, a regra de conflito pai × filho deixa de existir (a confirmar com o usuário).

### D-049 — Cortes cadastrados no sistema; grupos calculados; planilha só exportada (2026-10-27)
- **Contexto:** hoje a pedagógica escreve a planilha de cortes à mão para o impresso; ela tem erros de grupo (9EF-MT SE deveria ser grupo 6 e SALVADOR 7; 5EF-MT SALVADOR deveria ser 6).
- **Decisão:** UI própria para preencher cortes por parceiro × etapa × CC, antes mesmo de existir projeto. O sistema numera os grupos (cortes iguais = mesmo grupo); o usuário não informa grupo. O sistema é a fonte da verdade e gera a planilha na mesma estrutura (abas ETAPA - CC) para o impresso. Não há importação dessa planilha.
- **Motivo:** inverter o fluxo: a pedagógica alimenta o sistema, o sistema escreve as planilhas do impresso; grupo digitado à mão gera erro.
- **Descartadas:** grupo como cadastro manual (tabela de grupos das anotações) — gera os erros vistos; importar a planilha — o sistema passa a ser a origem.
- **Arquivos afetados:** nenhum ainda.
- **Status:** ativa.

### D-050 — Quantidade de cortes variável; padrões = cortes + 1 (2026-10-27)
- **Contexto:** 2EF-LP SE tem só 2 cortes (725, 800), gerando 3 padrões; não é erro.
- **Decisão:** aceitar menos de 3 cortes por parceiro × etapa × CC; a única consequência é ter menos padrões na escala.
- **Motivo:** o parceiro decide; não assumir que só o SE fará isso.
- **Descartadas:** fixar 3 cortes.
- **Arquivos afetados:** nenhum ainda.
- **Status:** ativa. Mínimo e máximo de cortes em aberto.

### D-051 — Projeto só referencia a matriz; conteúdo se ajusta na matriz (substitui D-045) (2026-10-27)
- **Contexto:** D-048 tirou a edição de conteúdo dos projetos.
- **Decisão:** não há herança de conteúdo entre projetos: o projeto aponta para uma das matrizes e todo ajuste de habilidade/descritor/tarefa é feito na matriz. A regra de conflito pai × filho da D-045 deixa de existir.
- **Motivo:** confirmado pelo usuário.
- **Descartadas:** herança viva com sobrescrita por projeto (D-045).
- **Arquivos afetados:** nenhum ainda.
- **Status:** ativa.

### D-052 — Projeto tem tabela própria: nome, textos da revista, intervalo mínimo (2026-10-27)
- **Contexto:** saber se "projeto" ainda é entidade, já que cortes e conteúdo vivem fora dele.
- **Decisão:** tabela Projeto com nome, textos da revista (editados por projeto) e sobrescrita do intervalo mínimo; lista completa de campos ainda incompleta (o usuário não lembra de todos).
- **Motivo:** os textos variam por projeto.
- **Descartadas:** projeto = só parceiro + ano + matriz.
- **Arquivos afetados:** nenhum ainda.
- **Status:** ativa.

### D-053 — Intervalo mínimo: padrão na matriz, sobrescrita por projeto × etapa × CC (2026-10-27)
- **Contexto:** o extrator (`scripts/extrair_descritores.py`) não distingue linha vazia comum de linha vazia vinda do intervalo mínimo.
- **Decisão:** a matriz guarda o intervalo mínimo de cada etapa × CC (informado na criação, a partir do PDF/XLSX que já tem as linhas vazias). O projeto pode sobrescrever em uma etapa e/ou CC; as linhas vazias são recalculadas.
- **Motivo:** permitir ajuste local sem mexer na matriz.
- **Descartadas:** só na matriz — sem ajuste local; só no projeto — repetiria o mesmo valor em todos.
- **Arquivos afetados:** futuro: modelos Django; extrator.
- **Status:** ativa.

### D-054 — Ano novo nasce clonando o ano anterior (2026-10-27)
- **Contexto:** D-046 (dados por ano).
- **Decisão:** abrir um ano copia o anterior inteiro (matrizes, cortes, participação); edita-se só o que mudou.
- **Motivo:** a maior parte se repete.
- **Descartadas:** começar vazio — retrabalho.
- **Arquivos afetados:** nenhum ainda.
- **Status:** ativa só para cadastros; cortes e participação ~~substituídos por D-119~~

### D-055 — Limites e validação dos cortes (2026-10-27)
- **Contexto:** UI de cortes (D-049, D-050).
- **Decisão:** 1 a 4 cortes (2 a 5 padrões); inteiros estritamente crescentes; faixa 0–1000 no 2EF e 0–500 nas demais etapas.
- **Motivo:** regra informada pelo usuário.
- **Descartadas:** fixar 3 cortes.
- **Arquivos afetados:** futuro: UI de cortes; escala precisa de cor/estilo para o 5º padrão (hoje há 4).
- **Status:** ativa.

### D-056 — Numeração dos grupos (2026-10-27)
- **Contexto:** grupos calculados (D-049).
- **Decisão:** por aba (etapa × CC), ordenar as listas de cortes distintas comparando corte a corte (lexicográfico) e numerar a partir de 1. A ordem dos parceiros dentro do grupo não importa.
- **Motivo:** reproduz a planilha atual (com as correções do usuário).
- **Descartadas:** número manual.
- **Arquivos afetados:** futuro: gerador da planilha de cortes.
- **Status:** ativa.

### D-057 — Matriz é cadastro por ano; parceiro × ano aponta a matriz (2026-10-27)
- **Contexto:** pode surgir 5ª matriz ou um parceiro trocar de matriz entre anos.
- **Decisão:** matrizes são cadastradas por ano (não lista fixa de 4); a matriz usada é dado de parceiro × ano.
- **Motivo:** confirmado pelo usuário (opção a).
- **Descartadas:** 4 matrizes fixas.
- **Arquivos afetados:** nenhum ainda.
- **Status:** ativa.

### D-058 — Regra da D-044 vale para corte em qualquer valor (2026-10-27)
- **Contexto:** cortes fora do passo (ex.: SALVADOR 5EF-LP 175, 210, 228) caem dentro de um intervalo da régua.
- **Decisão:** tarefa cujo intervalo cruza um corte usa a cor do padrão da âncora maior, qualquer que seja o corte.
- **Motivo:** confirmado pelo usuário.
- **Descartadas:** partir a linha em duas.
- **Arquivos afetados:** futuro: cálculo de padrão na renderização.
- **Status:** ativa.

### D-059 — Importação da matriz descarta os cortes do PDF (2026-10-27)
- **Contexto:** o PDF do SAEGO traz os cortes de GO; o extrator exige 3 cortes e já distribui as tarefas por padrão.
- **Decisão:** a matriz guarda só o intervalo de cada tarefa; os cortes impressos no PDF são descartados. Padrão é calculado na renderização com os cortes do parceiro. Importação principal: PDF; XLSX no mesmo layout da exportação (uma planilha por etapa × CC) fica como alternativa.
- **Motivo:** os cortes são do parceiro, não da matriz.
- **Descartadas:** guardar os cortes do PDF como referência.
- **Arquivos afetados:** futuro: `scripts/extrair_descritores.py` (tirar a exigência de 3 cortes e a distribuição por padrão).
- **Status:** ativa.

### D-060 — Cores dos padrões: global com sobrescrita por projeto (2026-10-27)
- **Contexto:** D-031 copiava as cores por projeto.
- **Decisão:** cores atuais viram o padrão global; o projeto só define cor quando diverge (sobrescrita).
- **Motivo:** a maioria dos projetos não muda as cores.
- **Descartadas:** cor obrigatória em cada projeto.
- **Arquivos afetados:** futuro: modelos Django; diálogo de cores do editor.
- **Status:** ativa. Em aberto: existe um nível intermediário (na definição de cortes/etapa)? Cor do 5º padrão.

### D-061 — Projetos criados em cascata a partir do preenchimento dos cortes (2026-10-27)
- **Contexto:** os cortes são preenchidos antes dos projetos (D-049).
- **Decisão:** preencher cortes de um parceiro no ano gera o projeto dele automaticamente; associação de matriz e textos por parceiro numa página própria (o usuário propôs "Templates").
- **Motivo:** evitar criar projeto a projeto.
- **Descartadas:** criação manual de cada projeto.
- **Arquivos afetados:** nenhum ainda.
- **Status:** ativa.

### D-062 — Textos da revista: modelo + sobrescrita por bloco com aviso, sem fusão automática (2026-10-27)
- **Contexto:** usuário queria um "diff tipo git" entre texto-modelo e texto do projeto.
- **Decisão:** texto-modelo dividido em blocos; projeto herda ou sobrescreve o bloco inteiro e guarda a versão do modelo usada (`versao_base`). Se o modelo mudar naquele bloco, o projeto mostra "modelo mudou desde sua edição" com o diff; o usuário resolve.
- **Motivo:** fusão automática de texto corrido pode gerar frase quebrada sem ninguém ver, e isso vai impresso.
- **Descartadas:** fusão de três vias automática (estilo git) — risco e custo; sem aviso — projeto ficaria defasado sem saber.
- **Arquivos afetados:** nenhum ainda.
- **Status:** ~~substituída por D-099~~

### D-063 — Matriz e texto-modelo são escolhas separadas por parceiro × ano (2026-10-27)
- **Contexto:** proposta de Template = par matriz + texto-modelo.
- **Decisão:** o parceiro escolhe a matriz e o texto-modelo separadamente.
- **Motivo:** flexibilidade; na empresa as regras mudam rápido.
- **Descartadas:** Template como par fixo — engessa.
- **Arquivos afetados:** nenhum ainda.
- **Status:** ativa para a matriz; parte do texto-modelo ~~substituída por D-098/D-125~~

### D-064 — Cores em 2 níveis; padrões usam as cores 1..n; 5º padrão #FFF provisório (2026-10-27)
- **Contexto:** D-060 deixou em aberto nível intermediário e cor do 5º padrão.
- **Decisão:** global → projeto (sobrescrita). Com n padrões, usam-se as cores 1..n da paleta. Cor do 5º padrão: #FFF até definirem outra.
- **Motivo:** confirmado pelo usuário.
- **Descartadas:** nível intermediário na definição de cortes.
- **Arquivos afetados:** futuro: paleta global, CSS da escala.
- **Status:** ativa.

### D-065 — Ciclo de vida do projeto criado em cascata (2026-10-27)
- **Contexto:** projeto nasce do preenchimento de cortes (D-061).
- **Decisão:** parceiro retirado de uma etapa × CC → a etapa some da revista. Retirado de todas → projeto arquivado. Nome inicial = valor da coluna Parceiro + " - NOME DO PROJETO" (string literal, ex.: "GO - NOME DO PROJETO"); o usuário edita o nome depois de criado.
- **Motivo:** forçar o usuário a revisar o nome real do projeto.
- **Descartadas:** apagar o projeto; pedir o nome antes de criar.
- **Arquivos afetados:** nenhum ainda.
- **Status:** ativa.

### D-066 — Matriz editável após o envio, com relatório "o que mudou desde o envio" (2026-10-27)
- **Contexto:** mudar a matriz comunitária afeta ~25 revistas; o impresso precisa saber.
- **Decisão:** a matriz continua editável; toda mudança fica no histórico e o sistema lista o que mudou desde o envio ao impresso.
- **Motivo:** acordado com o time do impresso.
- **Descartadas:** travar a matriz após o envio; não registrar nada.
- **Arquivos afetados:** futuro: histórico (django-simple-history) + marco de envio.
- **Status:** ativa.

### D-067 — Blocos de texto são dados, não estrutura fixa (2026-10-27)
- **Contexto:** o usuário não sabe a lista de blocos e exige flexibilidade extrema.
- **Decisão:** blocos do texto-modelo são cadastráveis (criar, remover, reordenar) em vez de campos fixos no modelo de dados.
- **Motivo:** mudanças vão surgir no meio do caminho.
- **Descartadas:** uma coluna por seção da revista — engessa.
- **Arquivos afetados:** nenhum ainda.
- **Status:** ~~substituída por D-098~~

### D-068 — Projeto arquivado não volta; parceiro readicionado gera projeto novo (2026-10-27)
- **Contexto:** ciclo de vida da D-065.
- **Decisão:** se o parceiro volta a ter cortes no mesmo ano, nasce outro projeto ("PARCEIRO - NOME DO PROJETO"); o arquivado fica como está.
- **Motivo:** escolha do usuário (opção b).
- **Descartadas:** desarquivar o mesmo projeto.
- **Arquivos afetados:** nenhum ainda.
- **Status:** ativa.

### ~~D-069 — Envio ao impresso = download pelo perfil Impresso; mudança posterior marca o projeto (complementa D-066) (2026-10-27)
- **Contexto:** hoje a pedagógica comenta o PDF do impresso e espera reexportação. No sistema, ela edita e valida no preview em tempo real; só depois o impresso recebe as planilhas prontas.
- **Decisão:** perfil dedicado ao impresso baixa as planilhas. A data/hora do download é o marco; qualquer mudança posterior marca o projeto como "mudou" para todos os perfis. Não há relatório separado.
- **Motivo:** fluxo acordado com o impresso; menos correções chegando lá.
- **Descartadas:** relatório formal de mudanças (página/planilha/PDF) — não pedido.
- **Arquivos afetados:** futuro: perfil Impresso, registro de download, histórico.
- **Status:** ~~substituída por D-072~~.

### D-070 — Textos-modelo com marcadores preenchidos pelo projeto (2026-10-27)
- **Contexto:** partes variáveis dos textos (nome do projeto etc.).
- **Decisão:** texto-modelo usa marcadores (ex.: {NOME DO PROJETO}) que o sistema preenche com os dados do projeto.
- **Motivo:** reduz sobrescritas de bloco (D-062).
- **Descartadas:** texto fixo editado à mão em cada projeto.
- **Arquivos afetados:** nenhum ainda.
- **Status:** ~~substituída por D-100/D-125~~

### D-071 — Matriz é editada no sistema; reimportar substitui tudo (2026-10-27)
- **Contexto:** correções na matriz depois da importação.
- **Decisão:** edição no sistema (fonte da verdade). Reimportar o PDF/XLSX substitui a matriz inteira, com confirmação forte.
- **Motivo:** coerente com D-049; evita casar tarefa a tarefa entre importações.
- **Descartadas:** reimportação com aplicação só das diferenças.
- **Arquivos afetados:** nenhum ainda.
- **Status:** ativa.

### D-072 — Impresso vê só o que mudou e confirma com "Revista Impressa Atualizada" (substitui D-069) (2026-10-27)
- **Contexto:** o impresso não quer baixar de novo; quer saber exatamente o que mudar no InDesign.
- **Decisão:** sem segundo download e sem marco por data de download. Cada projeto mostra ao impresso o que mudou (texto antigo → novo); o botão "Revista Impressa Atualizada" zera as mudanças daquele projeto. Mudança só nos cortes do PE marca só o PE.
- **Motivo:** pedido do time de impresso.
- **Descartadas:** marco pela data/hora do download (D-069); reenviar planilhas.
- **Arquivos afetados:** nenhum ainda.
- **Status:** ativa.

### D-073 — Quatro perfis (2026-10-27)
- **Contexto:** lista de perfis estava em aberto.
- **Decisão:** admin; Equipe Pedagógica; Equipe de Impresso; Equipe de Mídias Digitais (mesmas permissões da Pedagógica).
- **Motivo:** informado pelo usuário.
- **Descartadas:** 2 perfis atuais (admin/editor).
- **Arquivos afetados:** futuro: auth/permissões.
- **Status:** ativa. Matriz papel × ação detalhada em aberto.

### D-074 — Botão "Validado" (pedagógica) libera "Revista Impressa Atualizada" (impresso) (2026-10-27)
- **Contexto:** o impresso não deve agir sobre dados ainda não revisados.
- **Decisão:** cada projeto tem o botão "Validado" para a pedagógica. Só depois dele o impresso pode clicar em "Revista Impressa Atualizada" (antes disso, só vê). Qualquer alteração após "Validado" exige validar de novo.
- **Motivo:** fluxo informado pelo usuário.
- **Descartadas:** impresso atualizar a qualquer momento.
- **Arquivos afetados:** nenhum ainda.
- **Status:** ativa.

### D-075 — Marcadores iniciais: {PARCEIRO}, {NOME DO PROJETO}, {ANO} (2026-10-27)
- **Contexto:** D-070.
- **Decisão:** só esses 3 por enquanto; lista aberta para crescer.
- **Motivo:** outros vão surgir no projeto.
- **Descartadas:** lista fechada.
- **Arquivos afetados:** nenhum ainda.
- **Status:** ~~substituída por D-100~~

### D-076 — Aviso de impacto ao editar matriz; 2026 começa do zero (2026-10-27)
- **Contexto:** mudança na matriz comunitária afeta ~25 revistas; dados atuais no Mongo.
- **Decisão:** antes de salvar uma edição de matriz, o sistema mostra quantos projetos ela afeta. Sem migração do Mongo: 2026 começa importando os 3 PDFs do SAEGO como matriz comunitária e preenchendo os cortes pela UI nova.
- **Motivo:** escolhas do usuário (4a, 5a).
- **Descartadas:** salvar sem aviso; script de migração do Mongo.
- **Arquivos afetados:** nenhum ainda.
- **Status:** ativa.

### D-077 — "O que mudou" = diferença entre fotos da revista montada (2026-10-27)
- **Contexto:** o texto final muda por vários caminhos (matriz, texto-modelo, marcador, corte que troca o padrão); rastrear por tabela é complexo.
- **Decisão:** ao clicar em "Revista Impressa Atualizada", guardar uma foto (JSON) da revista resolvida do projeto. O impresso vê a diferença entre essa foto e a revista atual. A comparação é sempre contra o último clique do impresso, independentemente de quantas validações houve no meio. Primeira vez: impresso baixa as planilhas e clica, criando a primeira foto.
- **Motivo:** pega qualquer caminho de mudança; garante que nenhum ajuste passe.
- **Descartadas:** reconstruir as mudanças pelo histórico de cada tabela.
- **Arquivos afetados:** nenhum ainda.
- **Status:** ativa.

### D-078 — Mudança compartilhada derruba "Validado" dos afetados, com validação em lote (2026-10-27)
- **Contexto:** correção na matriz comunitária afeta ~25 projetos (D-074).
- **Decisão:** todos os projetos afetados perdem o "Validado"; há botão "validar todos os afetados". O impresso pode baixar as planilhas a qualquer momento (o normal é usar a tela de mudanças).
- **Motivo:** escolha do usuário (opção a).
- **Descartadas:** validar um por um; mudança de matriz não derrubar a validação.
- **Arquivos afetados:** nenhum ainda.
- **Status:** ativa.

### D-079 — Permissões fora dos projetos (2026-10-27)
- **Contexto:** D-073.
- **Decisão:** Pedagógica e Mídias Digitais: abrir ano novo, criar/importar matriz, preencher cortes, editar textos-modelo e paleta global. Admin: gerenciar usuários.
- **Motivo:** informado pelo usuário.
- **Descartadas:** concentrar essas ações no admin.
- **Arquivos afetados:** futuro: permissões Django.
- **Status:** ativa.

### D-080 — Bloqueio de edição (quem abriu primeiro edita) para matriz e projeto (2026-10-27)
- **Contexto:** a matriz comunitária é compartilhada; dois usuários podem editar ao mesmo tempo.
- **Decisão:** bloqueio: o primeiro edita, o outro só vê.
- **Motivo:** evita colisão sem rastrear edições simultâneas.
- **Descartadas:** quem salva por último vence; recusa por versão (controle otimista).
- **Arquivos afetados:** futuro: modelo de bloqueio (hoje `bloqueio` embutido no projeto, na `api/`).
- **Status:** ativa. Granularidade e expiração do bloqueio em aberto.

### D-081 — Granularidade e expiração do bloqueio de escrita (2026-10-27)
- **Contexto:** D-080 deixou granularidade e expiração em aberto.
- **Decisão:** bloqueio é só de escrita (todos continuam vendo). Matriz: trava por matriz × etapa × CC. Projeto: trava o projeto inteiro. Expira em 30 s sem renovação (hoje 2 min, `BLOQUEIO_TTL_MS`); a renovação do editor precisa rodar bem abaixo disso (ex.: a cada 10 s).
- **Motivo:** permitir trabalho paralelo em partes diferentes da mesma matriz; liberar rápido quem saiu.
- **Descartadas:** travar a matriz inteira; manter 2 min.
- **Arquivos afetados:** futuro: modelo de bloqueio; renovação no editor.
- **Status:** ativa.

### D-082 — Manter histórico por tabela (django-simple-history) para auditoria (2026-10-27)
- **Contexto:** a foto da revista (D-077) já cobre o impresso.
- **Decisão:** manter o histórico por modelo para responder quem mudou o quê e quando.
- **Motivo:** custo de uma linha por modelo.
- **Descartadas:** sem histórico por enquanto.
- **Arquivos afetados:** futuro: modelos Django.
- **Status:** ativa.

### D-083 — Admin tem as permissões da Pedagógica + gerenciar usuários (2026-10-27)
- **Contexto:** D-079.
- **Decisão:** admin é superconjunto.
- **Motivo:** escolha do usuário.
- **Descartadas:** admin só gerencia usuários.
- **Arquivos afetados:** futuro: permissões Django.
- **Status:** ativa.

### D-084 — Rascunho do diagrama ER (2026-10-27)
- **Contexto:** grill-me encerrado (D-046 a D-083); usuário pediu o rascunho do ER.
- **Decisão (proposta, a revisar):** `docs/modelo-er.md` com 18 tabelas. Escolhas do rascunho: cortes ligados a parceiro × ano (não ao projeto, que nasce depois); matriz e texto-modelo escolhidos no Projeto; `valores` dos cortes como array de inteiros; "Validado" = hash da revista resolvida guardado no clique (qualquer mudança, de qualquer origem, invalida sem sinal por tabela); bloqueio com dois alvos opcionais e CHECK de exatamente um; perfis como `Group` do Django.
- **Motivo:** menos tabelas e menos código de invalidação; a revista resolvida já é calculada para o preview e para a foto do impresso.
- **Descartadas:** tabela de grupos de corte (calculado); tabela de participação parceiro × etapa (deduzida dos cortes); flag `validado` derrubado por sinais em cada tabela.
- **Arquivos afetados:** `docs/modelo-er.md`.
- **Status:** proposta; os 3 pontos em aberto foram fechados em D-085 a D-087.

### D-085 — Ano novo não clona projetos; eles renascem pela cascata (2026-10-27)
- **Contexto:** D-054 clona o ano; faltava dizer se os projetos entram no clone.
- **Decisão:** projetos não são clonados. Os cortes clonados recriam os projetos em cascata com "PARCEIRO - NOME DO PROJETO" (D-065); nome, sobrescritas e cores do ano anterior não passam.
- **Motivo:** escolha do usuário; força revisar o projeto a cada ano.
- **Descartadas:** clonar projeto com nome, sobrescritas e cores.
- **Arquivos afetados:** `docs/modelo-er.md`.
- **Status:** ativa.

### D-086 — Etapa, ComponenteCurricular e CorPadrao são por ano (2026-10-27)
- **Contexto:** rascunho ER os deixava globais.
- **Decisão:** as três tabelas ganham `ano_id`; UNIQUE (ano, codigo) e (ano, padrao). Entram no clone do ano.
- **Motivo:** tudo pode mudar de um ano para outro (D-046).
- **Descartadas:** tabelas globais.
- **Arquivos afetados:** `docs/modelo-er.md`.
- **Status:** ativa.

### D-087 — Bloco sobrescrito desatualizado só avisa; não bloqueia o "Validado" (2026-10-27)
- **Contexto:** `ProjetoBloco.versao_base` < `BlocoTexto.versao` (D-062).
- **Decisão:** o projeto mostra o aviso e o bloco fica marcado até o usuário revisar; o "Validado" continua permitido.
- **Motivo:** escolha do usuário.
- **Descartadas:** impedir o "Validado".
- **Arquivos afetados:** `docs/modelo-er.md`.
- **Status:** ativa.

### D-088 — Escolha de matriz e texto-modelo mora em ParceiroAno (2026-10-27)
- **Contexto:** revisão do ER: no Projeto, a escolha não existe quando a cascata cria o projeto e some no clone do ano (D-085).
- **Decisão:** nova tabela ParceiroAno(parceiro, ano, matriz nula, texto_modelo nulo), UNIQUE (parceiro, ano). Corte e Projeto apontam para ela. Ela entra no clone do ano; "Validado" exige matriz e texto-modelo escolhidos.
- **Motivo:** a escolha é dado de parceiro × ano (D-057, D-063) e precisa sobreviver ao clone.
- **Descartadas:** matriz/texto-modelo no Projeto (rascunho D-084); default comunitária na cascata — escolheria pelo usuário.
- **Arquivos afetados:** `docs/modelo-er.md`, `docs/Modelo_ER_Revista.pdf`.
- **Status:** ativa para a matriz; `texto_modelo` ~~substituído por D-125~~; clone da escolha ~~substituído por D-106~~

### D-089 — Cliques de estado levam o hash da versão vista (2026-10-27)
- **Contexto:** revisão: o impresso via o diff de V1, a pedagógica validava V2, o clique gravava V2 e a mudança V1→V2 nunca chegava ao InDesign.
- **Decisão:** "Validado" e "Revista Impressa Atualizada" enviam o hash da revista exibida; o servidor recusa se a atual for outra. FotoRevista guarda o hash.
- **Motivo:** garantir que ninguém confirma o que não viu.
- **Descartadas:** gravar o estado do momento do clique.
- **Arquivos afetados:** `docs/modelo-er.md`.
- **Status:** ativa.

### D-090 — Coerência de ano por FK composta (2026-10-27)
- **Contexto:** revisão: FKs simples aceitam corte 2027 com etapa 2026 ou matriz 2026.
- **Decisão:** tabelas por ano ganham UNIQUE (id, ano); ParceiroAno, MatrizEtapaCC e Corte carregam ano_id e usam FKs compostas (RunSQL). Sobrescritas do projeto validam o ano no `clean()`.
- **Motivo:** o banco recusa mistura de anos (testado em PostgreSQL 17).
- **Descartadas:** só validação na aplicação — não cobre outros clientes.
- **Arquivos afetados:** `docs/modelo-er.md`.
- **Status:** ativa.

### D-091 — "Intervalo mínimo" é o passo; um campo só (substitui o campo da D-053) (2026-10-27)
- **Contexto:** o rascunho tinha `intervalo_minimo` e `passo` em MatrizEtapaCC; no editor atual o rótulo "Intervalo mínimo" é o campo `passo`.
- **Decisão:** um campo `passo` (NULL = sem linhas vazias). Sobrescrita em ProjetoPasso; a existência da linha diz "sobrescrevi" e `passo` NULL nela diz "sem linhas vazias, de propósito". A regra da D-053 (padrão na matriz + sobrescrita no projeto) continua.
- **Motivo:** dois campos para o mesmo conceito divergiriam.
- **Descartadas:** manter os dois.
- **Arquivos afetados:** `docs/modelo-er.md`. O PDF de estudo v2 (seção 8 e questão 10) ainda usa o conceito antigo.
- **Status:** ativa.

### D-092 — Blocos de texto tipados: texto, parágrafos ou imagem (2026-10-27)
- **Contexto:** a página atual tem `heroTitulo` (texto), `introParagrafos` (lista) e `heroImagem` (imagem); BlocoTexto só tinha texto.
- **Decisão:** BlocoTexto e ProjetoBloco têm `tipo` e colunas texto / paragrafos / imagem; CHECK deixa só a coluna do tipo preenchida.
- **Motivo:** cobrir o que a revista já tem.
- **Descartadas:** JSONB genérico — perde o CHECK por tipo.
- **Arquivos afetados:** `docs/modelo-er.md`.
- **Status:** ~~substituída por D-098~~

### D-093 — Regras de integridade da revisão (2026-10-27)
- **Contexto:** achados médios da revisão do ER.
- **Decisão:** "Validado" recusado se houver corte sem MatrizEtapaCC na matriz escolhida ou nome terminando em " - NOME DO PROJETO"; cascata de projetos num único serviço transacional; arquivar grava FotoRevista(motivo=arquivamento) e congela o projeto; trocar texto-modelo lista e descarta sobrescritas com confirmação; remover bloco com sobrescritas é PROTECT; Bloqueio guarda `sessao_edicao` (aba) e fica fora do histórico.
- **Motivo:** cada regra fecha um cenário de erro silencioso.
- **Descartadas:** resolver projeto arquivado com cortes vivos; CASCADE em bloco removido.
- **Arquivos afetados:** `docs/modelo-er.md`.
- **Status:** ativa.

### D-094 — Respostas da revisão: revert, herança de foto, reimportação (2026-10-27)
- **Contexto:** perguntas de negócio da revisão do ER.
- **Decisão:** desfazer uma mudança faz o "Validado" voltar (hash basta); projeto readicionado (D-068) herda a última FotoRevista(motivo=impresso) do arquivado; reimportar matriz recriando ids e perdendo auditoria por registro é aceito.
- **Motivo:** respostas do usuário.
- **Descartadas:** contador de revisão no lugar do hash.
- **Arquivos afetados:** `docs/modelo-er.md`.
- **Status:** ativa.

### D-095 — Revista = projeto × componente; nasce dos cortes (2026-10-29)
- **Contexto:** a revista tem dois fascículos (escalas e infográfico) e é separada por componente (LP, MAT).
- **Decisão:** o projeto continua sendo parceiro × ano (nome e variáveis ficam nele). Cada projeto gera uma revista por componente em que o parceiro tem cortes; cada revista traz os fascículos em ordem (F1, F2).
- **Motivo:** respostas 1a e 3a do grill-me de fascículos.
- **Descartadas:** projeto = parceiro × ano × componente; toda revista sempre com LP e MAT.
- **Arquivos afetados:** futuro: `docs/modelo-er.md` (tabela Revista).
- **Status:** ativa.

### D-096 — Fascículo é cadastro ordenado (2026-10-29)
- **Contexto:** hoje F1 e F2; pode surgir F3.
- **Decisão:** tabela de fascículos com ordem; fascículo novo entra sem mudar código.
- **Motivo:** resposta 2a.
- **Descartadas:** F1/F2 fixos no código.
- **Arquivos afetados:** futuro: `docs/modelo-er.md`.
- **Status:** ~~substituída por D-122~~

### D-097 — "Validado" e "Revista Impressa Atualizada" valem por revista (F1 + F2) (2026-10-29)
- **Contexto:** D-074 e D-089 tinham o projeto como unidade.
- **Decisão:** os dois cliques, o hash e a foto do impresso passam a ser por revista. Mudar uma variável do projeto derruba o "Validado" das duas revistas dele.
- **Motivo:** resposta 4a.
- **Descartadas:** por fascículo.
- **Arquivos afetados:** futuro: `docs/modelo-er.md` (FotoRevista, hash).
- **Status:** ativa. Complementa D-074/D-089 (unidade muda de projeto para revista).

### D-098 — Template de texto = documento Handlebars único por fascículo × componente (2026-10-29)
- **Contexto:** textos fora das escalas e do infográfico mudam por projeto; D-067/D-092 tratavam o texto como blocos tipados.
- **Decisão:** cada template é um documento só, por fascículo × componente (hoje 2 no F1 e 2 no F2: LP e MAT), por ano (clonado no ano novo). Versão inicial em `.hbs` no repositório, carregada no banco; depois a fonte é o banco e a edição é pela interface. Formatação: negrito, itálico, parágrafos, listas. Sem lógica (`if`/`each`): caso diferente vira outro template. Revista de LP só oferece templates de LP.
- **Motivo:** respostas 5a, 6, 7a, 9, 14a, 18a, 21a.
- **Descartadas:** blocos cadastráveis e tipados (D-067, D-092); template só no código; lógica no template.
- **Arquivos afetados:** futuro: `templates/*.hbs`, `docs/modelo-er.md`.
- **Status:** ativa. Substitui D-067 e D-092.

### D-099 — Projeto sobrescreve o texto inteiro do template; edição do template propaga com aviso (2026-10-29)
- **Contexto:** D-062 previa sobrescrita por bloco.
- **Decisão:** a revista usa o template; o projeto pode editar o texto para si (só ele muda). Editar o template muda todas as revistas que o usam, com aviso de quantas antes de salvar (como D-076) e queda do "Validado". Matriz é diferente: só muda na própria matriz e vale para todos.
- **Motivo:** respostas 6 e 8a.
- **Descartadas:** sobrescrita por bloco (D-062).
- **Arquivos afetados:** futuro: `docs/modelo-er.md`.
- **Status:** ativa. Substitui D-062. Em aberto: efeito da edição do template numa revista que já sobrescreveu.

### D-100 — Variáveis: lista fixa no código, valores por projeto, falta bloqueia "Validado" (2026-10-29)
- **Contexto:** D-075 tinha 3 marcadores com chaves simples e lista aberta.
- **Decisão:** lista fixa no código (parceiro, nome do projeto, adjetivo pátrio em 4 variáveis: masc./fem. × sing./plural…). Valores só no projeto, que renasce vazio a cada ano. Sintaxe Handlebars `{{variavel}}`. Variável usada sem valor: destaque vermelho no preview e "Validado" bloqueado.
- **Motivo:** respostas 10b, 11b, 12b, 13a.
- **Descartadas:** valores no parceiro (durariam entre anos); lista criada pela interface; uma variável com 4 formas.
- **Arquivos afetados:** futuro: código das variáveis, `docs/modelo-er.md`.
- **Status:** ativa. Substitui D-075.

### D-101 — Matriz continua por parceiro × ano; exceção nasce duplicando uma matriz (2026-10-29)
- **Contexto:** "matriz como template".
- **Decisão:** escolha de matriz fica em ParceiroAno (D-088), valendo para LP e MAT. Projeto que mudou no ano: duplicar uma matriz, ajustar a cópia e apontar o parceiro para ela (mais uma exceção à comunitária).
- **Motivo:** respostas 15b e 16a.
- **Descartadas:** matriz por revista; editar a matriz em uso.
- **Arquivos afetados:** futuro: ação "Duplicar matriz".
- **Status:** ativa.

### D-102 — Página "Templates" com abas, atribuição em lote, quem edita (2026-10-29)
- **Contexto:** onde ver, editar e atribuir templates e matrizes.
- **Decisão:** página "Templates" com abas Textos F1, Textos F2, Matrizes, Variáveis. Atribuição de template e matriz selecionando vários projetos/revistas de uma vez; nada atribuído automaticamente. Editam: Pedagógica, Mídias Digitais e admin.
- **Motivo:** respostas 17a, 24a, 25a.
- **Descartadas:** páginas separadas; atribuição um a um; só admin.
- **Arquivos afetados:** futuro: editor.
- **Status:** ativa.

### D-103 — F2 é o infográfico do svg-tour; vai ao impresso; entrega em zip por revista (2026-10-29)
- **Contexto:** código do F2 em `~/dev/svg-tour` (JS puro, sem build: `common/svg-tour.js`, `svg-tour-modal.js`; página `avaliacao-e-curriculo/` com SVG nomeado à mão, `revista.json` com os passos do tour, `revista-modais.html` com os textos dos modais; empacotador `scripts/empacotar-avaliacao.py`). O SVG não tem `<text>`: os textos do desenho estão em curvas.
- **Decisão:** trazer esse código para este repositório. Textos dos modais vão ao impresso com o "o que mudou". Entrega: um site estático por revista (LP e MAT separadas), F1 e F2 em sequência com navegação, em `.zip`.
- **Motivo:** respostas 19, 20, 22, 23a.
- **Descartadas:** site único com todas as revistas.
- **Arquivos afetados:** futuro: cópia de `common/` do svg-tour, gerador do zip.
- **Status:** ativa. Origem do SVG por parceiro em aberto.

### D-104 — Template é usado ao vivo; vira cópia só quando o projeto edita (2026-10-29)
- **Contexto:** resposta 6 falava em "cópia reclamada na associação", o que anularia a propagação da D-099.
- **Decisão:** a revista lê o template ao vivo; a cópia nasce na primeira edição do texto pelo projeto. Template mudou e a revista tem cópia: o texto dela não muda, aparece aviso com diff, "Validado" segue permitido (D-087), e o usuário pode juntar os textos ou descartar a cópia e ficar com o template. Trocar de template descarta a cópia com confirmação forte (D-093).
- **Motivo:** respostas 26a, 27a, 28a.
- **Descartadas:** cópia na associação; template novo substituir a cópia sem perguntar.
- **Arquivos afetados:** futuro: `docs/modelo-er.md`.
- **Status:** ativa. Como funciona o "juntar" em aberto (rodada 4).

### D-105 — Editor com "Inserir variável"; texto guardado em Markdown restrito + Handlebars (2026-10-29)
- **Contexto:** resposta 29a; resposta 30 pediu sugestão do Claude.
- **Decisão:** variável entra por menu e aparece como etiqueta colorida. Armazenamento: Markdown restrito (negrito, itálico, parágrafos, listas) com `{{variavel}}`, no `.hbs` e no banco. O editor só oferece esses 4 recursos.
- **Motivo:** diff legível no git e na tela "o que mudou" do impresso (HTML mostraria tags); limita a formatação ao que o InDesign recebe; o mesmo arquivo serve para editar no código e na interface.
- **Descartadas:** HTML — diff poluído e permite formatação fora do combinado.
- **Arquivos afetados:** futuro: editor de template, `templates/*.hbs`.
- **Status:** ativa.

### D-106 — Ano novo: escolha de matriz e de template nasce vazia (2026-10-29)
- **Contexto:** D-088 clonava a escolha de matriz/texto-modelo com ParceiroAno.
- **Decisão:** no clone do ano, ParceiroAno nasce sem matriz e as revistas nascem sem template; "Validado" fica bloqueado até alguém escolher (atribuição em lote, D-102).
- **Motivo:** resposta 31b: nada é atribuído automaticamente.
- **Descartadas:** clonar a escolha do ano anterior.
- **Arquivos afetados:** futuro: serviço de clone do ano, `docs/modelo-er.md`.
- **Status:** ativa. Substitui a parte de clone da escolha da D-088.

### D-107 — Variáveis: automáticas do cadastro, cópia manual do ano anterior, aba em planilha (2026-10-29)
- **Contexto:** valores por projeto renascem vazios todo ano (D-100).
- **Decisão:** parceiro, nome do projeto e ano são variáveis preenchidas sozinhas pelo cadastro. Botão "Copiar valores do ano anterior" por projeto (clique manual). Aba "Variáveis": tabela projetos × variáveis editável como planilha, com descrição de cada variável e templates onde aparece.
- **Motivo:** respostas 32a, 33a, 34a.
- **Descartadas:** digitar tudo de novo; aba só de documentação.
- **Arquivos afetados:** futuro: editor (aba Variáveis).
- **Status:** ativa. Lista completa de variáveis em aberto (resposta 35: ainda não se sabe).

### D-108 — F2: SVG por revista com ids por convenção; template F2 = abertura, tour e modais (2026-10-29)
- **Contexto:** SVG do infográfico tem textos em curvas e ids colocados à mão.
- **Decisão:** o design entrega um SVG por parceiro × componente, já nomeado pela convenção; o upload na revista confere os ids e lista os que faltam. O template F2 contém o texto de abertura, os passos do tour e os textos dos modais; a quantidade de botões/modais é fixa por template. Os modais não têm dados do parceiro.
- **Motivo:** respostas 36a, 37a, 38a, 39a, 40.
- **Descartadas:** SVG único por template; sistema ou desenvolvedor nomeando ids.
- **Arquivos afetados:** futuro: upload de SVG, validação de ids, template F2.
- **Status:** ativa.

### D-109 — Entrega e código: capa como campo, página única, planilha F2, svg-tour arquivado, bloqueio de template (2026-10-29)
- **Contexto:** grupo J do grill-me.
- **Decisão:** imagem de capa é campo da revista (fora do template). A revista é uma página só com menu de capítulos (F1, F2). O impresso recebe planilha com textos dos modais e do tour, como no F1. O código do svg-tour é copiado para cá e o repositório é arquivado. Template ganha bloqueio de escrita inteiro (D-081).
- **Motivo:** respostas 41a, 42b, 43a, 44a, 45a.
- **Descartadas:** capa no template; duas páginas; manter os dois repositórios.
- **Arquivos afetados:** futuro: gerador do zip e das planilhas, cópia de `common/svg-tour*.js`.
- **Status:** ativa.

### D-110 — "Juntar" texto do projeto com template novo: proposta revisada, nunca automática (2026-10-29)
- **Contexto:** D-104 deixou o "juntar" em aberto; D-062 recusou fusão sem revisão.
- **Decisão:** o sistema propõe o texto juntado (fusão de três vias: versão do template usada na cópia, template novo, cópia do projeto), destaca cada trecho e só grava no clique "Aplicar". Trecho mexido pelos dois lados: o usuário escolhe "meu", "template" ou "editar à mão". A cópia guarda a versão do template de onde saiu (`versao_base`). Formato confirmado: Markdown restrito com `{{variavel}}` (D-105).
- **Motivo:** resposta 46a; a revisão obrigatória resolve o risco de frase quebrada que motivou a D-062.
- **Descartadas:** lado a lado sem proposta; fusão aplicada sem revisão.
- **Arquivos afetados:** futuro: serviço de fusão, tela de juntar, `docs/modelo-er.md`.
- **Status:** ~~substituída por D-115~~

### D-111 — Template F2: um `.hbs` com uma seção por id; as seções são o gabarito do SVG (2026-10-29)
- **Contexto:** o F2 tem ~11 textos (abertura, passos do tour, modais).
- **Decisão:** um `.hbs` com seções `## passo1`, `## dlg-p2`…; o upload do SVG exige o id correspondente a cada seção (ex.: `## dlg-p2` → `btn-action-p2`). O projeto pode sobrescrever o texto do F2 com a mesma regra do F1 (D-104).
- **Motivo:** respostas 47a, 48a, 49a.
- **Descartadas:** um arquivo por texto; lista de ids cadastrada à parte; F2 sem sobrescrita.
- **Arquivos afetados:** futuro: `templates/*.hbs`, validação do upload.
- **Status:** ativa.

### D-112 — Revista incompleta: sem template não há preview; faltar template, SVG ou capa bloqueia "Validado" (2026-10-29)
- **Contexto:** D-106 faz a revista nascer sem template no ano novo.
- **Decisão:** "Validado" bloqueado se faltar template, SVG do F2 ou imagem de capa. Sem template escolhido, o preview não abre. Novo upload de SVG não entra no "o que mudou" do impresso (só textos).
- **Motivo:** respostas 50a, 51a, 52b.
- **Descartadas:** preview com faixa no lugar do texto; aviso "SVG trocado" ao impresso.
- **Arquivos afetados:** futuro: regras do "Validado", preview.
- **Status:** ativa.

### D-113 — Matriz duplicada guarda "duplicada de", só para consulta (2026-10-29)
- **Contexto:** D-101 (exceção nasce duplicando uma matriz).
- **Decisão:** a cópia guarda a matriz de origem e mostra o que difere dela, sem herdar nada.
- **Motivo:** resposta 53a; coerente com "projeto não herda de outro projeto".
- **Descartadas:** cópia sem referência à origem.
- **Arquivos afetados:** futuro: `docs/modelo-er.md` (Matriz.duplicada_de).
- **Status:** ativa.

### D-114 — Template F1 com seções fixas `## introducao` e `## fechamento` (2026-10-29)
- **Contexto:** o texto do F1 aparece antes e depois das escalas.
- **Decisão:** o template F1 usa seções fixas, como o F2 (D-111); o sistema põe cada seção no seu lugar; sobrescrita pelo projeto segue a D-104.
- **Motivo:** resposta 54a.
- **Descartadas:** F1 com texto único antes das escalas.
- **Arquivos afetados:** futuro: `templates/*.hbs`.
- **Status:** ativa.

### D-115 — Cópia do texto é por seção; "juntar" é lado a lado com edição à mão (substitui D-110) (2026-10-29)
- **Contexto:** varredura com 7 agentes: cópia do documento inteiro deixava a revista fora de todas as seções por causa de uma correção; fusão de três vias custava serviço e tela de conflitos.
- **Decisão:** só a seção editada vira cópia (guarda a versão do template de onde saiu); as demais leem o template ao vivo. Template mudou numa seção com cópia: aviso + tela "seu texto | template novo com diff", edição à mão ou "descartar cópia". Títulos de seção não são editáveis.
- **Motivo:** respostas 55a e 56a.
- **Descartadas:** cópia do documento inteiro (D-104 no ponto da granularidade); fusão de três vias automática (D-110).
- **Arquivos afetados:** `docs/modelo-er.md` (revista_secao, template_versao).
- **Status:** ativa. Substitui D-110; ajusta a granularidade da D-104.

### D-116 — Preview abre sempre; seção sem template vira faixa vermelha (2026-10-29)
- **Contexto:** D-112 fechava o preview sem template; no ano novo ninguém via nem as escalas.
- **Decisão:** preview sempre abre; texto sem template aparece como faixa vermelha (mesmo destaque da variável sem valor). "Validado" continua bloqueado.
- **Motivo:** resposta 57a.
- **Descartadas:** preview fechado (resposta 52b).
- **Arquivos afetados:** futuro: preview.
- **Status:** ativa. Substitui a parte de preview da D-112.

### D-117 — Revista sem cortes do componente é arquivada na mesma linha e volta sozinha (2026-10-29)
- **Contexto:** nada dizia o que acontecia com a revista quando o parceiro perdia o componente.
- **Decisão:** revista nunca é apagada: sem cortes do componente, fica arquivada (grava foto de arquivamento, congela), mantendo SVG, capa, cópias e fotos. Voltando os cortes no mesmo ano, a mesma linha é reativada. O projeto só é arquivado quando todas as revistas dele estão arquivadas.
- **Motivo:** resposta 58a.
- **Descartadas:** revista nova vazia herdando só a foto.
- **Arquivos afetados:** `docs/modelo-er.md` (revista.arquivada_em).
- **Status:** ativa. Complementa D-065/D-068/D-093/D-094 no nível da revista.

### D-118 — Trocar SVG ou capa derruba o "Validado"; o impresso continua vendo só textos (2026-10-29)
- **Contexto:** SVG de outro parceiro passaria pela checagem de ids sem ninguém revisar.
- **Decisão:** o hash do "Validado" inclui o sha256 do SVG e da capa; a foto do impresso (diff) contém só textos (D-112).
- **Motivo:** resposta 59a.
- **Descartadas:** troca de arquivo sem revalidação.
- **Arquivos afetados:** `docs/modelo-er.md`.
- **Status:** ativa.

### D-119 — Ano novo nasce em branco: cortes e escolhas são preenchidos de novo (substitui D-054 em parte) (2026-10-29)
- **Contexto:** sugestão do ano anterior (pergunta 61) e variáveis por parceiro (60).
- **Decisão:** o clone do ano copia só cadastros (etapas, componentes, cores, matrizes, templates). Cortes não são clonados: são preenchidos todos de novo, e os projetos nascem da cascata desses cortes novos. Sem sugestões do ano anterior. Valores das variáveis continuam só no projeto (D-100); "Copiar valores do ano anterior" só por projeto (D-107).
- **Motivo:** respostas 60b, 61b, 63b ("o preenchimento dos cortes precisará ser feito todo de novo").
- **Descartadas:** sugestão cinza do ano anterior; variável com escopo parceiro; cópia em lote; clonar cortes e participação (D-054).
- **Arquivos afetados:** futuro: comando de abrir ano.
- **Status:** ativa. Substitui a parte "cortes e participação" da D-054 e o mecanismo da D-085 (cascata dos cortes clonados → cascata dos cortes novos).

### D-120 — Painel da temporada; validação em lote envia o hash de cada revista (2026-10-29)
- **Contexto:** "Validado" bloqueado por vários motivos espalhados; D-078 validava em lote sem ninguém ver.
- **Decisão:** tela principal com uma linha por revista (Matriz, Template F1, Template F2, Variáveis, SVG, Capa, Validado, Impresso; ✓ ou "falta" com link para a correção) e ações em lote. Validação em lote mostra o diff de cada revista e envia os pares (revista, hash visto); o servidor recusa as que mudaram.
- **Motivo:** respostas 62a e 64a.
- **Descartadas:** pendências espalhadas por aba; lote sem hash.
- **Arquivos afetados:** futuro: admin.
- **Status:** ativa. Complementa D-078 e D-089.

### D-121 — Interface no Django admin; bloqueio de edição mantido (2026-10-29)
- **Contexto:** ponytail: planilha de variáveis, ações em lote e cadastros saem quase de graça no admin.
- **Decisão:** a interface nova é o Django admin com páginas do servidor; o editor React atual não segue. Bloqueio de edição continua (D-080/D-081/D-109); a renovação passa a ser um JS pequeno na página do admin. Ações em lote pulam projetos travados e listam os pulados.
- **Motivo:** respostas 65b e 66a.
- **Descartadas:** manter o React (`editor/`); controle otimista.
- **Arquivos afetados:** futuro: app Django; `editor/` aposentado.
- **Status:** ativa.

### D-122 — Fascículo é lista fixa no código (F1, F2) (substitui D-096) (2026-10-29)
- **Contexto:** F1 e F2 têm renderizadores próprios; um F3 exigiria código de qualquer jeito.
- **Decisão:** coluna `fasciculo` com CHECK ('F1', 'F2'), sem tabela.
- **Motivo:** resposta 67a.
- **Descartadas:** tabela de fascículos (D-096).
- **Arquivos afetados:** `docs/modelo-er.md`.
- **Status:** ativa. Substitui D-096.

### D-123 — Editor é caixa de texto Markdown com "Inserir variável" e preview ao vivo (2026-10-29)
- **Contexto:** etiquetas coloridas dentro do texto exigem editor rico (semanas).
- **Decisão:** textarea em Markdown restrito; botão "Inserir variável" põe `{{var}}` no cursor; preview ao lado com as variáveis coloridas; ao salvar, recusa formatação fora do combinado e `{{` fora da lista.
- **Motivo:** resposta 68a.
- **Descartadas:** editor rico com etiquetas (parte da D-105).
- **Arquivos afetados:** futuro: widget do admin.
- **Status:** ativa. Formato guardado da D-105 continua.

### D-124 — FKs compostas de ano mantidas; matriz pode ser duplicada de qualquer ano (2026-10-29)
- **Contexto:** ponytail propôs cortar a D-090; os dois agentes de banco defenderam.
- **Decisão:** manter FKs compostas (RunSQL com `reverse_sql`, nome `fk_<tabela>_<alvo>_ano`, índice próprio, teste que lista as constraints em `pg_constraint`). `matriz.duplicada_de` é FK simples, `ON DELETE SET NULL`, origem de qualquer ano.
- **Motivo:** respostas 69a e 70b.
- **Descartadas:** validar ano só no código; duplicar só do mesmo ano.
- **Arquivos afetados:** `docs/modelo-er.md`.
- **Status:** ativa.

### D-125 — Correções técnicas da varredura (2026-10-29)
- **Contexto:** achados sem decisão de negócio; aprovados junto com as perguntas 55–70.
- **Decisão:** (1) ER sem blocos; tabelas revista, revista_fasciculo, revista_secao, template, template_versao, `projeto.ano_id`. (2) Base da cópia vem de `template_versao` (só inserção), não do histórico. (3) Hash em Python sobre JSON canônico (`sort_keys`); "Validado" cai só na revista cujo conteúdo mudou (corrige "derruba as duas" da D-097). (4) Bloqueio por `INSERT … ON CONFLICT … WHERE expira_em < now()`; cascata com `SELECT … FOR UPDATE` em parceiro_ano; foto em REPEATABLE READ; abrir ano em uma transação. (5) SVG lido com defusedxml, lista de tags/atributos, até 3 MB, ids/classes prefixados; Markdown com HTML desligado; zip com JSON/SVG embutidos; atalhos do F1 fora do F2; seções × ids do SVG conferidas no "Validado" e ao salvar template.
- **Motivo:** varredura de 7 agentes.
- **Descartadas:** texto-base pelo django-simple-history; hash do JSONB guardado; motor Handlebars aberto.
- **Arquivos afetados:** `docs/modelo-er.md`.
- **Status:** ativa. Reescreve a D-093 sem blocos; substitui D-063 (parte do texto), D-070 e o campo `texto_modelo` da D-088.

### D-126 — Plano de construção S01–S18 numa branch exclusiva (2026-10-29)
- **Contexto:** muitas decisões (D-046 a D-125) geram tarefas distintas; usuário pediu cronologia do código com `/ecc:blueprint`.
- **Decisão:** plano em `plans/revista-express-django.md`, 5 fases (A fundação, B serviços paralelos, C montagem, D admin, E ano e virada), 22 passos (S01–S18 com S03b, S11a, S11b1, S11b2, S11c). Integração na branch `refatoracao-django` (a partir de `dev`); `dev` e `main` ficam intactas; cada passo em `feat/sNN-*` com PR para `refatoracao-django`. App em `app/` (projeto `sistema`, app `nucleo`). Código antigo é copiado, nunca movido, até S17. Escolhas que a revisão adversarial trouxe: JS/CSS da revista generalizados para 2 a 5 padrões (S03b); foto do impresso inclui escalas do F1 e textos, sem SVG e capa (corrige a leitura "só textos" da D-112); seções do F2 têm a 1ª linha como título e há seção `abertura`; `svg_ids` guardados sem o prefixo `f2-`; variáveis como colunas de `projeto`; na Fase B só S14 cria migração.
- **Motivo:** pedido do usuário ("criar uma branch nova exclusivamente para essa refatoração; mantemos a dev e a main como estão").
- **Descartadas:** integrar direto na `dev`; partir da branch antiga `django` (Django 5.2 + JORNADA).
- **Arquivos afetados:** `plans/revista-express-django.md`, `state.md`.
- **Status:** ativa.

### D-127 — Fase A com commit local por passo, branches encadeadas (2026-10-29 15:00)
- **Contexto:** o usuário pediu a Fase A sem commit, com subagentes em worktree. Um worktree nasce do último commit e não vê arquivos não commitados, então S02/S03/S03b não receberiam o S01 e as branches `feat/sNN` ficariam vazias.
- **Decisão:** cada passo faz um commit local na sua `feat/sNN-*`, sem push e sem PR. As branches são encadeadas: `feat/s01-esqueleto` sai de `refatoracao-django`; `feat/s02-*` e `feat/s03b-*` saem de `feat/s01-esqueleto`; `feat/s03-*` sai de `feat/s02-*`. O merge em `refatoracao-django` fica para quando o usuário pedir. O `state.md` continua não commitado no checkout principal.
- **Motivo:** escolha do usuário entre 3 opções; é a única que mantém as branches por passo e permite worktrees em paralelo.
- **Descartadas:** tudo sem commit no checkout principal (passos misturados, sem branches); parar após cada passo para o usuário commitar (bloqueia o paralelismo).
- **Arquivos afetados:** nenhum (fluxo de git).
- **Status:** ativa.

### D-128 — Configuração do esqueleto S01 (2026-10-29 15:10)
- **Contexto:** decisões do subagente do S01, sem impacto de negócio.
- **Decisão:** `DATABASE_URL` lida com `urllib.parse`; defaults de dev no compose (`POSTGRES_PASSWORD:-revista`, `DATABASE_URL` → `db`, `DJANGO_SECRET_KEY` só de dev), sobrescrevíveis pelo `.env`; CMD do Dockerfile roda `migrate` e `runserver`; `PYTHONDONTWRITEBYTECODE=1`; login do admin no Playwright só roda com `E2E_ADMIN_USUARIO`/`E2E_ADMIN_SENHA`; `HistoryRequestMiddleware`; `TIME_ZONE=America/Sao_Paulo`; `db`/`app` sem `container_name` e Postgres sem porta no host.
- **Motivo:** `run --rm app ...` funciona sem `.env`, em vários worktrees ao mesmo tempo, sem segredo versionado e sem dependência nova.
- **Descartadas:** `dj-database-url` (dependência nova); `env_file: .env` no `app` (quebra sem `.env`); superusuário em migration/fixture (segredo no repositório); gunicorn (fora do escopo de dev).
- **Arquivos afetados:** `docker-compose.yml`, `app/Dockerfile`, `app/sistema/settings.py`, `app/e2e/*`, `app/.env.example`
- **Status:** ativa. Revisão (django-reviewer): 0 críticos; aplicados healthcheck por TCP (`pg_isready -h 127.0.0.1`), porta `127.0.0.1:${APP_PORT:-8000}`, `E2E_BASE_URL`, versões com limite (simple-history 3.13, markdown-it-py 4.2…), parsing de `DJANGO_DEBUG`/`DATABASE_URL` vazio. Não aplicados (menores): usuário não-root no container, aviso de senha no `.env.example`.

### D-129 — Modelos de cadastro e matriz (S02) (2026-10-29 15:40)
- **Contexto:** decisões do subagente do S02 que o ER não fixava.
- **Decisão:** `fk_composta(tabela, alvo, colunas=None, colunas_alvo=None, nome=None)` devolve um `RunSQL` que cria FK (NO ACTION, MATCH SIMPLE: nulo passa) e índice `ix_*`, e o `reverse_sql` derruba os dois; FKs compostas ficam em migração escrita à mão separada da gerada (0002); `db_table` com os nomes do ER (`matriz_etapa_cc`…); `IntegerField` com CHECK nomeado em vez de `PositiveIntegerField` (CHECKs automáticos fora do ER); CHECK de tamanho só em `codigo` (20), `nome` (200), `tarefa.arquivo` (500), textos longos sem limite; MEC com PROTECT em matriz/etapa/componente/ano, CASCADE só em descritor e tarefa; `django.contrib.postgres` em `INSTALLED_APPS` (`ArrayField`).
- **Motivo:** caso comum de FK composta em uma linha; catálogo do banco igual à lista do ER; não barrar importação real.
- **Descartadas:** assinatura de `fk_composta` com tupla obrigatória (verbosa); nomes padrão `nucleo_*`; CHECK em textos longos.
- **Arquivos afetados:** `app/nucleo/models/{cadastro,matriz}.py`, `app/nucleo/db.py`, `app/nucleo/migrations/000{1,2}*.py`, `app/nucleo/tests/test_constraints.py`, `app/sistema/settings.py`
- **Status:** ativa. Divergências do ER a corrigir no doc: índice próprio da FK composta (D-124 vence o "nenhum índice extra"); n do CHECK de tamanho não definido; apagar matriz duplicada com MEC é recusado (PROTECT).

### D-130 — Formato do JSON do F1 para N padrões (S03b) (2026-10-29 15:50)
- **Contexto:** o JS da revista só tratava 4 padrões; o resolver do S07 vai gerar o JSON que ele lê.
- **Decisão:** por etapa: `scaleRange {min,max}`, `cortes {"padrao-1".."padrao-<n-1>"}` (1 a 4, crescentes), `padroes [{chave, rotulo}]` (n = cortes + 1, de baixo para cima) e cada descritor com `scale` dividido em `padrao-1..n`, com as linhas `---` prontas. O número de padrões sai de `cortes` (`padroesDeCima(cortes)`); `padroes[]` só dá os rótulos, escapados. Cores por `--color-padrao-k` e `--color-padrao-k-bg`; CSS vai até o 5º (`#ffffff`). Teste Playwright sem servidor: `page.route` num host fictício monta a página a partir de `app/e2e/fixtures/f1.html`.
- **Motivo:** a assinatura de `montarFaixasRegua` não muda (testes antigos intactos); uma fonte só para n; teste não disputa a porta 8000.
- **Descartadas:** passar a lista de padrões à régua (duas fontes para n); cor inline por `--p`; `webServer` estático (outro processo e outra porta).
- **Arquivos afetados:** `app/nucleo/static/revista/f1/*`, `app/nucleo/tests/fixtures/revista-*.json`, `app/e2e/fixtures/f1.html`, `app/e2e/tests/f1-fixture.spec.ts`
- **Status:** ativa. Contrato com o S07: o resolver sempre gera `padroes[]` com n = cortes + 1.

### D-131 — JSON inválido do F1 falha de forma explícita (2026-10-29 16:00)
- **Contexto:** revisão do S03b: `padroes[]` ausente ou com tamanho errado deixava rótulos vazios sem aviso, e cortes fora de sequência punham `NaN` na régua.
- **Decisão:** o JS valida cada etapa ao carregar (1 a 4 cortes `padrao-1..k` crescentes dentro de (min, max); `padroes` com k+1 chaves em ordem). Inválido: `console.error` com etapa e motivo, e a escala da etapa não é renderizada.
- **Motivo:** JSON errado é bug do resolver (S07); numa página que vai ao impresso, rótulo inventado esconderia o bug.
- **Descartadas:** rótulo de reserva "Padrão 0N" (mascara o erro).
- **Arquivos afetados:** `app/nucleo/static/revista/f1/script.js`, `app/e2e/tests/f1-fixture.spec.ts`
- **Status:** ativa. Etapa inválida: só a escala some; descritor, pré-requisitos, BNCC e as outras etapas renderizam.

### D-132 — Revisões do S02 aplicadas no S02/S03 (2026-10-29 16:00)
- **Contexto:** revisão de banco do S02 (0 críticos): `duplicada_de` ficava NO ACTION no banco (contradiz D-124); `DB_SET_NULL` é recusado pelo Django 6.1 ao misturar com PROTECT (fields.E323).
- **Decisão:** `duplicada_de` com `db_constraint=False` + `RunSQL` `fk_matriz_duplicada_de … ON DELETE SET NULL`; teste que roda o `reverse_sql`; teste de componente de outro ano. No S03: `nome` obrigatório em `fk_composta` quando há `colunas` (FKs sem ano não ganham sufixo `_ano`); colunas de FK composta NOT NULL, exceto as anuláveis do ER (MATCH SIMPLE desliga a checagem com nulo), conferido por `attnotnull`; teste de catálogo sem depender do prefixo `fk_`.
- **Motivo:** o banco é quem garante a coerência (D-090, D-124).
- **Descartadas:** `DB_SET_NULL` (E323); `NOT VALID` em `fk_composta` (tabelas nascem vazias; fica para quando houver dados).
- **Arquivos afetados:** `app/nucleo/models/matriz.py`, `app/nucleo/migrations/*`, `app/nucleo/db.py`, `app/nucleo/tests/test_constraints.py`
- **Status:** ativa.

### D-133 — Modelos de projeto, revista, texto e controle (S03) (2026-10-29 16:30)
- **Contexto:** decisões do subagente do S03 que o ER não fixava.
- **Decisão:** `projeto_passo` ganha `ano_id` e 3 FKs compostas (projeto, etapa, componente); `projeto_cor` sem FK composta (só aponta para o projeto); `revista_fasciculo.componente_id/ano_id` e `revista_secao.template_id` como `ForeignKey` (FK simples e índice); variáveis como `TextField` declarados à mão com CHECK de 200 (`variaveis.TAMANHO_MAX`), conferidos contra `VARIAVEIS` por teste; corte com dois CHECKs (`corte_valores_1a4` por `cardinality`, `corte_valores_sem_nulo`); troca de template com cópias recusada pela FK `(revista_fasciculo_id, template_id)` NO ACTION no UPDATE; CASCADE em revista → fascículo → seção e nos alvos/usuário de `Bloqueio`, PROTECT no resto; `TemplateVersao.criada_por` anulável (seed sem usuário); `TemplateVersao.save()` recusa update.
- **Motivo:** o banco garante coerência de ano e de template; trava vencida não pode impedir apagar o alvo; histórico precisa das colunas de variável.
- **Descartadas:** `add_to_class` para as variáveis (a tabela de histórico nasce sem elas); `valores__len` (`array_length` de `[]` é NULL e passaria); `ON UPDATE CASCADE` na FK da seção (o ER não prevê); trigger de imutabilidade em `template_versao` (marcado `ponytail:`; entra se outro cliente gravar no banco).
- **Arquivos afetados:** `app/nucleo/models/{projeto,texto,revista,controle}.py`, `app/nucleo/variaveis.py`, `app/nucleo/db.py`, `app/nucleo/migrations/000{3,4,5}*.py`, `app/nucleo/tests/test_{revista,constraints}.py`
- **Status:** ativa. Revisão (database-reviewer): 0 críticos; `template_versao` ainda aceitava UPDATE por `QuerySet.update()`/`save()` com pk explícito → trigger `BEFORE UPDATE OR DELETE` no banco (substitui o "trigger só se outro cliente gravar" desta decisão); testes de recusa por FK composta. `criada_por` nulo mantido só para o seed. Ajustar no `docs/modelo-er.md`: CASCADE de `bloqueio` (só no ORM; no banco NO ACTION); `projeto_cor` sem `ano_id`; `projeto_passo.ano_id`; colunas "só para FK composta" marcadas como FK; `criada_por` nulo; tamanhos dos textos curtos; índice próprio por FK composta.

### D-134 — Fase B sem commit; um worktree por passo a partir de `refatoracao-django` (2026-10-29 17:00)
- **Contexto:** o usuário pediu a Fase B sem commit, push nem PR. Os 6 passos (S04, S05, S06, S09, S10, S14) só dependem de S03, que já está em `refatoracao-django` (be15a50).
- **Decisão:** cada passo roda num subagente com worktree próprio, na branch `feat/sNN-<nome>` criada a partir de be15a50, e termina com as mudanças não commitadas no worktree. Não há encadeamento de branches. Os PDFs SAEGO (10–11 MB cada) não são copiados para `app/`: o teste do S04 lê de um diretório montado e é pulado se o arquivo faltar. Só o S14 cria migração (0007).
- **Motivo:** sem dependência entre os passos, o worktree já nasce com tudo que precisa; a D-127 só existia por causa da cadeia S01 → S02 → S03.
- **Descartadas:** commit local por passo (D-127) — desnecessário aqui e contra o pedido; copiar os PDFs para `app/nucleo/tests/fixtures/` — 31 MB no git.
- **Arquivos afetados:** nenhum (fluxo de git).
- **Status:** ativa. D-127 continua valendo para a Fase A.

### D-135 — Cascata dos cortes (S06) (2026-10-29 17:20)
- **Contexto:** o plano não fixava a assinatura nem o formato das linhas; `FotoRevista.criada_por` é NOT NULL e a Fase B não pode criar migração.
- **Decisão:** `gravar_cortes(parceiro_ano, linhas, usuario)`, com `linhas` = lista de `(Etapa, Componente, valores)` e sempre o conjunto completo do parceiro_ano (corte ausente é apagado). Cortes gravados por upsert (só o que mudou entra no histórico). Validação antes da transação, com todos os erros juntos (D-055 + par etapa × componente repetido); coerência de ano fica com as FKs compostas. Trava: `select_for_update(of=("self",))` no ParceiroAno. Revista nova herda a última foto de impresso do mesmo componente em projetos arquivados do mesmo parceiro_ano, inclusive as já herdadas, com `herdada=True` e `criada_por` = usuário da cascata. Stub de `fotografar(revista, motivo, usuario)` grava `{}` com o sha256 de `{}` (o CHECK recusa hash vazio).
- **Motivo:** a grade do S11a envia a linha inteira do parceiro; histórico sem ruído; `of=` evita travar a linha do parceiro junto.
- **Descartadas:** lista só com mudanças (teria de dizer o que apagar); `criada_por` anulável (migração); apagar e recriar cortes (duplica o histórico); depender só dos UNIQUE (a 2ª aba recebe erro em vez de esperar); manter o autor original na foto herdada.
- **Arquivos afetados:** `app/nucleo/servicos/cascata.py`, `app/nucleo/servicos/foto.py`, `app/nucleo/tests/test_cascata.py`
- **Status:** ativa. Verificado: 42 testes, `makemigrations --check` limpo. S07 troca o corpo de `fotografar` e o teste que confere `SHA256_DE_VAZIO`.

### D-136 — Perfis e permissões (S14) (2026-10-29 17:35)
- **Contexto:** a migração não pode importar código que muda depois; banco novo não tem as permissões de modelo durante a migração.
- **Decisão:** `app/nucleo/permissoes.py` é a fonte única da tabela papel × ação; a migração `0007_perfis` guarda listas literais congeladas e o teste `GruposNoBancoTest` compara banco × tabela (mudou a tabela sem migração nova → teste falha). A 0007 chama `create_permissions` para `auth` e `nucleo` (com `models_module = True` temporário no stub da migração) e falha alto se faltar permissão; o reverso apaga os 4 grupos e as 3 permissões customizadas. Mínimo privilégio: Ano só por `abrir_ano` (sem `add_ano`), `templateversao` só `add`, `fotorevista` e `bloqueio` só `view`. Admin = Pedagógica + CRUD de `auth.user`/`auth.group`; não marca impressa (`ADMIN_MARCA_IMPRESSA = False`). Impresso: `view_*` + `marcar_impressa`. Mídias = Pedagógica. Contagens: Admin 83, Pedagógica 75, Mídias 75, Impresso 22.
- **Motivo:** migração reproduzível; os fluxos (abrir ano, clique do impresso, bloqueio) não podem ser contornados pelo CRUD do admin.
- **Descartadas:** migração importando `permissoes.py` (histórico quebra quando o arquivo muda); comando `sincronizar_perfis` pós-migrate (passo manual); CRUD em todos os modelos.
- **Arquivos afetados:** `app/nucleo/permissoes.py`, `app/nucleo/migrations/0007_perfis.py`, `app/nucleo/models/{cadastro,revista}.py` (`Meta.permissions`), `app/nucleo/tests/test_permissoes.py`
- **Status:** ativa. Verificado: 35 testes, `makemigrations --check` limpo, ciclo `migrate nucleo 0006` ↔ `0007` recria os 4 grupos. Revisão (django-reviewer) em andamento. A conferir no S11: Pedagógica/Mídias com `delete_*` (o fluxo previsto é arquivar, D-117); Admin com `auth.change_user` pode marcar superusuário.

### D-137 — Serviço de SVG e capa (S09) (2026-10-29 17:35)
- **Contexto:** o SVG real do Illustrator traz PNG embutido; cada troca de arquivo com nome uuid deixaria o anterior órfão; o S05 (seções) roda em paralelo.
- **Decisão:** arquivo antigo apagado em `transaction.on_commit`, só se o caminho mudou (limite `ponytail:`: se a transação falhar, o novo fica órfão). `<image href>` aceita `data:image/(png|jpeg|gif|webp);base64`; fora isso `href` só `#id` interno. `xlink:href` vira `href` (SVG 2). Elemento fora da lista sai com os filhos (inclui `a`, `animate`/`set`, comentários, outros namespaces); filtros `fe*` ficam na lista. CSS com `\`, `expression`, `image-set` ou `url(` malformada é recusado no `<style>` e removido nos atributos. `<!DOCTYPE>` é recusado. `ids_faltando(revista, secoes)` recebe as seções efetivas; a regra fica em `ids_esperados` (`passoN` → `passoN`, `dlg-xx` → `btn-action-xx`). Capa: tipo só pela assinatura mágica, extensão segue o conteúdo; arquivos em `f2/<uuid>.svg` e `capas/<uuid>.<ext>` via `default_storage`; erros como `ValidationError` em PT-BR.
- **Motivo:** imagem rasterizada não executa script; escapes de CSS escondem `@import`/`url(`; o S07 só precisa passar a lista de seções.
- **Descartadas:** manter arquivos antigos (storage sem limite); apagar antes do commit (rollback perderia o vigente); `href` só `#id` sempre (apagaria a imagem); `register_namespace` (estado global); parser de template neste passo.
- **Arquivos afetados:** `app/nucleo/servicos/arquivos.py`, `app/nucleo/tests/test_arquivos.py`, `app/nucleo/tests/fixtures/f2-lp.svg`
- **Status:** ativa. Verificado: 45 testes, `makemigrations --check` limpo. Revisão (security-reviewer) em andamento. S08 procura os ids com prefixo `f2-`.

### D-138 — Correções da revisão do S06 (2026-10-29 17:35)
- **Contexto:** revisão de banco do S06: 0 críticos; a foto de arquivamento era tirada depois de apagar os cortes, e `save()` completo podia desfazer edições concorrentes.
- **Decisão:** fotografar as revistas que vão ser arquivadas antes de apagar os cortes; `update_fields` nos saves da cascata; `fotografar` dentro de transação aberta usa a transação do chamador, e REPEATABLE READ só quando chamado fora de `atomic` (clique do impresso) — regra para o S07; `_history_user` nos registros da cascata; `FOR NO KEY UPDATE`; etapa e componente de outro ano viram `ValidationError`.
- **Motivo:** `SET TRANSACTION ISOLATION LEVEL` falha depois da primeira query; a foto precisa ver os cortes que estão saindo.
- **Descartadas:** foto fora da transação da cascata (a revista poderia mudar entre a foto e o arquivamento).
- **Arquivos afetados:** `app/nucleo/servicos/{cascata,foto}.py`, `app/nucleo/tests/test_cascata.py`
- **Status:** ativa. Aplicada: 48 testes, `makemigrations --check` limpo. `validar_linhas(linhas, ano_id)`; ordem: trava → foto das que serão arquivadas → grava cortes → arquiva → projeto → revistas; `_history_user` por `_salvar(obj, usuario)`.

### D-139 — Templates: formato, validação e seed (S05) (2026-10-29 17:45)
- **Contexto:** o marcador da variável não pode ser lido pelo markdown-it nem colidir com texto; `secoes(texto)` não recebe o fascículo; os PDFs de 2025 não têm texto depois das escalas.
- **Decisão:** (1) cada `{{var}}` vira um marcador de caracteres Unicode de uso privado (removidos do corpo antes) e o valor entra com `html.escape` depois do render. (2) Dois parsers: renderização com `MarkdownIt("zero", html=False)` + `emphasis`, `list`, `newline`, `escape`, `entity`; validação com `commonmark` e lista branca de tokens (parágrafo, listas, texto, quebra, `strong`, `em`) — crase, citação e linha horizontal também são recusadas. (3) A 1ª linha é título em toda seção, F1 inclusive (`introducao`: "ANÁLISE DOS RESULTADOS PARA INTERVENÇÃO PEDAGÓGICA"; `fechamento`: "Utilização dos resultados"). (4) F1: exatamente `introducao` e `fechamento`; F2: `abertura` + ao menos um `passoN`, ids `abertura|passoN|dlg-[a-z0-9-]+`; seção repetida e texto antes da 1ª seção recusados; todos os erros num `ValidationError(lista)`. (5) Variável sem valor sai como `<span class="variavel-vazia">{{nome}}</span>`. (6) `carregar_templates`: template "Padrão", `origem="templates_seed/<ano>/<arquivo>"`, `get_or_create` pela unique, nunca cria versão nova, uma transação, valida antes de gravar, erro claro sem Ano/Componente; o aviso `<!-- revisar com a Pedagógica... -->` é removido por regex. (7) Fechamento do F1 = seção "09 Utilização dos resultados" (texto igual nos PDFs de LP e MT). (8) F2 convertido de `revista.json` + `revista-modais.html` por script de uso único fora do repo.
- **Motivo:** caracteres de uso privado são letras para o markdown-it (`**{{x}}**` continua negrito); lista branca não deixa passar construção nova; uma regra de título só; o preview mostra a variável vazia (D-100) em vez de quebrar.
- **Descartadas:** marcadores ASCII (`@@0@@`, `VAR0`); motor Handlebars (D-125); lista negra de tokens; `secoes(texto, fasciculo)`; `KeyError` na variável vazia; chave por `origem` (não é unique); parágrafo final da seção 3 do LP como fechamento (não existe no MT).
- **Arquivos afetados:** `app/nucleo/texto.py`, `app/nucleo/management/commands/carregar_templates.py`, `app/templates_seed/2026/*.hbs`, `app/nucleo/tests/test_texto.py`
- **Status:** ativa. Verificado: 46 testes, `makemigrations --check` limpo. Revisão do parser (python-reviewer) em andamento.

### D-140 — Bloqueio de edição (S10) (2026-10-29 18:00)
- **Contexto:** o mixin precisa adquirir já no GET do change form, antes do JS rodar; cada carga de página é uma aba nova.
- **Decisão:** a sessão da aba é gerada no servidor (`secrets.token_hex(16)`, hidden `_bloqueio_sessao`) e o JS só a reutiliza (desvia da tarefa 3 do plano, que gerava no JS). Rota extra `POST /bloqueio/liberar` por `sendBeacon` no `pagehide`; o mixin também libera após save 302. Serviço com assinatura `(alvo, usuario, sessao)`; `alvo` é instância de MatrizEtapaCC, Projeto ou Template. Rota sem login responde 403 JSON; perda do bloqueio = 409; o JS desliga o form com 403/409. `renovar` nunca readquire. Mixin: `changeform_view` sobrescrito, somente leitura por `has_change_permission=False` no objeto, POST num `atomic` com `conferir_na_transacao`, gancho `alvo_do_bloqueio(obj)` (revista trava o projeto), template `nucleo/bloqueio_change_form.html` para os admins do S11 estenderem; `quem_bloqueia(alvo)` para os lotes pularem travados (D-121).
- **Motivo:** somente leitura renderizado pelo servidor e testável pelo client; sem `crypto.randomUUID` em http; recarregar não tranca o próprio usuário por 30 s; `fetch` seguiria o redirect do login como 200; bloqueio expirado = form possivelmente velho.
- **Descartadas:** sessão no `sessionStorage` (o GET não a conhece); sessão por cookie (é do navegador, não da aba); esperar 30 s ao recarregar.
- **Arquivos afetados:** `app/nucleo/servicos/bloqueio.py`, `app/nucleo/urls/{__init__,bloqueio}.py`, `app/nucleo/admin/bloqueio.py`, `app/nucleo/templates/nucleo/bloqueio_change_form.html`, `app/nucleo/static/nucleo/bloqueio.js`, `app/nucleo/tests/test_bloqueio.py`
- **Status:** ativa. Verificado: 47 testes, `makemigrations --check` limpo, `node --check` ok. Revisão (django-reviewer) em andamento. Não portado: saída por inatividade do editor React (`BLOQUEIO_INATIVIDADE_MS`). `delete_view` não confere o bloqueio (S11). POST recusado descarta o que foi digitado.

### D-141 — Cadastros e importador de matriz (S04) (2026-10-29 18:00)
- **Contexto:** a Comunitária 2026 vem de 3 PDFs importados na mesma matriz; o plano deixava abertos `substituir=False`, o mapeamento dos campos e as linhas "---".
- **Decisão:** a importação só mexe nas etapa × CC presentes no arquivo; `substituir=False` com alguma MEC existente recusa tudo (`ImportacaoRecusada`); `substituir=True` apaga essas MECs (`select_for_update`) e recria descritores e tarefas. `passo` com sentinela `MANTER` (omitido = mantém o da MEC substituída; `None` = sem linhas vazias). Linhas "---" (e "–", "..." na planilha) não viram Tarefa. `level→inicio`, `fim→fim`, `content→texto`, `arquivo=None`; ordem da tarefa de cima para baixo; código de descritor repetido fica com a última ocorrência; `relacionadas`/`correspondente` com a heurística do extrator. Recusa se a escala máxima do arquivo ≠ `Etapa.escala_max` ou faltar etapa/componente no ano. XLSX: lê abas com A1 "Etapa" e B1 "Descritor"/"Cód. Descritor", tarefas e pré-requisitos separados por "#", aba "Escala" ignorada. `carregar_cadastros` usa `get_or_create` (edição no admin sobrevive): 2EF=1 (1000), 5EF=2, 9EF=3, 3EM=4 (500); LP "Língua Portuguesa", MT "Matemática"; cores `#F72628`, `#FF8D43`, `#B3CCFF`, `#0ED3FF`, `#FFFFFF`. `bulk_create_with_history`; matriz criada na mesma transação da importação. Testes dos PDFs leem `SAEGO_PDFS` (padrão `/pdfs:/pdfs-alfa`) e são pulados sem os arquivos.
- **Motivo:** substituir a matriz inteira faria o PDF de LP apagar o Alfa; confirmação forte da D-071; linhas vazias vêm do `passo` (D-091).
- **Descartadas:** substituir a matriz inteira (leitura literal da D-071); mesclar; gravar Tarefa "---"; heurística `separarHabilidades` da API; `update_or_create`.
- **Arquivos afetados:** `app/nucleo/management/commands/{carregar_cadastros,importar_matriz}.py`, `app/nucleo/importacao/{pdf,xlsx}.py`, `app/nucleo/servicos/importar_matriz.py`, `app/nucleo/tests/test_importacao.py`
- **Status:** ativa. Verificado: extrator antigo = novo (descritores Alfa LP 8/15, MT 33/28; LP 21/21; MT 37/35; tarefas também); 46 testes com os PDFs montados; `makemigrations --check` limpo. Revisão (python-reviewer) em andamento. Efeito colateral: a faixa de uma linha vazia some (ex.: MT 2EF D27, 596–635). Limite: o `fim` da planilha é a coluna, não o original. Upload pelo admin (S11a) precisa gravar em arquivo temporário.

### D-142 — Correções da revisão do S14 (2026-10-29 18:00)
- **Contexto:** revisão (django-reviewer): Admin com `auth.change_user`/`change_group` podia virar superusuário ou entrar no grupo Impresso; a reversa da 0007 apagava os Groups e, com eles, os vínculos usuário↔grupo; `delete_*` sem decisão que pedisse (D-117: revista nunca é apagada).
- **Decisão:** Admin só com `view_group` e `view/add/change_user` (sem `delete_user`: desativa, não apaga); o S11 registra `User` sem `is_superuser`, `is_staff` e `user_permissions` editáveis e com grupos limitados aos 4. Nenhum papel recebe `delete_*`. `hash_validado`, `validado_*` e `arquivada_em` serão `readonly_fields` no admin; só os serviços os escrevem. A reversa da 0007 apaga só as 3 permissões customizadas e mantém os Groups. Teste que confere `MODELOS_NUCLEO` contra os modelos do app.
- **Motivo:** sem isso, "Admin não marca impressa" é só aparência; rollback e redeploy não podem tirar o papel dos usuários.
- **Descartadas:** aceitar o risco e documentar como regra organizacional.
- **Arquivos afetados:** `app/nucleo/permissoes.py`, `app/nucleo/migrations/0007_perfis.py`, `app/nucleo/tests/test_permissoes.py`
- **Status:** ativa. Aplicada: 37 testes; contagens Admin 60, Pedagógica 56, Mídias 56, Impresso 22; ciclo 0006↔0007 mantém os grupos.

### D-143 — Correções da revisão do S10 (2026-10-29 18:15)
- **Contexto:** revisão (django-reviewer) do S10: 0 críticos; `delete_view` e inlines escapavam do bloqueio; aba em segundo plano perdia o bloqueio e o form `disabled` perdia o texto; F5 podia mostrar "somente leitura" contra o próprio usuário.
- **Decisão:** `has_delete_permission` nega com bloqueio alheio, e o mixin proíbe `list_editable` e actions de escrita nos admins que o usam; inlines sem change/add/delete no modo somente leitura; JS renova no `visibilitychange`, desliga com `readOnly` + aviso e reseta o envio no `pageshow`; aviso próprio quando quem bloqueia é o mesmo usuário; ids da rota validados (400); `liberar` pós-save não derruba a resposta.
- **Motivo:** a regra "escrita com bloqueio de outra sessão é recusada" (D-081) vale para qualquer caminho de escrita; renovar nunca readquire, então o texto digitado precisa continuar copiável.
- **Descartadas:** aceitar o mesmo usuário em outra aba (quebra "mesma aba", D-093); readquirir no 409 (o form pode estar velho).
- **Arquivos afetados:** `app/nucleo/admin/bloqueio.py`, `app/nucleo/static/nucleo/bloqueio.js`, `app/nucleo/urls/bloqueio.py`, `app/nucleo/tests/test_bloqueio.py`
- **Status:** ativa. Aplicada: 51 testes, `node --check` ok. Excluir é negado só com bloqueio de OUTRO usuário (a página de exclusão não tem sessão e o próprio usuário cairia na corrida do `sendBeacon`); a exclusão não confere com `FOR SHARE` (S11 adiciona se a corrida importar). JS: `readOnly` em campos de texto, `disabled` no resto, submit bloqueado. Inlines só para ver trocando os métodos de permissão na instância + `max_num=0`. Resolve a pergunta "`delete_view` confere o bloqueio?" da D-140.

### D-144 — Correções da revisão do S05 (2026-10-29 18:15)
- **Contexto:** revisão do parser do S05: 0 críticos, sem XSS; entidade `&#xE000;` forjava o marcador (IndexError ou valor de outra variável); regex `CHAVES` quadrática (40 KB = 16 s).
- **Decisão:** marcador com nonce por chamada; `CHAVES = \{\{[^{}]*\}\}|\{\{|\}\}`; recusar chaves soltas (`{{{x}}}`), caracteres de controle e bidi e definição de referência de link; BOM ignorado; valor só com espaços conta como vazio; `variaveis_usadas` só devolve nomes da lista; `carregar_templates` avisa seed divergente da versão 1 e seed faltando.
- **Motivo:** template persistido não pode derrubar a página nem o impresso.
- **Descartadas:** recusar só a entidade na validação (frágil).
- **Arquivos afetados:** `app/nucleo/texto.py`, `app/nucleo/management/commands/carregar_templates.py`, `app/nucleo/tests/test_texto.py`
- **Status:** ativa. Aplicada: 51 testes; `CHAVES` também recusa `{`/`}` soltos.

### D-145 — Correções da revisão de segurança do S09 (2026-10-29 18:25)
- **Contexto:** security-reviewer reproduziu 3 críticos no sanitizador: CSS no `tail` de filho de `<style>` escapava do filtro (exfiltração por seletor de atributo + `url()` externo, `@import`); regex `url(` com `.*?` e busca de ids em lista davam DoS quadrático (3 MB = horas); XML profundo virava `RecursionError` (500). Importantes: `<style>` global (`body{}`, `*`, `@layer`), `style` do `<svg>` raiz com `position:fixed` cobrindo o admin, funções CSS que buscam recurso sem `url(`, ids sem formato.
- **Decisão:** `<style>`, `<title>` e `<desc>` só com texto e `tail` zerado em todo elemento; só `url(#id)`; ids em `dict`; limites de 1 MB por `<style>`, 4 KB por atributo, 200 mil nós e profundidade 100; seletores só de `.classe`/`#id` com combinadores, qualquer at-rule recusa o arquivo; raiz sem `style`/`width`/`height`/`x`/`y`; propriedades de posicionamento e animação recusadas; `image(`, `cross-fade`, `src(` e afins e qualquer `//` ou esquema recusados; ids `[A-Za-z][\w.:-]{0,100}`; sem declaração `<?xml?>`; arquivo novo apagado se o save falhar.
- **Motivo:** o SVG vai inline no preview autenticado e no zip; lista branca estreita é mais fácil de garantir que lista negra.
- **Descartadas:** parser de CSS (`tinycss2`, dependência nova); prefixar o seletor inteiro com um escopo (mais código, mesmo efeito para o SVG do Illustrator); re-encode da capa com Pillow (dependência nova) — no lugar, S08/S15 servem capas com `nosniff` e `Content-Type` fixo.
- **Arquivos afetados:** `app/nucleo/servicos/arquivos.py`, `app/nucleo/tests/test_arquivos.py`
- **Status:** ativa. Aplicada: 54 testes; DoS (`url(` ×10 mil, 5 mil níveis) recusado em ~0,02 s, 50 mil ids em 0,33 s; o SVG real passa sem ampliar a lista (só `.stN`, `fill`, `stroke*`, `clip-path`, `mask`, `opacity`, `display`). Detalhes: CSS inválido recusa o arquivo inteiro (antes era removido em silêncio); atributo/tag fora da lista, `on*` e `href` externo continuam só removidos; `:` em valor de CSS conta como esquema (regex de esquema seria quadrática); `data:image/...;base64` em `<image>` fica fora do limite de 4 KB por regex linear (o PNG embutido do SVG real tem 496 KB); texto misto em `<text>` perde o trecho depois do filho (o F2 não tem `<text>`, D-103). Segunda revisão de segurança: C1, C2, C3, I1, I3, I5 fechados; I2 reaberto (raiz com `class`/`overflow`/`transform` + CSS de layout ainda cobria a página) → lista branca de propriedades CSS, raiz sem `class`/`overflow`/`transform`, `tail` zerado só sob `style`/`title`/`desc`, `data-*` com `:` descartado em vez de recusar, limites de 1.000 `<use>` e 5.000 ids; aplicadas: 57 testes; o SVG real passa (só `fill`, `stroke*`, `clip-path`, `mask`, `opacity`, `display:none`; nenhum `<use>`). Lista branca CSS: exatas `fill`, `stroke`, `opacity`, `text-anchor`, `letter-spacing`, `clip-path`, `clip-rule`, `mask`, `filter`, `mix-blend-mode`, `isolation`, `shape-rendering`, `visibility`, `display` (`none`/`inline`); prefixos `fill-`, `stroke-`, `font-`, `stop-`, `flood-`.

### D-146 — Correções da revisão do S04 (2026-10-29 18:40)
- **Contexto:** revisão (python-reviewer) do S04: 0 críticos; substituir apagava a MEC e, pelo CASCADE, a trava de quem edita; a planilha deixava código repetido e intervalo invertido chegarem ao banco (IntegrityError); exceções reais saíam como traceback.
- **Decisão:** a substituição mantém a linha da MEC (id, histórico e trava preservados), apaga só descritores e tarefas e recria; `passo` só muda quando informado; com bloqueio não expirado numa MEC a substituir, a importação é recusada dizendo quem edita; a `Matriz` é travada no início; o arquivo é lido fora da transação; XLSX valida intervalos, contiguidade e código repetido antes do banco; `pdftotext` com timeout de 120 s e UTF-8; `--passo` ≤ 0 recusado; código repetido no PDF com conteúdo diferente vira erro.
- **Motivo:** quem edita não pode perder a trava nem receber 404 no meio; erro de dado vira mensagem, não traceback.
- **Descartadas:** apagar e recriar a MEC (texto original do plano S04); flag `--forcar` para passar por cima do bloqueio.
- **Arquivos afetados:** `app/nucleo/servicos/importar_matriz.py`, `app/nucleo/importacao/{pdf,xlsx}.py`, `app/nucleo/management/commands/importar_matriz.py`, `app/nucleo/tests/test_importacao.py`
- **Status:** ativa. Aplicada: 53 testes com os PDFs montados, sem pulos; contagens iguais. Serviço dividido em `ler(arquivo)` (fora da transação) e `gravar_matriz(matriz, dados, substituir, passo, origem)`; `importar_matriz` chama os dois. Travas: Matriz → MECs (`of=self`) → recusa com `Bloqueio` não expirado ("em edição agora: LP 5EF (pedagogica)"). Histórico com `history_change_reason="importação de <arquivo>"`. Responde a pergunta "reimportar apaga a trava" da D-141. Limite registrado: o `fim` vindo da planilha é a coluna (união dos níveis), não o original; `#` dentro de texto da planilha é separador.

### D-147 — Fase C com commit local por passo encadeado; S16 sem commit (2026-10-29 19:05)
- **Contexto:** o usuário pediu a Fase C sem commit. O S08 depende do S07 e o S15 do S08, e um worktree novo nasce do último commit (mesmo problema da D-127).
- **Decisão:** S07, S08 e S15 fazem um commit local cada um na própria `feat/sNN-*`, sem push nem PR. `feat/s08-*` sai de `feat/s07-resolver` e `feat/s15-*` sai de `feat/s08-*`. O S16 não depende de ninguém da fase e fica sem commit (D-134). O merge em `refatoracao-django` fica para quando o usuário pedir.
- **Motivo:** escolha do usuário entre 3 opções. É a única que mantém uma branch por passo sem parar entre eles.
- **Descartadas:** empilhar S07, S08 e S15 no mesmo worktree sem commit (passos misturados); parar a cada passo para o usuário commitar (mais lento).
- **Arquivos afetados:** nenhum (fluxo de git).
- **Status:** ativa.

### D-148 — Serviço e comando abrir_ano (S16) (2026-10-29 19:20)
- **Contexto:** o plano não fixava de qual ano copiar, a assinatura do serviço nem para onde aponta `duplicada_de` de uma matriz que já era exceção.
- **Decisão:** copia do maior ano menor que o novo, sem `--de`; sem ano anterior, `AnoRecusado` e nada é criado. `abrir_ano(ano, usuario=None) -> (novo, origem)`: `usuario` vai ao histórico e a `TemplateVersao.criada_por`; o serviço não confere a permissão `abrir_ano` (a ação do S11a confere; o comando roda sem usuário). Uma `atomic()` que começa por `Ano.save()` num savepoint: o `IntegrityError` do UNIQUE vira `AnoRecusado("2027 já está aberto")`, o que também cobre duas execuções simultâneas. `copiar(modelo, **trocas)` clona com `bulk_create_with_history` e devolve o mapa id velho → novo, na ordem Etapa, Componente, CorPadrao, Matriz, MEC, Descritor, Tarefa, Template; `TemplateVersao` (só INSERT, sem histórico) com `bulk_create` e `DISTINCT ON (template_id)`. Toda matriz copiada aponta `duplicada_de` para a matriz de mesmo nome no ano anterior (exceção de 2026 vira, em 2027, cópia da exceção de 2026). `Template.origem` e `Tarefa.arquivo` copiados como estão (mesmo arquivo no storage). Motivo no histórico: "abrir ano 2027 a partir de 2026".
- **Motivo:** a virada é sempre a partir do ano anterior; o diff da D-113 mostra o que mudou desde o ano passado.
- **Descartadas:** `--de` opcional (sem caso de uso); conferir permissão no serviço (o comando de ops não tem usuário); `TransactionTestCase` (não há teste de concorrência).
- **Arquivos afetados:** `app/nucleo/servicos/abrir_ano.py`, `app/nucleo/management/commands/abrir_ano.py`, `app/nucleo/tests/test_abrir_ano.py`, `app/nucleo/models/texto.py` (só comentário)
- **Status:** ativa; ~~sem ano anterior, `AnoRecusado`~~ substituída por D-246 (banco vazio: o 1º ano nasce vazio). Verificado por mim: 162 testes OK (8 de PDF pulados), `makemigrations --check` limpo. Revisão (django-reviewer) em andamento. Limite `ponytail:`: leitura da origem sem trava (edição concorrente pode entrar pela metade). A confirmar com o usuário: `Tarefa.arquivo` compartilhado entre anos.

### D-149 — Correções da revisão do S16 (2026-10-29 19:35)
- **Contexto:** revisão (django-reviewer) do S16: 0 críticos, 3 importantes. Uma substituição de matriz concorrente recria descritores e tarefas com ids novos, e a cópia em READ COMMITTED quebrava com `KeyError` (500). Um ano digitado errado (`20277`) criava milhares de linhas que nada apaga (FKs PROTECT). Nenhum teste provava que uma falha no meio desfaz tudo.
- **Decisão:** a cópia lê a origem em REPEATABLE READ (fora de `atomic`, mesma regra do `foto.py`, D-138); o ano novo tem de ser `maior ano existente + 1`, sem buracos (resolve também a corrida 2027 × 2028); ano repetido responde "já está aberto" antes de "nenhum ano anterior"; teste de falha no meio com `mock.patch`; testes do mapa com 2 etapas × 2 componentes e histórico conferido por modelo, inclusive sem usuário.
- **Motivo:** o abrir ano não tem desfazer; erro de entrada ou corrida não pode deixar um ano errado no banco.
- **Descartadas:** `pg_advisory_xact_lock` (o ano consecutivo já resolve a corrida); `--forcar` para pular ano (sem caso de uso).
- **Arquivos afetados:** `app/nucleo/servicos/abrir_ano.py`, `app/nucleo/tests/test_abrir_ano.py`
- **Status:** enviada ao subagente do S16. `Tarefa.arquivo` resolvido na D-150.

### D-150 — Arquivo de tarefa compartilhado entre anos; só se apaga sem outra referência (2026-10-29 19:45)
- **Contexto:** o abrir ano (D-148) copia `Tarefa.arquivo` como caminho, então 2026 e 2027 apontam para o mesmo arquivo. Hoje o campo é sempre nulo (o importador grava `None`) e nenhum código escreve ou apaga esse arquivo.
- **Decisão:** manter o caminho compartilhado. Quem um dia implementar a troca do arquivo de uma tarefa só apaga o antigo se nenhuma outra `Tarefa` usar o mesmo caminho. A regra fica no comentário do campo.
- **Motivo:** escolha do usuário (opção 1). A proteção fica no único ponto onde o arquivo pode sumir, e o disco não duplica a cada ano.
- **Descartadas:** copiar o arquivo no abrir ano (o disco dobra a cada ano, para arquivos que hoje nem existem); nunca apagar arquivo de tarefa (órfãos sem limite).
- **Arquivos afetados:** `app/nucleo/models/matriz.py` (comentário de `Tarefa.arquivo`)
- **Status:** ativa.

### D-151 — Resolver, foto, hash e pendências (S07) (2026-10-29 20:10)
- **Contexto:** o mesmo dict serve ao preview, ao hash e à foto; a foto vai para jsonb, que não guarda ordem de chaves; o plano não fixava o formato, o marcador de template ausente nem os códigos de pendência.
- **Decisão:** (1) resolvido = `{f1: {etapas[], dados, cores, secoes}, f2: {secoes, svg_sha256, svg_ids}, capa_sha256, lacunas[]}`; `f1.dados` é o JSON da D-130; `etapas` guarda a ordem das abas; seções em lista `[{id, titulo, corpo}]` com HTML pronto. (2) `hash_validado` = sha256 do JSON canônico do resolvido inteiro; o resolvido leva só os textos renderizados (não os valores crus nem o nome do projeto), então variável usada só na LP não derruba a MT; o caminho do SVG/capa fica fora (reenviar o mesmo arquivo não muda o hash). (3) A foto guarda sempre o resolvido inteiro, nos dois motivos, com `hash` = `hash_validado` do momento; o S13 compara `impresso_de(foto.conteudo)` com `conteudo_impresso(revista)`; fora de `atomic`, `BEGIN` + `SET TRANSACTION ISOLATION LEVEL REPEATABLE READ` (testado com `TransactionTestCase`). (4) Template ausente: `secoes: None` + `faixa` (`<div class="faixa-vermelha" role="alert">…`) e lacuna `{tipo: template}`; variável vazia vira lacuna só se usada nos textos efetivos. (5) `RevistaSecao.texto` é só o corpo; o título vem do template (o S11b2 grava nesse formato); `secoes_desatualizadas` só avisa quando a seção mudou entre a versão-base e a atual. (6) Tarefa vai para o padrão 1 + nº de cortes menores que `fim` (âncora maior, topo aberto, igual ao JS); linha vazia segue o contrato (nível igual ao corte é do padrão de cima); `item` (arquivo da tarefa) fica para o S15. (7) `conteudo_impresso` inclui as cores do F1, além de escalas e textos. (8) Pendências: `matriz`, `corte_sem_matriz`, `template_f1`, `template_f2`, `svg`, `ids_svg`, `capa`, `variaveis`, `nome_projeto`; `link` nulo até existirem as telas (`ponytail:`). (9) Gabarito `tests/fixtures/resolver-4cortes.json` conferido por teste Django (`REGERAR_FIXTURES=1` regrava) e lido pelo Playwright f1-fixture.
- **Motivo:** ordem de abas e seções sobrevive ao jsonb; uma foto só serve a arquivamento, impresso e herança; o hash cai só na revista cujo conteúdo mudou (D-125).
- **Descartadas:** seções em dict (`passo10` antes de `passo2`); foto só com a parte do impresso (a arquivada precisa do resolvido inteiro); comando para gerar o gabarito.
- **Arquivos afetados:** `app/nucleo/servicos/{resolver,foto}.py`, `app/nucleo/tests/{test_resolver,test_cascata}.py`, `app/nucleo/tests/fixtures/resolver-4cortes.json`, `app/e2e/tests/f1-fixture.spec.ts`
- **Status:** ativa. Commit local 4ce2428 em `feat/s07-resolver` (D-147). Verificado por mim: suíte OK (8 de PDF pulados), `makemigrations --check` limpo, régua ok, Playwright f1-fixture 9/9 (resolvido de 4 cortes: 0 erros, 5 faixas). Revisão (python-reviewer) em andamento. A decidir com o usuário: cores no "o que mudou"; corte igual a 0 ou a `escala_max`.

### D-152 — Correções da revisão do S16 aplicadas (2026-10-29 20:10)
- **Contexto:** aplicação da D-149 e da D-150.
- **Decisão:** checagem `fora_de_atomic` antes do bloco e `SET TRANSACTION ISOLATION LEVEL REPEATABLE READ` como 1ª instrução; `ComandoAbrirAnoTest` virou `TransactionTestCase` para passar pelo `SET`; ordem das mensagens: "2027 já está aberto" → "nenhum ano anterior a 2027 para copiar" → "2028 recusado: o próximo ano que pode ser aberto é 2027"; atomicidade testada com `mock.patch.object(TemplateVersao.objects, "bulk_create")` falhando depois da cópia das tarefas; fixture com 4 MECs (5EF/9EF × LP/MT, passos 25, 50, nulo, 30); histórico conferido por modelo, inclusive com `usuario=None`; comentário de `Tarefa.arquivo` com a regra da D-150.
- **Motivo:** revisão (D-149).
- **Descartadas:** —
- **Arquivos afetados:** `app/nucleo/servicos/abrir_ano.py`, `app/nucleo/tests/test_abrir_ano.py`, `app/nucleo/models/matriz.py` (comentário)
- **Status:** ativa. Reverificado por mim: 167 testes OK (8 de PDF pulados), `makemigrations --check` limpo. S16 concluído, sem commit em `feat/s16-abrir-ano` (D-147).

### D-153 — Cores entram no "o que mudou"; corte nos limites da escala é recusado (2026-10-29 20:25)
- **Contexto:** perguntas do S07 (D-151). `conteudo_impresso` incluía as cores do F1, embora o impresso use uma rampa verde própria. A D-055 aceitava corte igual a 0 ou a `escala_max`, o que cria um padrão vazio que o JS recusa (D-131).
- **Decisão:** (1) as cores do F1 continuam em `conteudo_impresso` e aparecem no diff do impresso. (2) A cascata recusa corte ≤ 0 ou ≥ `escala_max`: cada corte fica estritamente dentro da escala. Ajuste em `validar_linhas` e no teste `test_aceita_limites` do S06, aplicado junto com as correções da revisão do S07 (2º commit em `feat/s07-resolver`).
- **Motivo:** escolhas do usuário. Recusar na entrada mostra o erro na tela de cortes, em vez de a escala sumir no preview.
- **Descartadas:** tirar as cores do impresso (recomendação do Claude: o impresso não usa essas cores); JS aceitar padrão vazio.
- **Arquivos afetados:** `app/nucleo/servicos/cascata.py`, `app/nucleo/tests/test_cascata.py`
- **Status:** ativa. Ajusta a D-055 (intervalo aberto nas pontas).

### D-154 — Correções da revisão do S07 (2026-10-29 20:40)
- **Contexto:** revisão (python-reviewer) do S07: 0 críticos, 4 importantes. (1) Corte nos limites gerava JSON que o JS recusa, sem pendência. (2) A foto lia SVG/capa/arquivamento da instância em memória, fora do retrato REPEATABLE READ. (3) ~35 queries por revista no painel (resolver + pendências + hash refazendo tudo). (4) Cópias de seção órfãs sem `order_by`: a ordem física do Postgres mudava o hash sozinha. Menores: `item` da tarefa fora do hash; linhas vazias caindo dentro de `[inicio, fim)` de tarefa larga; `titulo` é HTML, não texto.
- **Decisão:** além da D-153 (cascata recusa os limites), pendência defensiva `corte_invalido` espelhando o `problemaDaEtapa` do JS; `fotografar` fora de `atomic` recarrega a revista depois do `SET TRANSACTION`; `pendencias` e `hash_validado` aceitam `resolvido` pronto, `select_related` e descritores só das etapas com corte, com teto de queries em teste; `.order_by("secao")`; `item` (caminho de `Tarefa.arquivo`) na linha quando não nulo; nenhuma linha vazia dentro de `[inicio, fim)` de uma tarefa (decisão do orquestrador: o modelo novo tem `fim`; com `fim` = próximo nível o resultado é igual ao do TS); docstring: `titulo` e `corpo` são HTML escapado. 2º commit local em `feat/s07-resolver`; o S08 faz rebase.
- **Motivo:** o hash não pode cair sem edição; a foto precisa ser um retrato só; o painel do S12 resolve ~50 revistas.
- **Descartadas:** corrigir agora a cor com `passo` nulo (o JS pinta pelo topo = base da entrada de cima e diverge do Python com tarefas esparsas) — mexe no `script.js`, que o S08 está editando; fica para depois do S08. Teste de escrita concorrente na foto (o `SET TRANSACTION` testado basta).
- **Arquivos afetados:** `app/nucleo/servicos/{resolver,foto,cascata}.py`, `app/nucleo/tests/{test_resolver,test_cascata}.py`, `app/nucleo/tests/fixtures/resolver-4cortes.json`, `app/e2e/tests/f1-fixture.spec.ts`
- **Status:** aplicada no commit local 32d91db (`fix(s07)`). Reverificado por mim: 175 testes OK (8 de PDF pulados), `makemigrations --check` limpo, régua ok, Playwright f1-fixture 9/9; gabarito `resolver-4cortes.json` igual ao do 1º commit. `item = {id, tipo}` (nome do arquivo sem extensão + extensão), o formato que o JS já lê (`arquivos/itens/<id>.<tipo>`); o S15 grava o arquivo nesse caminho. `resolver.carregar(pk)` é o jeito de obter a revista antes de resolver (`select_related`). Tetos testados: `resolver` ≤ 12 queries; `pendencias` + `hash` com resolvido pronto ≤ 2.

### D-155 — Linhas vazias em todo nível do intervalo mínimo, mesmo dentro de uma tarefa (substitui parte da D-154) (2026-10-29 20:50)
- **Contexto:** a D-154 suprimia as linhas vazias dentro de `[inicio, fim)` de uma tarefa. O usuário corrigiu.
- **Decisão:** toda linha do passo efetivo que não tem tarefa começando naquele nível vira `---`, mesmo dentro do intervalo de uma tarefa mais larga, igual ao TS antigo. O intervalo mínimo é definido globalmente na matriz por etapa × componente (`MatrizEtapaCC.passo`). O código confere se a matriz traz todos os níveis do intervalo e gera os que faltam, mesmo quando a base já tem linhas. O usuário pode mudar o intervalo na matriz (S11a) e por projeto (`ProjetoPasso`, S11c), como na D-053 e na D-091.
- **Motivo:** palavras do usuário: "é necessário que haja essas linhas vazias com os intervalos mínimos definidos".
- **Descartadas:** suprimir as linhas vazias dentro do intervalo da tarefa (D-154, item das linhas vazias).
- **Arquivos afetados:** `app/nucleo/servicos/resolver.py`, `app/nucleo/tests/test_resolver.py`
- **Status:** ativa. Substitui só o item das linhas vazias da D-154. O resto da D-154 continua valendo.

### D-156 — Página única F1 + F2 (S08) (2026-10-29 21:30)
- **Contexto:** a mesma página serve ao preview (com faixas vermelhas, servidor) e ao zip (sem faixas, `file://`); o svg-tour usa `textContent`; o plano não fixava como testar sem servidor nem como o usuário vê o preview.
- **Decisão:** (1) um template só, `templates/revista/index.html`, com `contexto_pagina(revista, *, preview, estaticos, capa)` em `servicos/html.py` (com `json_seguro` e `css_das_cores` para N padrões); o preview passa `static("revista/")` e a rota da capa, o S15 passa `"revista/"` e `"arquivos/capa.<ext>"` com `preview=False`. (2) Playwright sem servidor: o Django renderiza em modo zip o gabarito `e2e/fixtures/pagina.html` (conferido por `test_preview`, `REGERAR_FIXTURES=1` regrava) com um SVG pequeno (`passo1`, `passo2`, `btn-action-p2`); `page.route` serve os estáticos (como D-130). (3) Título e texto do tour derivados com `unescape(strip_tags(html))` (negrito/itálico dos passos se perdem); `<dialog>` e seções do F1 recebem o HTML do resolver com `|safe`. (4) Config do tour como constantes em `f2-init.js` (`helpOnStart: false`); `BOTOES_MODAL` vem das seções `dlg-*`; `<dialog>` com id sem prefixo (`dlg-p2`). (5) `dialog[id^="dlg-"] { margin: auto }` contra o reset do F1. (6) Capa servida por `preview/<id>/capa` com `Content-Type` da extensão gravada e `nosniff`. (7) Comando `criar_demo` idempotente: parceiro "DEMONSTRAÇÃO" (`--ano`, padrão 2026), matriz própria, LP 5EF/9EF, templates do seed, SVG real da fixture, capa PNG gerada com a stdlib, usuário `demo` (`is_staff`) com senha nova impressa a cada execução. (8) `svg-tour.js` e `svg-tour-modal.js` copiados sem alteração (svg-tour bcadc29); `revista.css` com os estilos de `revista-modais.html` e seletores `f2-`.
- **Motivo:** um template evita divergência entre preview e zip; `{% static %}` quebra no `file://`; o teste não depende de servidor nem de credenciais.
- **Descartadas:** dois templates; servidor + login no Playwright (pularia sem variáveis); SVG real (850 KB) no gabarito; `innerHTML` no texto do tour (`<p>` dentro de `<p>`); capa por MEDIA.
- **Arquivos afetados:** `app/nucleo/servicos/html.py`, `app/nucleo/templates/revista/index.html`, `app/nucleo/static/revista/f2/*`, `app/nucleo/static/revista/f1/script.js` (guarda do Ctrl+setas), `app/nucleo/urls/{__init__,preview}.py`, `app/nucleo/management/commands/criar_demo.py`, `app/nucleo/tests/test_preview.py`, `app/e2e/tests/pagina.spec.ts`, `app/e2e/fixtures/pagina.html`, `app/.gitignore`
- **Status:** ativa. Commit local f1ec6e2 em `feat/s08-pagina` (sobre 32d91db). Verificado por mim: 183 testes OK (8 de PDF pulados), `makemigrations --check` limpo, régua ok, Playwright f1-fixture + pagina 14/14 (o subagente rodou também o `fumaca` com servidor: 16/16). Revisões a11y-architect e security-reviewer em andamento. Pendente: o preview não serve `arquivos/itens/<id>.<tipo>` (os itens de tarefa ainda não existem; o zip do S15 grava nesse caminho).

### D-157 — Correções das revisões de acessibilidade e segurança do S08 (2026-10-29 21:50)
- **Contexto:** a11y-architect: 3 críticos (abas de etapa com ARIA inválido e estado congelado; escala sem estrutura para leitor de tela; foco invisível nas bolinhas do SVG do F2), 5 importantes, 2 menores. security-reviewer: 0 críticos, 3 importantes (preview só com login, sem `view_revista`; `criar_demo` sem guarda de DEBUG e trocando senha de usuário existente; sem CSP), 5 menores.
- **Decisão:** aplicar no 2º commit de `feat/s08-pagina`: abas como grupo de botões com `aria-pressed`; texto oculto com padrão e faixa em cada linha da escala e `aria-hidden` no que é só visual; tour segue o foco e outline de 3px; seletor de descritores com foco devolvido, Esc, `aria-current` e região `role="status"`; contraste do `.descritor-btn`; foco ao sumir "Anterior"; guarda do Ctrl+setas com o modal "Ver item"; reflow do F2 em zoom; `prefers-reduced-motion`; faixas com `role="status"`; h2 no F1. Segurança: `view_revista` no preview e na capa; `criar_demo` só com DEBUG, usuário `demo-preview` e recusa de usuário que o comando não criou; CSP por meta tag; capa com `no-store`/`sandbox` e 404 sem arquivo; `css_das_cores` mais estrito; teste das chaves do tour; `faixa` sem `mark_safe` de dado guardado; `DEBUG` padrão desligado e erro com `SECRET_KEY` padrão fora do DEBUG.
- **Motivo:** a revista é lida por professores e vai ao zip; a defesa contra XSS não pode ser uma camada só.
- **Descartadas:** editar `svg-tour.js` (cópia fiel, D-103; contornado em `f2-init.js`); trocar já o branco sobre vermelho do número destacado (3,99:1) — decisão de design, pergunta ao usuário; validação de cor no `clean` dos modelos (S11).
- **Arquivos afetados:** `app/nucleo/templates/revista/index.html`, `app/nucleo/static/revista/{f1,f2}/*` (sem os arquivos do svg-tour), `app/nucleo/servicos/html.py`, `app/nucleo/urls/preview.py`, `app/nucleo/management/commands/criar_demo.py`, `app/sistema/settings.py`, testes e gabarito
- **Status:** aplicada no commit local d070ae9 (`fix(s08)`). Reverificado por mim: 187 testes OK (8 de PDF pulados), `makemigrations --check` limpo, régua ok, Playwright f1-fixture + pagina 15/15 (com CSP, 0 erros no console). Desvios: foco após "Anterior" por `click` no botão (no `svgtour:change` o Chrome já tirou o foco); faixas como flags (`sem_template_f1/f2`), texto fixo no template; `FileNotFoundError` do SVG sobe de `html.py` e a view devolve 404; usuário de demonstração agora é `demo-preview`, só com `view_revista`. Ficou de fora: CSP no `file://` (teste no S15); foco no SVG em 390px com o bloco maior que o palco (2.4.11); links de itens no preview. Pendências: texto alternativo dos itens de tarefa (o modelo não tem campo); contraste branco sobre `#f72628` no número destacado.

### D-158 — Número destacado da régua com texto preto (contraste WCAG) (2026-10-29 22:00)
- **Contexto:** branco sobre o vermelho do padrão 1 (#f72628) dá 3,99:1, abaixo do AA (4,5:1). `corTextoSobre` escolhia branco por APCA.
- **Decisão:** a cor do texto do número destacado sai da razão de contraste do WCAG 2 (preto ou branco, a maior). Com as 5 cores atuais, sempre preto (#f72628 → 5,3:1).
- **Motivo:** escolha do usuário (opção 1). Muda uma função e mantém as cores dos padrões.
- **Descartadas:** escurecer o vermelho do padrão 1 mantendo o branco (muda a cor em toda a revista).
- **Arquivos afetados:** `app/nucleo/static/revista/f1/script.js` (`corTextoSobre`), `app/nucleo/static/revista/f1/regua.test.mjs`
- **Status:** ativa. Enviada ao subagente do S08 (2º commit).

### D-159 — Zip por revista (S15) (2026-10-29 22:20)
- **Contexto:** a ação de admin podia aceitar várias revistas; ainda não havia admin de Revista; o plano não fixava onde ficam os itens das tarefas nem como testar `file://` sem servidor.
- **Decisão:** `zip_revista(revista) -> (nome, bytes)`, `nome_zip` (NFKD → ASCII, minúsculas, fora de `[a-z0-9]` vira `-`; ex.: `sao-paulo-demonstracao-lp-2026.zip`) e exceção `Pendente` com a lista de pendências. Uma revista por zip ("Escolha uma revista por vez"). `RevistaAdmin` só leitura em `nucleo/admin/revista.py` (`has_add/change/delete` falsos; `hash_validado`, `validado_*`, `arquivada_em` em `readonly_fields`, D-142), ação com `permissions=["view"]`. Itens: tarefas da matriz e do componente da revista com `arquivo`, gravadas como `arquivos/itens/<nome do arquivo>` (só o nome: sem `../`), sem repetição. `*.test.mjs` fora do zip. Zip em memória (`BytesIO`, `ponytail:`; trocar por `SpooledTemporaryFile` se crescer). Playwright: o teste Django grava o gabarito `e2e/fixtures/revista.zip` (48 KB, `REGERAR_FIXTURES=1`); o spec extrai com ~15 linhas de `node:zlib` e abre `index.html` por `pathToFileURL`.
- **Motivo:** o caminho mais simples; o S11c só precisa liberar `has_change_permission`; nenhuma dependência nova.
- **Descartadas:** zip de zips para várias revistas (lote fica para S11c/S12); alterar `html.py` para aceitar o resolvido pronto (arquivo do S08; a revista é resolvida duas vezes); diretório extraído versionado; `unzip`/`python` externos no teste.
- **Arquivos afetados:** `app/nucleo/servicos/empacotar.py`, `app/nucleo/admin/{__init__,revista}.py`, `app/nucleo/tests/test_empacotar.py`, `app/e2e/tests/zip.spec.ts`, `app/e2e/fixtures/revista.zip`
- **Status:** ativa. Commit local 9fab07c em `feat/s15-zip` (sobre f1ec6e2). Verificado por mim: 191 testes OK (8 de PDF pulados), `makemigrations --check` limpo, régua ok, Playwright f1-fixture + pagina + zip 16/16. Revisão (django-reviewer) em andamento. Falta rebase sobre o 2º commit do S08 e regerar o gabarito. `svg-tour.js` mantém `SvgTour.load` com `fetch(`, nunca chamado. Item com extensão maiúscula (`.PDF`) não abre no JS.

### D-160 — Correções da revisão do S15 (2026-10-29 22:40)
- **Contexto:** revisão (django-reviewer) do S15: 0 críticos, 4 importantes. O zip levava itens de etapas sem corte; na revista arquivada o HTML vinha da foto e os itens da matriz atual; `PurePosixPath(c).name` devolvia `..` e a barra invertida passava (zip slip em extrator de Windows); dois caminhos com o mesmo nome se sobrescreviam; arquivo ausente virava 500.
- **Decisão:** itens derivados do resolvido (`item` das linhas), inclusive na arquivada; arquivada com `svg_sha256`/`capa_sha256` diferentes dos da foto é recusada; nome do item só `[A-Za-z0-9_-]+\.(pdf|png|jpg)`, colisão vira `Pendente`, `order_by("pk")`; arquivo ausente vira `Pendente`; cópia por `copyfileobj`; zip reprodutível (data fixa 1980-01-01, atributos fixos, `ZIP_STORED` para pdf/png/jpg); estáticos por lista de permissão de extensões; testes dos casos novos, 403 nas rotas de alteração do admin, gabarito com 1 item PNG aberto por `file://`.
- **Motivo:** o zip vai a outras pessoas e é aberto por duplo clique; tem de levar só o que o HTML usa e ser igual a cada geração.
- **Descartadas:** `SpooledTemporaryFile` + `FileResponse` já agora (fica marcado `ponytail:` para quando os itens pesarem).
- **Arquivos afetados:** `app/nucleo/servicos/empacotar.py`, `app/nucleo/admin/revista.py`, `app/nucleo/tests/test_empacotar.py`, `app/e2e/tests/zip.spec.ts`, `app/e2e/fixtures/revista.zip`
- **Status:** aplicada. Commits locais em `feat/s15-zip`, rebaseados sobre d070ae9: 68f2cf4 (feat), 7d1af9a (fix da revisão), b961b98 (ajustes do rebase: `FileNotFoundError` do `html.py` vira `Pendente`, gabarito regerado; 3º commit porque o hook bloqueou `--amend`). Reverificado por mim: 202 testes OK (8 de PDF pulados), `makemigrations --check` limpo, régua ok, Playwright f1-fixture + pagina + zip 18/18. CSP do `<meta>` no `file://` (Chromium): 0 violações; scripts, estilos, capa, item PNG e iframe de PDF passam; Firefox não testado. Arquivo ausente conferido com `default_storage.exists` antes de montar; mesmo caminho repetido não é colisão (D-150); ação do admin com 2 queries.

### D-161 — Fase D com commit local por passo encadeado (2026-10-29 23:05)
- **Contexto:** o usuário pediu a Fase D sem commit. S11a, S11b1 e S11c só dependem de `refatoracao-django` (33e0621), mas S11b2 depende de S11b1, S12 de S11b2 + S11c e S13 de S12; um worktree novo nasce do último commit (mesmo problema das D-127 e D-147).
- **Decisão:** cada passo da Fase D faz 1 commit local na própria `feat/sNN-*`, sem push nem PR. `feat/s11b2-*` sai de `feat/s11b1-admin-templates`; `feat/s12-*` nasce de um merge local de `feat/s11b2-*` + `feat/s11c-admin-projeto` (e `feat/s11a-admin-cadastros`, para o painel ter as telas de cortes) feito na própria `feat/s12-*`; `feat/s13-*` sai de `feat/s12-*`. Nada entra em `refatoracao-django` sem pedido do usuário.
- **Motivo:** escolha do usuário entre 3 opções. Mantém uma branch por passo sem parar a cadeia.
- **Descartadas:** parar a cada passo para o usuário commitar (a cadeia espera); empilhar tudo num worktree sem commit (passos misturados).
- **Arquivos afetados:** nenhum (fluxo de git).
- **Status:** ativa.

### D-162 — Admin de templates (S11b1) (2026-10-29 23:20)
- **Contexto:** o plano não fixava o fluxo salvar → impacto → confirmar, a marcação das variáveis no preview nem o que fazer com texto igual.
- **Decisão:** o 1º POST com texto mudado valida, confere o bloqueio e mostra a tela de impacto sem gravar; a tela reenvia o POST inteiro em campos hidden com a mesma sessão de bloqueio; "Confirmar" (`_confirmar`) passa pelo mixin (bloqueio na transação), revalida e cria a versão N+1 com `criada_por`. "Voltar e editar" reenvia com `_voltar` e o form recusa de propósito para reabrir com o texto (`ponytail:`). Texto igual ao atual (`strip=False`, `\r\n`→`\n`) salva só o nome, sem versão. Preview `POST /templates/preview` renderiza sem valores: cada variável sai como `<span class="variavel-vazia">{{nome}}</span>`, colorida por CSS, e devolve os erros do `validar`. Na edição, ano/componente/fascículo só leitura; editar exige `change_template` + `add_templateversao`; `actions = None`; template novo nasce com a versão 1; abas Matrizes/Variáveis só aparecem quando os admins do S11a/S11c existirem; link "usado por" = `/painel/<ano>/?template=<id>` à mão (`ponytail:`, o S12 cria a rota). Revista sem SVG não entra como "SVG incompleto" no impacto (já é outra pendência).
- **Motivo:** dados pendentes ficam na página (sem estado no servidor); `history.back()` dispararia o `pagehide` e liberaria o bloqueio; valor de exemplo seria escapado e perderia o span.
- **Descartadas:** texto pendente na sessão do Django; `history.back()`; rótulo da variável como valor de exemplo.
- **Arquivos afetados:** `app/nucleo/admin/templates.py`, `app/nucleo/urls/templates.py`, `app/nucleo/templates/nucleo/{template_change_list,template_impacto}.html`, `app/nucleo/templates/nucleo/widgets/editor_texto.html`, `app/nucleo/static/nucleo/template_editor.{js,css}`, `app/nucleo/tests/test_admin_templates.py`, `app/nucleo/{admin,urls}/__init__.py`
- **Status:** ativa. Verificado por mim: 229 testes OK (8 de PDF pulados), `makemigrations --check` limpo, `node --check` ok. Sem commit em `feat/s11b1-admin-templates`. Revisão (django-reviewer) em andamento. JS não testado em navegador.

### D-163 — Correções da revisão do S11b1 (2026-10-29 23:40)
- **Contexto:** revisão (django-reviewer) do S11b1: 1 crítico, 3 importantes. (1) O JS do editor nunca inicializava: `{{ media }}` sai no `<head>` e o script síncrono rodava antes do `<body>`. (2) Duplo "Confirmar" com a mesma sessão passava pelo `FOR SHARE` e o 2º dava `IntegrityError` (500). (3) `texto.validar` com `ids.count` era O(n²) (40 mil seções = 23 s), alcançável pelo preview. (4) A confirmação não estava amarrada ao texto e à versão-base mostrados no impacto.
- **Decisão:** script com `defer` + teste Playwright do editor; `save_model` trava o Template (`select_for_update`), relê a versão atual e é idempotente com texto igual; botão desabilitado no submit; `Counter` em `texto.validar` + teto `TEXTO_MAX` no form e no preview (400); hidden assinado (`signing`) com hash do texto e número da versão-base, e confirmação que não bate reabre o impacto; testes de bloqueio de outro usuário, Impresso, XSS no preview, CSRF e dupla confirmação.
- **Motivo:** o editor é a tela principal da Pedagógica; o impacto mostrado tem de ser o que grava.
- **Descartadas:** —
- **Arquivos afetados:** `app/nucleo/admin/templates.py`, `app/nucleo/texto.py`, `app/nucleo/urls/templates.py`, `app/nucleo/static/nucleo/template_editor.js`, testes e e2e
- **Status:** aplicada no commit local 975c5fd (`feat(s11b1)`). Reverificado por mim: suíte OK (8 de PDF pulados), `makemigrations --check` limpo, Playwright `templates-admin` 1/1 (servidor na 8012, derrubado). Detalhes: `TEXTO_MAX = 100_000` (maior seed ~9,6 mil); assinatura com `max_age` de 30 min (a tela fica aberta sob o bloqueio renovado); duplo envio barrado por `form[data-envio-unico]` (botão desabilitado sairia do POST); o spec libera o bloqueio no fim. Fica: "Voltar e editar" mostra o cabeçalho "Corrija os erros".

### D-164 — Admin de projeto, variáveis, uploads e lotes (S11c) (2026-10-29 23:40)
- **Contexto:** o plano não fixava o que fazer com SVG com ids faltando, onde ficam a planilha de Variáveis e os lotes (o mixin proíbe `list_editable` e actions de escrita) nem como pular travados sem corrida.
- **Decisão:** SVG com ids faltando é gravado com aviso (faltantes, esperados e "Baixar gabarito de ids", CSV `id_no_svg,secao_do_template`); arquivo inválido é erro no campo; validação no `clean` (`sanitizar_svg`, `tipo_imagem`) e gravação no `save_model` (`receber_*`; sanitiza 2 vezes, `ponytail:`). Variáveis e lotes são views em `get_urls()` do ProjetoAdmin/RevistaAdmin (sem proxy model, que criaria migração); "Escolher matriz" em `/admin/nucleo/projeto/escolher-matriz/`. Lotes adquirem o bloqueio do projeto com sessão nova dentro da transação, gravam e liberam (`escrever_travado`); a mesma pessoa com o projeto aberto também é pulada. Planilha grava só as células alteradas (`show_hidden_initial` + `update_fields`), só projetos ativos. Template com cópias: pulado no lote, erro no form da revista. Ano anterior = projeto do mesmo parceiro em `ano - 1`, maior pk, mesmo arquivado. `RevistaAdmin` passa a usar o mixin (alvo = projeto), com fieldsets para o S11b2. Mixin: `changeform_view` usa `self.has_change_permission` (objeto só leitura não trava o alvo por 30 s). Permissões: Variáveis ver `view_projeto`/gravar `change_projeto`; matriz `change_parceiroano`; template `change_revistafasciculo`; gabarito `view_revista`.
- **Motivo:** o template pode ganhar seções depois e a pendência `ids_svg` já bloqueia o Validado; adquirir o bloqueio fecha a corrida entre conferir e gravar.
- **Descartadas:** recusar o upload com ids faltando; proxy model; action com página intermediária; só `quem_bloqueia`.
- **Arquivos afetados:** `app/nucleo/admin/{projeto,variaveis,lote,revista,bloqueio,__init__}.py`, `app/nucleo/templates/nucleo/{variaveis,lote,_filtros,change_list_lotes}.html`, `app/nucleo/tests/test_admin_projeto.py`
- **Status:** ativa. Verificado por mim: suíte OK (8 de PDF pulados), `makemigrations --check` limpo. Sem commit em `feat/s11c-admin-projeto`. Revisão (django-reviewer) em andamento. Telas não conferidas no navegador. Pergunta ao usuário: `delete_projetopasso`/`delete_projetocor` (sem eles, não há como voltar ao passo/cor da matriz).

### D-165 — Admin de cadastros, matriz e grade de cortes (S11a) (2026-10-29 23:40)
- **Contexto:** o plano não fixava a forma das telas de duplicar/reimportar, o aviso de impacto, a grade nem o admin de usuários.
- **Decisão:** Duplicar, Reimportar, Diferenças e Abrir ano são páginas em `get_urls()`. Duplicar exige `add_matriz`, trava a origem com `FOR NO KEY UPDATE`, casa etapa/componente do ano destino por `codigo` e reaproveita `clonar(queryset, usuario, motivo, **trocas)` extraído de `abrir_ano.py`; diff = tabela (onde, campo, origem, cópia) por código de descritor. Reimportar: digitar o nome exato da matriz, só quando o arquivo traz etapa × CC existentes; `passo` vazio mantém. Aviso D-076 = caixa "Confirmo: afeta N revista(s) ativa(s)" no form da MEC e do Descritor (N = revistas não arquivadas do componente cujo ParceiroAno usa a matriz e tem corte na etapa × CC; N = 0 salva direto). MEC nasce só por importação/duplicação; Tarefa é inline do Descritor (alvo do bloqueio = MEC); sem exclusão. Grade substitui o changelist de Corte (`?ano=`, padrão maior ano): todos os parceiros × etapa × CC, célula com vírgula/espaço/ponto e vírgula, grava só as linhas mudadas numa transação única, hidden do valor original detecta conflito entre abas, ParceiroAno nasce no 1º corte; exige `add_corte` + `change_corte`. Planilha com todas as abas "ETAPA - CC" do ano, grupo só na 1ª linha. Usuários: sem `is_superuser`/`is_staff`/`user_permissions`, grupos só os 4, novo nasce `is_staff=True`, não-superusuário não vê superusuários, sem exclusão. `MatrizEtapaCC.__str__`.
- **Motivo:** duplicar e reimportar pedem formulário; tela intermediária para o aviso exigiria repostar inlines; trava na origem resolve a corrida com menos código.
- **Descartadas:** actions do changelist; REPEATABLE READ na duplicação; segunda função de cópia; `difflib` no diff; confirmação em 2 passos guardando o upload.
- **Arquivos afetados:** `app/nucleo/admin/{cadastro,matriz,cortes,usuarios,__init__}.py`, `app/nucleo/servicos/{matriz,abrir_ano}.py`, `app/nucleo/models/matriz.py`, `app/nucleo/templates/admin/`, `app/nucleo/templates/nucleo/{admin_form,cortes,matriz_diferencas}.html`, `app/nucleo/tests/test_admin_cadastro.py`, `app/e2e/tests/cortes.spec.ts`
- **Status:** ativa. Verificado por mim: suíte OK (8 de PDF pulados), `makemigrations --check` limpo, Playwright `cortes` 1/1 (servidor na 8011, derrubado). Sem commit em `feat/s11a-admin-cadastros`. Revisão (django-reviewer) em andamento. Achado: a planilha real também erra os grupos do 2EF-LP (MA, PI e SALVADOR no 8, iguais ao AM no 7; SE 9 em vez de 8). Pergunta ao usuário: `delete_tarefa`/`delete_descritor` para a Pedagógica.

### D-166 — Exclusão só das sobrescritas do projeto; impacto do template ignora revista sem SVG (2026-10-29 23:55)
- **Contexto:** nenhum papel tinha `delete_*` (D-142), então ninguém voltava do passo/cor sobrescrito ao valor da matriz/paleta, e a Pedagógica não apagava tarefa ou descritor. Na tela de impacto do template, revista sem SVG não aparecia como "SVG incompleto" (D-162).
- **Decisão:** (1) Pedagógica, Mídias Digitais e Admin ganham `delete_projetopasso` e `delete_projetocor` ("voltar ao valor da matriz"), por migração de dados `0008` no S11c; Tarefa e Descritor continuam sem exclusão (só reimportação ou superusuário). (2) A tela de impacto lista só os SVGs enviados que perderiam ids; a falta de SVG aparece no painel.
- **Motivo:** escolhas do usuário (opções recomendadas). Uma exclusão errada na Comunitária afetaria ~25 revistas.
- **Descartadas:** liberar também Tarefa/Descritor; manter tudo sem exclusão; listar "sem SVG" no impacto.
- **Arquivos afetados:** `app/nucleo/permissoes.py`, `app/nucleo/migrations/0008_*.py`, `app/nucleo/tests/test_permissoes.py`
- **Status:** ativa. Ajusta a D-142 (só esses dois `delete_*`).

### D-167 — Correções da revisão do S11c (2026-10-29 23:55)
- **Contexto:** revisão (django-reviewer) do S11c: 0 críticos, 4 importantes. (1) A cascata arquiva sem pegar o Bloqueio: lote, planilha e "Copiar" podiam gravar em projeto/revista arquivado. (2) Inlines pareciam editáveis em objeto arquivado (o POST já dava 403). (3) Sem como remover sobrescrita (resolvido pela D-166). (4) Nome/variável acima de 200 caracteres virava `IntegrityError` (500) no change form.
- **Decisão:** `select_for_update` com `arquivado_em/arquivada_em IS NULL` dentro da transação de `escrever_travado`, do lote de template, da planilha e do "Copiar" (arquivado é pulado); inlines só leitura quando o objeto é só leitura; `ProjetoForm` com `MaxLengthValidator(TAMANHO_MAX)`; menores: `update_fields` filtrado por `EDITAVEIS`, `try/except` por alvo no lote, `__str__` de Revista/RevistaFasciculo, prefetch nos lotes, CSV do gabarito à prova de fórmula, help text do upload. Ficam `ponytail:`: sanitizar uma vez só e varredura de arquivos órfãos.
- **Motivo:** D-093: arquivado é congelado; o 500 vira mensagem.
- **Descartadas:** a cascata pegar o Bloqueio de cada projeto (mais código no caminho quente e corrida com quem edita).
- **Arquivos afetados:** `app/nucleo/admin/{lote,variaveis,projeto,revista,bloqueio}.py`, `app/nucleo/models/revista.py` (`__str__`), testes
- **Status:** aplicada no commit local 5de1a91 (`feat(s11c)`), com a migração `0008_excluir_passo_cor`. Reverificado por mim: suíte OK (8 de PDF pulados), `makemigrations --check` limpo. Detalhes: `escrever_travado` devolve `None` ou o motivo do pulo; revista com cópia num fascículo entra em "Pulados", o outro fascículo é trocado; fascículos lidos dentro da trava (sem prefetch antes do bloqueio). Contagens da D-142 mudam: Admin, Pedagógica e Mídias com +2 permissões.

### D-168 — Correções da revisão do S11a (2026-10-30 00:10)
- **Contexto:** revisão (django-reviewer) do S11a: 0 críticos, 7 importantes. (1) O Admin podia se pôr no grupo Impresso e ganhar `marcar_impressa` (anula a D-142), e editar senha/grupos de outro Admin. (2) Nome de parceiro começando com `=` virava fórmula na planilha do impresso. (3) Upload da reimportação sem limite de tamanho nem de tipo; erro do `pdftotext` virava 500. (4) `history_change_reason` (varchar 100) estourava com nome longo. (5) UNIQUE com campo readonly virava 500 na edição. (6) Corrida na grade de cortes e `IntegrityError` no 1º corte simultâneo. (7) A grade passava do limite de 1000 campos do POST com ~60 parceiros.
- **Decisão:** não-superusuário não oferece os grupos Impresso e Admin, não mexe nos próprios grupos/`is_active` e não edita outro Admin (atribuir Impresso/Admin fica com o superusuário); células de texto da planilha forçadas a string e nome de aba sanitizado; upload até ~20 MB com assinatura `%PDF-`/`PK`, erros do `pdftotext` viram `ImportacaoRecusada`; motivo do histórico truncado em 100; `codigo`/`padrao` readonly na edição, `nome` da matriz e `codigo` do descritor conferidos no `clean`, `escala_max` readonly com cortes ou MEC; grade trava os ParceiroAno em ordem de pk e relê sob trava, `get_or_create` do ParceiroAno; um campo de conferência por parceiro e célula ausente = erro. Menores baratos aplicados; ficam `ponytail:` o snapshot misto na duplicação, reimportar × editor e `escala_max` entre anos.
- **Motivo:** a regra "Admin não marca impressa" só vale se o Admin não puder entrar no Impresso; a planilha é aberta no Excel pelo impresso.
- **Descartadas:** Admin atribuir Impresso (exigiria abandonar a D-142); subir `DATA_UPLOAD_MAX_NUMBER_FIELDS` (adia o problema).
- **Arquivos afetados:** `app/nucleo/admin/{usuarios,cortes,matriz,cadastro}.py`, `app/nucleo/servicos/{matriz,importar_matriz,abrir_ano}.py`, `app/nucleo/templates/nucleo/cortes.html`, testes
- **Status:** aplicada no commit local 5e22020 (`feat(s11a)`). Reverificado por mim: suíte OK (8 de PDF pulados), `makemigrations --check` limpo, Playwright `cortes` 1/1 (servidor na 8011, derrubado). Detalhes: Admin só oferece Pedagógica e Mídias; usuário com grupo fora dos permitidos fica com `groups` readonly; outro Admin e `/password/` dele dão 403; planilha com `data_type = "s"` e aba sanitizada (31 caracteres); `LIMITE_UPLOAD` 20 MB e conversão de erro em `ler()` (vale também para o comando); corte de 100 caracteres em `clonar`, `duplicar_matriz` e `gravar_matriz`; conflito na grade mantém o digitado e o 2º salvar sobrescreve de propósito; um `o-` por parceiro (teto ~110 parceiros); "Abrir ano" sem valor inicial. Confirmado pelo usuário: só o superusuário põe alguém no Impresso ou no Admin.

### D-169 — S11b2 parte do merge local de S11b1 + S11c (2026-10-30 00:30)
- **Contexto:** a D-161 tirava `feat/s11b2-*` só de `feat/s11b1-admin-templates`, mas o S11b2 edita o `RevistaAdmin` que o S11c reescreveu (mixin, fieldsets, inline de template por fascículo).
- **Decisão:** `feat/s11b2-copia-secao` sai de 975c5fd e recebe um merge local `--no-ff` de `feat/s11c-admin-projeto` (5de1a91) antes do trabalho; o conflito em `admin/__init__.py` (imports dos dois lados) é trivial. O S12 sai de `feat/s11b2-*` + merge de `feat/s11a-admin-cadastros`.
- **Motivo:** evita refazer a parte de texto sobre um `revista.py` antigo e um conflito grande no S12. Mesmo fluxo escolhido pelo usuário (commit e merge locais nas `feat/*`, nada em `refatoracao-django`).
- **Descartadas:** S11b2 só sobre o S11b1 e conflito resolvido no S12.
- **Arquivos afetados:** nenhum (fluxo de git).
- **Status:** ativa. Ajusta a D-161.

### D-170 — Cópia de texto por seção na revista (S11b2) (2026-10-30 01:00)
- **Contexto:** o plano não fixava onde editar as seções, de qual versão a cópia nasce nem o formato da confirmação forte.
- **Decisão:** cada seção é um campo no change form da revista (rótulo `id · título` não editável), salvo pelo `BloqueioAdminMixin`; `versao_base` = versão mostrada na tela (hidden `versao__F1/F2`), para o aviso aparecer se o template mudou entre abrir e salvar; cópia só quando o texto muda (`show_hidden_initial` + normalização de quebras e pontas), e texto igual ao template ao vivo não cria cópia; seção desatualizada mostra `difflib.HtmlDiff` "Seu texto | Template novo" com "Manter meu texto" (atualiza `versao_base`) e "Descartar cópia" (vale para qualquer cópia); editar e descartar no mesmo envio é erro; troca de template pede digitar "descartar N cópia(s)", apaga as cópias antes do UPDATE na transação do admin; editar textos exige `change_revista` + `add/change_revistasecao`, e o descarte roda sob essas permissões (grupos intactos); `select_for_update` nos fascículos; `texto.validar_corpo(corpo)`; preview da seção isolada pelo atributo `data-cabecalho`. Cópia que a pessoa deixa igual ao template continua cópia (só o descarte explícito apaga) — confirmado pelo usuário (sugestão do revisor de apagar sozinha descartada).
- **Motivo:** tela separada perderia o bloqueio na navegação (`pagehide`); uma transação só para texto, troca e bloqueio.
- **Descartadas:** tela de diff por GET; POST interceptado como o impacto do template; `versao_base` = versão atual no salvar (o aviso sumiria sem ninguém ver); assinatura do hidden.
- **Arquivos afetados:** `app/nucleo/admin/revista.py`, `app/nucleo/texto.py`, `app/nucleo/templates/nucleo/widgets/editor_texto.html`, `app/nucleo/static/nucleo/template_editor.{js,css}`, `app/nucleo/tests/test_admin_revista_textos.py`, `app/e2e/tests/revista-textos.spec.ts`
- **Status:** ativa. Commit local 95c6790 em `feat/s11b2-copia-secao` (sobre o merge 2b1f8b2 de S11c em S11b1). Verificado por mim: suíte OK (8 de PDF pulados), `makemigrations --check` limpo, Playwright `revista-textos` + `templates-admin` 2/2 (servidor na 8014, derrubado). Revisão (django-reviewer) em andamento. Sem teste de concorrência para o duplo envio.

### D-171 — Correções da revisão do S11b2 (2026-10-30 01:20)
- **Contexto:** revisão (django-reviewer) do S11b2: 0 críticos, 2 importantes. (1) A contagem "descartar N cópia(s)" podia ficar velha com duas abas: apagava cópia não confirmada ou dava `IntegrityError` (500). (2) A aba Textos só leitura mostrava o texto ao vivo numa revista arquivada, diferente da foto congelada (D-117). Sem XSS no `HtmlDiff` (testado), sem bypass de bloqueio; `versao__F1/F2` sem assinatura é seguro (validado contra o template do próprio fascículo + FK composta).
- **Decisão:** travar o fascículo (`select_for_update`) no `clean` antes de contar; revista arquivada mostra as seções do resolvido (foto); `gravar_textos` trava a revista e recusa arquivada; troca que apaga cópias exige `add/change_revistasecao` e avisa quantas saíram; menores baratos (`update_fields`, mensagens, preview com erros de `validar_corpo`, faixa "Sem template"). 2º commit local em `feat/s11b2-copia-secao`.
- **Motivo:** confirmação forte só vale se a contagem confirmada for a que se apaga; o Impresso revisa o que sai no zip.
- **Descartadas:** só avisar "texto congelado" na arquivada (mostraria o texto errado).
- **Arquivos afetados:** `app/nucleo/admin/revista.py`, testes
- **Status:** ativa. Commit local 74bf143 em `feat/s11b2-copia-secao`. Verificado por mim: suíte 279 OK (8 pulados), `makemigrations --check` limpo; Playwright revista-textos + templates-admin 2/2 (subagente). Fora do escopo: troca de template em revista arquivada no mesmo envio não é travada (só `gravar_textos` recusa); nesse caso ainda sai o "alterado com sucesso" do Django.

### D-172 — Lista oficial de variáveis dos templates (2026-10-30 11:00)
- **Contexto:** a equipe entregou `revistas_variaveis.xlsx` com 25 variáveis (sintaxe `<<x>>`), fechando a pendência da D-107.
- **Decisão:** 3 automáticas mantidas (`parceiro`, `nome_projeto`, `ano`) + 25 colunas text de `Projeto`, na ordem da planilha. Sintaxe continua `{{x}}` (D-123). Os 4 `gentilico_*` viram `adjetivo_patrio_{singular,plural}_{masculino,feminino}` por `RenameField`. Exemplos singular/plural da planilha estavam trocados (corrigidos). `no_na_ em_nome_parceiro` → `no_na_em_nome_parceiro`; `ISSN` → `issn`. ~~`nome_parceiro` é manual (nome por extenso), distinto da automática `parceiro` (código do cadastro).~~ substituído por D-173. `pd01..pd05` são texto livre, sem ligação com rótulos do F1 nem `CorPadrao`. Documentação em `docs/variaveis.md` (para a Pedagógica) e `docs/modelo-er.md`.
- **Motivo:** planilha é a fonte oficial; rename preserva dados; ligar pdNN ao F1 seria escopo novo.
- **Descartadas:** aceitar `<<x>>` (dois formatos de marcador); manter `gentilico_*` com alias (dois nomes para a mesma coisa); `nome_parceiro` automático de `Parceiro.nome` (o cadastro guarda código, não nome por extenso).
- **Arquivos afetados:** `app/nucleo/variaveis.py`, `app/nucleo/models/projeto.py`, migração `0009_variaveis_oficiais`, `app/nucleo/admin/variaveis.py`, testes, `docs/variaveis.md`, `docs/modelo-er.md`
- **Status:** ativa. Juntada em `refatoracao-django`; migração renumerada para `0010_variaveis_oficiais` (depois de `0009_validators_cor_padrao` da auditoria).

### D-173 — `nome_parceiro` automático e `pd01..pd05` como rótulo dos padrões (2026-10-30 11:30)
- **Contexto:** pergunta aberta da D-172; o usuário respondeu.
- **Decisão:** a automática `parceiro` passa a se chamar `nome_parceiro` (valor de `Parceiro.nome`; "o sistema obtém o valor por outro meio"); não há coluna manual `nome_parceiro`. `pd01..pd05` ("pd01 significa padrão 01") são o rótulo de cada padrão no F1, no lugar do fixo "Padrão 01..05"; `pdNN` vazio de padrão que a revista tem é pendência de variável vazia e mostra o marcador de lacuna; padrão inexistente não cobra. Continuam utilizáveis nos textos. Cor segue em `CorPadrao`/`ProjetoCor`.
- **Motivo:** resposta do usuário; rótulo é texto impresso, então entra no hash e no `conteudo_impresso`.
- **Descartadas:** coluna manual `nome_parceiro` (D-172, valor viria duplicado); fallback silencioso para "Padrão 0N" com `pdNN` vazio (sairia impresso o rótulo errado sem ninguém ver).
- **Arquivos afetados:** `app/nucleo/variaveis.py`, `app/nucleo/servicos/resolver.py`, migração de variáveis, testes, `docs/variaveis.md`
- **Status:** ~~parte do pdNN vazio = pendência substituída por D-175~~. Juntada (f17d53a). Substitui em parte D-172 (item `nome_parceiro`).

### D-174 — Correções da revisão do S12 (2026-10-30 12:00)
- **Contexto:** revisão (django-reviewer) do 25d24ec: 0 críticos, 2 importantes, 6 menores. Sem caminho que grave `hash_validado` sem hash visto ou sem bloqueio; CSRF, POST-only, permissões e XSS OK.
- **Decisão:** (1) `change_view` só calcula hash/pendências no GET e após permissão; (2) teste de teto de queries por linha no painel, filtro de parceiro antes do loop, sem paginação por ora; (3) revalidar com o mesmo hash não regrava `validado_por/em` (preserva a trilha); (4) lote avisa pares não encontrados e só mostra sucesso com feitos > 0; (5) `liberar` com try/except + log, ponto duplo, botão desabilitado no envio; (6) "Validado" em form separado (não reenvia upload nem perde edição sem aviso); (7) reusar `preview.protegida`, `alvo_do_bloqueio`. 2º commit local `fix(s12)`.
- **Motivo:** cálculo pesado em todo POST; trilha de quem validou se perdia; mensagens enganosas.
- **Descartadas:** paginação agora (sem medida de custo ainda); "SVG/Capa alterados" no diff do lote — vai para o S13.
- **Arquivos afetados:** `app/nucleo/admin/revista.py`, `app/nucleo/urls/painel.py`, `app/nucleo/servicos/validacao.py`, templates do painel e da revista, testes
- **Status:** ativa. Commit local f52fffc em `feat/s12-painel`. Verificado por mim: suíte OK (8 pulados), `makemigrations --check` limpo; Playwright painel + revista-textos 2/2 (subagente). Teto medido: 15 queries por linha. Fora: coluna Impresso compara JSON inteiro (precisaria coluna `hash_impresso` com migração) — anotado com `ponytail:` em `ultima_impressa`.

### D-175 — Nome dos padrões: padrão por ano junto da cor, `pdNN` do projeto sobrescreve (2026-10-30 12:40)
- **Contexto:** usuário: "o nome dos padrões é definido uma vez na criação [...] em lote e cada curso pode sobrescrever esse valor apenas definindo o valor dessa variável". Pergunta de onde fica o padrão: "Por ano, junto da cor".
- **Decisão:** `CorPadrao` (por ano, padrão 1..5) ganha `nome`; rótulo do padrão no F1 e `{{pdNN}}` nos textos = `pdNN` do projeto se preenchido, senão `CorPadrao.nome`. Pendência só se os dois estiverem vazios. Mesmo modelo de cor do ano + `ProjetoCor`. `abrir_ano` copia o nome junto da cor.
- **Motivo:** escolha do usuário; reaproveita o padrão ano + sobrescrita já existente.
- **Descartadas:** `pdNN` obrigatório em cada projeto (D-173, digitar em todo projeto); ação em lote gravando `pdNN` (valor duplicado em cada projeto); padrão por parceiro (usuário escolheu por ano).
- **Arquivos afetados:** `app/nucleo/models/cadastro.py`, `app/nucleo/servicos/resolver.py`, `app/nucleo/servicos/abrir_ano.py`, `carregar_cadastros`, admin de CorPadrao, testes, `docs/variaveis.md`
- **Status:** ativa. Commit local 222627b em `feat/nome-padrao`, migração `0011_cor_padrao_nome` (preenche "Padrão 0N" nas linhas existentes). Verificado por mim: suíte OK (8 pulados), `makemigrations --check` limpo, merge em `refatoracao-django` sem conflito. Tetos de consulta +1 (resolver 13, painel 16 por linha). Nome de exibição corrigido para "Padrões do ano (cor e nome)" (892af5e, migração 0012 sem SQL). Juntada em `refatoracao-django`. Substitui parte de D-173 (pdNN vazio = pendência).

### D-176 — Texto de abertura das escalas (F1) por componente, vindo da Pedagógica (2026-10-30 13:10)
- **Contexto:** docx "Interpretação pedagógica da escala — textos de abertura LP e MT". O usuário disse "abrem o fascículo 2", mas o texto é a introdução das escalas; perguntado, escolheu "F1, abertura das escalas".
- **Decisão:** substituir a seção `introducao` de `f1-lp.hbs` e `f1-mt.hbs` pelo texto do docx (título "INTERPRETAÇÃO PEDAGÓGICA DA ESCALA", 3 parágrafos cada). O MT ganha o texto próprio (Unidades Temáticas, eixo cognitivo Saeb), fechando a pendência da D-139 ("f1-mt diz Para Língua Portuguesa"); aviso `<!-- revisar -->` removido. Texto copiado sem revisão ("conforme com o grau" mantido como veio). Abertura do F2 inalterada.
- **Motivo:** escolha do usuário; texto é da Pedagógica.
- **Descartadas:** F2 `abertura` (o texto fala da escala, não do tour); nos dois.
- **Arquivos afetados:** `app/templates_seed/2026/f1-lp.hbs`, `app/templates_seed/2026/f1-mt.hbs`
- **Status:** ativa. Commit local na `feat/seed-abertura-f1`; suíte OK (8 pulados), `makemigrations --check` limpo. Seed só vale em banco novo (`carregar_templates` nunca sobrescreve): em banco já carregado, a mudança entra como nova versão do template pelo admin.

### D-177 — Respostas do inventário das telas (2026-10-30 14:30)
- **Contexto:** 5 perguntas do inventário das telas (`docs/telas/inventario.md`, seção 5).
- **Decisão:** (1) Admin **não** marca "Revista Impressa Atualizada" (mantém `ADMIN_MARCA_IMPRESSA` desligado; fecha a pergunta aberta do plano); (2) "Padrões do ano" ganha aviso "afeta N revistas" antes de salvar nome/cor; (3) tela do impresso é página própria; (4) planilhas saem por revista; (5) o Painel é a página de entrada.
- **Motivo:** respostas do usuário, todas iguais às recomendações.
- **Descartadas:** Admin marcar impressa (separação de papéis, D-074); impresso como seção da revista; planilhas por ano (zip de várias revistas, sem pedido); índice do admin como entrada.
- **Arquivos afetados:** `app/nucleo/permissoes.py` (sem mudança), `feat/t07-impacto`, `feat/s13-impresso`, `feat/ui-navegacao`
- **Status:** ativa. (3) e (4) já no S13 (bdc32ca); (2) em `feat/t07-impacto`; (5) em `feat/ui-navegacao`.

### D-178 — Correções da revisão do S13; clique do impresso sem REPEATABLE READ (2026-10-30 15:00)
- **Contexto:** revisão (django-reviewer) do bdc32ca: 0 críticos, 3 importantes, 4 menores. Foto `impresso` segura, injeção de fórmula bloqueada (`data_type="s"` → `inlineStr`), sem XSS, permissões/CSRF/método OK.
- **Decisão:** o clique "Revista Impressa Atualizada" roda na transação do `escrever_travado` (READ COMMITTED) e grava a foto num savepoint, conferindo `foto.hash == hash_visto == hash_validado`; se não bater, desfaz. Substitui D-097/D-125 neste ponto (REPEATABLE READ no clique): como o hash é função do conteúdo, leitura misturada só gera recusa falsa, nunca aceite falso. Correções: diff mostra `fim` e `item` das tarefas; mudança só de formatação aparece (`**`/`*`/listas no texto puro) e mensagem honesta quando o diff não mostra; caracteres de controle limpos antes do openpyxl (500 no download); revista arquivada sem "Intervalo mínimo"; docstring do `foto.py`; testes de override de `ProjetoPasso`, item removido, fórmula, XSS e POST anônimo; botão "Copiar" com fallback sem TLS.
- **Motivo:** o Impresso via "nada mudou" quando só `fim`, item ou negrito mudavam; texto colado do Word derrubava as planilhas.
- **Descartadas:** levar o passo efetivo para o resolvido (mudaria o hash de todas as revistas validadas); REPEATABLE READ forçado no clique (o `escrever_travado` já abriu a transação).
- **Arquivos afetados:** `app/nucleo/urls/impresso.py`, `app/nucleo/texto.py`, `app/nucleo/servicos/planilhas.py`, `app/nucleo/servicos/foto.py`, `app/nucleo/templates/nucleo/impresso.html`, `app/nucleo/tests/test_impresso.py`
- **Status:** ativa. 2º commit 1ce0b17 em `feat/s13-impresso` (360 testes no relatório do subagente); minha verificação em andamento. Suíte do bdc32ca verificada por mim: OK (8 pulados).

### D-179 — Respostas do rascunho de UI: item por tarefa, `/` no Painel, zip na lista (2026-10-30 15:20)
- **Contexto:** 3 perguntas do rascunho de UI (`docs/telas/rascunho-ui.md`), via grill-me.
- **Decisão:** (1) parte das tarefas de 2026 tem arquivo do item (PNG ou PDF): a tela de upload entra agora, desenhada a partir do editor antigo (`editor/src/projetos/ano/EditorEscala.tsx:230-385`, `api/src/modules/itens/routes.ts`: botão anexar por linha, PDF/PNG/JPG até 5 MB, tipo conferido pelos bytes, link com o nome + "Remover arquivo", arquivo nunca apagado); detalhes na rodada 2 do grill-me. (2) `/` leva ao Painel do maior ano; o índice do admin continua em `/admin/` com o módulo "Temporada" no topo. (3) "Baixar zip" continua só na lista de Revistas.
- **Motivo:** respostas do usuário.
- **Descartadas:** trocar o índice do admin pelo Painel (Admin perderia Usuários e cadastros); botão de zip por linha no Painel e zip do ano inteiro (sem necessidade agora).
- **Arquivos afetados:** futuro: admin da matriz (Tarefa), `servicos/arquivos.py`; `feat/ui-navegacao` (item 2)
- **Status:** ativa; (1) pendente da rodada 2.

### D-180 — Arquivo do item: da matriz, PDF/PNG/JPG, um a um num modal com texto alternativo opcional (2026-10-30 15:40)
- **Contexto:** rodada 2 do grill-me sobre o upload do item (D-179).
- **Decisão:** o arquivo do item é da **matriz** (`Tarefa.arquivo`), cadastrado na edição da matriz, e aparece em toda revista que usa a matriz (aviso "afeta N revistas" da D-076 ao subir/trocar). Aceita PDF, PNG e JPG até 5 MB, tipo conferido pelos bytes (como `api/src/modules/itens/routes.ts`). Upload um a um, por tarefa, num **modal** (`<dialog>`) que pede o arquivo e um campo "Texto alternativo" **opcional** (o item entra sem ele; fecha a pendência D-157 do campo, não a do conteúdo).
- **Motivo:** respostas do usuário: o item é da prova comum; poucos itens, aos poucos.
- **Descartadas:** item por projeto (exceção ao "projeto só aponta para a matriz"); só PDF/PNG; upload em lote por zip (pode vir depois sobre o mesmo serviço); texto alternativo obrigatório.
- **Arquivos afetados:** futuro: `app/nucleo/models/matriz.py` (campo de texto alternativo), `app/nucleo/admin/matriz.py`, `app/nucleo/servicos/arquivos.py`, `app/nucleo/static/revista/f1/script.js` (alt no modal do item)
- **Status:** ativa; quem remove/exclui em aberto (rodada 3).

### D-181 — Exclusão pela tela: arquivo do item, tarefa e descritor, com confirmação forte (2026-10-30 16:10)
- **Contexto:** rodada 3 do grill-me. O usuário quis rever a D-166 ("só se exclui a sobrescrita do projeto").
- **Decisão:** Pedagógica, Mídias Digitais e Admin passam a poder excluir pela tela, além das sobrescritas do projeto: o arquivo do item, a **tarefa** e o **descritor** da matriz. O Impresso continua sem excluir. Excluir tarefa/descritor exige confirmação forte com impacto: lista as revistas afetadas e as que perdem o "Validado" e pede para digitar o código (padrão da troca de template com cópias). Remover o arquivo do item desliga da tarefa e apaga do disco **só quando nenhuma tarefa de nenhum ano** aponta mais para ele (D-150).
- **Motivo:** respostas do usuário; desde a D-166 existem aviso de impacto (D-076), "Validado" por hash e histórico; reimportar a matriz para corrigir uma tarefa é caro.
- **Descartadas:** só o arquivo do item; só Admin exclui; lixeira restaurável por 30 dias (+4 h, `excluido_em`); confirmação simples do Django; nunca apagar o arquivo do disco.
- **Arquivos afetados:** `app/nucleo/permissoes.py`, migração de dados dos grupos, `app/nucleo/admin/matriz.py`, `app/nucleo/servicos/arquivos.py`, testes de permissão
- **Status:** ativa. Código da tarefa na confirmação = `D01 100-150` (descritor + faixa), aprovado pelo usuário em 2026-10-30. Substitui D-166 no ponto "tarefa e descritor não se excluem pela tela" (~~D-166 nesse ponto~~). Implementação junto da D-180.

### D-182 — Fonte dos PDFs da matriz Comunitária: `revista/modelo/PDFs Matriz Comunitária/` (2026-10-30 12:55)
- **Contexto:** o preparo do S17 precisa dos 3 PDFs SAEGO 2025; a learning de 29/10 dizia que o Alfa (2EF/5EF) estava só na máquina do usuário.
- **Decisão:** a fonte é `revista/modelo/PDFs Matriz Comunitária/` (Alfa, LP e MT; ~32 MB), que **já está versionada**; LP e MT em `examples/` são cópias idênticas. Nada novo entra no git. Antes de apagar `revista/` no S17, mover `revista/modelo/` (PDFs e planilhas, incluindo `planilhas importantes/Cortes dos Padrões por Etapa e Parceiro.xlsx`) para um lugar que fica e atualizar caminhos.
- **Motivo:** indicação do usuário; o repositório é privado.
- **Descartadas:** copiar o Alfa de `~/Documentos` para `examples/` (duplicaria o que já está no git).
- **Arquivos afetados:** roteiro do S17 (`docs/s17-carga-2026.md`, em preparo)
- **Status:** ativa. A learning "Passos paralelos… PDFs grandes fora do app" está desatualizada no ponto do Alfa.

### D-183 — Telas do dia a dia como páginas próprias no Django com o visual do editor React (2026-10-30 13:50)
- **Contexto:** o usuário reavaliou a D-121 ao ver as telas do editor React; ele também é do time de design.
- **Decisão:** opção B. As telas do dia a dia (Painel, Cortes, Variáveis, Revista e textos, Matriz e descritores, Templates, Impresso, Lotes, Projeto) viram páginas próprias renderizadas pelo Django (HTML do servidor + CSS com os tokens do editor React, JS vanilla pequeno), fora do Django admin. O admin fica para o raro (usuários, etapas, componentes, parceiros). Backend, regras e testes não mudam. Troca tela por tela; o admin segue funcionando até cada página nova ficar pronta. Primeiro: protótipo da grade de cortes para comparar com o admin.
- **Motivo:** escolha do usuário; mantém o visual já desenhado, uma linguagem só (Python), sem parar a temporada.
- **Descartadas:** A — ficar só no admin (interface fria, pouco a desenhar); C — React sobre API Django (API por tela, duas linguagens, telas refeitas de qualquer jeito pelo modelo novo).
- **Arquivos afetados:** futuro: `app/nucleo/templates/ui/`, `app/nucleo/static/ui/`, views próprias; `editor/` fica como referência visual até a última tela migrar
- **Status:** ativa. Substitui D-121 no ponto "a interface nova é o Django admin" (~~D-121 nesse ponto~~); o bloqueio de edição da D-121 continua. Apagar `editor/` no S17 segue bloqueado.

### D-184 — Carga 2026: cortes digitados, PDF como fonte dos descritores, intervalo pela tela (2026-10-30 14:10)
- **Contexto:** 3 perguntas que o preparo do S17 deixou para a Pedagógica; o usuário respondeu.
- **Decisão:** (1) os cortes de 2026 **não** repetem os de 2025 por ora: a Pedagógica digita na grade (D-119 mantida; sem `importar_cortes`). (2) LP 2EF tem **8** descritores: o PDF SAEGO 2025 é a referência; a planilha `NÍVEIS - LP 2EF.xlsx` (10) não é fonte. (3) O intervalo mínimo 25 de 5EF/9EF/3EM entra pela tela da MEC depois da carga, como no roteiro; sem ele a escala sai sem linhas vazias, e tudo bem.
- **Motivo:** respostas do usuário.
- **Descartadas:** comando `importar_cortes` a partir da planilha de 2025; planilhas de níveis como fonte; `--passo 25` na importação (valeria também para o 2EF).
- **Arquivos afetados:** `docs/s17-carga-2026.md` (em `feat/s17-preparo`)
- **Status:** ativa.

### D-185 — Correções da revisão de segurança do upload do item e da exclusão (2026-10-30 14:30)
- **Contexto:** revisão (security-reviewer) de e93babb e 299de99: 0 críticos, 1 importante, 6 menores. Sem path traversal, sem IDOR entre revistas, sem XSS no `alt`; polyglot e SVG-como-PNG barrados; CSRF, código conferido no servidor e permissões OK.
- **Decisão:** (1) rota do item com `X-Frame-Options: SAMEORIGIN` e `frame-ancestors 'self'` — o PDF ficava em branco no iframe do F1; e2e com PDF; (2) GET do item no admin vira anexo (preview segue inline); (3) `clean_arquivo` recusa acima de 5 MB no form; (4) sai a conferência do mime declarado (o cliente controla; os bytes decidem); (5) exclusão confere o bloqueio da MEC com FOR SHARE na transação; (6) corrida `post_delete` × cópia não commitada só anotada (`ponytail:`).
- **Motivo:** o PDF não abria; arquivos grandes enchiam o disco temporário antes da recusa; navegadores mandam mimes variados.
- **Descartadas:** filtrar a rota do item por etapa (a revista cobre várias etapas; todos os papéis têm `ver_tudo`); sandbox no PDF (quebra o visualizador); servir itens de outro domínio.
- **Arquivos afetados:** `app/nucleo/urls/preview.py`, `app/nucleo/admin/matriz.py`, `app/nucleo/servicos/arquivos.py`, `app/e2e/tests/item.spec.ts`
- **Status:** ativa. 3º commit cb6b8b4 em `feat/item-exclusao` (354 OK no relatório; e2e com PDF). Fora: corrida post_delete × cópia não commitada (só `ponytail:`); excluir logo após sair do change form da mesma MEC pode pedir para recarregar.

### D-186 — HTMX liberado; time de agentes faz as telas B a partir do protótipo (2026-10-30 14:50)
- **Contexto:** o usuário gostou do protótipo B da grade de cortes (b0623f4) e pediu um time de agentes especialistas com um supervisor para planejar, desenhar e codar todas as telas do dia a dia.
- **Decisão:** HTMX (versão fixa, servido de `static/ui/`, sem CDN) liberado para interatividade nas páginas B; o sistema não precisa ser tão interativo quanto o React. Base comum em `feat/ui-b` (a partir de `feat/ui-b-cortes`): HTMX, fonte Inter local, peça comum de bloqueio, navegação com todas as rotas e design system documentado. Uma branch por tela a partir da base; cada tela tem ficha (planejamento) em `docs/telas/fichas/`, código e testes, revisão do supervisor e uma rodada de correção; o supervisor integra tudo em `feat/ui-b`. O admin continua funcionando.
- **Motivo:** pedido do usuário; telas independentes rodam em paralelo; arquivos compartilhados (rotas, navegação) são preparados na base para evitar conflito.
- **Descartadas:** React; cada agente editar a navegação e as rotas (conflitos certos); Google Fonts (dependência externa, offline quebra).
- **Arquivos afetados:** `app/nucleo/templates/ui/`, `app/nucleo/static/ui/`, `app/nucleo/urls/`, `docs/telas/`
- **Status:** em andamento (workflow).

### D-187 — Compose sobe só o sistema novo: saem mongo, api e editor (2026-10-30 15:10)
- **Contexto:** telas B aprovadas e juntadas (7b55ee8). O usuário pediu para desligar os contêineres do React e do Mongo e subir só os novos. Isso desbloqueia a parte `editor` da ação B do S17 (`docs/s17-carga-2026.md`).
- **Decisão:** `docker-compose.yml` fica só com `db` e `app`, conforme o diff da ação B. Os contêineres `revista-editor`, `revista-api` e `revista-mongo` foram parados e removidos. O volume `revista-eletronica_mongo-dados` foi mantido.
- **Motivo:** o editor React deixou de ser usado com as telas B. Sem o editor, a API e o Mongo não têm mais quem os use.
- **Descartadas:** apagar o volume do Mongo — os dados antigos ainda podem servir para exportar usuários (S17 §6a), e só o usuário decide apagar; apagar as pastas `api/` e `editor/` agora — isso é a ação C, que exige a tag da ação A e o ok do usuário.
- **Arquivos afetados:** `docker-compose.yml`
- **Status:** ativa

### D-188 — CRUD de cortes para todos menos Impresso: já existia, só ganhou teste (2026-10-30 15:40)
- **Contexto:** o usuário pediu que todos os grupos, menos o Impresso, criem, editem e excluam cortes pela UI.
- **Decisão:** sem código novo. A grade `/cortes/<ano>/` já faz isso: digitar cria, mudar edita, esvaziar a célula apaga (`gravar_cortes`). `preencher_cortes` (add/change/view) já está em Admin, Pedagógica e Mídias Digitais; o Impresso vê só leitura e leva 403 no POST. Um teste novo trava a regra para os 3 grupos.
- **Motivo:** reaproveitar 100%: a regra, a cascata e a UI já estavam prontas e testadas.
- **Descartadas:** CRUD por formulário (um corte por vez) — duplicaria a grade; dar `delete_corte` — a exclusão passa pelo serviço da cascata, não pelo delete do Django.
- **Arquivos afetados:** `app/nucleo/tests/test_ui_cortes.py`
- **Status:** ativa

### D-189 — Grade de cortes cria parceiro (linha nova) sem passar pelo admin (2026-10-30 15:55)
- **Contexto:** o usuário apontou que cada linha da grade é um parceiro (vira projeto), mas a UI não deixava criar linhas, só o admin. A D-188 tinha olhado só as células. Regra do usuário: "o front deve prever todas as funcionalidades do back e não mostrar algo errado".
- **Decisão:** formulário "Nova linha" abaixo da grade (`POST /cortes/<ano>/parceiro/`, `add_parceiro`), só visível com a permissão. O parceiro nasce sem cortes; o projeto nasce ao salvar os cortes. Nome duplicado ou longo: mensagem de erro, nada grava.
- **Motivo:** reaproveita a validação do modelo (`modelform_factory`), o sistema de mensagens e o aviso de "alteração não salva" da grade.
- **Descartadas:** link para o admin — é justamente o que o usuário rejeitou; adicionar a linha só no JS e criar o parceiro no "Salvar cortes" — mistura dois cadastros numa transação e complica o controle de conflito da grade.
- **Arquivos afetados:** `app/nucleo/urls/cortes.py`, `app/nucleo/templates/ui/cortes.html`, `app/nucleo/tests/test_ui_cortes.py`
- **Status:** ativa

### D-190 — Blueprint das telas B: 21 lacunas em 10 passos (2026-10-30 16:40)
- **Contexto:** a auditoria (D-189) achou 18 lacunas nas telas B; o usuário achou mais 3: matriz não se atribui pela ficha do projeto (0 de 2 ParceiroAno com matriz no banco local), nome do projeto sem edição na revista, preview sem matriz sai vazio sem faixa.
- **Decisão:** plano `plans/revista-express-telas-b-lacunas.md`, S0 a S9 + fechamento, branch `feat/telas-b-lacunas`, um commit por passo. Revisão adversarial incorporada: a matriz pela ficha grava sob `com_bloqueio` (sem `lotes.aplicar`, que abre outra sessão e é recusado); o nome do projeto se edita na própria revista; a faixa "sem matriz" fica fora do resolvido (senão muda o hash de todas as revistas); usuários B copiam as regras de `UsuarioAdmin` (D-142).
- **Motivo:** regra do usuário: toda função do back precisa de controle na tela B, sem admin e sem mostrar o que o perfil não pode usar.
- **Descartadas:** link para `ui_projeto#nome` (abriria só leitura por causa do bloqueio da revista); `FAIXA_SEM_MATRIZ` no resolvido (derruba o Validado de todas); botão "Abrir próximo ano" (o admin obriga digitar o ano, sem desfazer); esconder o botão Admin já no S1 (Pedagógica perderia acesso até o S7).
- **Arquivos afetados:** `plans/revista-express-telas-b-lacunas.md`
- **Status:** ativa

### D-191 — Bloqueio: a mesma pessoa em outra aba ou carga nova assume (2026-10-30 17:40)
- **Contexto:** o Playwright do S1 mostrou que ir da ficha do projeto para a revista do mesmo projeto deixava a revista em "Somente leitura" por até 30 s: a página anterior só solta o bloqueio no `pagehide`, depois que a nova já pediu o dela. Afeta usuários reais, não só o teste.
- **Decisão:** `adquirir` aceita quando o bloqueio expirou OU é do mesmo usuário (antes: mesmo usuário E mesma sessão). A sessão antiga perde renovação e escrita (`renovar`/`conferir_na_transacao` continuam exigindo a sessão) e o JS mostra "Você perdeu o bloqueio". Outra pessoa continua barrada. Escolhida pelo usuário.
- **Motivo:** determinístico, no servidor, sem corrida de rede.
- **Descartadas:** soltar o bloqueio no `beforeunload` (corrida: o envio não tem ordem garantida; falha se a pessoa cancela a saída); manter e só ajustar o teste (usuários seguiriam travados por 30 s).
- **Consequências:** o aviso "sua outra aba ainda segura a edição" saiu (não acontece mais); um lote do mesmo usuário toma o bloqueio da ficha que ele tem aberta, e a ficha vira só leitura; Playwright passa a rodar em série (`workers: 1`), porque painel, impresso e revista-textos gravam a mesma revista com o mesmo usuário.
- **Achado junto:** o botão "Copiar texto novo" da tela B do impresso não tinha nome acessível (`<span role="status">` dentro do botão); trocado por `aria-live="polite"`.
- **Arquivos afetados:** `app/nucleo/servicos/bloqueio.py`, `app/nucleo/admin/bloqueio.py`, `app/nucleo/lotes.py`, `app/nucleo/tests/test_bloqueio.py`, `app/nucleo/templates/ui/parciais/impresso_detalhe.html`, `app/nucleo/static/ui/ui.js`, `app/e2e/playwright.config.ts`
- **Status:** ativa

### D-192 — Abrir ano na tela B: página `/ui/anos/` (2026-10-30 17:35)
- **Contexto:** S3 de D-190. Só o admin abria ano; as telas B mandavam "Abra um ano no admin".
- **Decisão:** rota `ui_anos` (`/ui/anos/`) com a lista dos anos e o form "Abrir ano" (digitar o ano, dica do próximo, o mesmo aviso do admin), chamando `servicos/abrir_ano.abrir_ano`. Ver exige `view_ano` (os 4 perfis); o form só aparece e o POST só passa com `abrir_ano` (403). O seletor de anos (`_componentes/anos.html`) ganha "+ Abrir ano" só com `abrir_ano`. As mensagens "Abra um ano no admin" e o `/` sem ano (antes `admin:index`) e `/ui/impresso/` sem ano passam a ir para `ui_anos`. Sem ano nenhum, a página diz que o primeiro ano entra pela carga (o serviço recusa abrir sem ano anterior).
- **Motivo:** regra do usuário (toda função do back com controle na tela B); a página é a mesma que o S4 e o S5 vão estender (etapas, componentes, paleta), por isso o Impresso a lê.
- **Descartadas:** importar `AbrirAnoForm` do admin — import circular (`admin` → `urls` → `admin`); o form de 1 campo foi copiado. Item "Anos" no menu principal — o menu já tem 9 itens e o seletor de anos já está em toda tela B.
- **Arquivos afetados:** `app/nucleo/urls/ui_anos.py`, `app/nucleo/urls/__init__.py`, `app/nucleo/urls/ui_impresso.py`, `app/nucleo/templates/ui/anos/anos.html`, `app/nucleo/templates/ui/_componentes/anos.html`, `ui/cortes.html`, `ui/templates/lista.html`, `ui/variaveis/pagina.html`, `ui/matriz/lista.html`, `ui/revista/lista.html`, `app/nucleo/tests/test_ui_anos.py`, `test_ui_links.py`, `test_navegacao.py`
- **Status:** ativa

### D-193 — Etapas e componentes na página do ano, sem HTMX (2026-11-03)
- **Contexto:** item 5 da auditoria (S4 de D-190): só o admin criava/editava `Etapa` e `Componente`.
- **Decisão:** página `/ui/anos/<ano>/` (rota `ui_ano`) com dois modelformsets (`extra=1`; a linha vazia é o "Adicionar"), um form por tabela (campo `tabela`). Regras do admin copiadas: código só leitura na edição; `escala_max` só leitura com corte ou matriz (anotação `Exists`). `clean_codigo` checa o UNIQUE (ano fora do form → Django pula); o formset recusa código repetido no mesmo envio; `save()` em `atomic()` com `IntegrityError` virando mensagem (corrida). `codigo`/`nome` como `CharField(max_length)` para a mensagem não ser a do CHECK. GET exige `view_etapa`; POST exige add+change do modelo (403). Sem excluir e sem bloqueio de edição, como no admin.
- **Motivo:** menos da metade do código do padrão HTMX de `ui_projeto_linha`; aprovado pelo usuário. A revisão (agente) reproduziu 500 com duas linhas novas iguais; corrigido com teste.
- **Descartadas:** edição em linha com HTMX — mais código, ganho só em adicionar várias linhas sem salvar; `min_value` em `escala_max` — o admin também aceita ≤ 0 (paridade); bloqueio com `com_bloqueio` — o admin de etapa/componente não trava.
- **Arquivos afetados:** `app/nucleo/urls/ui_anos.py`, `app/nucleo/templates/ui/anos/ano.html`, `app/nucleo/templates/ui/anos/anos.html`, `app/nucleo/tests/test_ui_anos.py`, `app/e2e/tests/anos.spec.ts`
- **Status:** ativa

### D-194 — Paleta do ano na tela B: módulo comum e um form por padrão (2026-11-03)
- **Contexto:** item 4 da auditoria (S5 de D-190): `CorPadrao` só se editava no admin, e a confirmação de impacto (`PadraoImpactoForm`, `revistas_afetadas_padrao`) morava em `admin/cadastro.py`, que a tela B não pode importar (import circular).
- **Decisão:** mover esse bloco, sem mudar código, para `nucleo/paleta.py` (o admin importa de lá). Na página do ano, seção "Padrões" com um form por padrão (prefixo `pN`, POST `tabela=padroes` + `padrao=<pk>` do ano da URL, senão 404); só o form enviado calcula o impacto; sem confirmar → "Não salvo" + lista; confirmado → grava e avisa quem perdeu o "Validado" (mesmo texto do admin). "Adicionar padrão" só com < 5, choices só dos livres, cor inicial cinza. Cor com outra caixa não conta como mudança (`CorField`/`clean_cor`): o seletor do navegador manda minúsculas e a carga gravou maiúsculas. Ver: `view_etapa`; editar: `change_corpadrao`; incluir: `add_corpadrao`.
- **Motivo:** a confirmação é por padrão (cada um com sua lista de revistas), por isso não formset; calcular o impacto das 5 linhas no GET resolveria todas as revistas 5 vezes.
- **Descartadas:** importar do admin — import circular; formset — a confirmação é por linha; exigir nome no POST (revisor, achado 3) — nome vazio é válido no admin e o navegador sempre manda o campo; checar `view_corpadrao` à parte (achado 6) — todos os papéis com `view_etapa` têm `view_corpadrao` (`ver_tudo`).
- **Arquivos afetados:** `app/nucleo/paleta.py`, `app/nucleo/admin/cadastro.py`, `app/nucleo/urls/ui_anos.py`, `app/nucleo/templates/ui/anos/ano.html`, `app/nucleo/tests/test_ui_anos.py`, `app/e2e/tests/anos.spec.ts`
- **Status:** ativa

### D-195 — Telas B: Alpine (build CSP) somado ao HTMX, com fetch no autosave (2026-11-03)
- **Contexto:** revisão de UX de 03/11 (docx com 18 comentários + 2 prints extras) pede modal de impacto, autosave, linha nova por botão e edição inline; o usuário autorizou adicionar lib JS.
- **Decisão:** Alpine.js `@alpinejs/csp` 3.14.9 para estado local (componentes em `Alpine.data`), SortableJS 1.15.6 para reordenar; HTMX 2.0.4 continua onde já está; autosave por campo via `fetch` com protocolo JSON único.
- **Motivo:** HTMX já serve 6 telas; Alpine cobre só o que falta sem reescrever views.
- **Descartadas:** migrar tudo para Alpine — reescreve 6 telas (2 a 3 dias) sem ganho; só JS puro — código demais por tela; htmx + SortableJS sem Alpine — o usuário escolheu Alpine.
- **Arquivos afetados:** `plans/revista-express-telas-b-ux.md` (U1 em diante)
- **Status:** ativa

### D-196 — Autosave só sem impacto; com impacto, modal antes de gravar (2026-11-03)
- **Contexto:** "é preciso clicar em Salvar em quase toda página"; e a confirmação de impacto era um checkbox (o usuário quer modal).
- **Decisão:** campo salva ao sair dele; o servidor calcula na hora se a gravação tira o "Validado" de alguma revista e, se tirar, não grava e devolve a lista para o modal. Editor de templates mantém "Salvar" (versão assinada).
- **Motivo:** a mesma variável pode ou não afetar revista validada; o impacto precisa aparecer antes.
- **Descartadas:** tudo sozinho com "desfazer" — impacto só depois de gravado; manter Salvar — é a queixa.
- **Arquivos afetados:** `plans/revista-express-telas-b-ux.md` (U2, U3)
- **Status:** ativa

### D-197 — Grade de Cortes vira visão de Projetos, e cada projeto ganha aba Cortes (2026-11-03)
- **Contexto:** fusão de páginas (menu de 9 itens).
- **Decisão:** Projetos com visões Lista / Cortes / Variáveis; Lotes vira ação em massa na Lista; Revistas lista some dentro de Projetos; URLs antigas redirecionam.
- **Motivo:** a grade serve para lançar muitos parceiros de uma vez; a aba serve para um.
- **Descartadas:** só a aba no projeto — 30 parceiros viram 30 páginas.
- **Arquivos afetados:** `plans/revista-express-telas-b-ux.md` (U7)
- **Status:** ativa

### D-198 — Reforma de UX antes de S6–S9 (2026-11-03)
- **Contexto:** faltavam S6–S9 do plano de lacunas.
- **Decisão:** executar `plans/revista-express-telas-b-ux.md` (U0–U10, U8b, U9b) antes; S6–S9 nascem no padrão novo.
- **Motivo:** evitar 4 telas novas no padrão rejeitado.
- **Descartadas:** fazer S6–S9 antes e adaptar depois — retrabalho.
- **Arquivos afetados:** `plans/revista-express-telas-b-lacunas.md`, `plans/revista-express-telas-b-ux.md`
- **Status:** ativa

### D-199 — Menu de 5 itens e ano no cabeçalho; CDN liberada (2026-11-03)
- **Contexto:** "+ Abrir ano" em toda página confunde (parece adicionar parceiro); página do ano difícil de achar; usuário liberou CDN.
- **Decisão:** menu Painel · Projetos · Matrizes · Templates · Impresso; seletor de ano no cabeçalho com "Configurar <ano>" e "Abrir novo ano" (com permissão); libs novas via jsDelivr com versão exata e SRI.
- **Motivo:** o ano é contexto de trabalho; abrir ano é tarefa rara.
- **Descartadas:** seletor dentro de cada página — é a queixa; vendorizar libs novas — desnecessário com CDN liberada.
- **Arquivos afetados:** `plans/revista-express-telas-b-ux.md` (U1, U6)
- **Status:** ativa

### D-200 — Contador "alteração não salva" de Cortes comparava células deslocadas (2026-11-03)
- **Contexto:** "2 parceiro(s) com alteração não salva" nunca sumia e o aviso de saída aparecia sem edição (comentários 3 e 6).
- **Decisão:** limitar o seletor às células: `tr.querySelectorAll("td input.input")`. Teste Playwright "cortes sem edição não acusa alteração".
- **Motivo:** o `input.input` do Renomear (dentro do `<th>`) entrava no índice 0 e deslocava a comparação com o gravado.
- **Descartadas:** nenhuma. Variáveis e editor de template conferidos: comparam por nome/`defaultValue`, sem o bug.
- **Arquivos afetados:** `app/nucleo/templates/ui/cortes.html`, `app/e2e/tests/cortes.spec.ts`
- **Status:** ativa

### D-201 — Reforma de UX em worktrees paralelos, integrados em `feat/telas-b-ux` (2026-11-03)
- **Contexto:** o usuário pediu para manter a prática da refatoração Django: um agente por passo, cada um no seu worktree, e merge numa branch só.
- **Decisão:** a partir do U3, cada passo roda num subagente com worktree próprio (`feat/ux-<passo>-<nome>`), com compose isolado (APP_PORT único, banco próprio, `criar_demo` e usuários E2E locais) e commit na própria branch. Eu integro com `merge --no-ff` em `feat/telas-b-ux` e rodo as suítes no resultado de cada onda. Ondas: 2 = U3, U6, U8, U9b; 3 = U4→U9, U5→U8b; 4 = U7; 5 = U10.
- **Motivo:** ~12,5 dias em série caem para ~6; o banco de cada worktree é descartável, então os testes não sujam o banco de dev do usuário.
- **Descartadas:** sem commit no worktree (Fase B da refatoração, D-134) — aqui os passos de uma onda dependem da onda anterior, e o merge precisa de commit; tudo na raiz em série — lento.
- **Arquivos afetados:** `plans/revista-express-telas-b-ux.md`
- **Status:** ativa

### D-202 — Modal de impacto só quando a gravação tira o "Validado" (2026-11-03)
- **Contexto:** no U2, o agente trocou "afeta N revistas" por "tira o Validado de N revistas" como gatilho do modal; o usuário confirmou.
- **Decisão:** gravação que só afeta revistas ainda não validadas grava direto, sem modal; o modal aparece quando alguma revista perde o "Validado". Vale para autosave (U3) e para todos os passos seguintes. O admin mantém o checkbox antigo.
- **Motivo:** o risco real é desfazer uma validação; avisar sobre revista não validada é atrito sem ganho.
- **Descartadas:** confirmar sempre que houver revista afetada — o título do modal fala em Validado e o usuário pediu menos atrito.
- **Arquivos afetados:** `app/nucleo/servicos/impacto.py`, `app/nucleo/matriz.py` (`ImpactoForm(modal=True)`)
- **Status:** ativa

### D-203 — Limite de campos do POST em 10 000 para a grade de Cortes do admin (2026-11-04)
- **Contexto:** o "Salvar cortes" do admin manda 1 campo por célula + 1 por parceiro, de todos os parceiros. Com 4 etapas × 7 componentes, ~35 parceiros passam de 1000 campos, e o Django recusa o POST com 500.
- **Decisão:** `DATA_UPLOAD_MAX_NUMBER_FIELDS = 10_000` em `app/sistema/settings.py`. O corpo continua limitado a 2,5 MB, o que dá um teto de ~340 parceiros com 28 células.
- **Motivo:** o Django só lê o limite do settings, e o `CsrfViewMiddleware` lê o POST antes da view, então não dá para subir o limite numa rota só.
- **Descartadas:** mandar só as linhas alteradas, que é uma mudança maior e fica para quando o teto chegar; subir o limite por view, que é impossível pelo motivo acima.
- **Arquivos afetados:** `app/sistema/settings.py`, `app/nucleo/tests` (`test_40_parceiros_com_7_componentes_salvam_a_grade`)
- **Status:** ativa

### D-204 — Trava por linha na planilha de Variáveis marcada no template (2026-11-04)
- **Contexto:** um 409 de bloqueio de um projeto desligava a planilha inteira.
- **Decisão:** o `<tbody>` de cada projeto leva `data-trava-linha`. Um 409 ali trava só aquela linha. A rota `campo` compara o `original` com o valor gravado e responde 409 com `atual` sem gravar.
- **Motivo:** quem edita um projeto não deve impedir os outros de editar os demais.
- **Descartadas:** a heurística "`data-url` interno = linha", porque a revista também usa `data-url` interno e lá o 409 deve travar tudo.
- **Arquivos afetados:** `app/nucleo/static/ui/componentes/autosave.js`, `app/nucleo/urls/ui_projeto.py`, `templates/ui/parciais/variaveis_linha.html`, `app/e2e/tests/variaveis.spec.ts`
- **Status:** ativa

### D-205 — Exclusão só do que não está em uso, em todas as entidades (2026-11-04)
- **Contexto:** o usuário viu que o banco impede várias exclusões (PROTECT em ~40 FKs, `TemplateVersao` só aceita inserção) e que o admin nega a exclusão de Ano, Projeto, Revista e Usuário.
- **Decisão:** toda entidade pode ser excluída quando nada depende dela. Quando algo depende, a tela diz o que impede e oferece arquivar ou desativar. O PROTECT continua no banco. As versões de template continuam só de inserção. Usuário é desativado, nunca excluído.
- **Motivo:** dá ao usuário uma saída para o que foi criado por engano, sem apagar histórico em cascata (D-0xx: o banco guarda o histórico de cada ano).
- **Descartadas:** cascata para o admin com modal de impacto — apaga histórico que não volta; arquivar tudo (soft delete) — filtro em toda consulta, de 1 a 2 dias.
- **Arquivos afetados:** `plans/revista-express-exclusao.md` (E0 a E5)
- **Status:** ativa

### D-206 — Admin apaga o ano inteiro pela tela B (2026-11-04)
- **Contexto:** o ano aberto por engano nunca saía, porque o `abrir_ano` copia templates com versões e a `TemplateVersao` só aceita inserção (D-125).
- **Decisão:** o Admin, e só ele, apaga o ano inteiro pela tela B de Anos. A página lista as contagens do que vai sair e pede que ele digite o ano. O serviço `apagar_ano` apaga tudo na ordem das dependências, numa transação. O trigger da `TemplateVersao` passa a deixar o DELETE passar só quando a transação liga `SET LOCAL revista.apagar_versoes = 'on'`. O UPDATE continua proibido. `delete_ano` fica só no grupo Admin.
- **Motivo:** decisão do usuário. Um ano errado precisa sair sem ajuda do banco, e só quem administra deve poder.
- **Descartadas:** ano fica como histórico (padrão do plano): o usuário quer apagar; Pedagógica e Mídias excluírem ano: o usuário restringiu ao Admin; apagar pelo admin do Django: o usuário quer pela interface.
- **Arquivos afetados:** `servicos/exclusao.py`, `migrations/0016_*`, `0017_versao_apagavel`, `templates/ui/anos/anos.html`, `permissoes.py`
- **Status:** ativa (refina a D-205 e abre uma exceção na D-125)

### D-207 — Template sem uso é excluído de fato, com as versões, por todos menos o Impresso (2026-11-04)
- **Contexto:** pela D-205 o template seria arquivado, porque as versões não se apagam.
- **Decisão:** o template que nenhuma revista usa é excluído pela tela B junto com as versões, usando a mesma chave do trigger da D-206. Se está em uso, a tela lista as revistas. Podem excluir Pedagógica, Mídias e Admin. O Impresso não pode. O campo `Template.arquivado_em` sai do plano.
- **Motivo:** decisão do usuário. Sem uso, a versão não protege nenhum hash de revista.
- **Descartadas:** arquivar (padrão do plano): o usuário quer apagar; campo `arquivado_em`: deixou de ser necessário.
- **Arquivos afetados:** `servicos/exclusao.py`, `templates/ui/templates/editar.html`, `lista.html`, `permissoes.py`
- **Status:** ativa (exceção na D-125)

### D-208 — Desativar parceiro em vez de excluir quando há histórico (2026-11-04)
- **Contexto:** o parceiro é global e aparece em todo ano na grade de Cortes. O que sai do programa ficaria numa linha vazia para sempre, e não pode ser excluído porque tem cortes antigos.
- **Decisão:** `Parceiro.desativado_em`. O desativado some dos anos em que não tem Corte nem Projeto ativo e continua aparecendo nos anos em que tem dados (`parceiros_do_ano`). Reativar desfaz. Pedagógica, Mídias e Admin podem desativar; o Impresso não. A página de excluir parceiro em uso oferece "Desativar".
- **Motivo:** decisão do usuário. Tira o parceiro dos anos novos sem apagar o histórico.
- **Descartadas:** só explicar o impedimento (padrão do plano): o usuário quer a saída; boolean `ativo`: a data diz quando saiu, como o `Projeto.arquivado_em`.
- **Arquivos afetados:** `models/cadastro.py`, `migrations/0018_*`, `servicos/exclusao.py`, `urls/ui_excluir.py` (E0); `urls/cortes.py`, `cortes_grade.html` (E2)
- **Status:** ativa

### D-209 — Endereço de escuta do app configurável por `APP_BIND` (2026-11-05)
- **Contexto:** o usuário quer acessar o app do dev por outros computadores da rede. A porta estava fixa em `127.0.0.1`, e o `ALLOWED_HOSTS` não tinha o IP da máquina.
- **Decisão:** a porta publicada passa a ser `"${APP_BIND:-127.0.0.1}:${APP_PORT:-8000}:8000"`. Para abrir na rede: `APP_BIND=0.0.0.0 DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,<ip> docker compose up -d app`.
- **Motivo:** sem a variável, o padrão continua fechado. Abrir para a rede é escolha explícita a cada subida.
- **Descartadas:** fixar `0.0.0.0` (expõe o servidor de dev com DEBUG a toda a rede sempre); `docker-compose.override.yml` (no Compose, `ports` se soma em vez de substituir, e as duas ligações na 8000 conflitam).
- **Arquivos afetados:** `docker-compose.yml`
- **Status:** ativa

### D-210 — S6–S9 em 3 worktrees paralelos, com o blueprint atualizado ao código pós-reforma (2026-11-05 09:45)
- **Contexto:** o blueprint `plans/revista-express-telas-b-lacunas.md` é de 30/10, antes de U0–U10 e E0–E5. Sobram 7 `admin:` nas telas B (cortes, templates ×2, item da matriz ×2, gabarito) e o vazio da matriz manda rodar comando.
- **Decisão:** Agente A faz S6 → S8 em série (`feat/s6-s8-matriz-downloads`, compose `lac-a`, 8021); Agente B faz S7 (`feat/s7-novo-template`, `lac-b`, 8022); Agente C faz S9 com o modelo mais forte (`feat/s9-usuarios`, `lac-c`, 8023). Integração e Fechamento em `feat/telas-b-ux`. Ajustes ao blueprint: planilhas F1/F2 só na ficha da revista (a lista de revistas saiu no U7); item 17 (botão Admin) já feito em `e4b65f7`; gabarito vira função comum em `servicos/arquivos.py`; download do item em rota GET própria, fora do `com_bloqueio`; Usuários entra como link no cabeçalho ao lado de "Sair", sem mudar o menu de 5 itens (D-199).
- **Motivo:** padrão D-201 (worktrees paralelos); S6 e S8 tocam `urls/ui_matriz.py`, por isso em série. Tempo de parede ~4 h 45 contra ~9 h em série.
- **Descartadas:** executar o blueprint como está (aponta para arquivos que não existem mais); Usuários no menu principal (quebraria a D-199).
- **Arquivos afetados:** `urls/ui_matriz.py`, `urls/ui_templates.py`, `urls/ui_revista.py`, `urls/cortes.py`, `servicos/arquivos.py`, `admin/revista.py`, `admin/usuarios.py`, `nucleo/usuarios.py` (novo), `urls/ui_usuarios.py` (novo), templates em `ui/matriz/`, `ui/templates/lista.html`, `ui/revista/revista.html`, `ui/cortes.html`, `ui/base.html`
- **Status:** ativa

### D-211 — Perfil Admin só vê usuário Impresso: não redefine senha nem altera (2026-11-05)
- **Contexto:** o S9 apontou um furo herdado do admin: o perfil Admin (não superusuário) podia redefinir a senha de um usuário Impresso e entrar como ele, ganhando `marcar_impressa`, o que anula `ADMIN_MARCA_IMPRESSA = False`.
- **Decisão:** `pode_editar` passa a recusar qualquer alvo com grupo fora de `grupos_permitidos(ator)` (Admin e Impresso), para dados, senha, grupo e ativo. Só o superusuário altera esses usuários. Vale para o admin e para a tela B, que usam o mesmo `nucleo/usuarios.py`.
- **Motivo:** decisão do usuário ("fecha o furo"). Uma regra num lugar só fecha as duas telas.
- **Descartadas:** bloquear só a senha — dados e "Desativar" continuariam abertos a um perfil que não pode dar o grupo Impresso; manter (o furo anula a regra do Impresso).
- **Arquivos afetados:** `app/nucleo/usuarios.py`, `nucleo/tests/test_ui_usuarios.py`, `nucleo/tests/test_admin_cadastro.py`, `docs/regras-de-negocio.md`
- **Status:** ativa em parte: ~~Admin não atribui o Impresso nem marca impressa~~ substituído pela D-220 (o título não vale mais; hoje o Admin altera Pedagógica, Mídias e Impresso e só vê outro Admin)

### D-212 — Login e logout próprios das telas B; o login do admin some (2026-11-05)
- **Contexto:** o usuário viu o "Administração do Django" ao sair e ao trocar de perfil: o "Sair" ia ao logout do admin, todas as views mandavam o anônimo para `admin:login`, e o `next=/admin/` deixava a pessoa no índice do admin depois de entrar.
- **Decisão:** `LoginView`/`LogoutView` do Django em `/conta/entrar/` (`entrar`, página `ui/entrar.html` no estilo B) e `/conta/sair/` (`sair`). Settings: `LOGIN_URL = "entrar"`, `LOGIN_REDIRECT_URL = "inicio"`, `LOGOUT_REDIRECT_URL = "entrar"`. As 58 views trocaram `login_url="admin:login"` pelo padrão. `/admin/login/` vira `RedirectView` para `entrar` com a query (o admin continua mandando o anônimo para lá, e o superusuário volta ao `/admin/` com o `next`). O logout do próprio admin também cai no `entrar`, pelo `LOGOUT_REDIRECT_URL`.
- **Motivo:** pedido do usuário: o login do admin não deve aparecer. Um ponto de entrada só, sem tocar no admin.
- **Descartadas:** sobrescrever o template `admin/login.html` (continuaria em `/admin/`, com o `next` levando ao índice do admin); `AdminSite.login` customizado (mais código para o mesmo efeito do redirect).
- **Arquivos afetados:** `sistema/settings.py`, `sistema/urls.py`, `nucleo/urls/conta.py`, `templates/ui/entrar.html` (novo), `static/ui/ui.css`, `templates/ui/base.html`, 15 módulos `urls/*.py`, 14 testes, `e2e/tests/item.spec.ts`, docs de telas
- **Status:** ativa

### D-213 — S17 ações A e C: tag `legado-express` e o sistema antigo apagado (2026-11-05)
- **Contexto:** o usuário autorizou as ações A e C do roteiro `docs/s17-carga-2026.md` e pediu o push da versão atual para a branch `dev`. O bloqueio de apagar o `editor/` (decisão React × Django) já tinha caído com a D-183/D-187.
- **Decisão:** tag anotada `legado-express` em `30b0de3` (último commit com `api/`, `editor/`, `revista/`, `scripts/`), publicada no `origin`. `revista/modelo` movida para `docs/fontes/2025` (PDFs e planilhas SAEGO 2025) e as 4 pastas apagadas (`fa7b748`). No disco, os artefatos ignorados (`node_modules`, `dist`, `__pycache__`) também saíram. O `api/.env` ficou: pode ter segredos do sistema antigo, e só o usuário decide apagar. `contrato/` fica (fora da ação C).
- **Motivo:** pedido do usuário; o código antigo continua recuperável pela tag.
- **Descartadas:** editar a learning de 29/10 que cita os caminhos antigos — learning não se edita; o caminho novo está no README, no CLAUDE.md e no roteiro.
- **Arquivos afetados:** `api/`, `editor/`, `revista/`, `scripts/` (apagados), `docs/fontes/2025/` (movido), `README.md`, `CLAUDE.md`, `docs/s17-carga-2026.md`, `docs/design-revista-impressa.md`, `app/nucleo/tests/test_importacao.py`
- **Status:** ativa

### D-214 — Compose de produção: Gunicorn, Django serve os estáticos, HTTPS atrás do proxy (2026-11-05)
- **Contexto:** pedido de servidor à Infra; o repositório só tinha o compose de dev (`runserver`, DEBUG ligado, código montado de `./app`).
- **Decisão:** `docker-compose.prod.yml` separado: Gunicorn (`-w 3 --timeout 120`), `DEBUG=0`, código na imagem, volume `media` em `/app/media`, `restart: unless-stopped`, `migrate` + `collectstatic` ao subir, porta só em `127.0.0.1:${APP_PORT:-8000}`, variáveis obrigatórias com `:?`. Settings: `STATIC_ROOT`, `CSRF_TRUSTED_ORIGINS` e `SESSION/CSRF_COOKIE_SECURE` por variável. `sistema/urls.py` serve `/static/` com `django.views.static.serve` só sem DEBUG. Modelo `.env.prod.example` na raiz.
- **Motivo:** menor diff que roda sozinho, sem depender da Infra configurar o Nginx para estáticos. Testado numa stack isolada: login, CSRF com origem https, estáticos, admin, host errado 400, path traversal 400.
- **Descartadas:** override do compose de dev (`ports` e `volumes` se somam: o `./app` montado e duas ligações na 8000); whitenoise (dependência nova para o que uma linha faz com poucos usuários internos; vira o caminho se o tráfego crescer); `SECURE_PROXY_SSL_HEADER` (depende de o proxy mandar `X-Forwarded-Proto`; `CSRF_TRUSTED_ORIGINS` não depende); `collectstatic` no build (o settings exige `DJANGO_SECRET_KEY` sem DEBUG).
- **Arquivos afetados:** `docker-compose.prod.yml` (novo), `.env.prod.example` (novo), `app/requirements.txt`, `app/sistema/settings.py`, `app/sistema/urls.py`, `docs/docker.md`, `README.md`, `.gitignore`
- **Status:** ativa

### D-215 — Favicon das telas B: a árvore amarela (2026-11-05 14:15)
- **Contexto:** a aba do navegador mostrava o globo genérico (`<link rel="icon" href="data:,">`).
- **Decisão:** `app/nucleo/static/ui/favicon.png` (240×240, fundo transparente: o branco da imagem original virou alfa, centralizada num quadrado) ligado em `ui/base.html` e `ui/entrar.html`.
- **Motivo:** as duas são as únicas cascas com `<head>` das telas B; PNG serve em todo navegador atual, sem `.ico`.
- **Descartadas:** manter o fundo branco (quadrado branco na aba escura); favicon na página da revista (`revista/index.html`), que é o produto entregue no zip, não o sistema; admin do Django (ferramenta do superusuário).
- **Arquivos afetados:** `app/nucleo/static/ui/favicon.png` (novo), `app/nucleo/templates/ui/base.html`, `app/nucleo/templates/ui/entrar.html`
- **Status:** ativa

### D-216 — "Link de acesso" na tela Usuários; a página de criar senha sai do admin (2026-11-05 15:40)
- **Contexto:** o link para a pessoa definir a própria senha só saía pelo terminal (`criar_usuarios`); dar acesso pela tela exigia digitar e repassar uma senha. A página aberta pelo link usava os templates do admin ("Administração do Django"), contra a D-212.
- **Decisão:** botão "Link de acesso" na linha do usuário (POST `/ui/usuarios/<pk>/link/`, `ui_usuarios_link`), com a regra de "Redefinir senha" (`pode_editar`) e só para ativo. Mostra o link + mensagem pronta para copiar. O endereço vem do cabeçalho `Origin` do POST (já validado pelo CSRF), com `build_absolute_uri` de reserva. Geração do link em `nucleo/usuarios.py::caminho_definir_senha`, usada também pelo `criar_usuarios`. Páginas `ui/senha_definir.html` e `ui/senha_pronto.html` no padrão do login. "Novo usuário" continua pedindo senha (decisão do usuário).
- **Motivo:** ninguém precisa conhecer nem mandar senha; o link vale 3 dias, funciona uma vez e cai quando a senha muda. `build_absolute_uri` sozinho daria `http://` em produção (o proxy faz o HTTPS e não há `SECURE_PROXY_SSL_HEADER`, D-214).
- **Descartadas:** "Novo usuário" nascer sem senha e cair no link (o usuário preferiu manter); link por GET (ficaria em histórico e logs); envio automático por e-mail (não há SMTP configurado); endereço do sistema em variável nova (o `Origin` já traz o certo).
- **Arquivos afetados:** `app/nucleo/urls/ui_usuarios.py`, `app/nucleo/urls/conta.py`, `app/nucleo/usuarios.py`, `app/nucleo/management/commands/criar_usuarios.py`, `app/nucleo/templates/ui/usuarios/{lista,link}.html`, `app/nucleo/templates/ui/senha_{definir,pronto}.html`, `app/nucleo/static/ui/ui.css`, `app/nucleo/static/ui/telas/usuarios.css`, `app/nucleo/tests/test_ui_usuarios.py`, `app/e2e/tests/usuarios.spec.ts`, `docs/regras-de-negocio.md`, `README.md`
- **Status:** ativa

### D-217 — Tela Usuários: ações da linha em botões-ícone e "Mudar" só quando o grupo muda (2026-11-05 16:20)
- **Contexto:** com "Link de acesso" a coluna Ações quebrava em duas linhas (alturas desiguais) e cada linha repetia um botão "Mudar" mesmo sem mudança.
- **Decisão:** Link de acesso, Redefinir senha e Desativar/Ativar viram botões-ícone (lucide `link`, `key-round`, `user-x`/`user-check`) com `aria-label` e `data-dica`, coluna justa à direita. "Mudar" fica com `visibility: hidden` até o seletor sair do grupo atual (`option[selected]` + `:has`, só CSS, dentro de `@supports`). Linha de desativado com usuário e nome em `--muted-foreground`.
- **Motivo:** padrão "Botão-ícone" do design-system.md para ação de linha; uma linha por usuário; o botão aparece quando há o que gravar. `visibility` em vez de `display` mantém a largura da coluna.
- **Descartadas:** gravar o grupo ao mudar o seletor (no Firefox a seta do teclado já dispara `change` e trocaria a permissão por engano); menu "⋯" com as ações (um clique a mais para 3 ações).
- **Arquivos afetados:** `app/nucleo/templates/ui/usuarios/lista.html`, `app/nucleo/static/ui/telas/usuarios.css`
- **Status:** ativa

### D-218 — Excluir usuário pela tela, só quem não tem rastro (2026-11-05 16:50)
- **Contexto:** pedido de o perfil Admin excluir usuários, não só desativar. A D-205 dizia "usuário não é excluído". Quem trabalhou deixa rastro: `history_user` nas tabelas do simple-history (SET_NULL, escondido), versões de template, validações e fotos (PROTECT) e o log do admin (CASCADE).
- **Decisão:** ícone "Excluir" na linha (rota `ui_usuarios_excluir`, GET/POST), com a regra de desativar (`pode_mudar_ativo`: ninguém se exclui; Admin só Pedagógica/Mídias; superusuário invisível = 404). `nucleo/usuarios.py::rastros` conta as relações diretas (menos Bloqueio) e o `history_user` de cada tabela de histórico; com rastro, a página comum `ui/excluir.html` lista o que impede e manda desativar. Sem rastro, confirmação forte digitando o usuário; `excluir` trava a linha (`select_for_update`) e confere de novo. Gate em `auth.change_user`, sem `auth.delete_user`. Escolha do usuário: "só sem rastro".
- **Motivo:** tira da lista quem foi criado por engano ou para teste sem apagar autoria. Reaproveita a página de exclusão (D-205) e não exige migração.
- **Descartadas:** excluir sempre, com autor vazio (perda de auditoria e migração de 3 FKs PROTECT→SET_NULL; o usuário escolheu "só sem rastro"); dar `auth.delete_user` ao Admin (o excluir do admin do Django não conhece a regra de rastro e apagaria o autor do histórico em silêncio); esconder o ícone de quem tem rastro (~20 contagens por linha na lista).
- **Arquivos afetados:** `app/nucleo/usuarios.py`, `app/nucleo/urls/ui_usuarios.py`, `app/nucleo/templates/ui/usuarios/lista.html`, `app/nucleo/tests/test_ui_usuarios.py`, `app/e2e/tests/usuarios.spec.ts`, `app/nucleo/urls/ui_excluir.py` (docstring), `app/nucleo/permissoes.py` (comentário), `docs/regras-de-negocio.md`
- **Status:** ativa. Modifica a D-205 só para usuário.

### D-219 — Comando `tornar_superusuario` (2026-11-05 17:40)
- **Contexto:** o usuário procurou no admin o botão de superusuário para promover alguém; o form de usuário não tem `is_superuser` de propósito (D-142), e o caminho era um `shell -c` à mão.
- **Decisão:** comando `manage.py tornar_superusuario <usuario>...`: liga `is_superuser` e `is_staff` dos usuários informados, numa transação; se um nome não existir, nada muda. Avisa quem já era e quem está desativado.
- **Motivo:** promover a superusuário continua só para quem tem acesso ao servidor (nenhuma tela), mas sem digitar código Python.
- **Descartadas:** campo de superusuário no admin ou na tela Usuários (um Admin poderia se promover, contra a D-142); opção de rebaixar (ninguém pediu; o `shell` resolve até lá).
- **Arquivos afetados:** `app/nucleo/management/commands/tornar_superusuario.py` (novo), `app/nucleo/tests/test_tornar_superusuario.py` (novo), `INFRA.md`, `README.md`, `CLAUDE.md`
- **Status:** ativa

### D-220 — Admin atribui o grupo Impresso e marca impressa (2026-11-05 18:10)
- **Contexto:** o usuário quer que o perfil Admin dê o grupo Impresso. Pela D-211 o Impresso era só do superusuário, porque o Admin que gerencia um Impresso pode entrar como ele (senha, link de acesso, ou criar com senha conhecida e mover) e marcar impressa, anulando `ADMIN_MARCA_IMPRESSA = False`.
- **Decisão:** `GRUPOS_DO_ADMIN` ganha Impresso; o Admin gerencia o Impresso por inteiro (grupo, senha, link, desativar, excluir sem rastro). `ADMIN_MARCA_IMPRESSA = True`, com a migração de dados 0019 (grupo Admin ganha `nucleo.marcar_impressa`); o menu "Impresso" aparece para o Admin. Grupo Admin e outros Admins seguem só com o superusuário. Escolha do usuário entre 3 opções.
- **Motivo:** liberar o Impresso já dava ao Admin o poder de marcar impressa por contorno; dar a permissão às claras deixa o histórico com o nome de quem marcou de fato e não finge uma garantia que não existe.
- **Descartadas:** liberar o Impresso mantendo `ADMIN_MARCA_IMPRESSA = False` (garantia só de fachada); manter como estava e delegar com `tornar_superusuario` (o usuário preferiu liberar); liberar só a atribuição sem gerenciar o Impresso depois (contornável criando o usuário com senha conhecida na Pedagógica e movendo).
- **Arquivos afetados:** `app/nucleo/permissoes.py`, `app/nucleo/usuarios.py`, `app/nucleo/migrations/0019_admin_marca_impressa.py` (nova), `app/nucleo/tests/test_ui_usuarios.py`, `app/nucleo/tests/test_admin_cadastro.py`, `README.md`, `docs/regras-de-negocio.md`
- **Status:** ativa. Substitui a parte da D-211 (e da D-168) que deixava o Impresso só com o superusuário.

### D-221 — "Em edição por … será pulado" ignora o próprio usuário (2026-11-05 19:00)
- **Contexto:** voltando de Cortes/Variáveis/projeto para a Lista (ou Lotes, Validar), o projeto aparecia "Em edição por otavio: será pulado" até recarregar. A página deixada só solta o bloqueio no `pagehide` (sendBeacon), que chega depois do GET da página nova.
- **Decisão:** `lotes.em_edicao(projetos, usuario)` exclui o bloqueio do próprio usuário; Lista, Lotes (matriz e template) e Validar (`itens_validar`) usam essa função.
- **Motivo:** o lote usa `bloqueio.adquirir`, que deixa o mesmo usuário tomar o próprio bloqueio (D-191): esse projeto nunca é pulado, então a etiqueta mentia. Mesma regra de `exclusao._em_edicao`.
- **Descartadas:** liberar o bloqueio no clique do link antes de navegar — corrida continua (beacon assíncrono) e não cobre voltar/abrir em nova aba; `location.reload()` no `pageshow` — não é a causa.
- **Arquivos afetados:** `app/nucleo/lotes.py`, `app/nucleo/urls/ui_projeto.py`, `app/nucleo/urls/ui_lotes.py`, `app/nucleo/urls/painel.py`, `app/nucleo/urls/ui_validar.py`, `app/nucleo/templates/ui/parciais/validar_cartao.html`, testes `test_ui_projetos.py` e `test_ui_validar.py`.
- **Status:** ativa

### D-222 — Página restaurada do bfcache recarrega em vez de renovar o bloqueio (2026-11-05 19:30)
- **Contexto:** abrir uma revista, voltar e avançar mostrava "Você perdeu o bloqueio de edição" até recarregar. Ao voltar, o `pagehide` libera o bloqueio da sessão da aba; ao avançar, o navegador restaura a página do bfcache com a sessão antiga, o `renovar` responde 409 (nunca readquire) e o formulário vira somente leitura.
- **Decisão:** `bloqueio.js`: no `pageshow` com `persisted`, `location.reload()`. O GET novo adquire outro bloqueio (o mesmo usuário assume, D-191) e traz a página atualizada. Vale para as telas B e o change form do admin.
- **Motivo:** a página do bfcache já não tem bloqueio e pode estar velha; recarregar é o que o usuário fazia à mão.
- **Descartadas:** não liberar no `pagehide` quando a página entra no bfcache — o bloqueio ficaria preso 30 s ao sair de verdade; readquirir pelo JS com a sessão antiga — exigiria rota nova e o conteúdo continuaria velho; `Cache-Control: no-store` — o Chrome já restaura páginas no-store do bfcache em alguns casos.
- **Arquivos afetados:** `app/nucleo/static/nucleo/bloqueio.js`, `app/e2e/tests/bfcache.spec.ts` (simula o bfcache: o Playwright o mascara, `notRestoredReasons: "masked"`).
- **Status:** ativa

### D-223 — Diálogo do sistema ao sair por clique com campo não salvo (2026-11-05 20:00)
- **Contexto:** digitar num campo de autosave e sair da página sem sair do campo abria o diálogo nativo do navegador. O usuário quer um diálogo do sistema que obrigue a salvar ou descartar.
- **Decisão:** componente `sairSemSalvar` (`autosave.js`) + `<dialog>` em `_componentes/status_salvo.html` (só para quem grava). Intercepta (captura) mousedown/click em link, gatilho HTMX e botão de outro form quando há campo sujo em foco, falha ou envio pendente. Botões: Salvar e sair (dispara o change; impacto abre o modal; sai no `autosave:salvo`), Descartar e sair (volta o gravado), Continuar editando. Envio já em andamento sem campo sujo: sai sozinho quando termina. O campo fica "segurado" (`segurado`) enquanto o diálogo está aberto; ao continuar, o próximo blur salva.
- **Motivo:** o usuário escolheu os 3 botões e manter o nativo no Voltar. O `beforeunload` não aceita diálogo próprio em Voltar/Avançar, fechar, recarregar ou URL digitada.
- **Descartadas:** truque de entrada falsa no histórico para o Voltar — frágil (o Chrome pula entradas sem gesto, conflita com o hx-push-url das seções, entrada extra no histórico); diálogo no `base.html` — aparecia em páginas somente leitura ("Salvar" no HTML) e só faz sentido onde há autosave.
- **Arquivos afetados:** `app/nucleo/static/ui/componentes/autosave.js`, `app/nucleo/templates/ui/_componentes/status_salvo.html`, `docs/telas/design-system.md`, `app/e2e/tests/autosave.spec.ts`, `app/nucleo/tests/test_ui_matriz.py` (o recorte do cabeçalho parava no `</header>` do diálogo).
- **Status:** ativa

### D-224 — Playwright apaga no fim o que os specs criam no banco de dev (2026-11-05 20:40)
- **Contexto:** cada execução dos specs de Cortes, Projeto, Autosave, Impacto e Revista deixa parceiros "E2E …" (com parceiro-ano, cortes, projeto e revista da cascata), e um spec que para no meio deixa o template "E2E textos …". O usuário pediu que os specs apaguem o que criam.
- **Decisão:** comando `limpar_e2e` (só com DEBUG). Ele apaga os parceiros e templates "E2E …" cujo registro de criação no histórico é do usuário de teste. Parceiro: na ordem do `apagar_ano`. Template: pelo `exclusao.excluir` (regra da tela, D-207); se estiver em uso, fica e o comando avisa. O `globalTeardown` do Playwright (`app/e2e/limpar.ts`) o roda via `docker compose exec` no fim de toda execução; `E2E_COMPOSE_PROJECT` para stack de worktree; falha só avisa.
- **Motivo:** limpar dentro de cada spec não roda quando o spec falha no meio (foi assim que o template de hoje ficou). E o parceiro com projeto não sai pela tela (o parceiro-ano o protege).
- **Descartadas:** `afterAll` em cada spec — não cobre falha no meio e repete a limpeza em 5 arquivos; rota HTTP só com DEBUG — superfície nova no app; apagar por nome sem olhar o autor — apagaria um "E2E …" que uma pessoa criou.
- **Arquivos afetados:** `app/nucleo/management/commands/limpar_e2e.py`, `app/nucleo/tests/test_limpar_e2e.py`, `app/e2e/limpar.ts`, `app/e2e/playwright.config.ts`, comentários em `cortes`, `projeto`, `impacto` e `revista-textos.spec.ts`, `CLAUDE.md`.
- **Status:** ativa

### D-225 — Teste E2E nunca edita revista que não criou (2026-11-05 20:55)
- **Contexto:** specs E2E gravavam em dados reais do banco de dev (variáveis do 1º/último projeto da planilha, revista DEMONSTRAÇÃO) e "voltavam o original no fim". Uma rodada que falhou hoje deixou a regional do SAESE como "E2E".
- **Decisão:** regra do usuário, no `CLAUDE.md` (Conventions): teste E2E nunca edita revista que o próprio teste não criou, nem o que a alimenta (projeto, variáveis, cortes, textos, arquivos, template escolhido). O spec cria o próprio parceiro "E2E …" e edita só ele; o `limpar_e2e` apaga no fim (D-224).
- **Motivo:** "volto o valor no fim" não roda quando o teste falha no meio.
- **Descartadas:** restaurar o valor original no fim do teste — falha no meio deixa o dado real alterado.
- **Arquivos afetados:** `CLAUDE.md`. Specs a corrigir: ver Perguntas em aberto.
- **Status:** ativa

### D-226 — Fluxo git: worktree própria → branch intermediária → usuário mergeia na main (2026-11-06 14:40)
- **Contexto:** o usuário pediu que nada seja modificado direto na worktree da `main`.
- **Decisão:** cada trabalho roda numa worktree irmã (`/home/otavio.peres/dev/revista-express-<tema>`) com branch própria (`feat/…`, `docs/…`), criada a partir de uma branch intermediária `integ/<tema>` (saída da `main`). Merge na intermediária só com testes verdes; o merge de `integ/<tema>` na `main` é do usuário. O `state.md` é editado na worktree, nunca na `main`.
- **Motivo:** o usuário revisa e decide o que entra na `main`; o padrão (`integ/ui-b`, worktrees de agentes) já foi usado com sucesso.
- **Descartadas:** commitar direto na `main` — contraria o pedido; PR por branch direto na `main` sem intermediária — perde o ponto único de teste integrado.
- **Arquivos afetados:** nenhum código; fluxo de trabalho.
- **Status:** ativa

### D-227 — F2 preenchido todo na interface: direção aprovada (2026-11-06 15:20)
- **Contexto:** mapeamento de 06/11 (`docs/superpowers/specs/2026-11-06-f2-na-interface-mapeamento.md`); o usuário respondeu "Concordo".
- **Decisão:** o F2 passa a ser montado pelo sistema sobre um template único de passos canônicos (`abertura`, `descritor` fixos; `habilidades`, `progressao`, `tarefas` desligáveis por projeto); render recomendado = SVG gerado pelo servidor com o svg-tour intocado, confirmado por um protótipo de 1 dia (fase 0) antes das fases 1 a 5. Estimativa aceita: 8 a 12 dias úteis.
- **Motivo:** texto real (acessível, no hash e no "o que mudou"), fim do SVG nomeado à mão no Illustrator e do risco de ordem de camadas da animação.
- **Descartadas:** HTML por blocos com tour próprio — fica como plano B se o protótipo falhar no zoom/minimapa; manter o SVG do design só preenchendo textos — não resolve passos desligáveis nem layout.
- **Arquivos afetados:** futuro: `servicos/f2.py`, `templates/revista/f2.svg`, modelos `DescritorProgressao`/`RevistaF2Descritor`, coluna `Projeto.f2_passos_desligados`; remoção do upload/sanitizador de SVG.
- **Status:** ativa (fase 0 ainda não disparada)

### D-228 — Fase 0 aprovada: F2 em SVG gerado pelo servidor, svg-tour intocado (2026-11-06 17:10)
- **Contexto:** protótipo `example/f2-gerado/` (fase 0 da D-227) com os 5 critérios do plano passando no Chromium; o usuário abriu e disse que a navegação funciona e que só falta caprichar nos estilos.
- **Decisão:** as fases 1 a 5 do mapeamento seguem com SVG gerado pelo servidor (template com `<text>` e `<foreignObject>`, posições calculadas em Python), `svg-tour.js` sem alteração. O visual do protótipo não é referência: o estilo final vem do design (fase 2, com referência de layout por bloco ligado/desligado).
- **Motivo:** zoom/pan, minimapa, texto longo com clamp, passo desligado com reflow e acessibilidade mínima funcionam sem mexer no tour nem adicionar dependência.
- **Descartadas:** plano B (HTML por blocos com tour leve) — não foi preciso; perderia minimapa, zoom e a animação por passo já aprovada em demo.
- **Arquivos afetados:** `example/f2-gerado/` (referência de implementação para `servicos/f2.py` e `templates/revista/f2.svg`).
- **Status:** ativa

### D-229 — Passos do F2 desligados por revista, não por projeto (2026-11-06 17:30)
- **Contexto:** o mapeamento propunha a escolha no projeto (LP e MT juntos); pergunta aberta na D-228.
- **Decisão:** a lista de passos desligados fica na revista (parceiro × ano × componente), não no projeto. Ex.: coluna `Revista.f2_passos_desligados` (lista com CHECK nos nomes canônicos), gravada com o modal de impacto (D-202) e incluída no resolvido (hash, foto, planilha do impresso seguem sozinhos).
- **Motivo:** decisão do usuário em 06/11; LP e MT podem precisar de composições diferentes.
- **Descartadas:** coluna no projeto (proposta do mapeamento) — obrigaria LP e MT à mesma composição.
- **Arquivos afetados:** futuro: `models/revista.py`, migração, tela da revista (ficha), `resolver.py`, `servicos/f2.py`.
- **Status:** ativa

### D-230 — Até dois infográficos F2 por revista (Alfa e Outras Etapas), derivados dos cortes (2026-11-06 18:00)
- **Contexto:** pergunta 1 do levantamento dos campos do docx (`docs/superpowers/specs/2026-11-06-f2-campos-do-docx.md`): o arquivo recebido chama-se "AF_EM" e o mapeamento supunha um infográfico por revista.
- **Decisão:** cada revista (projeto × componente) tem até 2 infográficos no F2: "Avaliação e Currículo – Alfa" e "Avaliação e Currículo – Outras Etapas". Até 4 por projeto (2 LP + 2 MT). A existência é derivada dos cortes, não escolhida: o Alfa existe se e só se o parceiro tem cortes para o 2EF naquele componente (o Alfa é o 2EF); o Outras Etapas existe se e só se há cortes para alguma etapa diferente do 2EF, todas aglutinadas num só. A interface mostra só os que existem. A derivação entra na cascata (`servicos/cascata.py:gravar_cortes`, onde hoje nascem e se arquivam as revistas por componente). Refina a D-229: os passos desligados ficam por infográfico (revista × tipo), não por revista.
- **Motivo:** regra do usuário em 06/11; a composição dos infográficos acompanha as etapas avaliadas.
- **Descartadas:** um infográfico por revista (mapeamento de 06/11) — não cobre o Alfa; escolha manual de quais infográficos a revista tem — a regra é determinística pelos cortes e a escolha abriria incoerência.
- **Arquivos afetados:** futuro: `servicos/cascata.py`, modelo novo (`revista_f2_infografico` com `tipo` CHECK alfa/outras e os passos desligados), `resolver.py`, `html.py`/`empacotar.py` (navegação do F2 com até 2 infográficos), `planilhas.py`, `validacao.py`, seeds do template F2 (um por tipo × componente?).
- **Status:** ativa

### D-231 — Merge na main feito por mim, só depois do "ok" explícito do usuário (2026-11-06 18:20)
- **Contexto:** a D-226 deixava o merge de `integ/<tema>` na `main` exclusivamente com o usuário.
- **Decisão:** posso fazer o merge de `integ/<tema>` na `main` (fast-forward quando possível), mas só depois de confirmar com o usuário e receber o "ok" dele naquela leva; sem "ok", o merge fica com ele. O resto da D-226 continua: trabalho em worktree própria, merge na intermediária só com testes verdes, nada editado direto na `main`.
- **Motivo:** pedido do usuário em 06/11 ("Você tem autorização pra fazer o merge na main. É só confirmar comigo e esperar meu ok").
- **Descartadas:** merge automático ao fim de cada leva — o usuário quer dar o ok a cada vez.
- **Arquivos afetados:** nenhum código; fluxo de trabalho (ajusta a D-226).
- **Status:** ativa

### D-232 — Abertura na web, um modal por item, imagem única do item, fechamento só texto (2026-11-06 18:40)
- **Contexto:** perguntas 2 a 5 de `docs/superpowers/specs/2026-11-06-f2-campos-do-docx.md` §5.
- **Decisão:** (2) os 4 parágrafos da abertura do docx aparecem também na web, como texto corrido antes do infográfico. (3) Tarefas: um item em cada modal, 4 itens, 4 modais (`dlg-tarefa-1..4`), cada um com a imagem do item e os 2 parágrafos de análise daquele item. (4) Item e suporte chegam como uma única imagem montada pelo design: `Tarefa.arquivo` continua com um arquivo só, sem campo de suporte. (5) "Agora é com você" entra só como texto (seção `fechamento`); o link "Acesse aqui" para o template do infográfico fica de fora por enquanto, sem campo de arquivo/URL.
- **Motivo:** respostas do usuário em 06/11.
- **Descartadas:** modal único com os 4 itens — o usuário quer um por item; segundo arquivo de suporte na tarefa — o design monta a imagem; campo para o template do infográfico — ninguém sabe ainda o que é o arquivo.
- **Arquivos afetados:** futuro: seeds do template F2 (`abertura` com os 4 parágrafos, `fechamento`, `dlg-tarefa-N`), `servicos/f2.py`, página do F2.
- **Status:** ativa. Pendência pequena: a abertura (1 parágrafo) e o fechamento (2 parágrafos) comuns do bloco ❹ ficam fora dos modais; proposta: abertura vai no texto do passo `tarefas` do painel do tour, fechamento só no impresso.

### D-233 — Uma página por fascículo e por infográfico, dados do F2 digitados na tela B, animação por último (2026-11-06 19:00)
- **Contexto:** conversa de 06/11 que fechou o plano das fases 1 a 5 do F2 gerado (`~/.claude/plans/planeje-antes-de-fazer-eager-snowflake.md`); fecha a pergunta em aberto "F1 e F2 deixam de ficar na mesma página".
- **Decisão:** (1) cada fascículo e cada infográfico é uma página própria (`f1.html`, `f2-alfa.html`, `f2-outras-etapas.html`); a página inicial (`index.html`) traz capa + sumário com um link por página existente; tudo no mesmo zip. (2) Os dados específicos de cada infográfico (habilidade destacada, textos dos cliques ❶ a ❸, tabela por etapa 1EF–3EM, 4 itens com análise) são digitados na tela B da revista, sem importador. (3) Abertura do bloco de tarefas vai no painel do tour; o fechamento dele, só no impresso (fecha a pendência da D-232). (4) Animação por passo é a última fase (5). Modelo de dados: tabelas `revista_infografico`, `revista_infografico_etapa`, `revista_infografico_item`, com as etapas do referencial numa lista fixa no código (como `Fasciculo`, D-122).
- **Motivo:** uma página por infográfico evita colisão dos ids globais (`#revista`, `#dados-tour`, `dlg-*`) e deixa `f2-init.js` e `svg-tour.js` como estão; digitar na tela segue a regra "toda função do back tem controle na tela B" (D-189); a animação depende do SVG final.
- **Descartadas:** F1 e F2 na mesma página com os dois infográficos (ids colidem); importador de planilha do referencial (não há planilha estruturada; a Pedagógica digita); etapas do referencial na tabela `Etapa` do ano (o ano letivo só cadastra as etapas avaliadas, o referencial cobre 12).
- **Arquivos afetados:** fase 1: `models/revista.py`, migrações 0020+, `servicos/cascata.py`, `permissoes.py`, `servicos/exclusao.py`; fases 2 a 5: ver o plano.
- **Status:** ativa

### ~~D-234 — Tarefa usada por item de infográfico impede a exclusão e a reimportação da matriz (2026-11-06 19:10)~~ ~~substituída por D-235~~
- **Contexto:** o item do infográfico aponta para `Tarefa` com `PROTECT` (plano, fase 1). A reimportação da matriz (`servicos/importar_matriz.py`) apaga todos os descritores das MECs reimportadas, e com eles as tarefas; a exclusão com confirmação forte (D-181, `matriz.excluir`) chama `delete()` direto. Os dois quebrariam com `ProtectedError` (erro 500) assim que um item fosse preenchido.
- **Decisão:** manter `PROTECT` e transformar o uso em recusa explicada: a reimportação levanta `ImportacaoRecusada` listando os infográficos que usam tarefas das MECs reimportadas; a exclusão de tarefa ou descritor (tela B e admin) recusa com mensagem, sem apagar nada. A exclusão de matriz (D-205) mostra os itens como "revistas" em uso (`exclusao.GRUPO`).
- **Motivo:** mesmo princípio da D-205 ("exclui só o que nada usa"); trocar a tarefa de um item muda o conteúdo da revista, e isso tem de ser um ato de quem edita o infográfico, não efeito colateral da matriz.
- **Descartadas:** `SET_NULL` no item — a reimportação esvaziaria itens em silêncio (o hash mudaria e o "Validado" cairia sem explicação); remapear o item para a tarefa nova de mesmo código e faixa — código a mais sem pedido; fica como evolução se a recusa atrapalhar a equipe.
- **Arquivos afetados:** `servicos/importar_matriz.py`, `matriz.py`, `urls/ui_matriz.py`, `admin/matriz.py`, `servicos/exclusao.py`.
- **Status:** ~~substituída por D-235~~ (premissa errada: o item não usa tarefa da matriz)

### D-235 — Item do infográfico não é tarefa da matriz: tem descritor, etapa, imagem e análise próprios (2026-11-06 20:00)
- **Contexto:** o plano e a D-234 supunham `RevistaInfograficoItem.tarefa` → `Tarefa` da matriz (a imagem viria de `Tarefa.arquivo`). O usuário corrigiu em 06/11: "Nenhum item do infográfico usa a matriz de tarefas". O docx mostra cada item como "(4,1) D05 – 2º ano do Ensino Fundamental", com imagem `P00208914` (item + suporte numa imagem só, D-232) e 2 parágrafos de análise.
- **Decisão:** o item guarda o que é dele: `etapa` (lista fixa `EtapaReferencial`, vazio permitido), `descritor` (código na matriz de referência, texto, ex. `D05`), `imagem` + `imagem_sha256` (caminho no storage, juntos como a capa, D-118), `texto_alternativo` (até 1000, como a tarefa, D-180) e `analise`. Sai a FK para `Tarefa`. Substitui D-234: sem FK, exclusão e reimportação da matriz não são afetadas. Como a branch não foi mergeada e nenhum banco aplicou a 0020, a própria 0020 é corrigida (sem migração de ida e volta). As etapas ganham rótulos por extenso ("2º ano do Ensino Fundamental", "3ª série do Ensino Médio").
- **Motivo:** correção do usuário; o rótulo do item no docx é exatamente descritor + etapa.
- **Descartadas:** FK para `Tarefa` (premissa errada); guardar o código do item (`P00208914`) — o nome do arquivo já o traz e ninguém o exibe; entra quando alguém pedir.
- **Arquivos afetados:** `models/revista.py`, `migrations/0020_infograficos.py`, `servicos/exclusao.py` (GRUPO), testes de constraints e exclusão.
- **Status:** ativa

### ~~D-236 — A fase 1 do F2 entra na main só junto com a fase 2 (2026-11-06 21:00)~~ ~~substituída por D-237~~
- **Contexto:** fase 1 (dados e cascata dos infográficos) pronta e mergeada em `integ/f2-gerado` (`70989fc`, 833 OK); pela D-231 o merge na `main` espera o ok do usuário.
- **Decisão:** `integ/f2-gerado` só entra na `main` junto com a fase 2 (render e páginas separadas). As fases seguintes continuam saindo de `integ/f2-gerado`.
- **Motivo:** decisão do usuário em 06/11; a fase 1 sozinha não muda nada visível, e a fase 2 derruba o "Validado" de toda revista uma vez — melhor um deploy só, combinado com a validação da carga 2026.
- **Descartadas:** merge na `main` agora — duas entregas sem ganho visível na primeira.
- **Arquivos afetados:** nenhum código; fluxo de trabalho.
- **Status:** ~~substituída por D-237~~ (premissa errada: a fase 2 sozinha trava o "Validado" e o zip)

### D-237 — `integ/f2-gerado` entra na main só com as fases 1 a 3 (2026-11-09 10:30)
- **Contexto:** a D-236 supunha que a fase 2 sozinha podia ir para produção. A fase 2 cria pendências por infográfico (habilidade vazia, passo ligado sem dado, item sem imagem); `servicos/validacao.py:43` recusa o "Validado" e `servicos/empacotar.py:101` recusa o zip com pendência, e a tela que as resolve só chega na fase 3.
- **Decisão:** a `integ/f2-gerado` só entra na `main` junto com as fases 1, 2 e 3. Substitui a D-236.
- **Motivo:** com só a fase 2 em produção, nenhuma revista poderia ser validada nem baixada. Opção A escolhida pelo usuário em 09/11; não pede código e mantém um único dia em que o "Validado" cai.
- **Descartadas:** (B) a fase 2 sem pendências novas, que entrariam na fase 3 — revistas com infográfico vazio poderiam ser validadas.
- **Arquivos afetados:** nenhum código; fluxo de trabalho.
- **Status:** ~~ativa~~ substituída por D-249 no escopo do merge (deploy das fases 1 a 4 juntas); as citações "D-237" no código continuam marcando a entrada do infográfico no resolvido e no hash.

### D-238 — Troca dos ids do template F2 sai da fase 3 e entra na fase 2 (2026-11-09 10:40)
- **Contexto:** o render da fase 2 precisa saber qual seção alimenta cada passo; o template tinha ids antigos (`passo1..4`, `dlg-p2`, `dlg-p3`, `dlg-p4-iN`, com títulos trocados), e o plano deixava a troca para a fase 3.
- **Decisão:** a fase 2 troca o F2 para 8 seções fixas e obrigatórias, como o F1: `abertura`, `passo-descritor`, `passo-habilidades`, `passo-progressao`, `passo-tarefas`, `dlg-descritor`, `tarefas-fechamento`, `fechamento`. Seeds reescritos a partir do docx; migração 0023 grava uma versão nova de cada template F2 (só inserção, D-207) e leva as cópias `dlg-p2`/`dlg-p3` para `texto_progressao`/`texto_habilidades` do infográfico.
- **Motivo:** escolha do usuário em 09/11; como as fases 1 a 3 vão juntas para a `main` (D-237), não há por que escrever um mapa provisório dos ids antigos e apagá-lo na fase 3.
- **Descartadas:** manter a troca na fase 3 com um mapa provisório `passo1→descritor … passo4→tarefas` — código e testes jogados fora.
- **Arquivos afetados:** `texto.py`, `templates_texto.py`, `templates_seed/2026/f2-*.hbs`, `migrations/0023_template_f2_secoes.py`.
- **Status:** ativa

### D-239 — O desenho do F2 é o SVG em uso; Alfa e Outras Etapas têm a mesma estrutura (2026-11-09 10:50)
- **Contexto:** a D-228 dizia que o visual do protótipo não era referência e que o estilo final viria do design; havia ainda a pergunta "o Alfa tem a mesma estrutura do Outras Etapas?".
- **Decisão:** o desenho final é o do SVG em uso (`app/nucleo/tests/fixtures/f2-lp.svg`, Illustrator, viewBox `0 0 1190.6 793.7`). A fase 2 o porta bloco a bloco para `templates/revista/f2.svg` (formas, cores e traços como estão; texto em curva vira `<text>`/`foreignObject`). Alfa e Outras Etapas usam o mesmo desenho; mudam só os textos e os itens do último passo.
- **Motivo:** o usuário conferiu com a equipe em 09/11.
- **Descartadas:** esperar uma referência nova do design — não virá; um layout por tipo de infográfico — a estrutura é a mesma.
- **Arquivos afetados:** futuro: `templates/revista/f2.svg`, `servicos/f2.py`.
- **Status:** ativa

### D-240 — Fechamento do bloco de tarefas no template só com o texto genérico (2026-11-09 12:30)
- **Contexto:** o plano da fase 2 mandava as linhas 150-158 do docx para a seção `tarefas-fechamento`; as linhas 150-154 falam do item (4,4) da 3ª série do EM (P121137H6).
- **Decisão:** `tarefas-fechamento` leva só os 2 parágrafos genéricos (md 156 e 158). O texto sobre cada item é da revista: vai na `analise` do item (tela da fase 3).
- **Motivo:** confirmado pelo usuário em 09/11 — o conjunto de itens muda com o descritor de cada revista.
- **Descartadas:** as linhas 150-158 inteiras no template — o trecho do item (4,4) apareceria igual em toda revista.
- **Arquivos afetados:** `templates_seed/2026/f2-*.hbs`, `migrations/0023_template_f2_secoes.py`.
- **Status:** ativa

### D-241 — Clique ❹ abre só a abertura do bloco de tarefas, num botão próprio (2026-11-09 14:00)
- **Contexto:** o usuário viu o PNG da tarefa 2 e pediu o botão amarelo + sob "Tarefas por nível de complexidade", como nos passos anteriores. O texto do clique ❹ no docx é só o parágrafo "Aqui, apresentamos alguns itens exemplares…" (md 112); cada item é a imagem montada + o texto que a segue.
- **Decisão:** nova seção fixa `dlg-tarefas` no template F2 (9 seções) com a abertura do ❹, aberta pelo botão `f2-btn-action-tarefas` sob o título do bloco. `passo-tarefas` fica só com o texto curto do tour. Os + de cada item continuam abrindo imagem + análise (D-232, D-235). Não há botão sob "Itens". Substitui a parte da D-233 que punha a abertura do bloco de tarefas no painel do tour.
- **Motivo:** decisão do usuário em 09/11; segue o padrão dos outros passos (botão sob o título abre o texto do clique).
- **Descartadas:** abertura no painel do tour (D-233) — o usuário quer o botão; botão sob "Itens" — confusão do usuário, desfeita por ele; um modal único com abertura + 4 itens + fechamento (como no docx) — mantido um modal por item (D-232).
- **Arquivos afetados:** `texto.py`, `templates_seed/2026/f2-*.hbs`, `migrations/0023_template_f2_secoes.py`, `templates/revista/f2.svg`, `servicos/f2.py`.
- **Status:** ativa

### D-242 — Lacunas do brief da tarefa 3 fechadas antes de implementar (2026-11-10 10:00)
- **Contexto:** ao planejar a tarefa 3 (gerador `servicos/f2.py`), o brief não batia com o código: o `f2.svg` usa `componente`, que o infográfico da T4 não traz; `html.py` importaria `f2` e vice-versa; os conectores (`linhas`) não tinham regra; a "progressão sem linha" do protótipo não existe no `f2.svg`; o resolvido só traz as etapas gravadas, e o desenho tem 12.
- **Decisão:** `gerar(infografico, secoes, base_imagens, componente)`; `ROTULO_TOUR` e `_texto` passam de `html.py` para `f2.py` (`texto_puro`); `CONECTORES` com os 3 pontos do desenho, e os pontos iniciais com o y do 1º andam com o bloco; tabela e progressão sempre com as 12 etapas de `EtapaReferencial`, completando as vazias em cinza; linha vazia do topo vira célula vazia própria; título do modal do item por `format_html`; `analise` chega renderizada (T4).
- **Motivo:** menor diff que fecha cada lacuna sem mexer no `f2.svg` aprovado; o import em uma direção só evita ciclo quando a T5 importar `f2`.
- **Descartadas:** `componente` dentro do dict do infográfico (repetiria o mesmo valor em todo infográfico e mexeria no hash); conectores recalculados por geometria (só a progressão se move); manter a regra "menos de 2 marcas" (não há polilinha no desenho).
- **Arquivos afetados:** `servicos/f2.py`, `servicos/html.py`, `tests/test_f2.py`, briefs das tarefas 3, 4 e 5.
- **Status:** ativa

### D-243 — Conselho da tarefa 4: passo Tarefas desligado tira os itens do resolvido (2026-11-10 12:30)
- **Contexto:** depois da revisão da tarefa 4 (texto de passo desligado não conta variável, 4e16fae), o /conselho (5 analistas + debate) achou o mesmo defeito na análise dos itens: com o passo Tarefas desligado, `renderizado(i.analise)` ainda contava variáveis e uma variável vazia num item invisível travava o "Validado".
- **Decisão:** com `tarefas` em `passos_desligados`, `itens` sai `[]` do resolvido (O3). Veredito unânime na rodada final (5×0); na rodada 1 o placar foi O2 3 × O3 2.
- **Motivo:** a regra "passo desligado é invisível" fica num lugar só (o resolver), igual ao que `f2.gerar` mostra; pelo plano da T6 o zip copia e exige as imagens dos itens do resolvido, então com a O2 uma imagem invisível sumida barraria o zip ou a T6 repetiria o filtro. O banco continua guardando os itens.
- **Descartadas:** O1 manter (deixa o Validado travar por texto invisível); O2 só esvaziar a análise (imagem invisível continuaria no hash e no zip); O4 como opção de voto (sem voto). A O4 entrou como acréscimo, a pedido do usuário em 10/11: `docs/regras-de-negocio.md` (pendência `infografico`), `docs/modelo-er.md` (hash com `imagem_sha256`) e marca `ponytail:` na ponte de `empacotar.py`.
- **Pendência registrada para a T6:** `empacotar.py:110` faz `default_storage.exists(revista.svg_f2)` com `svg_f2=None` desde que a pendência `svg` saiu → 500 no zip entre T4 e T6.
- **Arquivos afetados:** `servicos/resolver.py`, `servicos/empacotar.py` (comentário), `tests/test_resolver.py`, `docs/regras-de-negocio.md`, `docs/modelo-er.md`; dossiê, mesa, análises e réplicas em `.superpowers/sdd/2026-11-09-f2-fase-2/conselho-t4-*.md`.
- **Status:** ativa

### D-244 — Tarefa 5 também ajusta os chamadores de contexto_pagina (2026-11-10 14:00)
- **Contexto:** a tarefa 5 muda a assinatura de `contexto_pagina` e divide o `index.html`, mas os únicos chamadores (preview e zip) só mudariam na tarefa 6: a tarefa 5 fecharia com a suíte vermelha.
- **Decisão:** a tarefa 5 inclui as rotas `preview`, `preview_f1`, `preview_f2`, a gravação das páginas no zip e os gabaritos da pasta `e2e/fixtures/pagina/`. A tarefa 6 fica com as imagens dos itens (rota e cópia), o `zip_foto` por item e a remoção das checagens de SVG. Junto: `f2.gerar` usa só o nome do arquivo da imagem no `src` (no banco é `infograficos/<x>`).
- **Motivo:** escolha do usuário em 10/11; todo chamador da função que muda, muda junto, e cada tarefa fecha com a suíte verde.
- **Descartadas:** juntar T5 e T6 numa tarefa só (um ciclo de revisão de ~2 dias); seguir o plano (suíte vermelha entre T5 e T6).
- **Arquivos afetados:** `servicos/html.py`, `templates/revista/*`, `urls/preview.py`, `servicos/empacotar.py`, `servicos/f2.py`, briefs das tarefas 5 e 6.
- **Status:** ativa

### D-245 — Tarefa 6: imagens do zip vêm do caminho atual, conferidas pelo sha da foto (2026-11-10 15:30)
- **Contexto:** o zip da revista arquivada sai da foto, mas os arquivos são os atuais; o brief não dizia de onde copiar a imagem do item nem como tratar dois itens com o mesmo nome de arquivo.
- **Decisão:** o `src` usa o nome da foto; os bytes vêm do caminho atual do item, achado por (tipo, posição); sha da foto ≠ atual (ou item sumido) = `zip_foto` por item, com mensagem própria; a capa ganha mensagem própria. Mesmo nome com caminhos diferentes = `zip_arquivo`. A rota `preview_imagem_infografico` serve só imagem de item da própria revista (png/jpg/webp). O zip deixa de ler o SVG.
- **Motivo:** mesmo padrão da capa (compara o sha, copia o atual); reenviar a mesma imagem (caminho novo com uuid) não quebra o zip; a colisão evitaria uma imagem cobrindo outra.
- **Descartadas:** copiar do caminho da foto (o arquivo antigo é apagado ao trocar, e o zip quebraria mesmo com conteúdo igual); validar o nome por regex como nos itens do F1 (o `src` já sai escapado por `format_html` e o upload da fase 3 grava com uuid).
- **Arquivos afetados:** `servicos/empacotar.py`, `urls/preview.py`, `tests/test_empacotar.py`, `tests/test_preview.py`, `e2e/fixtures/revista.zip`, brief da tarefa 6.
- **Status:** ativa

### D-247 — Tarefa 7: specs E2E por página e situação "5 de 6" até a fase 3 (2026-11-10 18:00)
- **Contexto:** desde a T5 a revista tem 4 páginas e os specs `pagina`, `zip` e `item` procuram F1 e F2 numa página só; desde a T4 a pendência `infografico` deixa a situação em "5 de 6 prontos", e `helpers.ts:revistaPropria` espera "6 de 6".
- **Decisão:** `pagina.spec.ts` serve a pasta `fixtures/pagina/` por `page.route` e cobre sumário, F1 e o F2 Outras Etapas (tour completo, `dlg-habilidades`, `dlg-tarefa-1` com imagem, sem erro de console); `zip.spec.ts` faz o mesmo percurso por `file://` a partir do `index.html`; `item.spec.ts` abre `/preview/<id>/f1/`; `revistaPropria` espera "5 de 6" com `ponytail:` até a fase 3; sai o teste "Ctrl+→ dentro do F2". O Playwright inteiro roda numa stack isolada e a lista dos vermelhos esperados vai para este arquivo.
- **Motivo:** cada página tem seu percurso; o zip é o que o usuário final abre, então ele repete o percurso por `file://`.
- **Descartadas:** manter o teste "Ctrl+→" (F1 e F2 não dividem mais a página); preencher o infográfico no `revistaPropria` (a tela de edição só existe na fase 3).
- **Arquivos afetados:** `app/e2e/tests/pagina.spec.ts`, `zip.spec.ts`, `item.spec.ts`, `helpers.ts`, brief da tarefa 7.
- **Status:** ativa

### D-248 — Gabaritos da revista com os dados reais do docx do infográfico (2026-11-10 19:30)
- **Contexto:** na conferência no Firefox, o usuário achou as tabelas do F2 com pouca informação: o helper `dois_infograficos` usava dados curtos (só 5EF "I" e 9EF "A"), decididos na T5 porque o container só monta `./app`.
- **Decisão:** os dados do docx real "AVALIAÇÃO E CURRÍCULO_LP_2026_AF_EM" (descritor D05, 12 marcas I I A A C A A A A A A A, 5 habilidades com as mesclagens 1-2EF, 3-5EF, 6-7EF, 8-9EF e 1-3EM, textos de clique ❶ a ❸, 4 itens com as análises do ❹) ficam em `app/nucleo/tests/dados/infografico-docx.json`; `dois_infograficos` lê dele; gabaritos (páginas e zip) regerados. Fora, sem campo no modelo: abertura, códigos dos itens, abertura e fechamento do ❹, legenda e "Agora é com você".
- **Motivo:** escolha do usuário em 10/11; a conferência visual com dado real mostra a tabela como a revista vai sair.
- **Descartadas:** `example/f2-gerado/dados.json` (diverge do docx: 3EM "R" e textos das habilidades com explicação pedagógica misturada); deixar os dados curtos até a fase 3.
- **Arquivos afetados:** `app/nucleo/tests/dados/infografico-docx.json`, `app/nucleo/tests/test_preview.py`, `app/e2e/tests/pagina.spec.ts`, `zip.spec.ts`, `app/e2e/fixtures/pagina/*.html`, `revista.zip`.
- **Status:** ativa. Limite: todo texto real cabe na caixa, então o gabarito não prova o corte com reticências do `foreignObject` (falta um caso de texto maior que a caixa).

### D-249 — `integ/f2-gerado` entra na main só com as fases 1 a 4 (2026-11-10 21:00)
- **Contexto:** a D-237 levava as fases 1 a 3 juntas para a `main`, mas a planilha e o "o que mudou" do impresso só ganham os infográficos na fase 4; sem ela, o time do impresso não vê o conteúdo novo do F2.
- **Decisão:** a `integ/f2-gerado` só entra na `main` depois da fase 4 (fases 1 a 4 juntas). Substitui a D-237 só no escopo do merge: as citações "D-237" no código (`resolver.py`, `html.py`, `admin/revista.py`, `regras-de-negocio.md`) continuam marcando a entrada do infográfico no resolvido e no hash, no lugar do SVG.
- **Motivo:** escolha do usuário em 10/11 (pergunta do planejamento da fase 3).
- **Descartadas:** puxar a parte do impresso da fase 4 para a 3 (fase 3 maior, deploy mais cedo).
- **Arquivos afetados:** `state.md`, `docs/superpowers/plans/2026-11-09-f2-fase-2.md`.
- **Status:** ativa

### D-250 — Conselho da fase 2: pendência do texto do clique e registro do deploy (2026-11-10 21:10)
- **Contexto:** conselho de 5 analistas (Mínimo, Justificativa, Alternativas, Falha, Futuro leitor) sobre as decisões D-237 a D-248, pedido pelo usuário.
- **Decisão:** veredito O4, unânime na rodada final (5×0; 3×2 O4×O5 na 1ª): registrar a D-249; nova falta da pendência `infografico` "o passo Habilidades/Progressão está ligado e falta o texto do clique" (`resolver.pendencias`), porque o `+` abriria um modal só com o título e passaria no "Validado" (o plano mestre pede "passo ligado sem dado" e a D-233 conta os textos ❶ a ❸ como dado); registrar a D-251.
- **Motivo:** o modal vazio sai na web e no zip no deploy; a 0023 deixa ❷ e ❸ vazios nas revistas sem cópia dlg-p2/dlg-p3.
- **Descartadas:** O5 (tirar já o parágrafo 156 de `tarefas-fechamento` e apagar as redundâncias `empacotar.py` `zip_pagina` e `f2.py:110/:118`) — só pesam no impresso (fase 4) ou são limpeza; ficaram como pergunta e pendência. O7 (preview com as URLs do zip) — recomendação para a fase 3.
- **Arquivos afetados:** `servicos/resolver.py`, `tests/test_resolver.py` (`test_passo_ligado_sem_texto_do_clique`; `preencher_infograficos` com os textos), `docs/regras-de-negocio.md`.
- **Status:** ativa

### D-251 — Revista arquivada com foto antiga sai sem F2 no preview e no zip (2026-11-10 21:15)
- **Contexto:** a foto de arquivamento de antes da D-237 não tem `infograficos`; a regra antiga (D-117) dizia que a arquivada "congela, mantendo SVG, capa, cópias e fotos". Levantado pela lente Falha do conselho da fase 2.
- **Decisão:** essa revista sai só com sumário e F1 no preview e no zip, sem página F2 (`html.paginas`, `empacotar._imagens` com `.get("infograficos", [])`). Decisão registrada do que a fase 2 já fazia (plano da fase 2, linha 51).
- **Motivo:** a foto não guarda o infográfico, e montar o F2 da foto antiga exigiria manter o render do SVG enviado, que sai na fase 4.
- **Descartadas:** manter o SVG antigo até a fase 4 para essas revistas (dois renders do F2 em paralelo).
- **Arquivos afetados:** `servicos/html.py`, `servicos/empacotar.py`.
- **Status:** ativa

### D-252 — Achados da auditoria: o que entra na fase 3 e o que fica para depois (2026-11-10 22:00)
- **Contexto:** auditoria do código de 10/11 (só leitura) com 11 achados, consolidada com a revisão e o conselho da fase 2 num relatório de 40 achados por parte do código (https://claude.ai/artifact/2uF1hAkiZ5phNy1eqEaHYj).
- **Decisão:** a T1 da fase 3 separa `pendencias_f1`/`pendencias_f2` (`servicos/pendencias.py`, `ids_faltando` fora do ciclo) e leva junto os itens rápidos: falha explícita em `planilhas.py:97`, `EtapaReferencial.EF2` em `cascata.py`, `assert` das 12 etapas em `f2.py:98` e os comentários de `empacotar.py:150`, `cortes.py:132` e `settings.py:105`. Ficam para depois: constante `ANO_DEMO` no E2E, helper `pode(user, modelo, acao)`, hash do resolvido persistido e painel paginado (antes de ~50 revistas ativas).
- **Motivo:** recomendação aceita pelo usuário em 10/11 ("Gostei da sua recomendação"); a fase 3 vai mexer nas pendências, e os itens rápidos custam ~1 h.
- **Descartadas:** fazer tudo do "fazer agora" antes da fase 3 (~8 h fora do caminho da fase).
- **Arquivos afetados:** plano da fase 3; na T1, `servicos/resolver.py`, `servicos/pendencias.py` (novo), `planilhas.py`, `cascata.py`, `f2.py`, `empacotar.py`, `cortes.py`, `sistema/settings.py`.
### D-233 — Docs alinhados ao código de 06/11, F2 novo registrado como planejado (2026-11-09 10:00)
- **Contexto:** pedido do usuário: atualizar toda a documentação para a versão atual. Os docs foram alinhados em 05/11 11:30; depois entraram S6–S9 das telas B e D-209 a D-232, várias sem menção em doc nenhum.
- **Decisão:** worktree `revista-express-docs`, branch `docs/atualizacao-2026-11-09` a partir de `integ/docs-atualizacao`; 3 subagentes com arquivos separados (raiz + docker/e2e; telas e fichas; regras, ER e variáveis). O F2 gerado (D-227 a D-232) entra nos docs só como "decidido, não implementado", com link para as specs. `DESIGN.md` ganha o aviso de "editor antigo", como o `PRODUCT.md`. `inventario.md`, `rascunho-ui.md`, `contrato.md` e `s17-*.proposto.md` ficam como estão: já são marcados como históricos.
- **Motivo:** o código é a fonte da verdade; descrever como vigente o F2 novo enganaria quem lê.
- **Descartadas:** reescrever os docs históricos — perde o retrato da época; apagar `DESIGN.md` — a skill impeccable o lê, e o aviso basta.
- **Arquivos afetados:** `CLAUDE.md`, `README.md`, `INFRA.md`, `DESIGN.md`, `docs/docker.md`, `docs/e2e.md`, `docs/telas/**`, `docs/regras-de-negocio.md`, `docs/modelo-er.md`, `docs/variaveis.md`
- **Status:** ativa

### D-234 — Respostas às 5 perguntas da D-233: `workers: 1` fica, `.env.example` completo, comentários corrigidos (2026-11-09 11:00)
- **Contexto:** 5 perguntas abertas na revisão dos docs (D-233).
- **Decisão:** (1) `workers: 1` fica, com o motivo atual no `playwright.config.ts`: mesmo usuário em todos os specs (D-191) e o `anos.spec` abre e apaga 2027, o ano mais recente que as rotas `_inicio` e `/` mostrariam a outro spec no meio. (2) `app/.env.example` ganha `APP_PORT`, `APP_BIND` e `COMPOSE_PROJECT_NAME`. (3) Sai do `CLAUDE.md` a seção "Who is you?" (texto da skill frontend-design colado). (4) Comentários do login do admin (`usuarios.py`, `helpers.ts::entrar`) e do `limpar_e2e` (`playwright.config.ts`) atualizados. (5) Comentário do `Bloqueio` diz CASCADE do Django e NO ACTION no banco.
- **Motivo:** respostas do usuário (2 a 5); a 1 foi recomendação minha, pedida por ele.
- **Descartadas:** `workers: 2` — o ano 2027 do `anos.spec` vaza para os outros specs e a suíte fica instável sem ganho medido.
- **Arquivos afetados:** `CLAUDE.md`, `app/.env.example`, `app/e2e/playwright.config.ts`, `app/e2e/tests/helpers.ts`, `app/nucleo/usuarios.py`, `app/nucleo/models/controle.py`, `docs/e2e.md`, `docs/regras-de-negocio.md`
- **Status:** ativa. Achado à parte: `entrar()` confere o sucesso com `not.toHaveURL(/\/admin\/login\//)`, mas depois da D-212 o login falho fica em `/conta/entrar/`, então a conferência sempre passa.

### D-246 — Banco sem ano: "Abrir ano" cria o primeiro ano vazio (2026-11-10 17:00)
- **Contexto:** com o banco vazio, `abrir_ano` recusava ("nenhum ano anterior a X para copiar"), e a tela de anos nem mostrava o formulário; o 1º ano só nascia pela linha de comando (`carregar_cadastros`). O usuário apontou que não dá para abrir o primeiro ano.
- **Decisão:** sem ano nenhum, `abrir_ano(ano)` cria só a linha do ano, sem cópia, e devolve `(novo, None)`; qualquer número de ano é aceito (não há "seguinte" sem anterior). A tela de anos mostra o formulário também sem ano; mensagem comum `VAZIO` ("Ano X aberto vazio: cadastre etapas, componentes e cores.") na tela, no admin e no comando. O ano seguinte copia desse normalmente. `carregar_cadastros` continua valendo. Substitui, em parte, D-148.
- **Motivo:** escolha do usuário em 10/11 ("Vazio").
- **Descartadas:** nascer com os cadastros padrão do `carregar_cadastros` (4 etapas, LP/MT, 5 cores; recomendada, recusada pelo usuário); manter a recusa (o 1º ano só pela linha de comando).
- **Arquivos afetados:** `servicos/abrir_ano.py`, `urls/ui_anos.py`, `admin/cadastro.py`, `management/commands/abrir_ano.py`, `templates/ui/anos/anos.html`, `tests/test_abrir_ano.py`, `tests/test_ui_anos.py`, `docs/regras-de-negocio.md`.
- **Status:** ativa. Limite: a tela B só edita cores existentes (`ui_anos.py`, paleta); as 5 cores do 1º ano vazio só se criam pelo admin ou pelo `carregar_cadastros`. Ano digitado errado no 1º ano (ex.: 20266) sai pela exclusão de ano.

### D-253 — Tarefas num kanban.md, fora do state.md (2026-11-10 15:30)
- **Contexto:** o usuário pediu uma skill que mantenha, em toda conversa, um quadro Backlog · Doing · Review · Done de todas as tarefas. O "Plano" do `state.md` duplicaria a lista e estava parado em S17 "← agora", sem as fases do F2.
- **Decisão:** `kanban.md` na raiz é a lista única; o "Plano" do `state.md` só aponta para ele. Skill global `~/.claude/skills/kanban` (regras) + `kanban.py` (stdlib) que gera o `kanban.html` (fora do git) + hooks globais `SessionStart` (põe o quadro no contexto) e `PostToolUse` Write/Edit (regera o HTML). Doing com no máximo 1 card; Review = espera o usuário; Done = aprovado ou mergeado. Número D-253 porque D-247 a D-252 já estão em uso na `integ/f2-gerado`.
- **Motivo:** escolhas do usuário (markdown + HTML, todos os projetos, kanban vira a lista). Skill sozinha não roda em toda sessão; o hook garante. Vai para a `main` por PR próprio, saído da `main`, para não carregar o F2 (D-249).
- **Descartadas:** Artifact no claude.ai com banco (fora do repositório, depende do claude.ai); manter Plano e kanban juntos (as duas listas divergiriam); arrastar cards no HTML (exigiria servidor gravando o `.md`).
- **Arquivos afetados:** `kanban.md`, `.gitignore`, `state.md`; fora do repo: `~/.claude/skills/kanban/`, `~/.claude/settings.json`, `~/.claude/CLAUDE.md`.
- **Status:** ativa

## Perguntas em aberto
- [x] (D-252) (10/11, auditoria do código) Quais itens do "fazer agora" entram e onde: `planilhas.py:97` falha explícita para componente sem layout; enum no lugar de "2EF" em `cascata.py` e assert nas 12 etapas de `f2.py`; constante `ANO_DEMO` no E2E (138 ocorrências de 2026); separar `pendencias_f1`/`pendencias_f2`; helper `pode(user, modelo, acao)` (48 checagens fora de `permissoes.py`). Depois: hash do resolvido persistido (o resolver roda por revista no painel, impacto, matriz, paleta e impresso; teto ~50 revistas) e painel paginado com poda de fotos — depende de: Otavio
- [ ] (10/11, conselho da fase 2) O 1º parágrafo de `tarefas-fechamento` (seed `f2-lp.hbs`/`f2-mt.hbs` e migração 0023) fala dos itens do D05 de LP (tirinha, charge), contra o motivo da D-240. Tirar do seed e da 0023 antes da fase 4 (quando o impresso lê a seção)? — depende de: Otavio
- [x] (D-249: deploy das fases 1 a 4 juntas) (09/11, plano da fase 2) A planilha e o "o que mudou" do impresso só ganham os infográficos na fase 4. Se as fases 1 a 3 forem para a `main` sem a 4, o impresso não vê o conteúdo novo do F2. Puxar a parte do impresso da fase 4 para a 3, ou deployar 1 a 4 juntas? Decidir antes da fase 3 — depende de: Otavio
- [x] (D-237: opção A) (09/11, contra a D-236) Fase 2 sozinha na `main` trava o "Validado" e o zip de toda revista: as pendências novas do infográfico (habilidade vazia, passo ligado sem dado, item sem imagem) só se resolvem na tela da fase 3. Opções: (A) `integ/f2-gerado` entra na `main` só com as fases 1 a 3; (B) a fase 2 não cria pendência nova, e elas entram na fase 3 — depende de: Otavio
- [ ] No banco de dev, SAESE LP (revista 3) e SAEGO LP (revista 13) estão com o "Validado" desatualizado: o hash gravado não bate com a revista resolvida, já com o código da `main` (visto em 06/11 ao testar a fase 1; não é efeito dela). Revalidar ou investigar o que mudou — depende de: Otavio
- [x] (09/11: D-236 mantida; PR #7 fechado sem merge — fase 1 só vai à `main` com a fase 2, testadas juntas) PR #7 (`feat/f2-f1` → `main`) em conflito só no `state.md`: Estado atual, Próxima ação, D-233/D-234 (números usados nas duas branches), Perguntas em aberto e Sessões. Resolver na worktree `revista-express-f2-f1`, renumerando D-233/D-234 da F2 para D-237/D-238 (o código cita D-233 em 4 arquivos). E a D-236 diz que a fase 1 só entra na `main` junto com a fase 2: o PR #7 a substitui? — depende de: Otavio.
- [ ] Migração 0020 existe nas duas frentes: `0020_infograficos` (`feat/f2-f1`, seguida de 0021 e 0022) e `0020_etapa_do_projeto` (`feat/etapa-do-projeto`). A frente que entrar na `main` depois renumera a sua e refaz a dependência — depende de: ordem dos merges (usuário).
- [ ] Numeração de decisões colide entre branches: D-233 é "Docs alinhados" nesta branch (PR #6) e "Uma página por fascículo" em `feat/f2-f1`; D-229 a D-231 de `feat/etapa-do-projeto` são outras decisões na `main`. Renumerar na branch que entrar depois na `main` — depende de: ordem dos merges (usuário).
- [ ] (D-234) `entrar()` em `e2e/tests/helpers.ts` não detecta login falho (confere `/admin/login/`, mas o login falho fica em `/conta/entrar/`). Trocar para ir direto a `/conta/entrar/` e conferir que saiu dela? Muda teste: rodar a suíte E2E — depende de: Otavio
- [x] (D-234: sim) (D-233, 09/11) Comentários de código ainda falam do login do admin depois da D-212: `nucleo/usuarios.py` ("todo perfil entra pelo login do admin") e `e2e/tests/helpers.ts::entrar` ("Entra no admin", passa por `/admin/login/`, que redireciona). Corrigir? — depende de: Otavio
- [x] (D-234: fica 1, motivo novo no comentário) (D-233, 09/11) Playwright: `workers: 1` ainda é preciso? O motivo escrito (D-191: painel, impresso e revista gravam a mesma revista DEMONSTRAÇÃO) caiu com a D-225, em que cada spec grava na própria revista — depende de: Otavio (medir a suíte com 2 workers?)
- [x] (D-234: sim) (D-233, 09/11) `app/.env.example` não lista `APP_BIND`, `APP_PORT` nem `COMPOSE_PROJECT_NAME`. Acrescentar? — depende de: Otavio
- [x] (D-234: sai) (D-233, 09/11) O `CLAUDE.md` do projeto termina com "### Who is you?" (texto da skill frontend-design colado). Fica ou sai? — depende de: Otavio
- [x] (D-234: sim) (D-233, 09/11) A D-224 e o comentário de `playwright.config.ts` dizem que o `limpar_e2e` apaga parceiros e templates; ele apaga também matrizes "E2E …" (D-225). `docs/e2e.md` já segue o código; corrigir o comentário? — depende de: Otavio
- [ ] F2 animado (pasta `example/infografico-animado`, analisado em 05/11): viável sem mudar banco nem SVG. Escolher a integração: (A) abertura animada que termina no estado do svg-tour atual, ou (B) substituir o svg-tour pelo player do exemplo (perde minimapa, zoom e modais prontos). Risco: o roteiro acha as peças pela ordem dos filhos no SVG; só existe 1 SVG real (os 80 em `media/f2` são cópias do fixture) — depende de: Otavio + design (o SVG de MT e de outros parceiros mantém a mesma árvore?)
- [ ] Textos do tour do F2 (SAEGO LP, template "Padrão") trocados em relação ao desenho: o passo 3 do tour se chama "Progressão da habilidade", mas enquadra o bloco "Descrição das habilidades no referencial curricular"; o botão + desse bloco (`btn-action-p3`) abre o modal "Progressão…". O passo 2 ("Itens por ano/série", "percentual de acerto") enquadra a linha de progressão. Visto na demo de 05/11; vale também no sistema hoje — depende de: Pedagógica (corrigir o template ou os ids do SVG?)
- [x] F2 animado, ideia corrigida em 05/11: a animação não é só abertura; cada passo do svg-tour toca a animação do seu bloco (a câmera é a do tour, e o conector "viaja" do descritor até o bloco durante o movimento). A demo `example/f2-animado-tour/` ainda é a versão "só abertura". Sem mudar o `svg-tour.js`: basta o evento `svgtour:change`. Decidido em 05/11: (a) passo já visto aparece pronto, sem tocar de novo; ~~(b) antes da visita o bloco fica esmaecido, e a visão geral mostra o desenho inteiro~~ (substituída em 05/11: o usuário viu o bloco esmaecido sumir e reaparecer ao entrar no passo, e o passo 3 esmaecido acima do passo 2; agora (b) o bloco não visitado fica escondido e a visão geral mostra só fundo e título).
- [ ] (09/11, D-239: a estrutura do Alfa é a mesma; resta só "o docx AF_EM é o Outras Etapas?", que decide qual infográfico recebe o conteúdo, não o código) F2 preenchido todo na interface (mapeamento de 06/11, agente; substitui a avaliação de 05/11): documento em `docs/superpowers/specs/2026-11-06-f2-na-interface-mapeamento.md`. Recomendação: SVG gerado pelo servidor (`revista/f2.svg` + `servicos/f2.py`, `<text>`/`<foreignObject>`), svg-tour mantido sem alteração; passos canônicos `abertura`, `descritor` (fixos), `habilidades`, `progressao`, `tarefas` (desligáveis por `Projeto.f2_passos_desligados`, gravado com o modal de impacto); dados novos `DescritorProgressao` e `RevistaF2Descritor`; sai o upload/sanitizador de SVG. Estimativa: 8 a 12 dias úteis (7 a 10 sem a animação por passo), fase 0 = protótipo de 1 dia. Riscos: referencial curricular sem planilha estruturada; texto longo não reflui no SVG; minimapa com `foreignObject`. Perguntas: lista final de passos (Pedagógica + Otavio); desligar por projeto ou por revista (Otavio); planilha do referencial 1EF–3EM LP/MT (Pedagógica); webfont (design); acertos/série histórica no web algum dia (Pedagógica) — depende de: Otavio decidir se faz a fase 0 · Atualização 06/11 17:40: D-228 (fase 0 aprovada) e D-229 (desligar por revista); campos do docx levantados em `2026-11-06-f2-campos-do-docx.md` com 5 perguntas novas (AI × AF_EM; abertura na web; modal das tarefas; arquivo de suporte; template do infográfico) — depende de: Otavio (2 e 3), Pedagógica (1 e 5), design (4) · 18:00: D-230 responde a pergunta 1 (Alfa × Outras Etapas). Novas: a estrutura do Alfa é a mesma (progressão 1EF–3EM, itens só do 2EF?); o docx "AF_EM" recebido traz um item do 2EF — é o "Outras Etapas"?; template F2 por tipo × componente? — depende de: Pedagógica · 18:40: D-232 responde 2 a 5; restam só as da Pedagógica (estrutura do Alfa; o docx AF_EM é o Outras Etapas?) e, minha, onde vão abertura e fechamento comuns do bloco ❹ — depende de: Pedagógica; Otavio (bloco ❹)
- [x] (D-233) F1 e F2 deixam de ficar na mesma página (vão ficar separados; aviso de 05/11, conversa em 06/11). Afeta: página única `revista/index.html` (D-156), o zip (D-159) e o início do F2 animado (deixa de precisar do `IntersectionObserver`) — depende de: conversa de 06/11
- [x] (D-225, 05/11) Specs que gravavam na matriz/revista DEMONSTRAÇÃO passaram a usar `matrizPropria` (cópia "E2E …" da Demonstração) e `revistaPropria` (parceiro com revista 6 de 6); `limpar_e2e` apaga também matrizes "E2E …". Suíte inteira 164/164 numa stack isolada, sem sobra.
- [ ] Versões 2 a 8 do template "Padrão (F1)" LP 2026 (texto "Atualizado E2E…", de 03 e 04/11) continuam no banco de dev. A v9 já tem o texto limpo; a v8 é a base das cópias da introdução de SAESE LP e SAEGO LP. Versão só sai com o template (D-207). Apagar as v2–v7 por fora da tela, ou deixar como histórico? — depende de: Otavio
- [ ] Editor de templates (`editor-secoes.js`, Salvar explícito) ainda usa o aviso nativo ao sair com alteração; levar o diálogo do D-223 para ele? — depende de: Otavio
- [x] (05/11: liberar e deixar o Admin marcar; D-220) Admin atribuir o grupo Impresso (pedido em 05/11): dá ao Admin, na prática, "marcar impressa" (cria um usuário com senha conhecida, move para o Impresso e entra como ele), contra D-211 e `ADMIN_MARCA_IMPRESSA = False` — depende de: usuário
- [x] (05/11: só sem rastro; D-218) Excluir usuário pela tela (pedido em 05/11): contraria D-205 ("usuário não é excluído: é desativado"); o histórico perde o autor e versões de template, validações e fotos (PROTECT) impedem — depende de: usuário
- [x] (05/11: manter a senha; D-216) Link de acesso na tela Usuários: o "Novo usuário" passa a nascer sem senha e mostrar o link (muda o fluxo atual, que pede senha)? — depende de: usuário
- [x] Produção: `docker-compose.prod.yml` criado (D-214).
- [ ] Produção: `check --deploy` avisa HSTS e SSL redirect (W004, W008); decidir com a Infra se o proxy já faz o redirect e o HSTS — depende de: Infra
- [x] (aplicadas em 04/11) Aplicar as migrações 0016–0018 (permissões, trigger da `TemplateVersao`, `Parceiro.desativado_em`) no banco de dev? Sem elas, as telas do dev quebram com o código novo — depende de: usuário (migração de schema)
- [x] (05/11: usuário mandou corrigir; Agente D) (regras de negócio, seção 10.1) `docs/modelo-er.md` está desatualizado em dois pontos: o bloqueio é tomado pelo mesmo usuário, não pela mesma sessão (D-191); a foto guarda a revista resolvida inteira e roda em READ COMMITTED (D-151/D-153/D-178). Corrigir? — depende de: usuário
- [ ] (regras de negócio) O admin ainda pede o checkbox "afeta N revistas" sempre que há revista afetada; as telas B só avisam quando alguma perde o Validado (D-202). Igualar? — depende de: usuário
- [ ] (regras de negócio 10.1, divergência 4, D-055) O limite do corte é o `Etapa.escala_max` de cada etapa (código: `models/cadastro.py:60`, `servicos/cascata.py:38`) ou os valores fixos 1000/500 da D-055? Se for o `escala_max`, reescrever a D-055 — depende de: usuário
- [x] (D-234: sim) (regras de negócio 10.1, divergência 10) Corrigir o comentário de `models/controle.py:18` ("CASCADE"; no banco a FK é NO ACTION), sem mudar comportamento? Os 2 de `permissoes.py` já foram trocados na D-218/D-220 (conferido em 09/11) — depende de: usuário
- [ ] `.env.example` da raiz ainda é do sistema antigo (`SESSION_SECRET`, `ADMIN_EMAIL`); o certo é `app/.env.example`. Apagar ou substituir? — depende de: usuário
- [x] (D-211, fechado) (S9) O perfil Admin pode redefinir a senha de um usuário Impresso e entrar como ele, ganhando `marcar_impressa` (anula `ADMIN_MARCA_IMPRESSA = False`). Furo já existia no admin. Fechar com `pode_editar` em `nucleo/usuarios.py` exigindo alvo sem grupo fora dos permitidos? — depende de: usuário
- [x] (D-213; apagados em 05/11 a pedido do usuário) `api/.env`, `contrato/`, `escala.html`, `script.js`, `styles.css`, `descritores.json`, `saida/` e o `.env.example` da raiz
- [x] (D-206) Ano aberto por engano: fica como histórico ou exceção no trigger para apagar o ano inteiro? — depende de: usuário
- [x] (D-207) Template sem uso: arquivar basta ou excluir de fato (exceção à D-125)? — depende de: usuário
- [x] (D-208: sim) Criar "desativar parceiro" para quem sai do programa (hoje ele aparece numa linha vazia na grade de Cortes de todo ano novo)? Usuário não entendeu; pergunta refeita em 04/11 — depende de: usuário
- [x] (D-206: só Admin) Quem exclui Ano: Ped/Míd/Admin ou só Admin? — depende de: usuário
- [x] (D-205) Regras de exclusão (pedido do usuário, 04/11): o banco impede várias exclusões (PROTECT em ~40 FKs; trigger só-inserção em `TemplateVersao`), e o admin nega a exclusão de Ano, Projeto ("arquiva pela cascata"), Revista e Usuário. O que deve ficar excluível, e por quem? — depende de: usuário
- [x] (05/11: v9 gravada com o texto da v1) O template "Padrão (F1)" do dev está com "Atualizado E2E …" de 7 rodadas do Playwright. Gravar uma versão nova com o texto da v1? Isso pode mudar o hash das revistas que o usam. Corrigir também o spec, para ele editar só um template próprio — depende de: usuário
- [ ] (U10d) Trocar "(s)" por `pluralize` no sistema todo, num passo próprio (~25 mensagens e ~40 asserções)? — depende de: usuário
- [ ] (U10d) `tabular-nums` só nos números, para o hífen voltar ao normal? Contraria a Tabular Rule do DESIGN.md — depende de: usuário
- [ ] (U10d) Manter mono no `table.diff` e no editor de template? — depende de: usuário
- [ ] (U10a) A sombra do cabeçalho do Painel ao rolar na vertical deve voltar? Saiu pela Flat Rule — depende de: usuário
- [x] (U10c) Variáveis: célula travada desliga a planilha inteira, e duas pessoas na mesma célula = vale a última. — usuário (04/11): entram no U10d
- [ ] **Limpeza do banco de dev ao fim da reforma (autorizada por Otavio, 03/11):** apagar o que foi criado para teste — usuários `e2e`, `imp-e2e`, `demo-preview`; parceiro `DEMONSTRAÇÃO` (projeto/revista 2026, preview 13) e matriz `Demonstração`; parceiros `E2E A/B <sufixo>` criados pelo `cortes.spec.ts`; e o que os specs novos (U2+) criarem (nome com prefixo `E2E`). Não tocar em SAESE, TESTE, Novo parceiro, `otavio`, `midias`, `impresso`, `pedagogica`. Listar antes de apagar — depende de: fim do U10
- [x] (D-189 → D-190) Auditoria das telas B: o que o back faz e a tela B não oferece. Bloqueia: abrir ano, criar matriz, criar template, paleta do ano, etapas/componentes. Leva a erro: links do painel vão ao admin (Impresso recebe 403 em "Matriz", `urls/painel.py:43`), renomear parceiro, "abra um ano no admin" para quem não pode. Menu sem Projetos e Lotes. Por onde começar — depende de: usuário
- [x] (D-184) S17: os cortes de 2026 repetem os de 2025? Se sim, comando `importar_cortes` (~60 min) substituindo a D-119 nesse ponto — depende de: Pedagógica
- [x] (D-184) S17: LP 2EF tem 10 descritores na planilha `NÍVEIS - LP 2EF.xlsx` e 8 no PDF SAEGO 2025 — qual vale? — depende de: Pedagógica
- [x] (D-184) S17: passo 25 em 5EF/9EF/3EM (como 2025) entra pela tela T10 depois da carga — depende de: Pedagógica
- [x] (D-183) Reavaliar a D-121 (interface no Django admin, React aposentado): manter o visual/telas do editor React? Opções: admin como está; páginas Django próprias com o visual do editor (admin só para cadastros); React sobre API Django. Apagar `editor/` no S17 fica bloqueado até decidir — depende de: usuário
- [x] (D-179) Rascunho de UI: as matrizes de 2026 têm imagem/PDF por item (`tarefa.arquivo`)? Se sim, tela de upload sobe para agora (+4 h). `/` vai para o Painel mantendo o índice do admin com módulo "Temporada"? (rec.: sim). Botão "Baixar zip" por linha no Painel em 2026? (rec.: não) — depende de: usuário
- [x] (D-176) Docx "Interpretação pedagógica da escala — textos de abertura LP e MT": o usuário disse que abre o fascículo 2 (infográfico), mas o texto é quase igual à `introducao` do F1 nos seeds (`f1-lp.hbs`/`f1-mt.hbs`: "relação entre a Matriz de Referência e a Escala de Proficiência…"). Entra no F1 `introducao` ou no F2 `abertura`? — depende de: usuário
- [x] Mapa das telas (UI): inventário feito (2026-10-30): 28 telas, 25 existem ok, 0 desatualizadas, 3 faltam (T26 impresso, T27 planilhas, T28 histórico). Rascunho de UI em andamento.
- [x] (D-177) Inventário das telas — Admin marca impressa? (rec.: não); aviso "afeta N revistas" em Padrões do ano? (rec.: sim); tela do impresso página própria? (rec.: sim); planilhas por revista ou por ano? (rec.: por revista); painel como página inicial? (rec.: sim) — depende de: usuário
- [ ] Coluna Impresso do painel: criar `hash_impresso` na foto (migração) para não carregar o JSON inteiro por linha? Só se o painel ficar lento — depende de: medida com dados de 2026
- [x] (D-173) `pd01..pd05` devem virar os rótulos "Padrão 01..05" do F1? `nome_parceiro` substitui a automática `parceiro` nos textos? — depende de: usuário
- [x] Aplicar o Top 5 da auditoria de código com cara de IA (2026-10-30)? — usuário: todos, na branch `fix/auditoria-ia`
- [x] (D-115 a D-124) Varredura 7 agentes (2026-10-29), perguntas 55–70: cópia por seção; juntar lado a lado × proposta; preview sem template; ciclo de vida da revista sem cortes; SVG/capa derrubam Validado; variável com escopo parceiro; sugestão do ano anterior; painel da temporada; copiar em lote; validar em lote com hash; React × Django admin; bloqueio × otimista; fascículo fixo; editor textarea × etiquetas; FK composta; matriz duplicada entre anos — depende de: usuário
- [x] (D-125) Correções técnicas da varredura (sem decisão do usuário): ER sem TextoModelo/BlocoTexto/ProjetoBloco e com Revista/RevistaFasciculo/Projeto.ano_id; TemplateVersao só de inserção como base da fusão; hash em Python com JSON canônico (só cai a revista que usa a variável, corrige D-097); bloqueio por `INSERT … ON CONFLICT … WHERE expira_em < now()`; cascata com `FOR UPDATE` em ParceiroAno, foto em REPEATABLE READ, clone em uma transação; SVG sanitizado (defusedxml, lista de tags, 3 MB, ids prefixados); Markdown com `html: false` e `{{var}}` validado por regex; zip com JSON/SVG embutidos no index.html; atalhos do F1 só fora do F2; revalidar seções × ids do SVG no Validado e ao salvar template; marcar D-063 (texto), D-070 e D-088 (texto_modelo) como substituídas e reescrever D-093 — depende de: aprovação das perguntas 55–70
- [x] (D-114) Template F1: o texto aparece antes e depois das escalas; usar seções fixas (`## introducao`, `## fechamento`) como no F2? — depende de: usuário
- [x] (D-110 a D-113) Grill-me fascículos, rodada 4 (2026-10-29): 8 perguntas (juntar textos, estrutura do template F2, sobrescrita no F2, revista incompleta, SVG/capa no impresso) — depende de: usuário
- [x] (D-150) `Tarefa.arquivo` copiado no abrir ano aponta para o mesmo arquivo nos dois anos (D-148); se um passo futuro apagar o arquivo ao trocá-lo, o outro ano perde. Aceitável? — depende de: usuário
- [x] (D-153) As cores do F1 entram no "o que mudou" do impresso (D-151)? — depende de: usuário
- [x] (D-153) Corte igual a 0 ou à escala máxima: a cascata aceita (D-055), o JS recusa a etapa (D-131). Fechar onde? — depende de: usuário
- [x] (d873252, `fix/f1-js-css`) Cor da linha com `passo` nulo: JS pinta pelo topo (base da entrada de cima) e diverge do Python (âncora maior) com tarefas esparsas (D-154). Corrigir no `script.js` depois do S08 — depende de: S08 terminar
- [x] (D-158) Número destacado da régua: branco sobre o vermelho do padrão 1 (#f72628) dá 3,99:1, abaixo do AA (4,5:1). Trocar para preto (5,3:1) ou escurecer o vermelho? (D-157) — depende de: usuário/design
- [x] (D-180) Itens de tarefa (imagem/PDF) sem texto alternativo: campo opcional no modal de upload — depende de: usuário
- [x] (D-166) Liberar exclusão de sobrescritas do projeto e de tarefa/descritor? — só as sobrescritas
- [x] (D-166) Impacto do template sem listar revista sem SVG? — fica assim
- [x] (D-168) Só o superusuário põe alguém nos grupos Impresso e Admin — confirmado
- [x] (D-170) Cópia de seção editada até ficar igual ao template continua cópia — confirmado pelo usuário
- [x] (D-172) Lista completa de variáveis (D-107) — planilha recebida
- [ ] Seeds 2026 para a Pedagógica (D-139): `f1-mt.hbs` diz "Para Língua Portuguesa…" no 3º parágrafo (igual ao escala.hbs e ao PDF de MT 2025); fechamento do F1 = "Utilização dos resultados"?; `f2-mt.hbs` é cópia do LP; modais `dlg-p4-i1..i4` com "Conteúdo em breve."; nome do template "Padrão" — depende de: Pedagógica
- [ ] Bloqueio (D-140): portar a saída por inatividade do editor React?; POST recusado re-renderizar em vez de descartar o digitado? — depende de: usuário
- [ ] SVG com `<!DOCTYPE>` é recusado (D-137): o design exporta sem DOCTYPE? — depende de: usuário/design
- [ ] Autor da foto herdada (D-135): usuário da cascata (atual) ou autor da foto original? — depende de: usuário
- [x] (D-104 a D-109) Grill-me fascículos, rodada 3 (2026-10-29): 20 perguntas (template × sobrescrita, clone do ano, variáveis, SVG do F2, pacote, impresso, bloqueio) — depende de: usuário
- [x] (D-095 a D-103) Grill-me fascículos/templates (2026-10-29), rodadas 1 e 2 (25 perguntas, enviadas juntas a pedido do usuário): unidade revista × projeto; template no código ou no banco; blocos × documento .hbs; variáveis por parceiro ou projeto; escolha de matriz/template por revista ou por ParceiroAno; repositório do infográfico — depende de: usuário
- [x] (corrigido) PDF de estudo v2 desatualizado em 4 pontos: seção 8 e questão 10 (intervalo mínimo × passo, D-091), desafio (ParceiroAno já resolvido, D-088), bloqueio sem `sessao_edicao` (D-093) — depende de: usuário pedir a correção
- [x] (D-088 a D-094) Revisão do ER (2026-10-27), alta: (1) escolha de matriz/texto-modelo em ParceiroAno, não no Projeto; (2) clique "Validado" e "Revista Impressa Atualizada" devem enviar o hash da versão que a pessoa viu, e o servidor recusa se o atual for outro (senão um ajuste passa sem ser visto); (3) coerência de ano entre FKs (Corte, Projeto, MEC, sobrescritas) por FK composta ou derivando o ano do pai; (4) `passo` e `intervalo_minimo` são o mesmo campo ("Intervalo mínimo" na UI é o passo) — erro do rascunho; o PDF v2 (seção 8, questão 10) usa 125/100 como se fosse outro conceito; (5) blocos de texto só têm texto, mas a página hoje tem imagem (`heroImagem`) e parágrafos — depende de: usuário decidir
- [x] (D-088 a D-094) Revisão do ER, média: corte sem MatrizEtapaCC na matriz escolhida; projeto arquivado deve congelar (não resolver com cortes vivos); ProjetoBloco ao trocar de texto-modelo ou remover bloco; bloquear "Validado" com nome "… - NOME DO PROJETO"; Bloqueio precisa da sessão de edição (aba), como hoje, e ficar fora do histórico — depende de: usuário
- [x] (D-088 a D-094) Revisão do ER, negócio: valor revertido faz o "Validado" voltar sozinho (hash) — aceitável?; projeto readicionado (D-068) herda a última foto do arquivado?; reimportar matriz (D-071) recria ids e perde auditoria por registro — depende de: usuário
- [x] (D-088 a D-094) Escolha de matriz/texto-modelo mora no Projeto (D-084), mas projetos não são clonados (D-085): em 2027 o CE renasceria sem a matriz CE. Onde guardar a escolha por parceiro × ano para sobreviver ao clone? — depende de: sessão de modelagem (é o desafio do PDF v2)
- [ ] Intervalo mínimo e cor sobrescritos não têm `versao_base`: mudança no padrão não avisa o projeto que sobrescreveu. Precisa? — depende de: usuário
- [x] (D-220: sim) Admin pode clicar "Revista Impressa Atualizada"? (D-083 dá ao admin as permissões da Pedagógica, não as do Impresso) — depende de: usuário
- [x] (D-062) Textos da revista: modelo comum + edição por projeto com "diff tipo git". Proposta do Claude: sobrescrita por bloco, guardando a versão do modelo usada; se o modelo mudar, avisar e mostrar o diff, sem fusão automática — depende de: usuário
- [x] Propostas 1, 2, 5, 6 da revisão `make-interfaces-feel-better` aplicadas (D-040). Pendentes: 3 (`:active` do botão), 4 (feedback de toque), 7–10 — depende de: usuário
- [ ] Alternativa de exibição (régua proporcional ou lista por padrão) — só se a equipe pedagógica quiser; recomendação foi manter a régua.
- [ ] Modo de execução do plano: subagentes ou nativo? — depende de: usuário
- [ ] `skills[]` → "relacionadas" vs "correspondente" na planilha: heurística pelo "(" serve à impressão? — depende de: equipe de impressão
- [ ] Levar a opção 1 ajustada (D-032) para `revista/`? — depende de: usuário ver `demo-escala/opcao-1.html`
- [x] Cortes do 5º ano corretos? — confirmados pelo usuário
- [ ] Lista real de perfis e matriz papel × ação (tabela da seção 9 do PDF de modelagem) — depende de: usuário
- [ ] Onde guardar o status "aplicado no impresso" (cada modelo terá a própria tabela de histórico) e o formato do marcador de padrão sobrescrito — depende de: sessão de modelagem
- [ ] Migrar `api/` (Express + Mongo) para Django + PostgreSQL, mantendo o React de `editor/`? Motivos do usuário (2026-10-26): herança entre projetos, templates de escala por parceiro (com parentesco entre si), auth/perfis mais fortes (uso amplo todo ano), auditoria de mudanças de texto para avisar a equipe do impresso; equipe já sabe Django. Proposta de modelo apresentada, sem decisão — herança viva decidida (D-045); depende de: usuário confirmar a regra de conflito (sobrescrita local do filho vence ou o pai vence?)

## Sessões
### 2026-11-10
- Tarefa 3 planejada: 8 lacunas do brief fechadas (D-242); briefs 3, 4 e 5 ajustados.
- Tarefa 3 implementada (6b6685a), revisada (aprovada com 7 Minor) e corrigida (906b427); prova visual conferida.
- Tarefa 4 implementada (bf9cdd7), revisada (1 Important + 5 Minor) e corrigida (4e16fae).
- Conselho da tarefa 4: O3 unânime (D-243); mudança e O4 (docs, ponytail) aplicadas; suíte 862 OK.
- Tarefa 5 planejada com os chamadores (D-244), implementada (e5d8805), revisada (2 Important + 5 Minor) e corrigida (15740f2); prova visual conferida.

### 2026-11-09
- Retomada da fase 2 do F2. Antes: relatório da fase 1 julgado pela doutrina dos agentes (degraus, análise sóbria, meta-análise). Nada apagável no código da fase 1.
- Achado: a premissa da D-236 cai. A fase 2 cria pendências por infográfico (habilidade vazia etc.), e `servicos/validacao.py:43` recusa o "Validado" e `empacotar.py:101` recusa o zip com pendência; sem a tela da fase 3, ninguém as resolve. Usuário escolheu A: D-237.
- Suíte da fase 1 rodada de novo: 833 OK, 8 pulados; `makemigrations --check` limpo.
- Plano da fase 2 escrito e aprovado (`docs/superpowers/plans/2026-11-09-f2-fase-2.md`, 7 tarefas, 4 a 5 dias), com o mapa do que fica para a fase 3. D-238 (ids do template F2 na fase 2) e D-239 (desenho = SVG em uso; Alfa = mesma estrutura).
- Worktree `/home/otavio.peres/dev/revista-express-f2-f2` (`feat/f2-f2`, saída de `feat/f2-f1`) e stack `f2-f2` criadas; tarefa 0 concluída.
- Tarefa 1 concluída e revisada (434c4cd..3fb2dda; 843 OK). D-240 (fechamento das tarefas só genérico), confirmada pelo usuário.
- Tarefa 2 concluída e revisada (36232e7..03403f0): `f2.svg` fiel ao desenho; PNGs aprovados (letra por etapa, botão ❶ laranja). D-241: botão + e modal `dlg-tarefas` para o clique ❹. Tarefa 3 interrompida para encaixar a D-241.
- Ajuste da D-241 (2aa1ecc): seção `dlg-tarefas` e botão `f2-btn-action-tarefas`; 846 OK; re-revisão aprovada. Tarefa 3 retomada e parada de novo a pedido do usuário, sem deixar código. Sessão encerrada aqui; o usuário segue depois.
- Learnings da sessão commitados com o ok do usuário: deploy só com as fases 1 a 3 e template F2 com seções fixas; botões dos cliques ❶–❹ e `localize off` no `f2.svg`.
### 2026-11-06 19:00
- Fase 1 do plano do F2 gerado iniciada com subagentes (superpowers:subagent-driven-development): branch `integ/f2-gerado` saída da `main`, worktree `/home/otavio.peres/dev/revista-express-f2-f1` (`feat/f2-f1`), stack docker `-p f2-f1`.
- D-233 registrada (páginas separadas, dados na tela B, animação por último). D-234: tarefa usada por item impede exclusão e reimportação (achado na leitura: a reimportação apaga os descritores e quebraria com `PROTECT`).
- Tarefas 1 e 2 da fase 1 concluídas e revisadas (esquema; cascata + 0022). Tarefa 3 (D-234) parada: o usuário corrigiu que o item do infográfico não usa tarefa da matriz. D-235 substitui a D-234; o item ganha descritor, etapa, imagem e análise próprios.
- Revisão final da fase 1 (`ecc:django-reviewer`): 0 críticos; correções aplicadas numa leva (teste do hash agora prova algo, teste da revista arquivada que volta, `2EF` sem diferenciar maiúsculas, comentários) e re-revisadas.
- Verificação final: 833 OK, 8 pulados; régua ok. Cópia do banco de dev migrada até a 0022 na stack `f2-f1`: cada revista ativa ganhou os infográficos que os cortes pedem; nenhum hash mudou (SAESE LP e SAEGO LP já estavam fora do "Validado" antes).
- Commits da leva: 23d00d0, 660c806 (esquema, permissões), bf27df1 (cascata + 0022), 79a4e19 (item, D-235), f942878 (correções da revisão), bd41a90 (learning), e este `state.md`.
- Usuário escolheu o merge local: `feat/f2-f1` → `integ/f2-gerado` por fast-forward; suíte rodada de novo na `integ/f2-gerado`.
- D-236: a fase 1 entra na `main` só junto com a fase 2 (decisão do usuário).
### 2026-11-09 10:00
- D-234: respostas às 5 perguntas aplicadas (comentários, `.env.example`, `CLAUDE.md`); achado: `entrar()` do E2E não detecta login falho.
- D-233: atualização dos docs em `../revista-express-docs` (branch `docs/atualizacao-2026-11-09`, intermediária `integ/docs-atualizacao`); 3 subagentes em paralelo; `DESIGN.md` marcado como do editor antigo.

### 2026-11-06 14:30
- Agente de mapeamento disparado: F2 preenchido todo na interface sobre um template único de passos fixos, com passos desligáveis por projeto (tempo e tecnologia). Saída em `docs/superpowers/specs/2026-11-06-f2-na-interface-mapeamento.md`.
- D-227: usuário aprovou a direção do mapeamento.
- Fase 0 disparada: plano escrito em modo de plano e aprovado (protótipo estático em `example/f2-gerado/`, sem Django; tour reaproveitado de `example/f2-animado-tour/f2/` por caminho relativo; Playwright do checkout principal via `NODE_PATH`; 5 critérios de "serve": zoom/pan, minimapa, texto longo, passo desligado, acessibilidade mínima). Branch `feat/f2-fase0`.
- Fase 0 entregue (subagente + verificação minha): `example/f2-gerado/` com `dados.json`, `gerar.py` (`--check`, `--desligar`), `verificar.cjs` (17/17 OK), `LEIA-ME.md` com veredito proposto "SVG gerado serve". Ajustes que o protótipo revelou: o minimapa remove `class` do `<svg>` clonado (`svg-tour.js:559`), então o CSS interno não pode depender de classe na raiz; o stage do svg-tour tem `user-select:none`, e `user-select:text` nos divs do `foreignObject` libera a seleção sem atrapalhar o arrasto. Pendente de olho humano: bloco de habilidades mais alto que o stage em `minScale` 1,6 (ancora e pede arrasto); minimapa pequeno; Safari/Firefox. Título do modal de habilidades corrigido (o seed trazia "Progressão…").
- D-228: usuário aprovou a fase 0 ("a navegação em si está funcionando"; estilos a caprichar depois, com o design).
- D-229: desligar passos do F2 é por revista. Recebido o docx "AVALIAÇÃO E CURRÍCULO_LP_2026_AF_EM" que a Pedagógica manda ao impresso; convertido com anydoc para levantar os campos que o F2 precisa.
- Levantamento dos campos do docx em `docs/superpowers/specs/2026-11-06-f2-campos-do-docx.md` (13 campos; 6 diferenças em relação ao mapeamento: o descritor tem modal, abertura de 4 parágrafos, marca vem da tabela ❷, habilidade destacada não é um Descritor do banco, tarefas com 2 arquivos e análise por item, fechamento com link para o template do infográfico); fonte convertida em `docs/fontes/2026/`. Ponto estrutural: no F2 o conteúdo específico é da revista, não do template.
- D-230: até 2 infográficos F2 por revista (Alfa ⇔ cortes no 2EF; Outras Etapas ⇔ cortes em outra etapa), derivados pela cascata; passos desligados passam a ser por infográfico.
- D-231: usuário autorizou o merge na `main` por mim, mediante "ok" explícito a cada leva; primeiro ok dado às 18:20 e `integ/f2-interface` mergeada.
- D-232: abertura também na web; 4 modais (um por item); imagem única do item montada pelo design; "Agora é com você" só texto, sem link.
- Mapeamento concluído e commitado em `docs/f2-mapeamento`; pergunta em aberto do F2 reescrita com o resultado; branch mergeada em `integ/f2-interface` (merge na `main` é do usuário).
- Regra nova do usuário (D-226): toda modificação em worktree própria com branch própria; merge em `integ/<tema>` só depois de testado; o merge na `main` é do usuário. Worktree desta sessão: `/home/otavio.peres/dev/revista-express-f2` (`docs/f2-mapeamento` ← `integ/f2-interface` ← `main`).
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

### 2026-10-26
- Pergunta do usuário: refazer o sistema com Django + banco SQL + React. Achado: o editor já é React 19; a mudança real seria `api/` (Express 5 + Mongoose, ~3,2 mil linhas, 10 módulos) → Django e Mongo → PostgreSQL. Nenhuma decisão tomada; pergunta registrada em "Perguntas em aberto".
- Usuário deu o motivo: herança entre projetos, templates de escala por parceiro, perfis/auth mais fortes, trilha de mudanças de texto para a equipe do impresso. Estrutura atual lida: `ProjetoModel` é um documento único com `cadernos[]` aninhado, `bloqueio` embutido, 2 perfis (`admin`/`editor`). Proposta: tabelas normalizadas (Projeto com `base`, TemplateEscala com `base`, Membro com papel por projeto, django-simple-history, Marco de entrega ao impresso).
- Usuário decidiu herança viva (D-045). Estimativa só da modelagem, juntos: 3 a 4 h (teto 5 h).
- PDF de estudo gerado para a sessão de modelagem: `docs/Modelagem_Banco_Conceitos_Essenciais.pdf` (12 páginas, não versionado; gerador em scratchpad, não guardado no repo). Trechos de código testados num venv do scratchpad com Django 6.1 + django-simple-history 3.13 em SQLite: herança por NULL (`''` é vazio intencional), UNIQUE composto e parcial, PROTECT, CHECK, histórico com `diff_against`, CTE recursiva. Achados: `CHECK` barra A→A mas não ciclo longo; `history_user` do simple-history usa `SET_NULL` (desativar usuários, nunca apagar).
- Commits na `dev` (sem push), a pedido do usuário: PDF de modelagem e, por último, este `state.md`. Os `.~lock…xlsx#` de `revista/modelo/` ficaram de fora (planilhas abertas no LibreOffice).

### 2026-10-27
- Usuário trouxe anotações (papel) + planilha `Cortes dos Padrões por Etapa e Parceiro.xlsx`: matriz comunitária única (base SAEGO) para todos os parceiros, exceto CE, ES e JOINVILLE; projeto difere só pelos cortes e pelas etapas/CC avaliadas (ausência na planilha = não avalia). Grill-me iniciado antes de remodelar o banco; nenhuma decisão registrada ainda.
- Achados na planilha: 9EF-MT SE (250,300,350) sem grupo próprio, herdando o grupo 5 (225,300,350); 5EF-MT SALVADOR (200,235,253) dentro do grupo 5 (175,225,300); 2EF-LP SE = "725, 800" (fora da faixa das demais 2EF).
- Rodada 1 respondida: D-046 a D-050. "2EF sem valores mínimos" = 2EF não usa intervalo mínimo (linhas vazias da escala); 5EF/9EF/3EM usam.
- Rodada 2 respondida: D-051 a D-056 (D-045 substituída). Formato XLSX de descritores/tarefas visto: colunas Etapa, Cód. Descritor, Descritor, Pré-requisito e uma coluna por intervalo ("125 a 150"...).
- Rodada 3 respondida: D-057 a D-061.
- Rodada 4 respondida: D-062 a D-066.
- Rodada 5 respondida: D-067 a D-071.
- Rodada 6 respondida: D-072 a D-076 (D-069 substituída).
- Rodada 7 respondida: D-077 a D-080.
- Rodada 8 respondida: D-081 a D-083. Grill-me encerrado.
- Rascunho ER escrito em `docs/modelo-er.md` (D-084); Mermaid validado renderizando com mermaid 11.4.1 no navegador.
- Commits na `dev` (sem push), a pedido do usuário: modelo ER, PDFs da matriz comunitária + planilha de cortes, `.trail/` (learnings) e, por último, este `state.md`. `.claude/settings.json` fica fora (`.claude/` está no `.gitignore`).
- PDF para impressão: `docs/Modelo_ER_Revista.pdf` (5 páginas A4: visão geral, 3 diagramas por domínio, restrições). Gerado de `docs/modelo-er.md` com Mermaid 11.6.0 + Playwright (Chrome); gerador no scratchpad, não versionado.
- Pontos em aberto do ER fechados: D-085 a D-087; `docs/modelo-er.md` e PDF atualizados.
- PDF de estudo reescrito (v2): `docs/Modelagem_Banco_Conceitos_Essenciais.pdf`, 13 páginas, ancorado em D-046 a D-087. Trechos testados em PostgreSQL 17 (Docker descartável) + Django 6.1.2: UNIQUE por ano, UNIQUE parcial de projeto ativo, CHECK de 1 a 4 cortes em ArrayField, XOR do bloqueio, PROTECT, FK composta de mesmo ano, clone do ano com remapeamento, Coalesce da sobrescrita, `versao_base`, grupos com dados reais (batem com as correções). Achados: JSONB reordena chaves (hash precisa de `sort_keys`); FK do Django no banco é NO ACTION (`on_delete` roda em Python; Django 6.1 tem `DB_CASCADE`/`DB_SET_NULL`/`DB_SET_DEFAULT`); lacuna da matriz no clone (ver Perguntas em aberto).
- Revisão do ER: revisor independente (database-reviewer) + comparação com o sistema atual. 10 achados (5 altos, 5 médios) e 3 perguntas em "Perguntas em aberto". Refutados: "bloqueio expirado trava para sempre" (a aquisição sobrescreve o expirado, testado no lab) e "ordem dos grupos com tamanhos diferentes" (prefixo menor vem antes, bate com 2EF-MT).
- 10 correções da revisão aplicadas ao ER (D-088 a D-094): ParceiroAno, hash da versão vista, FKs compostas de ano, passo único, blocos tipados, regras médias. `docs/modelo-er.md` e PDF (6 páginas) regerados; Mermaid conferido renderizado.
- PDF de estudo v2 corrigido para D-088 a D-094: ParceiroAno na FK composta e no clone (seção 7), passo = "Intervalo mínimo" (seção 8), hash da versão vista (seção 9), bloqueio por usuário + aba (seção 10), questões 6, 10 e desafio reescritos. Reverificado em PostgreSQL 17: FK composta com matriz NULL é aceita; `Coalesce` erra a sobrescrita NULL de propósito (devolveu 25), `Exists` + `Case` acerta (NULL); aba 2 da mesma usuária é recusada.
### 2026-10-28
- Design system da revista impressa extraído dos 3 PDFs SAEGO 2025 (Alfa, LP, MT) com /impeccable document → `docs/design-revista-impressa.md` (tokens, tipografia, layout, componentes). `DESIGN.md` do editor não foi alterado. Achado: o impresso usa rampa verde nos padrões (#b8ffd8 → #00662e), diferente do padrão vermelho→azul do editor.
### 2026-10-29 12:20
- Novo grill-me: fascículos 1 (escalas) e 2 (infográfico) na mesma revista por componente (LP/MAT), templates de texto por fascículo escolhidos pelo usuário, matrizes como template, página de Templates, variáveis por projeto. Rodada 1 enviada; 25 respostas registradas (D-095 a D-103); rodada 3 enviada; conflita com D-088 (escolha em ParceiroAno, não no projeto) e D-070/D-075 (marcadores `{X}` × Handlebars).
- Varredura com 7 agentes (modelagem, contradições, UX, ponytail, casos-limite, postgres-patterns, postgres-best-practices): achados consolidados em 16 perguntas e 1 lista de correções técnicas.
- ER reescrito com postgres-best-practices (D-115 a D-125). Blueprint S01–S18 revisado por agente adversarial (5 críticos, 7 importantes corrigidos) e aprovado; branch `refatoracao-django` criada (D-126).
### 2026-10-29 15:00
- Fase A iniciada (S01, S02, S03, S03b). Decisão de git: commit local por passo, branches encadeadas (D-127). S01 rodando num subagente em worktree.
- S01 verificado e revisado (0 críticos, 4 correções em 7c278b4). S02 e S03b disparados em paralelo.
- S02 verificado (12 testes, ciclo migrate zero/migrate OK), commit 44b9283 em `feat/s02-cadastro-matriz`; revisão de banco em andamento.
- S03b verificado (régua ok, Playwright 4/4), commit fcdf714 em `feat/s03b-revista-n-padroes`; revisão de JS em andamento.
- Revisões S02 (banco) e S03b (JS): 0 críticos. Correções importantes enviadas aos agentes (D-131, D-132); S03 começa logo após o fix do S02.
- S03b concluído: fcdf714 + 877c96d em `feat/s03b-revista-n-padroes`; régua ok, Playwright f1-fixture 8/8.
- S02 concluído: 44b9283 + 8137471 (15 testes). S03 verificado: 57aafb7 em `feat/s03-projeto-revista` (27 testes, ciclo migrate OK); revisão de banco em andamento.
- S03 concluído: 57aafb7 + abc9e5c (29 testes; trigger só-INSERT em `template_versao`; uma recusa testada por FK composta). Fase A concluída.
- Merge local da Fase A em `refatoracao-django` a pedido do usuário: ff até abc9e5c + merge de `feat/s03b-revista-n-padroes` (1125cdb), sem conflito; reverificado (29 testes, régua, Playwright 8/8).
### 2026-10-29 17:00
- Fase B iniciada: S04, S05, S06, S09, S10 e S14 em paralelo, cada um num subagente com worktree próprio, sem commit (D-134).
- S06 verificado (42 testes, migrações limpas) em `feat/s06-cascata`, sem commit; revisão de banco em andamento.
- S14 verificado (35 testes, ciclo 0006↔0007) e S09 verificado (45 testes); revisões django-reviewer e security-reviewer em andamento.
- Revisão do S06: 0 críticos; correções importantes enviadas ao subagente (D-138).
- S05 verificado (46 testes, migrações limpas) em `feat/s05-templates`; revisão do parser em andamento.
- S06 concluído: correções da revisão aplicadas e reverificadas (48 testes).
- S10 verificado (47 testes) e S04 verificado (46 testes com PDFs; contagens do extrator antigo conferidas por mim); revisões em andamento. Revisão do S14: 1 crítico (escalada de privilégio do Admin), correções enviadas (D-142).
- Revisões S05 (0 críticos, 2 importantes) e S10 (0 críticos, 4 importantes): correções enviadas aos subagentes (D-143, D-144).
- Revisão de segurança do S09: 3 críticos (CSS fora do filtro, DoS, recursão); correções enviadas (D-145).
- S05 concluído (51 testes) e S14 concluído (37 testes, ciclo da 0007 mantém grupos), reverificados por mim após as correções.
- Revisão do S04: 0 críticos, 4 importantes; correções enviadas (D-146).
- S10 concluído: correções da revisão aplicadas e reverificadas (51 testes, `node --check` ok).
- S09: correções aplicadas e reverificadas (54 testes); segunda revisão de segurança em andamento.
- S04 concluído: correções aplicadas e reverificadas (53 testes com PDFs, contagens iguais).
- 2ª revisão do S09: 1 importante (lista negra de CSS não cobria layout); troca para lista branca enviada.
- S09 concluído: 2ª rodada aplicada e reverificada (57 testes).
- Fase B concluída. As 6 mudanças juntadas numa cópia descartável (sem conflito de arquivo): 152 testes OK, `makemigrations --check` limpo, régua ok; carga 2026 de ponta a ponta OK. Cópia removida. Nada commitado.
- A pedido do usuário: um commit por passo nas 6 branches, merge --no-ff de cada uma em `refatoracao-django` (S14 primeiro), sem conflito; reverificado (152 testes, migrações, régua, Playwright 8/8). Depois, commits do plano, do ER revisado, do design do impresso, dos learnings do trail (inclui o do sanitizador de SVG) e deste `state.md`.
### 2026-10-29 19:00
- Fase C iniciada: S07 (resolver) e S16 (abrir ano, paralelo) disparados, cada um num subagente com worktree próprio a partir de 7a0bfcc, sem commit. S08 → S15 seguem o S07 em sequência.
- Git da Fase C: commit local por passo encadeado (D-147), escolha do usuário.
- S16 verificado por mim (162 testes, migrações limpas) em `feat/s16-abrir-ano`, sem commit (D-148); revisão django-reviewer em andamento.
- Revisão do S16: 0 críticos, 3 importantes; correções enviadas (D-149).
- `Tarefa.arquivo`: usuário escolheu a opção 1 (D-150); comentário enviado ao subagente do S16.
- S07 verificado por mim (suíte OK, migrações, régua, Playwright 9/9), commit 4ce2428 (D-151); revisão python-reviewer em andamento. S08 disparado a partir de `feat/s07-resolver`.
- S16 concluído: correções da revisão reverificadas por mim (167 testes, migrações limpas), sem commit (D-152).
- Usuário: cores entram no impresso; cascata recusa corte nos limites da escala (D-153).
- Revisão do S07: 0 críticos, 4 importantes; correções + D-153 enviadas (D-154). S08 avisado: `titulo` é HTML e rebase sobre o 2º commit do S07.
- Usuário corrigiu a D-154: linhas vazias em todo nível do intervalo mínimo, mesmo dentro de uma tarefa (D-155); subagente do S07 avisado.
- S07 concluído: 2º commit 32d91db reverificado por mim (175 testes, migrações, régua, Playwright 9/9). S08 avisado para rebase.
- S08 verificado por mim (183 testes, migrações, régua, Playwright 14/14), commit f1ec6e2 (D-156); revisões a11y-architect e security-reviewer em andamento. S15 disparado a partir de `feat/s08-pagina`.
- Revisão de segurança do S08: 0 críticos, 3 importantes (preview sem `view_revista`; `criar_demo` sem guarda de DEBUG e redefinindo senha; sem CSP). Correções aguardam a revisão de acessibilidade para irem juntas ao subagente do S08.
- Revisão de acessibilidade do S08: 3 críticos, 5 importantes; correções das duas revisões enviadas ao subagente do S08 (D-157).
- Usuário: número destacado da régua em preto pelo contraste WCAG (D-158); enviado ao subagente do S08.
- S15 verificado por mim (191 testes, migrações, régua, Playwright 16/16 com `file://`), commit 9fab07c (D-159); revisão django-reviewer em andamento.
- Revisão do S15: 0 críticos, 4 importantes; correções enviadas (D-160).
- S08 concluído: 2º commit d070ae9 reverificado por mim (187 testes, migrações, régua, Playwright 15/15). S15 avisado para rebase e teste da CSP no `file://`.
- S15 concluído: b961b98 reverificado por mim (202 testes, migrações, régua, Playwright 18/18; CSP ok no `file://`). Fase C concluída.
- Conferência de integração: `feat/s15-zip` + mudanças do S16 numa cópia descartável: 217 testes OK, migrações limpas. Cópia removida.
- A pedido do usuário: commit do S16 (9109b28) e merge --no-ff de `feat/s07-resolver`, `feat/s08-pagina`, `feat/s15-zip` e `feat/s16-abrir-ano` em `refatoracao-django`, sem conflito; reverificado (217 testes, migrações, régua, Playwright 18/18, `trail check` sem conflito). Depois, commit dos 2 learnings do trail e deste `state.md`.
### 2026-10-29 23:00
- Fase D iniciada: S11a, S11b1 e S11c em paralelo, cada um num subagente com worktree próprio (`feat/s11a-admin-cadastros`, `feat/s11b1-admin-templates`, `feat/s11c-admin-projeto`) a partir de 33e0621, sem commit. Nenhum dos três cria migração. Depois: S11b2 → S12 → S13.
- Git da cadeia S11b2 → S12 → S13: commit local por passo (D-161), escolha do usuário.
- S11b1 verificado por mim (229 testes, migrações limpas, `node --check`), sem commit (D-162); revisão django-reviewer em andamento.
- Revisão do S11b1: 1 crítico (JS do editor não inicializa), 3 importantes; correções enviadas (D-163).
- S11c verificado por mim (suíte OK, migrações limpas), sem commit (D-164); revisão em andamento.
- S11a verificado por mim (suíte OK, migrações, Playwright cortes 1/1), sem commit (D-165); revisão em andamento.
- Usuário: exclusão só de ProjetoPasso/ProjetoCor; impacto do template ignora revista sem SVG (D-166).
- Revisão do S11c: 0 críticos, 4 importantes; correções + migração 0008 enviadas (D-167).
- Revisão do S11a: 0 críticos, 7 importantes (escalada para Impresso, fórmula na planilha, upload); correções enviadas (D-168).
- S11b1 concluído: 975c5fd reverificado por mim (suíte, migrações, Playwright templates-admin 1/1).
- S11c concluído: 5de1a91 reverificado por mim (suíte, migrações; migração 0008).
- S11b2 disparado em `feat/s11b2-copia-secao` = S11b1 + merge de S11c (D-169).
- Usuário confirmou: só o superusuário põe alguém nos grupos Impresso e Admin (D-168).
- S11a concluído: 5e22020 reverificado por mim (suíte, migrações, Playwright cortes 1/1).
- Pedido do usuário: ao fim da Fase D (depois do S13), merge em `refatoracao-django` do que foi feito e push da branch para o GitHub; último commit da leva só o `state.md`.
- S11b2 relatado (95c6790); minha verificação e revisão django-reviewer em andamento (D-170).
- S11b2 verificado por mim (suíte, migrações, Playwright 2/2); revisão em andamento.
- Revisão do S11b2: 0 críticos, 2 importantes; correções enviadas (D-171).
- Usuário: cópia editada até ficar igual ao template continua cópia (D-170).
- Sessão encerrada a pedido do usuário: subagente das correções do S11b2 parado sem mudanças; retomar pela D-171.
### 2026-10-30 09:30
- Usuário pediu "concluir a Fase D". Eu não li o `state.md` atualizado (só o da minha sessão anterior) e perguntei se era a Fase C; o usuário respondeu que sim, com base na minha premissa errada. Disparei um S07 duplicado: o subagente rodou `checkout -B feat/s07-resolver 7a0bfcc` e moveu a branch já juntada. Desfeito: ponteiro de volta em 32d91db (contido em `refatoracao-django`), worktree do S07 duplicado em detached HEAD (2a13061, descartável), minha edição do `state.md` descartada. Nada de `refatoracao-django` foi alterado.
- Fase D retomada pela D-171: subagente das correções no worktree do S11b2.
### 2026-10-30 10:30
- Conferência do plano: Fase D (S11a/b1/b2/c) já em `refatoracao-django` e no GitHub; D-171 pendente; "Estado atual" corrigido.
- D-171 disparada: subagente no worktree do S11b2.
- Auditoria de código com cara de IA (ponytail + tech-debt) disparada, só leitura, em `app/`; relatório no scratchpad da sessão.
- D-171 concluída: 74bf143, suíte 279 OK (8 pulados) verificada por mim.
- D-171 juntada em `refatoracao-django` e push feito.
- S12 disparado: subagente em worktree isolado, branch `feat/s12-painel` de ce9f6a3; checklist A–D (painel, Validado, lote, testes).
- Auditoria IA concluída: 33 achados (1 alta, 11 médias, 21 baixas), ~250 linhas removíveis; Top 5 = json_seguro→json_script, JS morto no F1, except/scaffolding inalcançável, helpers de teste duplicados, validação de cor em 3 camadas. Relatório só no scratchpad da sessão (não versionado). Item 3 esbarra no S12 (link /painel/ e Pendencia.link).
- Top 5 da auditoria disparado: 1 subagente sequencial em `fix/auditoria-ia` (de ce9f6a3), 5 objetivos com critério de pronto, 1 commit cada; link /painel/ e Pendencia.link ficam para o S12.
- Planilha de variáveis recebida (D-172); subagente em `feat/variaveis`.
- S12 entregue (25d24ec em `feat/s12-painel`): suíte OK (8 pulados) e `makemigrations --check` limpo verificados por mim; revisão django-reviewer rodando.
- Usuário respondeu D-172 → D-173 (`nome_parceiro` automático, `pdNN` = rótulo dos padrões); enviado ao subagente de variáveis.
- Revisão do S12: 0 críticos, 2 importantes; correções enviadas (D-174).
- S12 correções (f52fffc): suíte OK verificada por mim; pronto para merge.
- S12, auditoria e variáveis juntados em `refatoracao-django` (ensaio em worktree descartável antes: suíte OK); push feito.
- Usuário: nome dos padrões tem padrão por ano junto da cor e o projeto sobrescreve (D-175).
- D-175 disparada: subagente em `feat/nome-padrao`.
- D-175 entregue (222627b): suíte OK verificada por mim; merge simulado limpo.
- D-175 juntada com a correção do nome de exibição (892af5e) e a learning da escolha do usuário; push feito.
- Usuário preocupado: telas (UI) ainda não mapeadas com requisitos.
- Inventário das telas disparado (só leitura); agentes de UI por área entram depois, com o inventário como entrada.
- Docx de abertura LP/MT recebido; destino (F1 introducao × F2 abertura) em pergunta.
- Paralelo (pedido do usuário): S13 (`feat/s13-impresso`), F1 JS/CSS + cor com passo nulo (`fix/f1-js-css`), auditoria 2ª leva (`fix/auditoria-ia-2`), inventário de telas; seed abertura F1 (D-176) feito por mim.
- Inventário de telas entregue (scratchpad `inventario-telas.md`): 25 ok, 3 faltam; seção 6 "Estilo existente" repassada ao S13; agente de rascunho de UI disparado para navegação, links do preview, aviso em Padrões do ano, T28 e ajustes 4b.
- Rascunho de UI entregue: Fazer agora = links do Preview (1 h), aviso em Padrões do ano (4 h, disparado em `feat/t07-impacto`), painel como entrada (3 h), 2 links de T12 (1,5 h); 1, 3 e 4 esperam o S13 (mexem em `painel.py`/`revista.py`). Inventário e rascunho versionados em `docs/telas/` (branch `feat/seed-abertura-f1`).
- S13 entregue (bdc32ca em `feat/s13-impresso`): tela do impresso, "Revista Impressa Atualizada", planilhas F1/F2 com gabarito do TS antigo célula a célula; sem migração. Minha verificação da suíte e revisão django-reviewer em andamento. Itens 1, 3 e 4 do rascunho de UI disparados em `feat/ui-navegacao` (a partir do S13).
- Usuário respondeu as 5 perguntas do inventário (D-177), todas conforme recomendado.
- Revisão do S13: 0 críticos, 3 importantes; correções enviadas (D-178).
- `fix/f1-js-css` entregue: d873252 (cor com passo nulo = âncora maior, gabarito vindo do Python) + 1cac45c (CSS/animações sem duplicação; screenshots em repouso idênticas). Minha verificação em andamento.
- Entregues: S13 correções (1ce0b17), UI navegação (e2d7459, `feat/ui-navegacao`: preview, `/`→Painel, módulo Temporada, `?template=`; `nucleo` antes de `django.contrib.admin` em INSTALLED_APPS), T07 impacto (9fe75a5, `feat/t07-impacto`). Verificações minhas rodando.
- Usuário (grill-me rodada 2): item da matriz, PDF/PNG/JPG, um a um num modal com texto alternativo opcional (D-180); quer rever a exclusão pela tela (rodada 3).
- `fix/f1-js-css` verificado por mim: régua ok, suíte OK (8 pulados), `makemigrations --check` limpo.
- Usuário pediu página web de acompanhamento sincronizada; agente criando (artifact com banco compartilhado, atualizado por mim via ArtifactData).
- Rodada 3 do grill-me respondida (D-181): exclusão de item, tarefa e descritor pela tela com confirmação forte; arquivo apagado só sem referência.
- Verificados por mim: S13 1ce0b17 e UI e2d7459 (suíte OK, 8 pulados; migrações limpas). T07 rodando. D-180/D-181 disparadas em `feat/item-exclusao`.
- Página de acompanhamento: https://claude.ai/artifact/7RnMUM3c9irbwHcAGEBdG2 (banco: meta/geral, itens/<id>, plano/<código>; atualizo via ArtifactData). Dashboard vazio criado por engano: https://claude.ai/artifact/MhpqVSjr2saLwuhbx6jPhC. Apagado a pedido do usuário.
- Horários das entradas de hoje no state.md a partir de ~11:00 estavam adiantados em relação ao relógio (12:19 -03 real às 12:19); de agora em diante, hora do sistema.
- Ensaio dos 5 merges (worktree descartável): 0 conflitos, fixtures sem mudança, suíte OK (8 pulados), régua ok. Merges reais 24f7256..b31d17e com a learning da D-181; push feito.
- Preparo do S17 disparado em `feat/s17-preparo`: roteiro, ensaio em banco descartável, lista de usuários sem dados pessoais, ações destrutivas só por escrito, README/CLAUDE.md propostos.
- `examples/` apagada a pedido do usuário (cópias de `revista/modelo/PDFs Matriz Comunitária/`); docstring do `test_importacao.py` aponta a pasta nova; teste de importação com os 3 PDFs: 24 OK. Sem commit.
- `fix/auditoria-ia-2` entregue (7 commits A–H, 335 OK). Ensaio do merge sobre 9a574ae: conflitos em `revista.zip` (regerar) e `admin/templates.py` `usado_por` (fica a versão da integração, com `reverse` e `?template=`); suíte rodando.
- Leva: 835bec5 (remove `examples/`) + 3c74ac2 (merge `fix/auditoria-ia-2`: `usado_por` da integração, zip regerado; ensaio com suíte OK, 8 pulados; árvore igual ao ensaio fora a docstring já testada). Push feito.
- Usuário reavalia React × Django admin (D-121); telas mostradas são do editor React antigo (`editor/src/projetos/ListaProjetos.tsx`, `ano/TelaAno.tsx`). Apagar `editor/` bloqueado no roteiro do S17. Envio ao design em espera (usuário também é do design).
- Preparo do S17 entregue (77835dc em `feat/s17-preparo`): roteiro `docs/s17-carga-2026.md`, ensaio sem erros (198 descritores e 1093 tarefas, iguais ao extrator antigo nas 8 etapa × CC; 29 parceiros/58 revistas com os cortes de 2025), comando `criar_usuarios` (CSV fora do git, link de senha), README/CLAUDE propostos, ações destrutivas A–D só no texto (editor/ bloqueado). Minha verificação rodando.
- D-183: opção B escolhida; protótipo da grade de cortes disparado em `feat/ui-b-cortes`.
- Banco local: migrações 0011/0012 aplicadas; carga 2026 de cadastros, templates e matriz Comunitária (3 PDFs) feita; sem superusuário ainda.
- `feat/s17-preparo` (77835dc) verificado por mim com os PDFs montados: suíte OK, 0 pulados; `makemigrations --check` limpo.
- Usuário respondeu as 3 perguntas do S17 (D-184): cortes digitados, LP 2EF com 8 (PDF), intervalo 25 pela tela.
- `feat/item-exclusao` entregue: e93babb (D-180) + 299de99 (D-181), migrações 0013 (texto_alternativo) e 0014 (grupos); código da tarefa na confirmação = `D01 100-150`; arquivo apagado via `post_delete` + on_commit só sem referência; rota `preview/<id>/arquivos/itens/<nome>`. Minha suíte + revisão de segurança rodando.
- Usuário aprovou o código da tarefa `D01 100-150` (D-181).
- Revisão de segurança do item/exclusão: 0 críticos, 1 importante (PDF em branco no iframe); correções enviadas (D-185).
- D-186: HTMX liberado; workflow do time de telas B disparado.
- `feat/item-exclusao` (cb6b8b4) verificado por mim: suíte OK (8 pulados), migrações limpas. Prontos para merge: `feat/item-exclusao` e `feat/s17-preparo`.
- Ensaio dos 2 merges (item-exclusao + s17-preparo): conflitos em `admin/matriz.py` (imports: mantidos `path, reverse`, `format_html`, `CAMPO_SESSAO` e `lote.rota`) e `revista.zip` (regerado); suíte OK com os PDFs (0 pulados), régua ok. Merge real idêntico ao ensaio; push.
- 14:50 Workflow das telas B terminou (25 agentes): integração em `integ/ui-b` 3401dd9; suíte 519 OK com PDFs (verificada por mim), Playwright 26/26 (relatório do agente). Porta 8080 = editor React antigo; telas B ficam no Django (8000).
- Usuário aprovou as telas B ("mais do que aprovadas"); polimento de CSS/HTMX/JS fica para depois. Merge `integ/ui-b` → `refatoracao-django` (7b55ee8): conflitos em `urls/__init__.py` (mantidos `conta/` e `cortes/`) e `admin/matriz.py` (imports da integ/ui-b); suíte 521 OK com PDFs; trail check sem conflito; push.
- Usuário pediu para desligar os contêineres do React e do Mongo e subir só os novos.
- D-187: React (editor), API e Mongo parados, removidos e tirados do compose; sobram `db` e `app`. O volume do Mongo foi mantido. 8000 responde e 8080 está desligada.
- Commit do compose (D-187) feito a pedido do usuário; state.md em commit próprio.
- D-188: CRUD de cortes para todos menos Impresso já existia na grade; teste `test_todos_os_grupos_menos_impresso_gravam` adicionado (6 testes OK).
- D-189: grade de cortes ganhou 'Adicionar parceiro' (7 testes OK). Auditoria das telas B (back sem UI, links errados por perfil) disparada em segundo plano.
- Auditoria das telas B concluída: 5 lacunas bloqueiam o trabalho, 1 link dá 403 ao Impresso (painel → escolher matriz no admin, confirmado por mim).
- D-190: blueprint das 21 lacunas aprovado (S0–S9); S0 em execução.
- S1 (35d2cd0) + correção (5e8bf95): links do painel e mensagens sem admin nem 403. O Playwright achou o bloqueio de 30 s ao navegar entre ficha e revista: D-191 (mesma pessoa assume) + botão de copiar sem nome acessível. Suíte 527 OK; Playwright 26/26 numa pilha isolada (porta 8014). A pilha de dev foi encerrada à força (137) ao subir a isolada e foi religada.
- S2: matriz atribuída pela ficha do projeto (sessão de bloqueio da ficha), faixa "Falta escolher a matriz (etapas)" no preview e na ficha da revista (fora do resolvido, hash intacto), nome do projeto editável na própria revista, renomear parceiro na grade com confirmação quando revistas validadas perdem o Validado (simulação em transação desfeita). Suíte OK, Playwright 26/26.
- S3 (D-192): `/ui/anos/` abre o ano pela tela B; Pedagógica abre 2027, fora de sequência não grava, Impresso só lê (403 no POST). Suíte 541 OK; Playwright 19 OK, 7 pulados por falta de credenciais E2E no ambiente.

### 2026-11-03
- S4 planejado (plano aprovado: série TDD → paralelo revisor Django + E2E → correções). `npx skills find django formset` só achou skills com 1 e 4 instalações: nenhuma instalada.
- D-193: `/ui/anos/<ano>/` com etapas e componentes. Revisor achou 500 com código repetido no mesmo envio (corrigido + teste), limite só no HTML e consulta extra por linha (corrigidos). Suíte 547 OK; Playwright 19 OK, 9 pulados (2 novos do S4, sem credenciais E2E).
- S5 planejado e aprovado. 70bcdaa: paleta em módulo comum (testes do admin verdes sem mudança).
- D-194: paleta na página do ano. O E2E levantou e eu confirmei: cor em maiúsculas no banco × minúsculas do seletor → pedia confirmação e trocava a caixa (hash). Corrigido com teste. Revisor: amostra mostrava a cor não salva, valor lixo no re-render, textarea no novo padrão, erros sem `role=alert`/`aria-describedby` (corrigidos). Suíte 554 OK; Playwright 19 OK, 11 pulados (4 de `anos.spec.ts`, sem credenciais).
- Revisão de UX pedida (docx com 11 prints e 18 comentários). Só relatório, sem código. Causa achada do "2 parceiro(s) com alteração não salva" eterno e do aviso de saída sem mudança: em `ui/cortes.html`, `tr.querySelectorAll("input.input")` inclui o campo de Renomear e desloca a comparação célula × gravado.
- Plano da reforma de UX aprovado: `plans/revista-express-telas-b-ux.md` (U0–U10 + U8b página da revista + U9b editor de template com seções travadas; ~12,5 dias). Decisões: Alpine CSP + fetch somado ao HTMX, autosave com modal de impacto, Cortes como visão de Projetos, reforma antes de S6–S9, CDN liberada (jsDelivr com SRI). Registro formal D-195+ fica no U0.
- U1: Alpine CSP + SortableJS via jsDelivr com SRI na base, `componentes.js` vazio, design-system atualizado. Playwright completo rodou pela 1ª vez com credenciais: 28 OK, 4 falham só por falta da demo.
- `criar_demo --ano 2026` rodado no banco de dev (autorizado): revista DEMONSTRAÇÃO, matriz Demonstração e usuário demo-preview. Limpeza registrada em Perguntas em aberto.
- U2 (`beedcb6`, subagente): `servicos/impacto.py` (`perdem_validado` por savepoint desfeito, `avisar_perdidos`), `ImpactoForm(modal=True)`, `_componentes/impacto.html` + componente Alpine `impacto`. Decisão do agente: "impacto" = só quem perde o Validado (afetar revista não validada grava direto); matriz segue com a aproximação de `servicos/matriz.impacto`; admin mantém checkbox. Desvio: testes escritos depois do código.
- Branch de integração `feat/telas-b-ux` criada a partir de `feat/telas-b-lacunas`; onda 2 disparada (U3, U6, U8, U9b em worktrees, portas 8021–8024).
- Autorização do usuário: ao fim de cada onda, mergear em `feat/telas-b-ux` (com suítes verdes no resultado) e disparar a próxima sem esperar — onda 2 → 3 → 4.
- U8 (`521b894`) mergeado em `feat/telas-b-ux` (`116ff0b`): painel agrupado por parceiro, sem card "Próxima tarefa", select "Falta" trocado pelos contadores, "falta" neutro. Suítes no worktree: Django 578 OK, Playwright 34 OK.
- **Incidente:** o `.env` da raiz tem `COMPOSE_PROJECT_NAME=revista-eletronica`; copiado nos worktrees, fez U8 e U9b subirem o compose no projeto do dev do usuário (app recriado nas portas 8023/8024; `migrate` sem efeito e `criar_demo` trocando a senha do `demo-preview` no banco de dev, pelo U8; o que o U9b rodou ali está em apuração). App do dev recriado a partir da raiz (porta 8000, 200 OK). Plano corrigido: apagar a linha no `.env` do worktree.
- U9b (`2094ebf`) mergeado (`1123ded`): editor de template por seção (id em chip não editável, título, texto com barra N/I/lista/variável), ida e volta byte a byte nos seeds, id fora do fascículo → 422, prévia sem `## id` e erros por seção; Salvar explícito mantido. Suítes no worktree: Django 583 OK, Playwright 34 OK. No incidente, o U9b só rodou `up` e `migrate` (sem efeito) no projeto do dev. Decisões do agente: `passo1` fixo; numeração de passos só cresce; remover seção não abre modal (o Salvar já passa pela tela de impacto).
- U6 (`02fe6a8`) mergeado sem conflito (`29b3e75`): menu Painel · Projetos · Matrizes · Templates · Impresso; seletor "2026 ▾" no cabeçalho (popover nativo + Alpine `seletorAno`) com "Configurar <ano>" (`view_ano`) e "Abrir novo ano" (`abrir_ano`); `contexto.py:ano_atual` troca de ano mantendo rota e query (detalhe → mesmo parceiro, senão lista do ano); `_inicio` usa o ano da sessão. Suítes no worktree: Django 581 OK, Playwright 34 OK. Avisos: o worktree do Agent nasce em commit antigo (34f3579) — o agente precisa criar a branch a partir de `feat/telas-b-ux`; `item.spec.ts` quebra com 2027 aberto por `abrir_ano` (dois "D01").
- U3 (`556b12b`, `29deced`) mergeado (`f47cddf`), conflitos só de import e da linha de scripts na base. Protocolo de autosave em `ui_autosave.py` + `componentes/autosave.js` (`campoAuto`, `saida`); Cortes por célula (`cortes_celula`, 409 com `original`); Projeto e Variáveis na mesma rota `ui_projeto_campo`; 409 de bloqueio pelo `com_bloqueio` com `Accept: application/json`. No incidente, o U3 não tocou o banco de dev.
- Integração da onda 2: conflito de sentido U6 × U8 — o `ano.spec` do U6 usava o select `#filtro-falta`, que o U8 removeu; ajustado para `filtrarFalta` e o campo oculto `falta`. Django 617 OK, Playwright 41/41.
- Sessão nova (após /clear): nenhum worktree da onda 3 existia. Onda 3 disparada: U4→U9 em `feat/ux-u4-u9-linhas-mec` (`COMPOSE_PROJECT_NAME=ux-u4`, 8021) e U5→U8b em `feat/ux-u5-u8b-revista` (`ux-u5`, 8022).
- U4+U9 (`e4bbe49`, `354677b`) mergeados sem conflito (`35c80ce`). Worktree: Django 633 OK (8 pulados), Playwright 44/45 (falha `ano.spec.ts:7` igual na base: banco só com 2026). Decisões do agente: etapas sem reordenar, em ordem escolar (EF antes do EM, por série), renumeradas 1..N ao incluir (`ordem_escolar`/`renumerar_etapas`), o agente atribuiu a uma mensagem recebida no meio do trabalho; componente sem `ordem` (sem migração); linha nova pelo componente `linhaNova` (sem rota `ui_ano_linha`); `reordenar` em `ui_autosave.py` com impacto/409/422; 'Configurações' da MEC com popover nativo `popoverSob`. Achado: `cortes.spec.ts:19` (admin) dá `TooManyFieldsSent` em banco acumulado de E2E. Incidente leve: scratchpad compartilhado entre os 2 agentes, o U4 pode ter rodado segundos contra `ux-u5`; nada tocou o dev.
- U5+U8b (`8a777dd`, `6058ab3`) mergeados (`d0ff175`). Worktree: Django 627 OK, Playwright 42/42. Conflitos só de blocos novos no fim de `componentes.js`, `componentes/autosave.js` e `ui.css` (mantidos os dois lados). Decisões do agente: corrigiu Enter duplicado no `campoAuto` (dois modais); protocolo do U3 ganhou `trocar: {id: html}`, `simular=`/`modal=` e eventos `autosave:salvo|falhou|cancelado`; `arquivoSoltar` em `autosave.js`; sem 'Remover' arquivo (back não tem); sem menu '⋯' (Impresso virou link); mensagem de tamanho em `servicos/arquivos._ler` mudou.
- Integração da onda 3 (ux-integ, 8030): Django 643 OK (8 pulados), `makemigrations --check` limpo, Playwright 45/46. A falha era interação U4 × U8b: o spec novo do U8b preenchia `#novo-parceiro`, que o U4 passou para um `<template>` aberto pelo botão; corrigido com o helper `novoParceiro` (`446c8f5`), spec 2/2 OK.
- Onda 4 disparada: U7 (U7a lista com abas e ações em massa; U7b página do projeto com abas) em `feat/ux-u7-hub-projetos`, `ux-u7`, porta 8021, scratchpad `u7/`.
- U7 (`cb0fbe4` U7a, `99e64da` U7b) mergeado sem conflito (`93026a3`). A branch saiu de `446c8f5`; o resultado difere dela só no `state.md`, então as suítes do agente valem para a integração: Django 667 OK (8 pulados), `makemigrations --check` limpo, Playwright 48/48 com banco novo e com banco usado. Inventário em `test_nenhuma_acao_perdida` e `test_nenhuma_acao_da_ficha_perdida`; `atribuir_matriz` em `servicos/matriz.py`. Decisões do agente: abas Cortes/Variáveis do hub herdam os nomes de rota `cortes`/`ui_variaveis` (antigas viram `*_antiga`, 302); página do projeto com `?aba=`; checkbox da Lista leva o ParceiroAno, parceiro sem projeto também tem linha; Dados e Passos e cores no mesmo form; `revista/lista.html` removido. Specs `impacto`/`impresso`/`painel` passaram a esperar `Salvo às` visível (o `toContainText` achava o texto escondido pelo `x-show`); por que a corrida ficou consistente com o U7b está em aberto.
- Revisão do usuário (8 prints). Causa dos 'estilos quebrados' confirmada com Ctrl+F5: CSS antigo no cache do navegador (`runserver` serve `/static/` sem Cache-Control nem versão). Corrigido em `311bf1f`: storage `nucleo/estaticos.py` põe `?v=<mtime>` em todo `{% static %}`. Descartado: middleware com `Cache-Control: no-cache` (o `runserver` entrega estáticos antes dos middlewares). Correções disparadas em 3 worktrees: A toggle do contador + filtros Componente/Template/Matriz/Situação no painel (`ux-fa`, 8021); B lista de Projetos agrupada por parceiro como o painel (`ux-fb`, 8022); C alça única à esquerda nos descritores com teclado pela alça, editor de template com uma seção por vez, tarefas comparadas ao React (`ux-fc`, 8023).
- Revisão 2 do usuário (página do projeto). `098cdae`: `[hidden] { display: none !important }` em `ui.css` — `.card { display: flex }` vencia o atributo e a aba Passos e cores mostrava Nome e Variáveis. Modelo mental confirmado pelo usuário: Projetos › Variáveis/Cortes = definições do ano; página do projeto = sobrescrita. A paleta do ano já tinha tela (`/ui/anos/<ano>/`, 'Configurar 2026'), mas o usuário não a achou. Agente D (`feat/ux-fix-pagina-projeto`, `ux-fd`, 8024): cabeçalho com hierarquia, sai o botão da planilha, cores como 5 amostras herda/sobrescreve, passo como grade etapa × componente com herdado visível, cortes transpostos sem rolagem horizontal, texto de autosave uma vez só.
- Agente de auditoria página por página disparado (só relatório; skills impeccable critique + ecc:click-path-audit + ecc:accessibility; `ux-audit`, 8031; relatório em scratchpad/audit/relatorio.md).
- `7957240`: regressão minha do `311bf1f` corrigida — `static("revista/")` (pasta) recebia `?v=` e o preview montava `/static/revista/?v=N`+`styles.css`, revista sem estilo. Versão só em arquivo; teste `test_pasta_fica_sem_versao`.
- `e4b65f7`: menu Impresso só com `perms.nucleo.marcar_impressa`; Admin só para `is_superuser` (testes `MenuPorPerfilTest`; suíte Django inteira OK). A tela do Impresso continua acessível por URL em só leitura.
- B (lista de Projetos agrupada, `a41e4a9`) mergeado em `47fd5f7` sem conflito.
- Disparados: E lista de Projetos com badge numérico de pendências, Preview/Zip como ícones e tags suaves (`ux-fe`, 8025); F diff do Impresso por palavra, só o trecho que mudou para copiar, rótulos humanos (`ux-ff`, 8026).
- Auditoria concluída (relatório em scratchpad/audit/relatorio.md, heurísticas 28/40). Mais grave: texto da seção da revista se perde sem aviso (só grava com "Salvar seção"). Itens repassados: A (pendência "matriz sem etapa" leva à MEC), E (ações em massa desabilitadas sem marcação), F (LP/MT iguais na lista do Impresso; link "O que mudou" da revista ia ao admin). Agente G (`feat/ux-fix-auditoria`, `ux-fg`, 8027): perda de texto da seção, botão vazio vazando `url`, ids técnicos, configuração do ano (Salvar × "salva sozinho", `.input:disabled`), excluir descritor 403 ao Impresso, pseudo-abas de Templates, abas em 390 px. Pendente do usuário: criar matriz/template (S6, S7), usuários (S9), downloads que vão ao admin.
- Usuário: tags em tons neutros confirmadas (agente E segue o DESIGN.md); S6–S9 ficam para depois desta rodada.
- C (`a32c9b9`, `a309abb`, `e106c05`) mergeado sem conflito: alça única à esquerda com ↑/↓ e aria-live; template com uma seção por vez (prévia só da ativa; 1ª com erro abre); tarefas no grid do EditorEscala React (≥/< e ações na mesma linha, ícones). A falha de preview que o agente viu já estava corrigida em `7957240`.
- A (`4e6d8e5`) mergeado em `8985208`: filtros Parceiro/Componente/Template/Matriz/Situação + contador toggle (`button aria-pressed`); pendência "matriz sem etapa" abre a matriz. Conflito só em `estaticos.py`/`test_ui_base.py` (mesma correção do preview dos dois lados; mantida a da base). Suíte Django OK.
- E (`b861c50`) mergeado: balão de pendências, Preview/Zip como `.btn-icone`, tags `.tag`/`.tag-azul`/`.tag-lilas` (croma 0.018, quase neutras), ações em massa desabilitadas sem marcação.
- D (`fd9430f`) e G (`a423feb`…`94a918c`) mergeados sem conflito; suíte Django OK, `makemigrations --check` limpo. D: cabeçalho com pares rótulo/valor, sai o botão da planilha, cores como 5 amostras (escolher a cor do ano apaga a sobrescrita), passo por etapa com "Sem linhas vazias" ≠ herdar, cortes por etapa sem rolagem; removidos `ui_projeto_linha`, `projeto_linha.html`, `projeto_adicionar.html`. G: texto da seção da revista com autosave (perda de dado resolvida), vazio.html sem botão órfão, rótulos humanos nas seções, ano com `.input:disabled` e botões nomeados, excluir descritor 403 ao Impresso, Templates sem pseudo-abas, abas com fade em 390 px.
- Pergunta do usuário: token CSRF em `hx-headers` no `<body>` — esperado (padrão HTMX + Django), não é segredo.
- Editor de template mostrou tags Django cruas: `editar.html`, `revista_secao.html` e `templates.css` foram reformatados pelo Prettier do VS Code fora do git (16h44–16h45). Restaurados do commit (patch no scratchpad). `.vscode/settings.json` trata `**/templates/**/*.html` como `django-html`, sem formatar ao salvar (entrou em `ca03252`, junto da learning do Alpine CSP).
- Learnings da sessão commitadas: scratchpad compartilhado e `Salvo às` visível (em `311bf1f`), Alpine CSP com propriedade declarada (em `ca03252`).
- F (`b267933`) mergeado sem conflito: diff do Impresso por palavra (SequenceMatcher), contexto de 1 parágrafo, copiar só o trecho mudado, rótulos "5EF · D01", LP/MT visível na lista, link da revista vai à tela B.
- Lista de Projetos (pedido do usuário): coluna Situação por revista (Em preparo / Pronta para validar / Validada / Impressa / Arquivada); balão conta só pendências de preparo (antes contava Validado e Impresso, por isso todos davam 8); `.btn-icone[data-dica]` com dica imediata em CSS; ações centralizadas. Suíte Django OK.
- Lista de Projetos estourava a borda direita: a dica escondida (::after com opacity 0) contava na área de rolagem da tabela. Agora display:none fora do hover e ancorada à direita.
- `762a2e2`: lista de Projetos com Situação fixa em 12rem e Ações com min-width 7.5rem e respiro (pedido do usuário); agente de integração avisado.
- `f00c85d`: cor por situação (Em preparo neutra, Pronta para validar âmbar, Validada azul, Impressa verde, Arquivada tracejada); classes `.tag-ambar`, `.tag-verde`, `.tag-apagada` em ui.css.
- Limpeza do banco de dev (pedido do usuário): 11 parceiros "E2E…" apagados com projetos (11), revistas (17) e cortes (22). Ficaram TESTE/SAEGO 2, Novo parceiro/SAESE, DEMONSTRAÇÃO (demo do `criar_demo`, usada pelos specs). Backup antes: scratchpad/dev-antes-limpeza-e2e.sql (2,3 MB).
- Verificação final (`ux-integ`): Django 701 OK, Playwright 51/51; sem rolagem lateral em 1440/1024/768/390. Responsivo mergeado em `95cc0af` (Lista empilhada abaixo de 848 px; Padrões do ano no celular).
- Decisão do usuário: "projeto primeiro" — nome do projeto é a identidade principal; parceiro é contexto. Agente H (`feat/ux-fix-nomes`, `ux-fh`, 8028) aplica em Lista, revista, projeto, painel e Impresso.
- 9EF antes de 5EF no preview: `etapa.ordem` só seguia a lógica escolar quando a etapa era criada pela tela B (U4). `4de9cff`: `ordem_escolar`/`renumerar_etapas` foram para `models/cadastro.py`; `Etapa.save` renumera o ano por `update` (save daria recursão); migração 0015 renumera os anos existentes; teste `OrdemEscolarPorQualquerCaminhoTest`. Efeito: revista validada cuja ordem mudar perde o Validado (a ordem entra no hash). Commit feito com a suíte completa ainda rodando.
- Componentes Z44905 e Z84552 apagados do banco de dev a pedido do usuário (sem dependentes; sobram LP e MT). Backup: scratchpad/dev-antes-componentes-z.sql.
- Agente H terminou ("projeto primeiro", `721229e` em `feat/ux-fix-nomes`): Lista com nome do projeto como link e parceiro em cinza; revista com título "<projeto> · <componente>", pares Parceiro/Ano e trilha Projetos de 2026 › projeto; painel e Impresso na mesma regra; `models` intocado (hash não muda). Merge fica para 04/11.

### Para 04/11 (pedido do usuário: terminar o que falta)
1. ~~Confirmar a suíte Django com `4de9cff`~~ (OK, 8 pulados) e rodar `migrate` no banco de dev (aplica a 0015; o preview passa a mostrar 5EF antes de 9EF).
2. Fazer `git merge --no-ff feat/ux-fix-nomes` em `feat/telas-b-ux` e rodar a suíte Django.
3. Rodar o Playwright completo numa stack isolada (`ux-integ`, 8030) no resultado; depois commitar o `state.md`.
4. Descartar a reformatação do Prettier em `templates.css` (só formatação).
5. Perguntar ao usuário: onda 5 (U10) e S6–S9.

### 2026-11-04
- Retomada: 0015 já aplicada no dev; `feat/ux-fix-nomes` ainda não mergeada; `templates.css` segue modificado só por formatação.
- Merge de `feat/ux-fix-nomes`; Django 703 OK; Playwright 51/51 depois de recriar a demo e o ano 2025 (apagados na limpeza de 03/11).
- `templates.css` local: além da formatação, remove o `border-radius` de `.tpl-indice a`; não descartado.
- `templates.css`: usuário confirmou que a remoção do `border-radius` foi dele; commitado.
- Anotação do trail l-9fb3f4a9: como preparar o banco de dev para o Playwright depois da limpeza.
- Plano `plans/revista-express-telas-b-ux.md`: 33 caixas de U0 a U9 marcadas (todas têm commit na branch); U10 segue com 2 caixas abertas.

### 2026-11-04 (tarde)
- trail atualizado para 0.28.1 (`trail upgrade`).
- `CLAUDE.md`: nova seção "Finding code" manda usar `trail ask`/`grep`/`callers` antes de grep/Read e `trail check` antes de commitar. Camada `--deep` do trail ficou de fora (precisa de chave de API e custo; só se a busca errar).
- Plano da onda 5 escrito e aprovado: `plans/revista-express-onda5-u10.md` (U10a tabela rolável, U10b estados, U10c fichas em paralelo; U10d crítica do impeccable + Playwright em 1440/1280 depois da integração).
- Etapa 5.1 lançada a partir de `0a3ba86`: U10a (`feat/ux-u10a-tabela-rolavel`, compose `ux-u10a`, porta 8021), U10b (`feat/ux-u10b-estados`, `ux-u10b`, 8022), U10c (`feat/ux-u10c-docs`, sem docker).
- Usuário autorizou (04/11): ao fim de cada etapa da onda 5, testar, mergear e seguir para a próxima sem perguntar, até o fim da onda. Exceção: a limpeza do banco de dev (5.4) lista antes e espera confirmação.
- U10c mergeado (`2a19eba`, só docs). Divergências achadas pelo agente: (1) célula travada desliga a planilha de Variáveis inteira (`autosave.js:156-159` com 409 sem `atual`); (2) Variáveis sem proteção contra sobrescrita (rota não compara `original`); (3) mensagem de parceiro novo ainda manda "salve" (`urls/cortes.py:novo_parceiro`); (4) `lotes/template.html:11` ainda leva ao admin. (3) e (4) entram no lote do U10d; (1) e (2) esperam o usuário.
- Usuário: as divergências (1) e (2) de Variáveis entram no U10d, junto com (3) e (4).
- U10a mergeado (`c10830a`): `.tabela-rolavel` + `tabelaRolavel` (Alpine), sombra esq. na `.fixa` (`--sombra-borda-esq`), dir. no `::after` sticky do invólucro; sombra vertical do painel (`data-rolou-y`) saiu pela Flat Rule do DESIGN.md. Worktree: Django 703 OK, Playwright 55/55. Preparo de worktree: `imp-e2e` precisa de `is_staff=True`.
- U10b mergeado (`9cfa0c8`). Etapa 5.2 na integração: Django 712 OK (8 pulados), makemigrations limpo, Playwright 56/57. Única falha: `cortes.spec` 'preenche os cortes de 2 parceiros' — `Max number of fields exceeded` na grade do admin (`/admin/nucleo/corte/`) com 30 parceiros (26 `E2E`); limite do Django 1000. Bug real (30 parceiros reais quebram a grade do admin), anterior ao U10; vai para o U10d. `estados.spec` falhou 1 vez em 2 rodadas (`alpinePronto` estourou 5 s): intermitente, U10d endurece.
- U10d lançado de `a9854f0`: passo 0 (Variáveis 409 por linha e sem sobrescrita, textos velhos, limite de campos da grade do admin, `estados.spec` intermitente) + crítica do impeccable + Playwright em 1440/1280.
- Usuário: "+ Novo projeto" do vazio chega na aba Cortes com a linha "Adicionar parceiro" aberta (enviado ao U10d); "Novo template" do vazio segue no admin até o S7.
- U10d mergeado (`66b0870`, commits `8cc2abc` e `1a27159`): passo 0 a–f, projeto `desktop-1440`, lote do impeccable (crítica 30/40, P1 corrigidos), `design-system.md` atualizado, 3 learnings. Na raiz: Django 716 OK, makemigrations limpo, Playwright 120/120, 0 pulados. D-203 (limite de campos) e D-204 (trava por linha) registradas.
- Limpeza do dev listada: usuários `e2e`, `imp-e2e`, `demo-preview`, `e2e-outra`; parceiro DEMONSTRAÇÃO e matriz Demonstração; 50 parceiros `E2E…`; 14 componentes "Componente E2E…" em 2026; ano 2025 vazio. Aguarda confirmação.
- Limpeza do dev aplicada (transação única, ensaio antes, trava para manter os 3 projetos reais). Saíram 3 usuários, 51 parceiros, 45 projetos, 55 revistas, 14 componentes, 70 cortes, a matriz Demonstração e o ano 2025. Ficaram o `e2e` (inativo, sem senha) e o template "E2E editor por seção", travados pelo `TemplateVersao` só-inserção.
- Plano do U10 commitado (`7e7a3be`). Usuário: opção 1 para todas as entidades, ou seja, excluir só o que não está em uso (D-205).
- Usuário pediu as regras de negócio num MD em `docs/`. Agente lançado em worktree, branch `feat/docs-regras-negocio`, arquivo `docs/regras-de-negocio.md`, só leitura de código, decisões vigentes e learnings. Em paralelo, o agente de planejamento da D-205 segue rodando.
- Plano da D-205 escrito em `plans/revista-express-exclusao.md`: E0 base (serviço `exclusao.py`, rota `ui_excluir`, permissões 0016, `Template.arquivado_em` 0017), depois E1–E5 em paralelo. ~15 h de agente. Correção: a tela B não exclui Matriz hoje, só tarefa e descritor.
- `docs/regras-de-negocio.md` (511 linhas, 10 seções com a fonte de cada regra) mergeado (`10901a6`, branch `f7c4304`). A seção 10 lista 11 divergências entre as decisões e o código; as 5 principais são a D-205 por fazer, o `modelo-er.md` (bloqueio e foto), os limites da D-055 vindos de `Etapa.escala_max` e o aviso de impacto diferente no admin.
- Usuário respondeu a D-205: Admin apaga o ano inteiro pela tela (D-206); template sem uso sai com as versões, por todos menos o Impresso (D-207); só o Admin exclui ano. "Desativar parceiro" não ficou claro: pergunta refeita. Plano atualizado: `Template.arquivado_em` saiu, a 0017 só troca o trigger, o E4 caiu para 1,5 h. E0 lançado.
- Usuário: sim ao "desativar parceiro" (D-208). Campo e serviço enviados ao E0 em andamento; a grade fica com o E2.
- E0 mergeado (`54677aa`, commit `312c48a`): `servicos/exclusao.py`, rotas `ui_excluir` e `ui_parceiro_ativo`, migrações 0016–0018. Na raiz: Django 747 OK (8 pulados), makemigrations limpo. Dev ainda sem as migrações. E1–E5 lançados em paralelo a partir de `54677aa`. Specs de ano: abrir o próximo ano e apagá-lo no mesmo teste, porque o `abrir_ano` só abre o maior ano + 1. O E4 corrige os specs que gravavam no template real "Padrão (F1)".
- E3 mergeado (`7d6859a`, commit `1390870`; Django 748 OK, Playwright 132/132). O "Excluir matriz…" ficou numa `.zona-perigo` no fim da página, e não no `.acoes` do topo, seguindo o `design-system.md` §5 e o padrão do "Excluir descritor". O que impede a exclusão da matriz são os parceiros que a usam. O scratchpad é compartilhado entre os agentes E1–E5: cada um passou a usar a própria subpasta (`excl-eN/`).
- Migrações 0016–0018 aplicadas no banco de dev, com a autorização do usuário. O servidor responde (`/` 302, `/admin/login/` 200).
- Usuário autorizou (04/11): mergear E1, E2, E4 e E5 quando terminarem e seguir com a integração (Django, makemigrations, Playwright nas duas larguras no dev, seção 9 de `docs/regras-de-negocio.md`) sem perguntar.
- E5 mergeado (`0247dc5`, commit `02b0e46`; Django 755 OK, Playwright 128/128). Com o `ExclusaoAdminMixin`, o "Excluir" do admin leva ao `ui_excluir`, e o `delete_selected` sumiu, junto com o 500 do template. `AnoAdmin` usa `delete_ano`. `desativado_em` fica só leitura no admin: desativar passa pelo serviço. A grade de Cortes (`cortes.py:121`) passou a usar `parceiros_do_ano`, o que pode conflitar numa linha com o E2.
- E1 mergeado (commit `eede0f1`; Django 749 OK, Playwright 132/132). A lixeira "Excluir ano" aparece só para o Admin. Etapa e componente têm "Excluir" por linha (Pedagógica, Mídias e Admin; o Impresso não vê). O spec abre 2027 e apaga o mesmo ano. Pendência: o `linhas.spec.ts` deixa componentes "Z…" em 2026; vai excluí-los na integração.
- E2 mergeado (`a659a4c`, commit `b9a99b3`; Django 750 OK, Playwright 134/134). A grade tem lixeira no nome do parceiro e o selo "desativado". Na integração (`7961672`), o filtro repetido de `urls/cortes.py` saiu, porque a `grade` comum já usa `parceiros_do_ano` desde o E5, e a coluna do parceiro em 390px passou para 9–10rem.
- E4 mergeado (`09831b3`, commit `be10375`; Django 750 OK, Playwright 132/132). Template tem lixeira na lista e `.zona-perigo` no editor. A causa do "Atualizado E2E" no "Padrão (F1)" era o `revista-textos.spec.ts`: agora ele e o `templates-editor` e o `templates-admin` criam e excluem templates próprios (helper `e2e/tests/templates.ts`).
- `linhas.spec.ts` passou a excluir o componente que cria (`f6936c7`). `docs/regras-de-negocio.md` §9 reescrita e divergência 1 resolvida (`b5448a6`).
- Integração final: Django 764 OK (8 pulados), makemigrations limpo, Playwright 146/146 no dev, `trail check` sem conflito.
- O scratchpad compartilhado fez o E2 rodar 2 specs no banco descartável do E4. Os resultados não foram afetados, mas nos próximos lançamentos cada agente recebe a própria subpasta já no brief.
- Plano `plans/revista-express-exclusao.md` commitado.
- Limpeza do dev aplicada com a confirmação do usuário. Antes, ensaio com rollback e uma trava para manter os 3 projetos reais. Saíram: o template "E2E editor por seção" com as versões e o ano 2025, os dois pelo `servicos/exclusao.excluir`; 21 parceiros (DEMONSTRAÇÃO e 20 "E2E…"), com 21 projetos e 25 revistas; a matriz Demonstração; os usuários `imp-e2e`, `demo-preview` e `e2e-outra`. O `e2e` ficou inativo e sem senha, porque é autor de versões do "Padrão (F1)". A senha temporária do scratchpad foi apagada.

### 2026-11-05
- Containers `db` e `app` do dev estavam parados depois do reinício da máquina; foram subidos de novo (`docker compose up -d db app`).
- "Padrão (F1)" do dev ganhou a v9 com o texto da v1, sem os "Atualizado E2E…", com autor `otavio`, por `templates_texto.criar_versao`. Antes de gravar, o `perdem_validado` foi simulado: nenhuma revista perde o Validado, porque PAEBES, SAEGO e SAESE LP usam cópia própria da introdução.
- Usuário: esperar a ordem dele para começar S6–S9.
- App acessível pela rede sob demanda: `APP_BIND` no `docker-compose.yml` (D-209).
- Plano de S6–S9 atualizado ao código pós-reforma e aprovado (D-210). Agentes A (S6→S8), B (S7) e C (S9) lançados em worktrees paralelos a partir de `2dc2825`.
- Usuário autorizou (05/11): ao fim de cada onda de agentes, disparar a próxima sem perguntar, até terminar S6–S9.
- Usuário pediu: atualizar `modelo-er.md` e as docs desatualizadas. Agente D lançado (`feat/docs-atualiza-modelo-er`, só docs, sem docker; não documenta S6–S9, que o integrador atualiza depois do merge).
- Agente D mergeado (`cad2509`; commits `0a084a3`, `207c8a3`, só `.md`): `modelo-er.md` alinhado às migrações 0001–0018 (bloqueio por usuário D-191, foto inteira em READ COMMITTED); `regras-de-negocio.md` §10.1 com a situação de cada divergência (2, 3, 6, 7, 12 resolvidas; 4, 5, 8–10 abertas); README, CLAUDE.md, `docs/docker.md` e `docs/e2e.md` reescritos para o sistema Django; banners de histórico nos docs do sistema antigo.
- Para o Fechamento (docs que ainda dizem "só admin" e mudam com S6–S9): `regras-de-negocio.md` linhas ~152 (primeira matriz por comando), ~233 (criar template), ~423 e §8.2 (usuários), divergência 11; `docs/telas/telas-b.md` §2; README §4 "Ainda só pelo admin"; CLAUDE.md "o admin cobre o que ainda não tem tela"; fichas `templates`, `matriz`, `cortes`, `revista`, `anos`.
- Agente B (S7, `a878dc9`) mergeado sem conflito: rota `ui_templates_novo` (página `ui/templates/novo.html`), ano travado pela URL, componente do ano, fascículo da aba, texto inicial = esqueleto das seções fixas (`secoes_permitidas` + `form_para_corpo`), `IntegrityError` do nome repetido vira erro na tela. Worktree: Django 771 OK, Playwright 150/150. Integração (stack isolada `lac-integ`, dev parado): Django OK (8 pulados), makemigrations limpo. Pendente: o helper e2e `templates.ts` (`criarTemplate`) ainda cria pelo admin.
- Agente A (S6 `d6c7e60`, S8 `69eb7cc`) mergeado sem conflito. S6: diálogo "Nova matriz" na lista (`ui_matriz_nova`), leva ao reimportar; `vazio.html` ganhou 2º botão opcional (`url2`/`rotulo2`). S8: `gabarito_ids_csv` em `servicos/arquivos.py` (admin e `ui_revista_gabarito` usam a mesma), `cortes_exportar`, `ui_matriz_item_baixar` (GET, fora do bloqueio, reusa `servir`/`TIPOS_ITEM` de `urls/preview.py`), "Baixar planilhas" na ficha da revista. `grep admin:` nas telas B: só Admin e logout em `base.html`. Integração: Django 777 OK (8 pulados), makemigrations limpo. Pendente menor: `nucleo/revista.py:278` (`aviso_ids`, só no admin) ainda cita o gabarito do admin.
- Os 3 worktrees (A, B, D) nasceram em `34f3579` (main), não no HEAD de `feat/telas-b-ux`; os agentes refizeram a branch a partir de `2dc2825`. Em lançamentos futuros, o brief manda conferir o HEAD.
- Agente C (S9: `0ada222` regras de usuário em `nucleo/usuarios.py`, usadas pelo admin e pela B; `813b3a2` tela `/ui/usuarios/`) mergeado sem conflito. Permissão `auth.change_user` (criar: + `add_user`). Na B, um grupo por usuário; criar e redefinir senha em páginas próprias; superusuário sem restrição (como no admin). `usuarios.spec.ts` deixa um `e2e-midias-<sufixo>` desativado por execução.
- Fechamento: Django 790 OK (8 pulados), makemigrations limpo, Playwright na stack `lac-integ` com `E2E_ADMIN_*` e `E2E_IMPRESSO_*`: 159/160; a falha (`templates-editor.spec.ts:12`, chromium, timeout do `page.goto`) passou 3/3 isolada. Docs de S6–S9 e blueprint marcado como concluído em `eefde3c`, com a learning l-da214a7e (worktree de agente nasce no main).
- Usuário: "fecha o furo". D-211: `pode_editar` recusa alvo com grupo fora dos permitidos (Admin e Impresso); admin e tela B dão 403 em dados, senha, grupo e ativo do Impresso. Django 790 OK (8 pulados) na `lac-integ`. Commitado com a autorização do usuário.
- Usuário: o login e o índice do admin aparecem ao sair/trocar de perfil. D-212: login e logout B em `/conta/entrar/` e `/conta/sair/`, `/admin/login/` redireciona. Django 793 OK (8 pulados) no dev; Playwright 160/160 na `lac-integ` (derrubada depois). Commitado em `3843a76` com a autorização do usuário.
- Redigido o pedido de servidor para a Infra (2 vCPU/4 GB/40 GB, Docker Compose, proxy com HTTPS, backup de `pg-dados` e `app/media`). Medido no dev: app ~146 MB e banco ~106 MB de RAM, banco 26 MB e mídia 47 MB em disco.
- Revisão dos planos pedida pelo usuário: lacunas, UX (U0–U10), onda 5 e exclusão concluídos; Django S01–S16 concluídos; S17 parcial (faltam ações A, C, D e o preenchimento da equipe); S18 não começou.

- Usuário autorizou as ações A e C do S17 e o push para `dev`. A: tag `legado-express` (`30b0de3`) publicada. C: `fa7b748` (201 arquivos; `revista/modelo` → `docs/fontes/2025`). Suíte com os PDFs: 793 OK, 0 pulados. `docker-compose.yml` da D-209 commitado antes da tag (`30b0de3`).
- `api/.env` apagado a pedido do usuário (fora do git; a pasta `api/` sumiu do disco).
- Restos apagados a pedido do usuário: `contrato/`, `escala.html`, `script.js`, `styles.css`, `descritores.json`, `saida/`, `.env.example` da raiz (todos na tag `legado-express`). README e CLAUDE.md atualizados.
- D-214: compose de produção + `.env.prod.example`; smoke test em stack isolada (`revista-prod-teste`, apagada); Django 793 OK (8 pulados).
- `.env` local reescrito com as variáveis do sistema atual (COMPOSE_PROJECT_NAME, POSTGRES_PASSWORD=revista do volume existente, DJANGO_*); o antigo (chaves Express/Mongo) ficou só em backup no scratchpad da sessão. Banco do dev conecta (7 usuários).
- Revisado o texto do pedido à Infra: deploy por Portainer exige `docker-compose.prod.yml` como compose path, variáveis do `.env.prod.example` no stack, e o proxy precisa alcançar o app (porta só em 127.0.0.1).
- Learning salva: CSRF atrás do proxy com HTTPS (origem https nas confiáveis; curl com cookie Secure dá 403 falso).
- `INFRA.md` na raiz: guia da Infra (variáveis, stack no Portainer com `docker-compose.prod.yml`, Nginx com `Host`/50 MB/120 s, primeiro admin, backup com `pg_dump -Fc` + tar do volume `media`, restore, problemas comuns). Backup/restore testados num banco temporário do dev (7 usuários restaurados).
- `INFRA.md` seção 3 reduzida a pedido do usuário: só "proxy com HTTPS necessário" + particularidades (Host, 50 MB, 120 s, proxy em container). Push de `feat/telas-b-ux` para `main`.
- Learning salva: documento para a Infra diz o que o sistema exige, não como configurar o servidor.

### 2026-11-05 14:15
- Favicon da árvore amarela nas telas B (D-215).
- Plano do "Link de acesso" na tela Usuários (gerar pela tela o link de definir senha que hoje só sai pelo `criar_usuarios`); regra extraída para `nucleo/usuarios.py::caminho_definir_senha` (sem commit).
- "Link de acesso" na tela Usuários + páginas de criar senha fora do admin (D-216). Django 795 OK (8 pulados), makemigrations limpo, E2E usuarios 2/2 (o usuário `e2e` do dev estava desativado: reativado só para a execução e desativado de novo).
- UI de Usuários (D-217): ações em botões-ícone, "Mudar" só com mudança. Testes de usuários OK, E2E 2/2.
- Excluir usuário sem rastro (D-218). E2E de Usuários agora exclui o usuário que cria (antes deixava um desativado por execução). Sobram 4 `e2e-midias-*` antigos no banco de dev.
- 13 usuários conferidos/criados no banco de dev (12 da lista + fabiano.santana no Admin), sem senha: acesso pelo "Link de acesso". Comando `tornar_superusuario` (D-219).
- D-220: Admin atribui Impresso e marca impressa; migração 0019 aplicada no banco de dev.

### 2026-11-05 19:00
- D-221: a etiqueta "Em edição por … será pulado" deixa de contar o bloqueio do próprio usuário (Lista, Lotes, Validar). Testes: 90 OK nos módulos afetados.
- D-222: voltar/avançar numa página com bloqueio recarrega em vez de mostrar "perdeu o bloqueio". `bfcache.spec` passa com a correção e falha sem ela.
- D-223: diálogo "Alterações não salvas" (Salvar e sair / Descartar e sair / Continuar editando) ao sair por clique com campo sujo. Django completo OK (8 pulados); E2E autosave/bfcache 8 OK. Apagados os 7 parceiros "E2E …" que os specs criaram hoje no banco de dev; regional do SAESE devolvida ao vazio.
- D-224: `limpar_e2e` + `globalTeardown` do Playwright; comprovado numa execução real (apagou "E2E Autosave …" no fim). Template "E2E textos MW3X7F87" (de uma rodada que falhou) excluído pela regra da tela.
- D-225: helper `parceiroComProjeto` (e2e/tests/helpers.ts); o teste do diálogo (D-223) passou a gravar só no parceiro "E2E Saida …" que cria. 2/2 OK, limpos no fim.
- D-225: `autosave` (4 testes da planilha) e `estados` passaram a gravar só em parceiro próprio (helper `regional` em helpers.ts); 10/10 OK, limpos no fim. `variaveis` já cumpria a regra (só o comentário mudou).
- D-225 concluída: `painel`, `impresso`, `revista-textos`, `item` (revista própria) e `mec`, `linhas`, `autosave` descritor (matriz própria). `limpar_e2e` apaga matrizes "E2E …". Suíte E2E 164/164 na stack isolada `e2eiso` (porta 8040, desfeita no fim); 0 sobra.
- Learning da stack isolada para a suíte E2E (COMPOSE_PROJECT_NAME + -p, E2E_COMPOSE_PROJECT) commitada.

### 2026-11-05 20:30
- Análise de viabilidade do F2 animado (`example/`): mesmo SVG do sistema (ids `f2-` já sanitizados, árvore idêntica ao fixture); pergunta em aberto registrada.
- F1 e F2 vão ficar separados (conversa marcada para 06/11): pergunta em aberto registrada.
- Demo `example/f2-animado-tour/` (opção A): F2 real de SAEGO LP + svg-tour copiado + abertura animada; testada no Chromium (abertura de ~18 s, entrega sem salto de câmera, esmaecimento e modais do tour funcionando depois, "Pular" e "Rever"). Achado: textos dos passos 2 e 3 do tour não batem com o desenho.
- Avaliação "F2 a partir de dados" (como o F1): viável, custo e perguntas registrados nas Perguntas em aberto; nenhum código alterado.
- Ideia do F2 animado corrigida: animação dentro de cada passo do tour, não só na abertura; duas decisões de comportamento registradas.
- Demo refeita: animação por passo do tour (`animacao.js`, sem barra própria nem câmera própria). Testada no Chromium: visão geral esmaecida, passos 1 a 4, voltar (pronto), troca no meio (conclui), Explorar (tudo pronto), movimento reduzido (nada anima). Console sem erros.
- Polish (impeccable) na demo do F2: esmaecido de 0,18 → 0,32 (no celular a visão geral parecia vazia); o bloco começa a se montar quando a câmera do tour pousa (~650 ms, antes ~1.200 ms); seleção de texto no amarelo da revista. Visual da revista mantido (`revista.css`); o DESIGN.md do projeto é do editor, não da revista.
- Escala da demo do F2 corrigida: `--u` do tour de ~17px (até 22) para 13–15px no desktop e 16px no toque (o título do painel, 25,5px, ficava maior que o da seção, 24px; texto de 19px; botões de 47px); título da seção 28px; `maxZoom: 2.6` no tour (o passo 1 ia a 514%, a letra do desenho a ~60px; agora os passos ficam entre 207% e 260%). Só na demo; levar ao sistema é decisão em aberto.
- Bug da demo do F2 corrigido: dentro do passo ativo só as barras animavam; o texto já aparecia. Causa: o `svg-tour.js` tem `.svg-tour--dim .svg-tour-active * { opacity: 1 !important }`, que vence o `opacity: 0` inline das peças. Correção (só na demo, sem tocar o svg-tour): a animação grava também `--ab-o` e o `animacao.css` aplica com `#revista.svg-tour--dim .svg-tour-active [style*="--ab-o"] { opacity: var(--ab-o) !important }`. Conferido: logo após esconder, passo 2 com 4 de 176 peças visíveis (antes 176) e passo 3 com 5 de 1.571 (antes 1.571); as que sobram são as barras que crescem por escala.
- Decisão (b) revista: bloco não visitado fica escondido, não esmaecido. Demo ajustada (sem o estado "fantasma"); conferido no navegador: na visão geral os 4 blocos estão escondidos; no passo 2, o bloco do passo 3 continua escondido.
- Bug de enquadramento na demo do F2 corrigido: com os blocos escondidos desde o início, os passos 2 e 3 enquadravam o título e o descritor (219%). Causa: o tour mede a caixa do alvo (`getBBox`) ao trocar de passo, e as peças escondidas com escala 0 contavam como um ponto perto da origem, esticando a caixa até o canto superior esquerdo. Correção: em repouso a peça fica escondida só por opacidade; o deslocamento e a escala entram no 1º quadro da animação. Conferido: enquadramento dos 4 passos igual ao da versão sem animação.
- Usuário aprovou a demo ("ficou bom pra caramba"). Commit e push da pasta `example/` (exemplo original + demo) e de 2 aprendizados do trail (opacity !important do tour; esconder só por opacidade por causa do enquadramento).
- Tarefa 6 do F2 gerado: imagens dos itens no preview e no zip, zip sem SVG, arquivada conferida pelo sha da foto por item (D-245; fdfecd3); revisão aprovada com 4 minors corrigidos (NUL → 404, testes de login/403/nome parcial; 0e6918a); prova: 8 imagens carregam no revista.zip por file://. Suíte 883 OK, 8 pulados.
- Tarefa 7: Playwright inteiro na stack isolada `e2e-f2`: 155 OK; vermelhos esperados até a fase 3 (travam no "Validado" pela pendência `infografico`): `impacto.spec.ts`, `impresso.spec.ts`, `painel.spec.ts`, `revista-textos.spec.ts` (nos 2 projetos); `templates-admin` e `templates-editor` corrigidos para o F2 de 9 seções (8598596); `ano.spec.ts` instável no chromium (3/3 OK ao repetir). Gabaritos com os dados do docx real (D-248, 12b0b72). Conferência à mão no Firefox (zoom, minimapa, textos do `foreignObject`, tabela cheia): OK pelo usuário; Safari não conferido (sem Mac).
- Revisão da fase 2: Aprovado com ressalvas (2 Important, 7 Minor); correção em andamento. Usuário aprovou ("ok"): migração 0023 fica como está (apaga as cópias fora das 9 seções também em arquivada; só ganha comentário no cabeçalho); stack `e2e-f2` fica de pé até rodar de novo os specs com app depois da correção.
- Fase 2 do F2 gerado concluída: correção da revisão da fase (c33ae68: hash sem código/texto de etapa com Habilidades desligado, docs da main, código morto, teste da página F2 de arquivada); 0023 comentada (da8ac04); merge fast-forward de `feat/f2-f2` na `integ/f2-gerado` com o ok do usuário; stack `e2e-f2` derrubada com o volume.
- Conselho da fase 2 (5 analistas): O4 unânime — D-249 (deploy 1 a 4), D-250 (pendência do texto do clique), D-251 (arquivada antiga sem F2); T0 da fase 3 aplicada e mergeada (fast-forward) na `integ/f2-gerado`; suíte 885 OK. Auditoria do código (só leitura): 11 achados, riscos de escala no resolver por revista e no painel; itens "fazer agora" aguardam decisão.
- D-252 commitada na `integ/f2-gerado` (fast-forward da `feat/f2-f2`). Fora desta branch, já na `main` (PRs #8 a #11): kanban (D-253), limpeza de worktrees e Docker; a worktree `f2-f1` foi apagada.

### 2026-11-09 19:20
- Fora do repositório: agente `minimalista`, agente `conselheiro` e skill `/conselho` criados em `~/.claude` (mantidos como estão, sem comandante via Workflow).
- Diagnóstico do travamento da máquina às 11:05: sem OOM nem carga; suspeita sem prova no driver NVIDIA; SysRq sugerido para o próximo travamento.
- PR #6 aberto: `integ/docs-atualizacao` → `main`; conflitos do `trail check` justificados como falsos positivos.
- Inventário de branches: além da `main`, só 3 frentes vivas (`integ/docs-atualizacao`, `feat/f2-f1` só local, `feat/etapa-do-projeto` com WIP); colisão de numeração D-xxx registrada nas Perguntas em aberto.
- PR #6 mergeado na `main` (`0622996`) sem os 3 últimos commits da branch; `feat/f2-f1` confirmada no remoto.
- PR #7 (fase 1 do F2) fechado sem merge: D-236 mantida pelo usuário (fase 1 e 2 testadas juntas antes da `main`).
- D-246: banco sem ano — "Abrir ano" cria o 1º ano vazio (tela, admin e comando), na `fix/abrir-ano-vazio` a partir da `main`.
- `fix/abrir-ano-vazio` mergeada (fast-forward) na `integ/abrir-ano`, criada a partir da `main`; suíte 806 OK, 8 pulados.

### 2026-11-10 15:30
- D-253: skill `kanban` (global) e `kanban.md`; "Plano" migrado para cards. Branch `chore/kanban` saída da `main` para o PR não levar o F2.
- Raio-x das worktrees (87): 78 mergeadas e limpas apagadas (44 com arquivos do root, apagadas por container); `.env` do Express antigo guardados fora do repo; checkout da `main` mantido. Sobram 9: `main`, `f2-f1`, `f2-f2`, `ano-vazio`, `docs`, `etapa` (14 commits fora de tudo), `s7` (só `graft/` solto), `revista-eletronica` (`django`, 07/10) e um destacado do S07.
- PRs mergeados na `main` com o ok do usuário: #8 (`integ/abrir-ano`, D-246) e #9 (`integ/docs-atualizacao`, conflito do `state.md` resolvido mantendo as duas sessões). Em seguida, o PR da `chore/kanban`.
- `feat/etapa-do-projeto` fica parada por decisão do usuário (K-034 volta ao Backlog como pausada); branch e worktree `revista-express-etapa` intocadas.
- Pastas sobressalentes apagadas: `revista-express-ano-vazio`, `revista-express-docs` e as 2 últimas worktrees de agente (s7; S07 solto, guardado na branch local `arquivo/s07-agente`). Ficam 5 worktrees: `revista-eletronica` (tem o `.git`), `main`, `etapa` (pausada), `f2-f1`, `f2-f2`. Stacks Docker das worktrees apagadas continuam de pé (ano-vazio rodando; agent-*, uibchk, revista-e2e paradas).
- Docker: 15 stacks das worktrees apagadas derrubadas (agent-*, ano-vazio, uibchk, revista-e2e) com 20 volumes de banco; ficam as stacks/volumes de `revista-eletronica` (dev), `f2-f1`, `f2-f2`, `revista-express-f2-*` e `etapa-projeto`. 94 volumes anônimos soltos (sem dono identificável) não foram tocados.
- PR com a pausa da etapa do projeto (K-034), a limpeza de worktrees e Docker e o learning "branch que vai sozinha para a main sai da main".
- Learning: limpeza de worktree com arquivos do root termina por container; stacks Docker saem à parte (PR #11).
