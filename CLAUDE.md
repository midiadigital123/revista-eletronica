# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Finding code

Use `trail ask "<task>" --source` (or `trail grep` / `trail callers`) before grep or reading whole files. Run `trail check` before committing.

## Project Overview

**Revista Express** monta as revistas eletrônicas de resultados de avaliação da Fundação CAEd
(SAEGO e outros parceiros). Uma revista = **projeto × componente** (LP, MT), com dois fascículos:
**F1** (escalas de proficiência por etapa: 2EF, 5EF, 9EF, 3EM; descritores D01… mapeados à BNCC,
2 a 5 padrões de desempenho) e **F2** (infográfico svg-tour). Sistema **Django + PostgreSQL** em `app/`.
O dia a dia roda em telas próprias ("telas B": menu Painel · Projetos · Matrizes · Templates ·
Impresso, HTMX + Alpine); toda função do back tem controle na tela B
(D-189, D-210); o admin do Django é ferramenta do superusuário.

O sistema antigo (Express + Mongo + React: `api/`, `editor/`, `revista/`, `scripts/`) foi apagado
(D-213), junto com o protótipo estático (`escala.html`, `script.js`, `styles.css`) e `contrato/`;
tudo vive na tag `legado-express`. As fontes SAEGO 2025 (PDFs e planilhas) ficam em `docs/fontes/2025/`.

Leia antes de mudar algo: `state.md` (decisões D-xxx, append-only), `docs/regras-de-negocio.md`
(regras vigentes e divergências), `docs/modelo-er.md`, `docs/telas/telas-b.md` e
`docs/telas/design-system.md` (antes de mexer numa tela), `docs/variaveis.md`.

## Running

```bash
docker compose up -d --wait db
docker compose run --rm app python manage.py migrate
docker compose up -d app                      # http://localhost:8000
docker compose run --rm app python manage.py test              # OK; 8 pulados sem os PDFs SAEGO
docker compose run --rm app python manage.py makemigrations --check
node app/nucleo/static/revista/f1/regua.test.mjs
cd app/e2e && npx playwright test             # com o app de pé e E2E_ADMIN_USUARIO/E2E_ADMIN_SENHA
```

Suíte E2E inteira (precisa da demonstração): stack isolada, ver `docs/e2e.md`.

Worktrees: a de trabalho (`../revista-express-trabalho`) tem `.env` próprio (ignorado pelo git) com
`COMPOSE_PROJECT_NAME=revista-express-trabalho` e `APP_PORT=8001`: banco e volume próprios, sem disputar a
porta 8000 do dev. Sem `.env`, o compose usa o nome da pasta e sobe um banco vazio. PDFs SAEGO para os testes
de importação: montar em `/pdfs` (`-v "<pasta>:/pdfs:ro"`); sem eles, 8 testes são pulados.

## Architecture

- `app/sistema/`: settings (`DATABASE_URL`, `pt-br`, `USE_TZ`) e urls.
- `app/nucleo/`: app único. Um arquivo por área em `models/`, `admin/`, `urls/` (um `include`
  por módulo; `urls/ui_*.py` são as telas B) e `servicos/` (regra de negócio fora do admin:
  `cascata`, `resolver`, `pendencias`, `validacao`, `foto`, `html`, `f2`, `empacotar`, `planilhas`,
  `importar_matriz`, `matriz`, `abrir_ano`, `bloqueio`, `arquivos` (capa e itens), `impacto`, `exclusao`).
- Telas B: `templates/ui/` e `static/ui/`. A regra fica em módulo comum (`cortes.py`, `matriz.py`,
  `lotes.py`, `planilha_variaveis.py`…) ou em `servicos/`, e o admin importa dele: nunca duplique a regra.
- `app/nucleo/permissoes.py`: tabela papel × ação, fonte única (4 grupos: Pedagógica, Mídias
  Digitais, Admin, Impresso). Mudou a tabela? Migração de dados nova que sincroniza os grupos.
- `app/nucleo/variaveis.py`: lista fixa das variáveis `{{x}}` dos templates.
- Comandos: `carregar_cadastros`, `importar_matriz`, `carregar_templates`, `abrir_ano`,
  `criar_usuarios`, `tornar_superusuario`, `criar_demo`, `limpar_e2e` (o Playwright o roda no fim).

### Regras que o código garante

- Ano em toda tabela, com FK composta (`nucleo/db.py::fk_composta`, sempre com `reverse_sql`);
  o teste de `pg_constraint` muda junto.
- Histórico com django-simple-history (exceto `Bloqueio` e `TemplateVersao`, que é só INSERT: um
  trigger recusa UPDATE sempre e DELETE fora da exclusão pela tela, D-207).
- "Validado" e "Revista Impressa Atualizada" enviam o hash visto; o servidor recusa se mudou.
- Escrita concorrente passa pelo bloqueio (`servicos/bloqueio.py`, expira em 30 s); teste de
  concorrência usa `TransactionTestCase`.
- Gravação nas telas B que tira o "Validado" de alguma revista abre o modal de impacto antes de gravar (D-202).
- Exclusão só do que nada usa, por `/ui/excluir/<modelo>/<pk>/` (D-205).
- Nenhum segredo no repositório: credenciais só no `.env`.

### Revista (F1 e F2)

A revista tem várias páginas, as mesmas no preview e no zip (`templates/revista/`: `_base.html`,
`index.html` = sumário, `f1.html` e um `f2.html` por infográfico ativo); o SVG do F2 é gerado por
`servicos/f2.py` a partir dos infográficos (D-233, D-239). `servicos/resolver.py` monta o JSON `dados-revista`; `static/revista/f1/script.js` desenha a régua
para 2 a 5 padrões (cores em `--color-padrao-k`, sobrescritas por projeto); `static/revista/f2/`
é o svg-tour copiado sem alteração.

F2 hoje (branch `integ/f2-gerado`, fases 1 a 4): gerado pelo servidor como SVG a partir dos
infográficos da revista (até dois: Alfa e Outras Etapas), preenchidos no passo "Infográficos" da
ficha da revista (regra em `nucleo/infografico.py`, D-254). O SVG enviado pelo design saiu (migração
0024); o impresso vê os textos dos infográficos, sem a imagem dos itens (`f2.textos_impresso`, D-256). Specs em `docs/superpowers/specs/2026-11-06-*.md` (D-227 a D-232), planos das
fases em `docs/superpowers/plans/`. `example/` guarda
protótipos estáticos fora do sistema (`f2-gerado/` é a fase 0, D-228), cada um com `LEIA-ME.md`.

Formato do F1 por etapa: `{scaleRange, cortes, Dxx: {topic, description, prerequisites[],
bncc: {practices, knowledge, skills[]}, scale: {padrao-1..N: [{level, fim, content}]}}}`.

## Conventions

- Textos, nomes e mensagens em português (PT-BR).
- `state.md` é atualizado no mesmo turno de cada decisão (regras no CLAUDE.md global).
- Atalho deliberado com teto conhecido leva comentário `ponytail:`.
- Fluxo git (D-226, D-231, D-263): nada é editado na worktree da `main`. Existe **uma** worktree fixa de
  trabalho, `../revista-express-trabalho` (não crie uma pasta por tarefa): a cada tarefa troque de branch
  nela, `git switch -c feat/<tema> integ/<tema>` (a `integ/<tema>` sai da `main`). Uma tarefa por vez.
  Pasta extra só para trabalho em paralelo com subagentes, e apagada (pasta, stack e volume) ao mesclar.
  Merge na `integ/<tema>` só com testes verdes; merge na `main` só depois do "ok" explícito do usuário.
- **Testes E2E nunca editam revista que o próprio teste não criou. Nunca.** Isso vale também para o que
  alimenta a revista: projeto, variáveis, cortes, textos, arquivos e template escolhido. O spec cria o
  próprio parceiro "E2E …" (a cascata gera o projeto e a revista) e edita só ele. O `limpar_e2e` apaga
  tudo no fim (D-224). Sem exceção para "volto o valor original no fim": se o teste falhar no meio, o
  dado real fica alterado.
