# Revista Express

Sistema para montar as **revistas eletrônicas de resultados de avaliação** da Fundação CAEd.

Cada ano, a equipe cadastra a matriz (descritores e tarefas), os cortes de cada parceiro e
os textos. O sistema monta uma revista por **projeto × componente** (LP, MT), com dois
fascículos: **F1** (escalas de proficiência) e **F2** (infográfico). A revista é vista no
**preview**, validada e baixada como **zip** que abre offline. O impresso recebe "o que mudou"
e as planilhas.

Tudo roda num **Django admin** em `app/`, com PostgreSQL.

---

## 1. Como subir

Pré-requisito: Docker com o plugin `compose`.

```bash
docker compose up -d --wait db
docker compose run --rm app python manage.py migrate
docker compose run --rm app python manage.py createsuperuser
docker compose up -d app
```

Abra `http://localhost:8000/` (vai para o Painel do ano mais novo) ou `http://localhost:8000/admin/`.

- Variáveis: `app/.env.example`. O compose lê o `.env` da **raiz**. Todas têm default de
  desenvolvimento; em produção, preencha `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=0`,
  `DJANGO_ALLOWED_HOSTS` e `POSTGRES_PASSWORD`.
- Porta: `APP_PORT` (default 8000), só em `127.0.0.1`.
- Cada worktree pode subir o próprio banco com `docker compose -p <nome> …` (sem
  `container_name` fixo).
- Dados de demonstração para ver o preview: `docker compose run --rm app python manage.py criar_demo`
  (só com DEBUG; imprime a URL e a senha do usuário `demo-preview`).

## 2. Como testar

| O que | Comando | Observação |
|---|---|---|
| Suíte Django | `docker compose run --rm app python manage.py test` | O normal é **OK com 8 pulados** (testes dos PDFs SAEGO). |
| Com os PDFs | `docker compose run --rm -v "$PWD/<pasta dos PDFs>:/pdfs:ro" app python manage.py test` | Pasta: `revista/modelo/PDFs Matriz Comunitária/` (ou `docs/fontes/2025/…` depois do S17). 0 pulados. |
| Migrações | `docker compose run --rm app python manage.py makemigrations --check` | Tem que dizer `No changes detected`. |
| Régua do F1 (JS) | `node app/nucleo/static/revista/f1/regua.test.mjs` | Sem dependências. |
| E2E (Playwright) | `docker compose up -d app && cd app/e2e && npm ci && npx playwright test` | baseURL `http://localhost:8000`. |

## 3. Perfis

Grupos fixos, criados por migração. Tabela única em `app/nucleo/permissoes.py`.

| Grupo | Pode |
|---|---|
| **Pedagógica** | tudo do ano: cadastros, matriz, cortes, templates, padrões, projetos, variáveis, revistas, validar |
| **Mídias Digitais** | o mesmo que a Pedagógica |
| **Admin** | o da Pedagógica + gerenciar usuários (só dá os grupos Pedagógica e Mídias Digitais) |
| **Impresso** | ver tudo + marcar "Revista Impressa Atualizada" |
| superusuário | tudo; é o único que põe alguém em Admin ou Impresso |

Ninguém exclui revista nem usuário: revista é arquivada, usuário é desativado.
Usuários em lote: `manage.py criar_usuarios <csv usuario,grupo> --url <endereço>` cria sem
senha e imprime o link do Django para cada um definir a sua.

## 4. Jornada da temporada

Detalhe de cada tela em [`docs/telas/inventario.md`](docs/telas/inventario.md).

1. **Abrir o ano** (`/admin/nucleo/ano/abrir/`): copia etapas, componentes, padrões (cor e nome),
   matrizes e templates do ano anterior. Cortes, parceiros e escolhas começam em branco.
   O primeiro ano (2026) foi carregado por comandos: [`docs/s17-carga-2026.md`](docs/s17-carga-2026.md).
2. **Conferir cadastros**: etapas, componentes, padrões do ano.
3. **Matrizes**: editar, duplicar, reimportar de PDF ou planilha.
4. **Parceiros** e **cortes** (`/admin/nucleo/corte/?ano=AAAA`): salvar os cortes cria o projeto
   e as revistas do parceiro.
5. **Em lote**: escolher a matriz e os templates F1/F2.
6. **Templates** (Markdown com `{{variável}}`, lista em [`docs/variaveis.md`](docs/variaveis.md)) e
   **variáveis** de cada projeto.
7. **Revista**: SVG do F2, capa, textos por seção; **preview**.
8. **Painel** (`/painel/AAAA/`): o que falta em cada revista; **Validado** um a um ou em lote.
9. **Impresso**: "o que mudou" + planilhas + "Revista Impressa Atualizada".
10. **Zip**: lista de Revistas, ação "Baixar zip".

## 5. Onde está cada coisa

| Caminho | O quê |
|---|---|
| `app/sistema/` | projeto Django (settings, urls) |
| `app/nucleo/models/`, `admin/`, `urls/`, `servicos/` | um arquivo por área |
| `app/nucleo/management/commands/` | `carregar_cadastros`, `importar_matriz`, `carregar_templates`, `abrir_ano`, `criar_usuarios`, `criar_demo` |
| `app/nucleo/static/revista/` | JS e CSS da revista (F1 escalas, F2 svg-tour) |
| `app/templates_seed/<ano>/` | textos iniciais dos templates |
| `app/e2e/` | Playwright |
| [`docs/`](docs/) | modelo ER, variáveis, telas, roteiro do S17 |
| [`plans/revista-express-django.md`](plans/revista-express-django.md) | plano da refatoração, passo a passo (S01–S18) |
| [`state.md`](state.md) | decisões técnicas (D-001…), estado atual e perguntas em aberto |

## 6. Operação

- **Backup:** `docker compose exec db pg_dump -U revista revista > backup-$(date +%F).sql`.
- **Restore:** `docker compose exec -T db psql -U revista revista < backup-AAAA-MM-DD.sql` (banco vazio).
- Nunca faça commit do `.env`.
- O sistema antigo (Express + Mongo + React) está na tag `legado-express`.
