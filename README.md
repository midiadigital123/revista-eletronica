# Revista Express

Sistema para montar as **revistas eletrônicas de resultados de avaliação** da Fundação CAEd.

Cada ano, a equipe cadastra a matriz (descritores e tarefas), os cortes de cada parceiro e
os textos. O sistema monta uma revista por **projeto × componente** (LP, MT), com dois
fascículos: **F1** (escalas de proficiência) e **F2** (infográfico em SVG). A revista é vista no
**preview**, validada e baixada como **zip** que abre offline. O impresso recebe "o que mudou"
e as planilhas.

É uma aplicação **Django + PostgreSQL** em `app/`. O dia a dia roda em telas próprias (as "telas B",
com menu Painel · Projetos · Matrizes · Templates · Impresso); o admin do Django continua para o
que não tem tela (seção 4).

---

## 1. Como subir

Pré-requisito: Docker com o plugin `compose`.

```bash
docker compose up -d --wait db
docker compose run --rm app python manage.py migrate
docker compose run --rm app python manage.py createsuperuser
docker compose up -d app
```

Abra `http://localhost:8000/` (vai para o Painel do ano mais novo; sem ano, para `/ui/anos/`) ou
`http://localhost:8000/admin/`.

- O compose sobe só `db` (PostgreSQL 17) e `app` (`docker-compose.yml`). Mongo, API e editor React
  saíram (D-187).
- Variáveis: `app/.env.example`. O compose lê o `.env` da **raiz**. Todas têm default de
  desenvolvimento; em produção, preencha `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=0`,
  `DJANGO_ALLOWED_HOSTS` e `POSTGRES_PASSWORD`.
- Porta: `APP_PORT` (default 8000), só em `127.0.0.1`.
- Cada worktree pode subir o próprio banco com `docker compose -p <nome> …`.
- Dados de demonstração para ver o preview: `docker compose run --rm app python manage.py criar_demo`
  (só com DEBUG; imprime a URL e a senha do usuário `demo-preview`).
- Detalhes de Docker, backup e restore: [`docs/docker.md`](docs/docker.md).

## 2. Como testar

| O que | Comando | Observação |
|---|---|---|
| Suíte Django | `docker compose run --rm app python manage.py test` | O esperado é OK; 8 testes dependem dos PDFs SAEGO e ficam pulados sem eles. |
| Com os PDFs | `docker compose run --rm -v "$PWD/<pasta dos PDFs>:/pdfs:ro" app python manage.py test` | Pasta: `revista/modelo/PDFs Matriz Comunitária/`. 0 pulados. |
| Migrações | `docker compose run --rm app python manage.py makemigrations --check` | Tem que dizer `No changes detected`. |
| Régua do F1 (JS) | `node app/nucleo/static/revista/f1/regua.test.mjs` | Sem dependências. |
| Navegador (Playwright) | `docker compose up -d app && cd app/e2e && npm ci && E2E_ADMIN_USUARIO=… E2E_ADMIN_SENHA=… npx playwright test` | baseURL `http://localhost:8000`; roda em chromium 1280 e 1440. Sem as `E2E_*`, os specs pulam em silêncio. |

## 3. Perfis

Grupos fixos, criados por migração. Tabela única em `app/nucleo/permissoes.py`; versão por ação em
[`docs/regras-de-negocio.md`](docs/regras-de-negocio.md#8-perfis-e-permissões).

| Grupo | Pode |
|---|---|
| **Pedagógica** | tudo do ano: cadastros, matriz, cortes, templates, padrões, projetos, variáveis, revistas, validar, excluir o que não está em uso |
| **Mídias Digitais** | o mesmo que a Pedagógica |
| **Admin** | o da Pedagógica + gerenciar usuários (só dá os grupos Pedagógica e Mídias Digitais) + apagar o ano inteiro |
| **Impresso** | ver tudo + marcar "Revista Impressa Atualizada" |
| superusuário | tudo; é o único que põe alguém em Admin ou Impresso, e o único que vê o botão "Admin" no cabeçalho |

Revista nunca é apagada (é arquivada) e usuário não é excluído (é desativado). Usuários em lote:
`manage.py criar_usuarios <csv usuario,grupo> --url <endereço>` cria sem senha e imprime o link
do Django para cada um definir a sua.

## 4. Jornada da temporada e onde cada passo acontece

Fichas de cada tela: [`docs/telas/telas-b.md`](docs/telas/telas-b.md).

1. **Abrir o ano** (`/ui/anos/`, "Abrir novo ano" no seletor de ano): copia etapas, componentes,
   padrões (cor e nome), matrizes e templates do ano anterior. Cortes, parceiros e escolhas começam
   em branco. O primeiro ano (2026) foi carregado por comandos: [`docs/s17-carga-2026.md`](docs/s17-carga-2026.md).
2. **Conferir o ano** (`/ui/anos/<ano>/`, "Configurar <ano>"): etapas, componentes e padrões do ano.
3. **Matrizes** (`/ui/matriz/<ano>/`): editar, duplicar, reimportar de PDF ou planilha.
4. **Cortes** (hub **Projetos**, aba Cortes): digitar os cortes de cada parceiro cria o projeto e as
   revistas dele.
5. **Em massa** (hub Projetos, aba Lista): "Atribuir matriz…" e "Atribuir template…".
6. **Templates** (Markdown com `{{variável}}`, lista em [`docs/variaveis.md`](docs/variaveis.md)) e
   **variáveis** de cada projeto (aba Variáveis, ou a ficha do projeto).
7. **Revista**: SVG do F2, capa, textos por seção; **preview**.
8. **Painel** (`/painel/<ano>/`): o que falta em cada revista; **Validado** um a um ou em lote.
9. **Impresso** (`/ui/impresso/<ano>/`): "o que mudou" + planilhas + "Revista Impressa Atualizada".
10. **Zip**: botão "Baixar zip" na linha de cada revista, na aba Lista de Projetos.

Desde S6–S9 (D-210), tudo o que o back faz tem tela B: criar matriz e template, baixar gabarito de
ids, arquivo do item, planilha de grupos de corte e planilhas F1/F2, e gerenciar usuários (link
"Usuários" no cabeçalho, só para o perfil Admin). O admin fica como ferramenta do superusuário;
o que resta só nele está na seção 2 de [`docs/telas/telas-b.md`](docs/telas/telas-b.md).

## 5. Onde está cada coisa

| Caminho | O quê |
|---|---|
| `app/sistema/` | projeto Django (settings, urls) |
| `app/nucleo/models/`, `admin/`, `urls/`, `servicos/` | um arquivo por área; `urls/ui_*.py` são as telas B |
| `app/nucleo/templates/ui/`, `app/nucleo/static/ui/` | HTML (HTMX + Alpine) e CSS/JS das telas B |
| `app/nucleo/management/commands/` | `carregar_cadastros`, `importar_matriz`, `carregar_templates`, `abrir_ano`, `criar_usuarios`, `criar_demo` |
| `app/nucleo/static/revista/` | JS e CSS da revista (F1 escalas, F2 svg-tour) |
| `app/templates_seed/<ano>/` | textos iniciais dos templates |
| `app/e2e/` | Playwright |
| [`docs/`](docs/) | modelo ER, regras de negócio, variáveis, telas, roteiro do S17 |
| [`plans/`](plans/) | planos de trabalho (refatoração S01–S18, reforma de UX, exclusão, lacunas das telas B) |
| [`state.md`](state.md) | decisões técnicas (D-001…), estado atual e perguntas em aberto |
| `api/`, `editor/`, `contrato/`, `scripts/` | sistema antigo (Express + Mongo + React), aposentado; o compose não o sobe. Fica como referência de visual (`editor/`) e de extração de PDF. Está também na tag `legado-express` |

## 6. Operação

- **Backup:** `docker compose exec db pg_dump -U revista revista > backup-$(date +%F).sql`.
- **Restore:** `docker compose exec -T db psql -U revista revista < backup-AAAA-MM-DD.sql` (banco vazio).
- Nunca faça commit do `.env`.

## 7. Documentos relacionados

| Arquivo | Para quê |
|---|---|
| [`docs/regras-de-negocio.md`](docs/regras-de-negocio.md) | Regras vigentes, com a fonte de cada uma, e divergências abertas. |
| [`docs/modelo-er.md`](docs/modelo-er.md) | Tabelas, FKs compostas, restrições, trigger e permissões do banco. |
| [`docs/telas/telas-b.md`](docs/telas/telas-b.md) | Telas fora do admin, rotas e o que ainda é só admin. |
| [`docs/telas/design-system.md`](docs/telas/design-system.md) | Convenções visuais e de código das telas B. |
| [`docs/variaveis.md`](docs/variaveis.md) | Variáveis dos templates. |
| [`docs/docker.md`](docs/docker.md) | Docker, backup e restore. |
| [`state.md`](state.md) | Registro das decisões técnicas e do estado atual. |
