# state.md — Revista Eletrônica (editor + gerador)

## Estado atual
<!-- sobrescrever a cada atualização -->
Passo 7 de 7 concluído: Fase 5 fechada — E2E final 8/8 + 5 verificações novas passaram no Docker
Funcionando: tudo em http://localhost:8080 (login com rate limit, editor sem perda de texto, preview/zip sem localhost:3845, headers de segurança, CSP sem violação do Zod)
Quebrado/pendente: imagem padrão do hero (falta exportar do Figma); CP2 do usuário; commit e98d985 na branch `express-react` (a partir da main); na branch django esses arquivos seguem como não rastreados

## Próxima ação
<!-- sobrescrever: UMA ação concreta -->
Usuário abrir http://localhost:8080, entrar com o admin do .env e testar (CP2).

## Plano
Plano completo: `~/.claude/plans/eu-preciso-criar-uma-whimsical-hare.md` (v2, aprovado)
1. [x] CP0: commit 422cd19
2. [x] Fase 0 + CP1 (contrato aprovado): contrato (`docs/contrato.md`, `contrato/`) + esqueletos api/ e editor/ + fixtures → CP1 aprovação do contrato
3. [x] Fase 1 (8 agentes em paralelo): A1 auth ‖ A2 template ‖ A3 editor-casca ‖ A4 docker ‖ A5a api-projetos ‖ A5b bloqueio+imagens ‖ A6a editor-projeto ‖ A6b editor-ano
4. [x] Fase 2: A7 preview + zip
5. [x] Fase 3: A8 integração + E2E (cookie secure "auto" corrigido); CP2 adiado a pedido do usuário
6. [x] Fase 4: revisões R1 ‖ R2 ‖ R3 (nenhum crítico)
7. [x] Fase 5: correções R1/R2/R3 + E2E final (8/8)
8. [ ] CP2 usuário testa no navegador + decidir commit  ← agora

## Decisões
<!-- append-only -->

### ~~D-001 — Servidor Node só com stdlib~~ (2026-10-07 10:00) — ~~substituída por D-008~~
- **Contexto:** a equipe precisa de um lugar compartilhado para criar e editar projetos.
- **Decisão:** um único `server.js` com `node:http`, sem dependências.
- **Status:** substituída por D-008

### ~~D-002 — Modelo em pasta por projeto (JSON em disco)~~ (2026-10-07 10:00) — ~~substituída por D-009~~
- **Status:** substituída por D-009

### ~~D-003 — Campos editáveis via `campos.js` + `data-campo`~~ (2026-10-07 10:00) — ~~substituída por D-011~~
- **Status:** substituída por D-011

### ~~D-004 — Motor `montarPacote` com `dados.js` / `window.REVISTA`~~ (2026-10-07 10:00) — ~~substituída por D-011~~
- **Status:** substituída por D-011

### ~~D-005 — Bloqueio exclusivo em memória~~ (2026-10-07 10:00) — ~~substituída por D-010~~
- **Status:** substituída por D-010

### D-006 — Lixeira para projetos apagados (2026-10-07 10:00)
- **Decisão:** apagar um projeto não remove o dado de vez (no Mongo vira exclusão lógica, ver D-009).
- **Status:** ativa (adaptada ao Mongo)

### ~~D-007 — Docker com volume nomeado para data/~~ (2026-10-07 10:00) — ~~substituída por D-013~~
- **Status:** substituída por D-013

### D-008 — Stack: API Express + TypeScript, editor React + Vite (2026-10-07 15:00)
- **Contexto:** o usuário rejeitou a 1ª implementação, que tinha infra escrita à mão, tudo num arquivo, persistência em JSON e bloqueio em memória, além de remendos no script.js e `window.REVISTA`.
- **Decisão:** `api/` com Express + TypeScript em camadas (routes → controllers → services → models) e bibliotecas consolidadas. `editor/` com React + Vite + TypeScript + Tailwind, a mesma base do `menu-funcionalidade`. Pastas separadas, sem workspace.
- **Motivo:** escolha do usuário; código legível e manutenível pela equipe.
- **Descartadas:** stdlib pura (gambiarras); NestJS/Fastify (usuário escolheu Express); monorepo pnpm (usuário escolheu pastas separadas).
- **Arquivos afetados:** `api/`, `editor/`
- **Status:** ativa

### D-009 — Persistência em MongoDB (2026-10-07 15:00)
- **Decisão:** MongoDB com Mongoose. Coleções `users` e `projetos` (anos, descritores e escala como subdocumentos). Imagens no GridFS.
- **Motivo:** escolha do usuário; o documento espelha o formato da revista.
- **Descartadas:** JSON em disco (rejeitado), PostgreSQL e SQLite (usuário escolheu Mongo).
- **Status:** ativa

### D-010 — Bloqueio persistido no Mongo (2026-10-07 15:00)
- **Decisão:** campo `bloqueio {usuario, expiraEm}` no projeto, adquirido por `findOneAndUpdate` condicional (atômico), com TTL e heartbeat.
- **Motivo:** sobrevive a reinícios e funciona com várias instâncias.
- **Descartadas:** mapa em memória (rejeitado).
- **Status:** ativa

### D-011 — Revista gerada por template Handlebars com JSON embutido (2026-10-07 15:00)
- **Contexto:** o zip será aberto por `file://` (sem servidor), e os campos da página (título, intro, imagem e futuros) mudam por projeto.
- **Decisão:** `escala.html` vira template Handlebars. A API renderiza os campos da página nos placeholders e embute os descritores em `<script type="application/json" id="dados-revista">`. O `script.js` lê esse bloco. Preview e zip usam o mesmo render.
- **Motivo:** funciona por `file://`; tornar um campo editável = placeholder no template + campo no schema.
- **Descartadas:** `window.REVISTA` em `dados.js` (rejeitado); `fetch` de `dados.json` (não funciona em `file://`).
- **Status:** ativa

### D-012 — Login real com perfis (2026-10-07 15:00)
- **Decisão:** usuários com e-mail e senha no Mongo. Perfis `admin` (cadastra usuários) e `editor`; todos editam projetos.
- **Motivo:** escolha do usuário; o bloqueio mostra quem edita de forma confiável.
- **Descartadas:** só o nome (fraco); SSO Google (não escolhido agora).
- **Status:** ativa

### D-013 — docker-compose com mongo + api + editor (2026-10-07 15:00)
- **Status:** ativa

### D-014 — Execução por agentes com contrato primeiro (2026-10-07 16:00)
- **Contexto:** o usuário pediu agentes bem planejados e em paralelo.
- **Decisão:** a Fase 0 (feita por mim) congela o contrato, os pontos de registro e a infraestrutura comum. Depois, 8 agentes rodam em paralelo, cada um com pastas exclusivas. Os schemas Zod ficam em `contrato/` e são copiados para api/ e editor/ com checagem de hash. Express 5, bcryptjs, MSW só em DEV com VITE_MOCK=1.
- **Motivo:** o tempo cai de ~17 h para ~7–8 h sem conflito de arquivos.
- **Descartadas:** worktrees (os arquivos da raiz não estão commitados); um agente por camada em série (lento).
- **Status:** ativa

### D-015 — Fundação entrega login mínimo, bloqueio e mocks completos (2026-10-07 18:00)
- **Contexto:** a revisão do plano mostrou que os testes do A5a dependeriam do login (A1) e do bloqueio (A5b), e que os mocks teriam vários donos.
- **Decisão:** a Fase 0 implementa `auth` (login/logout/me), o serviço e as rotas de bloqueio, `exigirBloqueio`, o modelo/repository de Projeto, os mocks MSW de todas as rotas e os endpoints tipados do editor (`projetos/api.ts`) e `edicao.tsx` (contrato A6a↔A6b). A1 = usuários + seed + testes de auth; A5b = imagens + casos de borda do bloqueio.
- **Motivo:** os 8 agentes da Fase 1 ficam realmente independentes.
- **Descartadas:** agentes esperando uns pelos outros (perde paralelismo); stubs que lançam erro (testes não rodariam).
- **Arquivos afetados:** `api/src/{app,errors,config,db,logger,server}.ts`, `api/src/middlewares/*`, `api/src/modules/{auth,bloqueio,pagina,projetos/model,projetos/repository}`, `editor/src/{api,mocks,projetos/api.ts,projetos/edicao.tsx}`
- **Status:** ativa

### D-016 — Versões: TypeScript 5.9, Zod 4, Express 5, Mongoose 9, React 19, react-router 8, MSW 2 (2026-10-07 18:00)
- **Motivo:** o `typescript-eslint` não suporta TS ≥ 6.1; as demais são as estáveis atuais. Timestamps renomeados (`criadoEm`) quebram o `InferSchemaType` do Mongoose 9, por isso os documentos usam interfaces explícitas.
- **Status:** ativa

### D-017 — Ajustes da revisão da Fase 0 (2026-10-07 19:00)
- **Decisão:**
  - módulo `imagens/` (A5b) com as assinaturas `salvarImagem`, `abrirLeitura`, `removerImagens` e `copiarImagens`;
  - `Revista.pagina` = `PaginaTextos` (sem null);
  - `requireAuth` único em `modules/index.ts`, reconferindo o usuário no banco a cada requisição;
  - erros do Mongoose mapeados (VersionError 409, Validation/Cast 400);
  - helpers `definirCampoPagina`/`removerCampoPagina` (campo Mixed);
  - `novoBloqueio` exportado;
  - `nomeArquivoImagem` no contrato;
  - `salvar` do editor aplica a resposta no cache (`aplicar`) em vez de refetch;
  - mocks são da fundação: os agentes reportam divergências, não editam;
  - sem camada controller: routes (handler+Zod) → service.
- **Motivo:** a revisão adversarial apontou bugs (null em página importada → 500), lacunas de contrato e pontos onde agentes improvisariam.
- **Status:** ativa

### D-018 — Template sem o botão provisório de preview mobile (2026-10-07 20:00)
- **Contexto:** o fim de escala.html tem um bloco "BOTÃO PROVISÓRIO… remover depois de usar — não faz parte do site".
- **Decisão:** o A2 deixou esse bloco fora de revista/escala.hbs, para que ele não vá no zip entregue.
- **Motivo:** é uma ferramenta de desenvolvimento, e o comentário do próprio arquivo pede a remoção.
- **Status:** ativa (reverter = recolar o bloco no template)

### D-019 — Transação para a regra do último admin (2026-10-07 20:15)
- **Contexto:** contar admins e depois gravar permite que dois admins se rebaixem um ao outro e zerem os admins.
- **Decisão:** a checagem e a gravação ficam dentro de `session.withTransaction`. O Mongo passa a rodar como replica set de 1 nó (`--replSet rs0`) no compose, e os testes usam `MongoMemoryReplSet`.
- **Motivo:** o usuário pediu. É a solução correta e também habilita transações em outras operações de vários documentos.
- **Descartadas:** compensação (recontar e reverter), que funciona, mas o usuário quer a garantia transacional.
- **Quando:** depois que o A5a terminar, para não trocar o banco de teste no meio da verificação dele.
- **Arquivos afetados:** `docker-compose.yml`, `api/test/helpers.ts`, `api/src/modules/usuarios/service.ts`
- **Status:** ativa (implementada; teste de concorrência passou 5/5 isolado)

### D-020 — Cookie de sessão com secure "auto" (2026-10-07 21:00)
- **Contexto:** no Docker, NODE_ENV=production, mas o acesso é por http://localhost:8080. Com `secure: true` o cookie não era enviado, e o login "funcionava" mas não persistia.
- **Decisão:** `secure: "auto"` em api/src/app.ts. Com `trust proxy`, o cookie é secure quando a conexão chega por HTTPS.
- **Status:** ativa

### D-021 — Reconstrução em Django como trilha de aprendizado (2026-10-07 11:30)
- **Contexto:** o usuário quer aprender Django reconstruindo este sistema (skill mentor-django: ele escreve o código, Claude conduz).
- **Decisão:** novo projeto em `django/` neste repositório, Django 5.2 LTS, SQLite até o M9, MVP enxuto (Projeto → Ano → Descritor). O progresso fica em `JORNADA.md`. A versão Express+React (D-008) continua intacta, sem substituição.
- **Motivo:** reaproveita escala.html, styles.css e descritores.json; a LTS evita trocar de versão no meio do aprendizado.
- **Descartadas:** repositório novo (precisaria copiar os assets); paridade total no MVP (primeira vitória muito tarde); Django 6.1 (suporte mais curto).
- **Arquivos afetados:** `django/`, `JORNADA.md`
- **Status:** ativa

### D-022 — Correções de segurança da revisão R2 (2026-10-07 13:05)
- **Contexto:** o R2 apontou login sem rate limit, enumeração de e-mail por tempo, X-Forwarded-Proto fixo em http, editor sem headers de segurança e senha de exemplo aceita.
- **Decisão:** `express-rate-limit` só no `/login` (10 falhas/15 min por IP+e-mail, `skipSuccessfulRequests`, store em memória); bcrypt contra hash descartável quando o usuário não existe; `map` no nginx repassa o `X-Forwarded-Proto` recebido (fallback `$scheme`); CSP/X-Frame-Options/nosniff/Referrer-Policy só no `location /` (a /api já tem helmet); `config.ts` recusa SESSION_SECRET/ADMIN_SENHA começando por "troque".
- **Motivo:** biblioteca consolidada (D-008); a validação na config falha cedo e com mensagem clara.
- **Descartadas:** contador manual (reinventa a lib); deixar ADMIN_SENHA vazia no .env.example (seed silenciosamente não cria admin); store do limite no Mongo (uma instância só hoje).
- **Arquivos afetados:** `api/src/modules/auth/routes.ts`, `api/src/config.ts`, `api/test/auth.test.ts`, `api/package.json`, `editor/nginx.conf`, `.env.example`
- **Status:** ativa

### D-023 — Falhas de salvamento pendentes por chave (2026-10-07 13:40)
- **Contexto:** R3 achou que `repetir` guardava só a última falha e que qualquer sucesso a apagava (indicador "Salvo" com dado perdido).
- **Decisão:** `repetir` vira `Map` com a `descricao` da operação como chave (descrição inclui o ano); sucesso/423 limpa só a própria chave; "tentar de novo" reenvia todas. `beforeunload` em `useEdicaoProjeto` (fila, falha pendente ou campo sujo sem blur). Guard do `adquirir` por ref `montado` (StrictMode).
- **Descartadas:** `let vivo` no efeito (no StrictMode o DELETE da 1ª montagem poderia soltar o bloqueio da 2ª); chave sem ano (colidia D03 5EF × 9EF).
- **Arquivos afetados:** `editor/src/projetos/{AbaPagina,useBloqueio,useEdicaoProjeto}.tsx/ts`, `editor/src/projetos/ano/{TelaDescritor,ListaDescritores}.tsx`, `editor/src/projetos/projetos.test.tsx`
- **Status:** ativa

### D-024 — Assets do template locais; hero sem imagem padrão (2026-10-07 13:55)
- **Contexto:** R1: `escala.hbs` apontava para `localhost:3845` (Figma Desktop), quebrando zip e preview.
- **Decisão:** setas anterior/próxima viraram SVGs feitos à mão em `revista/assets/`, servidos no preview (`/preview/assets/:nome`) e incluídos no zip; `<img>` do hero só renderiza com `heroImagem`. PUT de imagem roda o multer antes de `exigirBloqueio`; headers de mídia removidos antes de erro; stream do GridFS destruído no `close`; fallback 4xx no errorHandler.
- **Motivo:** o servidor do Figma não respondia e não havia cópia no repo; hero vazio é melhor que imagem quebrada.
- **Descartadas:** manter URL do Figma (quebra offline/CSP).
- **Arquivos afetados:** `revista/escala.hbs`, `revista/assets/*.svg`, `api/src/modules/{revista/render,geracao/service,geracao/routes,imagens/routes}.ts`, `api/src/middlewares/{exigirBloqueio,errorHandler}.ts`, `api/test/{revista,geracao,imagens}.test.ts`, `docs/contrato.md`
- **Status:** ativa

### D-025 — Versão Express+React commitada na branch `express-react` (2026-10-07 13:35)
- **Contexto:** o usuário pediu o commit fora da branch `django`.
- **Decisão:** branch nova `express-react` a partir da `main` (422cd19), commit e98d985 com api/, editor/, revista/, contrato/, docs/, scripts/, docker-compose.yml, .dockerignore, .env.example e .gitignore (+ .env, .playwright-mcp/). Feito com índice temporário (`read-tree`/`commit-tree`), sem trocar de branch.
- **Motivo:** mantém a trilha Django isolada; não troca de branch, então `django/requirements.txt` e o trabalho do usuário ficam intactos.
- **Descartadas:** commit na `django` (usuário recusou); `git switch` para branch nova (removeria `django/requirements.txt` do disco e conflitaria no .gitignore).
- **Fora do commit:** django/, JORNADA.md, state.md.
- **Status:** ativa

## Perguntas em aberto
- [x] Quais achados do R1/R3 entram na Fase 5? → usuário aprovou R3 (ALTO 1–2, MÉDIO 3–5) e R1 (assets localhost:3845, bloqueio vs upload, headers em erro de stream + BAIXO 4–5); 2 agentes disparados em paralelo (editor/src/projetos ‖ api+revista). Candidatos: R3 ALTO 1–2 e MÉDIO 3–6 (perda de texto/bloqueio no editor); R1 ALTO imagens localhost:3845 no template, MÉDIO bloqueio vs upload lento, MÉDIO Content-Type errado em erro de stream — depende de: usuário
- [x] Checagem de "último admin" não é atômica → usuário decidiu: vale a transação (D-019).
- [x] Fase 5 — R2 aprovados e CORRIGIDOS: (1) rate limit no /login; (2) nginx X-Forwarded-Proto; (3) bcrypt fixo p/ e-mail inexistente; (4) headers de segurança no nginx do editor; (5) ADMIN_SENHA de exemplo — depende de: R1/R3 terminarem
- [x] Imagens do Figma (`localhost:3845`) quebram no zip offline → setas viraram SVG em `revista/assets/` (D-024).
- [ ] Imagem padrão do hero: exportar PNG do Figma para `revista/assets/` e usar no `{{else}}` de `revista/escala.hbs:17` — depende de: usuário exportar do Figma.
- [x] Reescrever em Django? → usuário decidiu reconstruir em Django como trilha de aprendizado, em paralelo (D-021).
- [x] Commitar state.md? → usuário: "comite tudo"; commitado na branch atual `django`.

## Sessões
### 2026-10-07 10:00
- Plano v1 aprovado; passos 1–3 implementados (stdlib) e testados.
### 2026-10-07 15:00
- Usuário rejeitou a implementação v1 (gambiarras). Tudo revertido: arquivos criados apagados; escala.html, script.js e descritores.json voltaram ao original.
- Novas decisões D-008 a D-013 coletadas com o usuário.
- Plano v2 de agentes aprovado (D-014), com revisão adversarial incorporada.
- CP0 commit 422cd19; Fase 0 concluída e revisada; CP1 aprovado; Fase 1 disparada.
### 2026-10-07 11:30
- Início da trilha Django (mentor-django): diagnóstico feito, MVP definido, JORNADA.md criado.
### 2026-10-07 (sessão nova)
- Usuário pediu para continuar as fases no código Express+React enquanto faz a trilha Django; CP2 adiado. Fase 4 disparada (R1 ‖ R2 ‖ R3).
- Fase 4 (nenhum crítico) e Fase 5 concluídas: D-022 a D-024; Zod `jitless` no editor (CSP); `.playwright-mcp/` no .gitignore; E2E final 8/8.
- Commits: e98d985 (express-react: api/editor/revista…) e 525dbd0 (django: config, app revista, JORNADA.md, .gitignore). Disco conferido igual ao express-react. state.md não commitado (pendente de decisão do usuário).
