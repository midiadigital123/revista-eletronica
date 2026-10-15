# state.md — revista-express

## Estado atual
<!-- sobrescrever a cada atualização -->
Polish da UI dos projetos: 5 de 5 concluídos (D-022), sem commit.
Funcionando: escala no celular com o texto em linha própria; "Novo descritor", "Novo ano", "Adicionar parágrafo" com ícone Plus; "Excluir ano" destructive; lista com "agora mesmo"/"Livre"; console sem 404 do favicon. Editor 58 testes, typecheck e lint verdes.
Quebrado/pendente: teste manual no docker da sessão anterior (extrator novo) segue pendente. Detector impeccable acusa border-b-2 nas abas (ProjetoLayout.tsx:169): falso positivo, é o sublinhado de 2px da DESIGN.md (raio só no foco).

## Próxima ação
Revisar o diff com `git diff editor/` e decidir o commit.

## Plano
1. [x] Extrator Python: topic, fim, split por habilidade, sem CORTES_SEM_NUMERO
2. [x] Contrato + API: LinhaEscala.fim / item, ITEM_MAX_BYTES (+ linhaSchema do Mongoose com fim/item)
3. [x] Editor: cards com ≥/<, linha com início/fim
4. [x] PDF do item: POST/GET /api/projetos/:slug/itens, pacote com <caderno>/arquivos/itens/<id>.pdf, editor anexar/remover
5. [x] Revista: hover no lugar de "Ver mais"; "Ver item" só com PDF (iframe)

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

## Perguntas em aberto
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
