# Revista Express

Sistema para montar as **revistas eletrônicas de resultados de avaliação** da Fundação CAEd.

Cada ano, a equipe cadastra a matriz (descritores e tarefas), os cortes de cada parceiro e
os textos. O sistema monta uma revista por **projeto × componente** (LP, MT), com dois
fascículos: **F1** (escalas de proficiência) e **F2** (infográfico em SVG). A revista é vista no
**preview**, validada e baixada como **zip** que abre offline. O impresso recebe "o que mudou"
e as planilhas.

Hoje o F2 é o SVG enviado pela equipe, mostrado pelo svg-tour. O F2 gerado pelo servidor e preenchido
na interface está aprovado, mas não implementado (D-227 a D-232); o plano está em
[`docs/superpowers/specs/`](docs/superpowers/specs/) (`2026-11-06-*.md`).

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
`http://localhost:8000/admin/`. Sem sessão, os dois levam ao login das telas B, `/conta/entrar/` (D-212).

- O compose sobe só `db` (PostgreSQL 17) e `app` (`docker-compose.yml`). Mongo, API e editor React
  saíram (D-187).
- Variáveis: `app/.env.example`. O compose lê o `.env` da **raiz**. Todas têm default de
  desenvolvimento. Produção: `docker-compose.prod.yml` com o `.env.prod.example`;
  guia da Infra em [`INFRA.md`](INFRA.md).
- Porta: `APP_PORT` (default 8000), por padrão só em `127.0.0.1`. Para abrir na rede: `APP_BIND=0.0.0.0` (D-209,
  ver [`docs/docker.md`](docs/docker.md#abrir-na-rede)).
- Cada worktree pode subir o próprio banco com `docker compose -p <nome> …`.
- Dados de demonstração para ver o preview: `docker compose run --rm app python manage.py criar_demo`
  (só com DEBUG; imprime a URL e a senha do usuário `demo-preview`).
- Detalhes de Docker, backup e restore: [`docs/docker.md`](docs/docker.md).

### Povoar um banco novo com a carga de 2026

`scripts/povoar-banco-2026.sh` recria, num banco **vazio**, o que a equipe usa de partida em 2026 (D-265).
O banco não vai para o git: o script refaz tudo pelos comandos do sistema, com as fontes do repositório.

```bash
ADMIN_SENHA='troque-esta-senha' ./scripts/povoar-banco-2026.sh   # na raiz do repositório
```

Sem `ADMIN_SENHA`, o script pergunta a senha no terminal. Ao fim, imprime a URL (`http://localhost:8000`,
usuário `admin`).

**O que ele cria**

| O quê | Quantidade | Fonte |
|---|---|---|
| Ano 2026, 4 etapas (2EF, 5EF, 9EF, 3EM), 2 componentes (LP, MT), 5 cores de padrão | 1 + 4 + 2 + 5 | `carregar_cadastros` |
| Usuário `admin` (superusuário) | 1 | `createsuperuser`, senha de `ADMIN_SENHA` |
| Parceiros, cortes de LP e MT, projetos e revistas (pela cascata) | 33, 148, 26, 52 | `docs/fontes/2026/Somativas 2026.xlsx` e `docs/fontes/2025/planilhas importantes/Cortes dos Padrões por Etapa e Parceiro.xlsx` (`importar_cortes`) |
| Templates de texto "Padrão" (F1 e F2 × LP e MT) | 4 | `app/templates_seed/2026/` |
| Matriz "Comunitária" | 198 descritores, 1093 tarefas | 3 PDFs em `docs/fontes/2025/PDFs Matriz Comunitária/` |

**Atributos que controlam o script**

| Atributo | Para que serve | Default |
|---|---|---|
| `ADMIN_SENHA` | Senha do usuário `admin` | pergunta no terminal |
| `COMPOSE_PROJECT_NAME` | Projeto Docker (banco e volume) onde carregar; troque para não tocar no banco principal | o da `.env` ou o nome da pasta |
| `APP_PORT` / `APP_BIND` | Porta e interface em que o app sobe no fim | `8000` / `127.0.0.1` |

**Regras e limites**

- Pré-requisitos: Docker com `compose`, o repositório clonado e rodar da raiz. Não precisa de Python local.
- O script recusa um banco que já tenha dados (parceiro ou ano). Para recomeçar do zero:
  `docker compose down -v` (apaga o volume do banco) e rode de novo.
- Parceiro sem etapa entre as 4 do sistema (Anchieta, Belo Horizonte, Niterói) nasce sem cortes e sem projeto.
  Faltam 40 cortes que a planilha não tem (RS, Angra dos Reis, Rio (município), SP sem nenhum; AL, RJ, TO,
  JOINVILLE, MG e PR em parte): a Pedagógica completa pela aba Cortes.
- Os valores de cortes são os da planilha de 2025 (o arquivo é idêntico); a Pedagógica valida para 2026.
- Não escolhe matriz nem template por revista: depois da carga, use "Atribuir matriz…" e "Atribuir
  template…" em Projetos. Também não cria usuários dos grupos Pedagógica, Mídias Digitais e Impresso
  (ver `criar_usuarios`).
- Para carregar sem tocar no dev: `COMPOSE_PROJECT_NAME=teste APP_PORT=8002 ./scripts/povoar-banco-2026.sh`
  e, ao terminar, `COMPOSE_PROJECT_NAME=teste docker compose down -v`.

## 2. Como testar

| O que | Comando | Observação |
|---|---|---|
| Suíte Django | `docker compose run --rm app python manage.py test` | O esperado é OK; 8 testes dependem dos PDFs SAEGO e ficam pulados sem eles. |
| Com os PDFs | `docker compose run --rm -v "$PWD/<pasta dos PDFs>:/pdfs:ro" app python manage.py test` | Pasta: `docs/fontes/2025/PDFs Matriz Comunitária/`. 0 pulados. |
| Migrações | `docker compose run --rm app python manage.py makemigrations --check` | Tem que dizer `No changes detected`. |
| Régua do F1 (JS) | `node app/nucleo/static/revista/f1/regua.test.mjs` | Sem dependências. |
| Navegador (Playwright) | `docker compose up -d app && cd app/e2e && npm ci && E2E_ADMIN_USUARIO=… E2E_ADMIN_SENHA=… npx playwright test` | baseURL `http://localhost:8000`; roda em chromium 1280 e 1440. Sem as `E2E_*`, os specs pulam em silêncio. No fim, `limpar_e2e` apaga o que os specs criaram. Preparo e stack isolada: [`docs/e2e.md`](docs/e2e.md). |

## 3. Perfis

Grupos fixos, criados por migração. Tabela única em `app/nucleo/permissoes.py`; versão por ação em
[`docs/regras-de-negocio.md`](docs/regras-de-negocio.md#8-perfis-e-permissões).

| Grupo | Pode |
|---|---|
| **Pedagógica** | tudo do ano: cadastros, matriz, cortes, templates, padrões, projetos, variáveis, revistas, validar, excluir o que não está em uso |
| **Mídias Digitais** | o mesmo que a Pedagógica |
| **Admin** | o da Pedagógica + gerenciar usuários (dá os grupos Pedagógica, Mídias Digitais e Impresso; outro Admin só vê) + apagar o ano inteiro + marcar "Revista Impressa Atualizada" (D-220) |
| **Impresso** | ver tudo + marcar "Revista Impressa Atualizada" |
| superusuário | tudo; é o único que põe alguém em Admin, altera outro Admin e vê o botão "Admin" no cabeçalho. Nenhuma tela cria superusuário: `createsuperuser` ou `tornar_superusuario` |

Superusuário novo: `createsuperuser`; tornar superusuário quem já existe: `manage.py
tornar_superusuario <usuario>...` (nenhuma tela faz isso, D-142).

Revista nunca é apagada (é arquivada). Usuário sai desativado; só se exclui quem nunca registrou
nada no sistema (tela Usuários, D-218). Para dar acesso sem
mandar senha: tela Usuários → "Link de acesso" (link para a pessoa criar a própria senha, com
mensagem pronta). Usuários em lote: `manage.py criar_usuarios <csv usuario,grupo> --url <endereço>`
cria sem senha e imprime o mesmo link para cada um.

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
| `app/nucleo/management/commands/` | `carregar_cadastros`, `importar_matriz`, `carregar_templates`, `abrir_ano`, `criar_usuarios`, `tornar_superusuario`, `criar_demo`, `limpar_e2e` |
| `app/nucleo/static/revista/` | JS e CSS da revista (F1 escalas, F2 svg-tour) |
| `app/templates_seed/<ano>/` | textos iniciais dos templates |
| `app/e2e/` | Playwright ([`docs/e2e.md`](docs/e2e.md)) |
| [`example/`](example/) | protótipos estáticos fora do sistema (F2 gerado, F2 animado, infográfico animado), cada um com `LEIA-ME.md` |
| [`docs/`](docs/) | modelo ER, regras de negócio, variáveis, telas, roteiro do S17 |
| [`plans/`](plans/) | planos de trabalho (refatoração S01–S18, reforma de UX, exclusão, lacunas das telas B) |
| [`state.md`](state.md) | decisões técnicas (D-001…), estado atual e perguntas em aberto |
| [`docs/fontes/2025/`](docs/fontes/2025/) | PDFs e planilhas SAEGO 2025 (fonte da matriz e dos testes de importação) |
| tag `legado-express` | o sistema antigo (`api/`, `editor/`, `revista/`, `scripts/`, `contrato/`) e o protótipo estático (`escala.html`), apagados da branch (D-213) |

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
| [`docs/e2e.md`](docs/e2e.md) | Testes de navegador: preparo, stack isolada, limpeza. |
| [`INFRA.md`](INFRA.md) | Implantação em produção, para a equipe de Infra. |
| [`state.md`](state.md) | Registro das decisões técnicas e do estado atual. |
