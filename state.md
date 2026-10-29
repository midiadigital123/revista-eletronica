# state.md — revista-express

## Estado atual
<!-- sobrescrever a cada atualização -->
Passo 13 de 22: Fase C (S07, S08, S15) e S16 concluídos e juntados em `refatoracao-django` (merges --no-ff f418c10, 470c86c, 5eb9cbd, 51b329f; sem push nem PR).
Funcionando: em `refatoracao-django`, 217 testes OK (8 de PDF pulados), `makemigrations --check` limpo, régua ok, Playwright f1-fixture + pagina + zip 18/18, `trail check` sem conflito. Preview `preview/<id>/` (comando `criar_demo`, usuário `demo-preview`), zip por revista, `abrir_ano 2027`.
Quebrado/pendente: cor da linha com `passo` nulo (JS × Python); preview sem rota para itens; alt dos itens; foco no SVG em 390px; seeds de 2026 aguardam a Pedagógica.

## Próxima ação
<!-- sobrescrever: UMA ação concreta -->
Liberar a Fase D: S11a, S11b1 e S11c em paralelo, a partir de `refatoracao-django`.

## Plano
<!-- plano completo: plans/revista-express-django.md -->
1. [x] S01 — Esqueleto Django + PostgreSQL + Playwright
2. [x] S02 — Modelos de cadastro e matriz + FK composta
3. [x] S03 — Parceiro_ano, corte, projeto, revista, texto, controle
4. [x] S03b — Revista JS/CSS para 2 a 5 padrões
5. [x] S04 — Cadastros iniciais + importador de matriz
6. [x] S05 — Templates: formato, validação, seed
7. [x] S06 — Cascata dos cortes
8. [x] S09 — Serviço de SVG e capa
9. [x] S10 — Bloqueio
10. [x] S14 — Perfis e permissões
11. [x] S07 — Resolver, foto, hash, pendências
12. [x] S08 — Página única F1 + F2
13. [x] S15 — Zip por revista
14. [ ] S11a — Admin: cadastros, cortes, matriz  ← próximo (Fase D)
15. [ ] S11b1 — Admin: templates
16. [ ] S11b2 — Admin: cópia por seção
17. [ ] S11c — Admin: projeto, variáveis, arquivos, lote
18. [ ] S12 — Painel + Validado
19. [ ] S13 — Impresso + planilhas
20. [x] S16 — Abrir ano
21. [ ] S17 — Carga 2026 + desligar o antigo
22. [ ] S18 — E2E da temporada

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
- **Status:** ativa. Verificado por mim: 162 testes OK (8 de PDF pulados), `makemigrations --check` limpo. Revisão (django-reviewer) em andamento. Limite `ponytail:`: leitura da origem sem trava (edição concorrente pode entrar pela metade). A confirmar com o usuário: `Tarefa.arquivo` compartilhado entre anos.

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

## Perguntas em aberto
- [x] (D-115 a D-124) Varredura 7 agentes (2026-10-29), perguntas 55–70: cópia por seção; juntar lado a lado × proposta; preview sem template; ciclo de vida da revista sem cortes; SVG/capa derrubam Validado; variável com escopo parceiro; sugestão do ano anterior; painel da temporada; copiar em lote; validar em lote com hash; React × Django admin; bloqueio × otimista; fascículo fixo; editor textarea × etiquetas; FK composta; matriz duplicada entre anos — depende de: usuário
- [x] (D-125) Correções técnicas da varredura (sem decisão do usuário): ER sem TextoModelo/BlocoTexto/ProjetoBloco e com Revista/RevistaFasciculo/Projeto.ano_id; TemplateVersao só de inserção como base da fusão; hash em Python com JSON canônico (só cai a revista que usa a variável, corrige D-097); bloqueio por `INSERT … ON CONFLICT … WHERE expira_em < now()`; cascata com `FOR UPDATE` em ParceiroAno, foto em REPEATABLE READ, clone em uma transação; SVG sanitizado (defusedxml, lista de tags, 3 MB, ids prefixados); Markdown com `html: false` e `{{var}}` validado por regex; zip com JSON/SVG embutidos no index.html; atalhos do F1 só fora do F2; revalidar seções × ids do SVG no Validado e ao salvar template; marcar D-063 (texto), D-070 e D-088 (texto_modelo) como substituídas e reescrever D-093 — depende de: aprovação das perguntas 55–70
- [x] (D-114) Template F1: o texto aparece antes e depois das escalas; usar seções fixas (`## introducao`, `## fechamento`) como no F2? — depende de: usuário
- [x] (D-110 a D-113) Grill-me fascículos, rodada 4 (2026-10-29): 8 perguntas (juntar textos, estrutura do template F2, sobrescrita no F2, revista incompleta, SVG/capa no impresso) — depende de: usuário
- [x] (D-150) `Tarefa.arquivo` copiado no abrir ano aponta para o mesmo arquivo nos dois anos (D-148); se um passo futuro apagar o arquivo ao trocá-lo, o outro ano perde. Aceitável? — depende de: usuário
- [x] (D-153) As cores do F1 entram no "o que mudou" do impresso (D-151)? — depende de: usuário
- [x] (D-153) Corte igual a 0 ou à escala máxima: a cascata aceita (D-055), o JS recusa a etapa (D-131). Fechar onde? — depende de: usuário
- [ ] Cor da linha com `passo` nulo: JS pinta pelo topo (base da entrada de cima) e diverge do Python (âncora maior) com tarefas esparsas (D-154). Corrigir no `script.js` depois do S08 — depende de: S08 terminar
- [x] (D-158) Número destacado da régua: branco sobre o vermelho do padrão 1 (#f72628) dá 3,99:1, abaixo do AA (4,5:1). Trocar para preto (5,3:1) ou escurecer o vermelho? (D-157) — depende de: usuário/design
- [ ] Itens de tarefa (imagem/PDF) sem texto alternativo: o modelo não tem campo (D-157) — depende de: usuário
- [ ] Lista completa de variáveis (D-107) — depende de: equipe pedagógica
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
- [ ] Admin pode clicar "Revista Impressa Atualizada"? (D-083 dá ao admin as permissões da Pedagógica, não as do Impresso) — depende de: usuário
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
