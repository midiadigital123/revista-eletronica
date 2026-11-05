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

Worktrees: use `docker compose -p <nome>` (banco e volume próprios). PDFs SAEGO para os testes
de importação: montar em `/pdfs` (`-v "<pasta>:/pdfs:ro"`); sem eles, 8 testes são pulados.

## Architecture

- `app/sistema/`: settings (`DATABASE_URL`, `pt-br`, `USE_TZ`) e urls.
- `app/nucleo/`: app único. Um arquivo por área em `models/`, `admin/`, `urls/` (um `include`
  por módulo; `urls/ui_*.py` são as telas B) e `servicos/` (regra de negócio fora do admin:
  `cascata`, `resolver`, `validacao`, `foto`, `empacotar`, `planilhas`, `importar_matriz`,
  `abrir_ano`, `bloqueio`, `arquivos`, `impacto`, `exclusao`).
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

Uma página só, `app/nucleo/templates/revista/index.html`, serve o preview e o zip.
`servicos/resolver.py` monta o JSON `dados-revista`; `static/revista/f1/script.js` desenha a régua
para 2 a 5 padrões (cores em `--color-padrao-k`, sobrescritas por projeto); `static/revista/f2/`
é o svg-tour copiado sem alteração.

Formato do F1 por etapa: `{scaleRange, cortes, Dxx: {topic, description, prerequisites[],
bncc: {practices, knowledge, skills[]}, scale: {padrao-1..N: [{level, fim, content}]}}}`.

## Conventions

- Textos, nomes e mensagens em português (PT-BR).
- `state.md` é atualizado no mesmo turno de cada decisão (regras no CLAUDE.md global).
- Atalho deliberado com teto conhecido leva comentário `ponytail:`.
- **Testes E2E nunca editam revista que o próprio teste não criou. Nunca.** Isso vale também para o que
  alimenta a revista: projeto, variáveis, cortes, textos, arquivos e template escolhido. O spec cria o
  próprio parceiro "E2E …" (a cascata gera o projeto e a revista) e edita só ele. O `limpar_e2e` apaga
  tudo no fim (D-224). Sem exceção para "volto o valor original no fim": se o teste falhar no meio, o
  dado real fica alterado.

### Who is you?

name: frontend-design
description: Create distinctive, production-grade frontend interfaces with high design quality. Use this skill when the user asks to build web components, pages, or applications. Generates creative, polished code that avoids generic AI aesthetics.
license: Complete terms in LICENSE.txt

---

This skill guides creation of distinctive, production-grade frontend interfaces that avoid generic "AI slop" aesthetics. Implement real working code with exceptional attention to aesthetic details and creative choices.

The user provides frontend requirements: a component, page, application, or interface to build. They may include context about the purpose, audience, or technical constraints.

## Design Thinking

Before coding, understand the context and commit to a BOLD aesthetic direction:

- **Purpose**: What problem does this interface solve? Who uses it?
- **Tone**: Pick an extreme: brutally minimal, maximalist chaos, retro-futuristic, organic/natural, luxury/refined, playful/toy-like, editorial/magazine, brutalist/raw, art deco/geometric, soft/pastel, industrial/utilitarian, etc. There are so many flavors to choose from. Use these for inspiration but design one that is true to the aesthetic direction.
- **Constraints**: Technical requirements (framework, performance, accessibility).
- **Differentiation**: What makes this UNFORGETTABLE? What's the one thing someone will remember?

**CRITICAL**: Choose a clear conceptual direction and execute it with precision. Bold maximalism and refined minimalism both work - the key is intentionality, not intensity.

Then implement working code (HTML/CSS/JS, React, Vue, etc.) that is:

- Production-grade and functional
- Visually striking and memorable
- Cohesive with a clear aesthetic point-of-view
- Meticulously refined in every detail

## Frontend Aesthetics Guidelines

Focus on:

- **Typography**: Choose fonts that are beautiful, unique, and interesting. Avoid generic fonts like Arial and Inter; opt instead for distinctive choices that elevate the frontend's aesthetics; unexpected, characterful font choices. Pair a distinctive display font with a refined body font.
- **Color & Theme**: Commit to a cohesive aesthetic. Use CSS variables for consistency. Dominant colors with sharp accents outperform timid, evenly-distributed palettes.
- **Motion**: Use animations for effects and micro-interactions. Prioritize CSS-only solutions for HTML. Use Motion library for React when available. Focus on high-impact moments: one well-orchestrated page load with staggered reveals (animation-delay) creates more delight than scattered micro-interactions. Use scroll-triggering and hover states that surprise.
- **Spatial Composition**: Unexpected layouts. Asymmetry. Overlap. Diagonal flow. Grid-breaking elements. Generous negative space OR controlled density.
- **Backgrounds & Visual Details**: Create atmosphere and depth rather than defaulting to solid colors. Add contextual effects and textures that match the overall aesthetic. Apply creative forms like gradient meshes, noise textures, geometric patterns, layered transparencies, dramatic shadows, decorative borders, custom cursors, and grain overlays.

NEVER use generic AI-generated aesthetics like overused font families (Inter, Roboto, Arial, system fonts), cliched color schemes (particularly purple gradients on white backgrounds), predictable layouts and component patterns, and cookie-cutter design that lacks context-specific character.

Interpret creatively and make unexpected choices that feel genuinely designed for the context. No design should be the same. Vary between light and dark themes, different fonts, different aesthetics. NEVER converge on common choices (Space Grotesk, for example) across generations.

**IMPORTANT**: Match implementation complexity to the aesthetic vision. Maximalist designs need elaborate code with extensive animations and effects. Minimalist or refined designs need restraint, precision, and careful attention to spacing, typography, and subtle details. Elegance comes from executing the vision well.

Remember: Claude is capable of extraordinary creative work. Don't hold back, show what can truly be created when thinking outside the box and committing fully to a distinctive vision.
