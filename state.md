# state.md — revista-express

## Estado atual
<!-- sobrescrever a cada atualização -->
Grill-me do novo modelo concluído (8 rodadas): D-046 a D-083 descrevem o redesenho (Django + PostgreSQL). Entidades levantadas: Ano, Parceiro, Matriz (por ano, etapa × CC, tarefa com intervalo, intervalo mínimo), Texto-modelo e blocos com marcadores, Cortes (parceiro × ano × etapa × CC, 1 a 4, grupos calculados), Projeto (cascata, nome, sobrescritas de bloco/cor/intervalo mínimo, Validado), Paleta global, Foto da revista (diff para o impresso), Bloqueio de escrita, 4 perfis.
Funcionando: nada novo em código; o sistema atual (Express + Mongo) segue como estava.
Quebrado/pendente: diagrama ER e modelos Django não escritos; lista de blocos de texto e de campos do projeto incompleta (aceitas como flexíveis); conferências visuais antigas (ver sessões anteriores).

## Próxima ação
<!-- sobrescrever: UMA ação concreta -->
Imprimir `docs/Modelagem_Banco_Conceitos_Essenciais.pdf` (v2 corrigido, 13 páginas) e ler a seção 1 (4 min).

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
- **Status:** ativa.

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
- **Status:** ativa. Lista de blocos em aberto.

### D-063 — Matriz e texto-modelo são escolhas separadas por parceiro × ano (2026-10-27)
- **Contexto:** proposta de Template = par matriz + texto-modelo.
- **Decisão:** o parceiro escolhe a matriz e o texto-modelo separadamente.
- **Motivo:** flexibilidade; na empresa as regras mudam rápido.
- **Descartadas:** Template como par fixo — engessa.
- **Arquivos afetados:** nenhum ainda.
- **Status:** ativa.

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
- **Status:** ativa.

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
- **Status:** ativa. Lista de marcadores em aberto.

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
- **Status:** ativa.

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
- **Status:** ativa.

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
- **Status:** ativa.

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

## Perguntas em aberto
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
