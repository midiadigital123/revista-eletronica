# Blueprint: novo revista-express (Django admin + PostgreSQL 17)

## Contexto

As decisões D-046 a D-125 (`state.md`) e o ER reescrito (`docs/modelo-er.md`) definem um sistema novo, que substitui o Express + Mongo (`api/`) e o React (`editor/`):
- Cada revista é **projeto × componente** (LP / MT) e tem dois fascículos: **F1** (escalas) e **F2** (infográfico svg-tour).
- Os textos vêm de **templates em Markdown restrito com `{{variavel}}`**, divididos em seções. O projeto faz **cópia por seção**.
- As variáveis são colunas de projeto, e a matriz é escolhida por parceiro × ano.
- Os cortes criam projetos e revistas em cascata.
- O "Validado" funciona por hash, e o impresso recebe uma foto com o "o que mudou".
- Há bloqueio de edição, Painel da temporada e entrega em zip por revista.

O objetivo é ordenar o código a escrever e testar em passos do tamanho de um PR, com dependências explícitas e executáveis por um agente que começa sem contexto.

**Preferências do usuário:**
- Python.
- Tarefas pequenas e testáveis, executadas e revisadas por subagentes especializados.
- Commit só quando ele pedir; o último commit de cada leva é só o `state.md`.

**Modo de trabalho:**
- Git + `gh` (conta `midiadigital123`). A integração é a branch **`refatoracao-django`**, criada a partir de `dev` em 2026-10-29. `dev` e `main` ficam como estão até a refatoração terminar.
- Cada passo trabalha numa branch `feat/sNN-<nome>` criada a partir de `refatoracao-django`, com PR para ela. A branch antiga `django` (Django 5.2 + JORNADA) **não** serve de base.
- Cada passo termina **pronto para commit**. Commit e PR só depois do "pode commitar" do usuário.
- Nenhum passo antes de S17 altera `revista/`, `api/`, `editor/` ou `scripts/`. Tudo o que é reaproveitado é **copiado** para `app/`.

## Reaproveitamento (copiar para `app/`, nunca mover antes de S17)

| Origem | Reuso | Ajuste necessário |
|---|---|---|
| `scripts/extrair_descritores.py` + teste | Importador de matriz (S04) | Tirar a exigência de 3 cortes e o `padrao_do_nivel` (D-059) |
| `revista/script.js`, `styles.css`, `assets/*` | Renderização do F1 (S03b) | Só tratam 4 padrões fixos (`PADROES_DE_CIMA`, `--color-padrao-1..4`, `cortes["padrao-1..3"]`) e esperam `scale` já dividido por padrão, com linhas vazias prontas. Precisam ser generalizados para 2 a 5 padrões (D-050, D-055, D-064) |
| `revista/escala.hbs` | Template Django `revista/index.html` (S08) | Portar a sintaxe e acrescentar as seções de texto e o F2 |
| `api/src/modules/revista/render.ts` (`jsonSeguro`, `cssDasCores`) | Python (S08), cerca de 30 linhas | — |
| `contrato/revista.ts` (`revistaDosAnos`), `contrato/schemas.ts` (`niveisDoPasso`, `linhasVaziasDoPasso`, `PADROES`) | Formato do JSON `dados-revista` e cálculo de linhas vazias (S07) | Portar para Python e generalizar para N padrões |
| `api/src/modules/planilhas/layout.ts` + `service.ts` | `openpyxl` (S13), mesmos `LAYOUTS` | Generalizar para N padrões |
| `svg-tour/common/svg-tour.js`, `svg-tour-modal.js`, `avaliacao-e-curriculo/revista.css`, `revista.js`, `revista.json`, `revista-modais.html` | F2 (S08) e seeds F2 (S05) | Só existe a versão de LP; o MT nasce como cópia (S05) |
| `editor/src/projetos/useBloqueio.ts` | Referência do JS de renovação (S10) | — |

## Invariantes (valem para todo passo)

1. `docker compose run --rm app python manage.py test` passa inteiro, e `makemigrations --check` não acusa nada.
2. `api/`, `editor/`, `revista/`, `scripts/` e o Mongo continuam funcionando até S17.
3. Toda FK composta tem `reverse_sql`, e o teste de `pg_constraint` (S02) é atualizado no mesmo passo.
4. Nenhum segredo no repositório: credenciais só no `.env`, que fica fora do git.
5. O `state.md` é atualizado no fim de cada passo.
6. **Arquivos compartilhados:**
   - O admin fica em `nucleo/admin/` com um módulo por área.
   - As URLs ficam em `nucleo/urls/` com um `include` por módulo.
   - Os modelos ficam em `nucleo/models/` com um arquivo por área.
   - Na Fase B, **só S14 cria migração**, para evitar dois `000N` com o mesmo número. Ao juntar as branches, rodar `makemigrations --check`.
7. Teste que exercita concorrência usa `TransactionTestCase`.

## Grafo de dependências

```
S01 ─┬─ S02 ─ S03 ─┬─ S04 (cadastros + importar matriz)
     │             ├─ S05 (templates + seed)
     │             ├─ S06 (cascata de cortes)
     │             ├─ S09 (upload SVG/capa: serviço)
     │             ├─ S10 (bloqueio: serviço + mixin)
     │             └─ S14 (perfis)
     └─ S03b (revista JS/CSS para 2 a 5 padrões + Playwright)

S07 (resolver + hash + pendências) ← S03b, S05, S06, S09
S08 (render F1+F2) ← S07
S15 (zip) ← S08
S11a (admin: cadastros, cortes, matriz) ← S04, S06, S10, S14
S11b1 (admin: templates) ← S05, S07, S09, S10, S14
S11b2 (admin: cópia por seção) ← S11b1
S11c (admin: projeto, variáveis, SVG/capa, lote) ← S07, S09, S10, S14
S12 (painel + Validado) ← S08, S11b2, S11c
S13 (impresso + planilhas) ← S12
S16 (abrir ano) ← S03, S05; ação de admin em S11a
S17 (carga 2026 + desligar o antigo) ← todos
S18 (E2E) ← S17
```

**O que pode rodar em paralelo:**
- Depois de S03: S04, S05, S06, S09, S10 e S14, todos com arquivos próprios em `nucleo/servicos/*`.
- S03b roda em paralelo desde S01.
- Depois de S08: S15 junto com a Fase D.
- S11a e S11c podem rodar em paralelo. S11b1 também, porque cada um tem o próprio módulo em `nucleo/admin/`.

## Passos

---

### Fase A: Fundação

#### S01: Esqueleto Django + PostgreSQL + Playwright
- **Contexto:** o app novo vive em `app/`, com o projeto `sistema` e o app único `nucleo`. Os pacotes `models/`, `admin/`, `urls/` e `servicos/` já nascem vazios.
- **Tarefas:**
  1. Criar `app/requirements.txt` com Django 6.1.x, psycopg[binary] 3, django-simple-history, defusedxml, openpyxl e markdown-it-py.
  2. Criar `app/Dockerfile` com Python 3.13 e `poppler-utils`.
  3. No `docker-compose.yml`, adicionar os serviços `db` (postgres:17, volume `pg-dados`) e `app` (porta 8000). Os serviços atuais ficam intactos.
  4. Configurar o `settings.py`:
     - `DATABASE_URL` vindo do `.env`;
     - `USE_TZ=True`, `DEFAULT_AUTO_FIELD=BigAutoField`, `pt-br`;
     - `MEDIA_ROOT`;
     - `simple_history` em `INSTALLED_APPS`.
  5. Criar `app/e2e/` com `package.json` (`@playwright/test`), `playwright.config.ts` (baseURL `http://localhost:8000`) e um teste de fumaça que abre `/admin/login/`.
  6. Criar um teste Django de fumaça: `SELECT version()` começa com "PostgreSQL 17".
- **Verificação:**
  - `docker compose up -d db app`
  - `docker compose run --rm app python manage.py check`
  - `docker compose run --rm app python manage.py test`
  - `cd app/e2e && npx playwright test`
- **Saída:** admin abre com superusuário.
- **Depende de:** nada. **Modelo:** padrão. **Estimativa:** 2 h. **Rollback:** apagar `app/` e os 2 serviços.

#### S02: Modelos de cadastro e matriz, com FK composta de ano
- **Contexto:** seção "Restrições" de `docs/modelo-er.md`. Decisões D-086, D-090 e D-124.
- **Tarefas:**
  1. Em `models/cadastro.py` e `models/matriz.py`, criar `Ano`, `Parceiro`, `Etapa`, `Componente`, `CorPadrao` (padrão 1 a 5), `Matriz` (com `duplicada_de` SET_NULL), `MatrizEtapaCC`, `Descritor` e `Tarefa`, com os UNIQUE e CHECK do ER.
  2. Usar `HistoricalRecords` em todos esses modelos.
  3. Criar `nucleo/db.py::fk_composta(...)`, que devolve `RunSQL` com `reverse_sql` e nome `fk_<tabela>_<alvo>_ano`.
  4. Criar `tests/test_constraints.py`, que lista em `pg_constraint` as FKs e CHECKs esperados.
- **Verificação:** os testes mostram o banco recusando:
  - MEC com etapa de outro ano;
  - cor fora de `#RRGGBB`;
  - padrão 6;
  - matriz duplicada de si mesma.
- **Depende de:** S01. **Modelo:** forte. **Estimativa:** 3 a 4 h. **Rollback:** `migrate nucleo zero`.

#### S03: Parceiro_ano, corte, projeto, revista, texto e controle
- **Contexto:** o restante do ER. Decisões D-095, D-097, D-098, D-104, D-115, D-117, D-118 e D-125.
- **Tarefas:**
  1. Criar `nucleo/variaveis.py::VARIAVEIS`, a lista fixa com nome, rótulo, descrição e flag `automatica`. As automáticas são parceiro, nome do projeto e ano. Por ora entram também os 4 gentílicos.
  2. Criar os modelos, com seus CHECKs:
     - `ParceiroAno` e `Corte` (ArrayField, 1 a 4 valores, sem NULL);
     - `Projeto`, com `arquivado_em`, UNIQUE parcial de projeto ativo e uma coluna `text` com CHECK de tamanho para cada variável não automática;
     - `ProjetoPasso` e `ProjetoCor`;
     - `Template` e `TemplateVersao`;
     - `Revista`, `RevistaFasciculo` e `RevistaSecao`;
     - `FotoRevista` e `Bloqueio`.
  3. Usar `HistoricalRecords` em todos, exceto `Bloqueio` e `TemplateVersao`.
  4. Criar todas as FKs compostas do ER.
  5. Fazer `TemplateVersao.save()` recusar update.
- **Verificação:** os testes mostram o banco recusando:
  - template de MT em revista de LP;
  - template de outro ano;
  - cópia apontando para versão de outro template;
  - troca de template com cópias existentes;
  - bloqueio com dois alvos;
  - dois projetos ativos no mesmo parceiro_ano.
- **Depende de:** S02. **Modelo:** forte. **Estimativa:** 4 a 6 h. **Rollback:** reverter as migrações do passo.

#### S03b: Revista JS/CSS generalizada para 2 a 5 padrões
- **Contexto:** `script.js` e `styles.css` só tratam 4 padrões fixos e esperam `scale` dividido por padrão (chaves `padrao-1..4`) e linhas vazias prontas. Os cortes vão de 1 a 4 (D-055), então são de 2 a 5 padrões, com a cor do 5º `#FFF` (D-064).
- **Tarefas:**
  1. Copiar `revista/{script.js,styles.css,assets/}` para `app/nucleo/static/revista/f1/`.
  2. Generalizar o código:
     - `PADROES_DE_CIMA` e `montarFaixasRegua` passam a ler a lista de padrões e cortes do JSON;
     - o CSS ganha `--color-padrao-5` e `--color-padrao-5-bg`;
     - os rótulos "Padrão 01..05" saem do JSON.
  3. Criar o fixture `tests/fixtures/revista-3cortes.json` (formato atual) e o `revista-1corte.json`, `revista-4cortes.json`.
  4. Copiar `regua.test.mjs` para junto do novo JS e acrescentar casos de 1 e 4 cortes.
  5. Criar o teste Playwright `e2e/f1-fixture.spec.ts`. Ele carrega um HTML mínimo com o JS portado e cada fixture e confere:
     - 0 erros no console;
     - abas de etapa;
     - número de faixas da régua igual ao de padrões;
     - cor do 5º padrão.
- **Verificação:** `node app/nucleo/static/revista/f1/regua.test.mjs` e `npx playwright test f1-fixture`.
- **Depende de:** S01. **Paralelo com:** S02 e S03. **Modelo:** forte. **Estimativa:** 4 h. **Rollback:** isolado.

---

### Fase B: Serviços (paralelos depois de S03)

#### S04: Cadastros iniciais e importador de matriz
- **Tarefas:**
  1. Criar o comando `carregar_cadastros --ano 2026`. Ele cria:
     - o Ano;
     - as Etapas: 2EF com escala_max 1000; 5EF, 9EF e 3EM com 500; ordem definida;
     - os Componentes LP e MT;
     - a CorPadrao 1 a 4 com as cores atuais de `styles.css` e a 5 com `#FFFFFF`.

     É idempotente.
  2. Copiar `scripts/extrair_descritores.py` para `nucleo/importacao/pdf.py`, sem a exigência de 3 cortes e sem `padrao_do_nivel`. O original não muda.
  3. Criar `importacao/xlsx.py`, no layout da exportação (uma planilha por etapa × CC).
  4. Criar o serviço `importar_matriz(matriz, arquivo, substituir=False)`. Ele roda em transação, apaga e recria MEC, Descritor e Tarefa e preserva o `passo` informado (D-053, D-091).
  5. Criar o comando `importar_matriz --ano 2026 --nome Comunitária <pdf> [--passo 25]`.
  6. Copiar os 3 PDFs SAEGO **2025** para `app/nucleo/tests/fixtures/`, se o tamanho permitir. Se não, o teste lê do caminho do repositório e é marcado para pular quando o arquivo faltar.
- **Verificação:** rodar o extrator antigo nos 3 PDFs e anotar as contagens de descritores (Alfa 84; LP e MT a anotar). O importador novo tem que bater exatamente.
- **Depende de:** S03. **Modelo:** padrão. **Estimativa:** 4 h. **Rollback:** isolado.

#### S05: Templates: formato, validação e seed
- **Contexto:**
  - Markdown restrito: negrito, itálico, parágrafos e listas (D-105).
  - `{{variavel}}` validado por regex contra `VARIAVEIS`; não há motor Handlebars (D-123, D-125).
  - Seções `## id`. F1: `introducao` e `fechamento` (D-114). F2: `abertura`, `passoN` e `dlg-*` (D-108, D-111).
  - **Convenção de título:** nas seções do F2, a 1ª linha é o título em texto puro e o resto é o corpo.
- **Tarefas:**
  1. Em `nucleo/texto.py`, criar:
     - `secoes(texto) -> dict[id, (titulo, corpo)]`;
     - `validar(texto, fasciculo)`. Exige as seções obrigatórias e recusa: títulos `#` dentro do corpo, links, imagens, HTML e `{{x}}` fora da lista;
     - `variaveis_usadas(texto)`;
     - `renderizar(corpo, valores) -> html`. Troca cada `{{var}}` por um marcador neutro, roda o markdown-it-py com `html=False` e só então põe os valores escapados no lugar. Isso evita escape duplo e formatação vinda do valor;
     - `renderizar_texto_puro(...)`, para títulos.
  2. Escrever os seeds em `app/templates_seed/2026/`:
     - `f1-lp.hbs` e `f1-mt.hbs`: introdução a partir do texto atual de `escala.hbs` (hero e intro) e fechamento a partir do PDF impresso;
     - `f2-lp.hbs`: `revista.json` (intro → `abertura`, steps → `passoN`) mais `revista-modais.html` (h3 → título, p → corpo), convertidos para Markdown;
     - `f2-mt.hbs`: **cópia do LP** com o aviso `<!-- revisar com a Pedagógica -->`, que é removido no seed.
  3. Criar o comando `carregar_templates --ano 2026`. Ele cria o template e a versão 1, preenche `origem` e nunca sobrescreve.
- **Verificação:** testes mostrando que:
  - seção faltando é recusada;
  - `{{inexistente}}` é recusado;
  - `<script>` vira texto;
  - valor com `_` ou `*` não vira formatação;
  - `**{{parceiro}}**` sai em negrito com o valor escapado;
  - não há escape duplo de `&`;
  - o comando é idempotente;
  - os 4 seeds passam em `validar`.
- **Depende de:** S03. **Modelo:** padrão, com revisão forte do parser. **Estimativa:** 5 h, mais a revisão dos textos pela Pedagógica (pendência registrada, não bloqueia).

#### S06: Cascata dos cortes
- **Contexto:**
  - Decisões D-061, D-065, D-068, D-093 e D-117.
  - Validação: de 1 a 4 valores, crescentes, dentro de 0..escala_max (D-055).
  - Nome inicial: `"<PARCEIRO> - NOME DO PROJETO"`.
- **Tarefas:**
  1. Criar `nucleo/servicos/cascata.py::gravar_cortes(parceiro_ano, linhas)`. Ele roda numa transação que começa com `select_for_update()` no ParceiroAno e:
     - grava os cortes;
     - garante o projeto ativo;
     - garante uma revista por componente com cortes, com 2 `RevistaFasciculo`;
     - arquiva a revista que ficou sem cortes, chamando `fotografar(revista, 'arquivamento')`;
     - reativa a mesma linha quando os cortes voltam;
     - arquiva o projeto quando todas as revistas dele estão arquivadas.
  2. Projeto readicionado depois de arquivado gera projeto novo (D-068). As revistas novas herdam a última foto de impresso, com `herdada=true` (D-094).
  3. Criar `nucleo/servicos/foto.py::fotografar` como **stub**: grava `{}` com hash vazio. A implementação real vem em S07.
- **Verificação:** testes com `TransactionTestCase` para:
  - só LP gera 1 revista;
  - remover MT arquiva a revista MT e não mexe na LP;
  - recolocar MT reativa a mesma linha;
  - remover tudo arquiva o projeto;
  - readicionar gera projeto novo e herda a foto;
  - duas threads simultâneas não duplicam a revista.
- **Depende de:** S03. **Modelo:** forte. **Estimativa:** 4 h.

#### S09: Serviço de SVG e capa
- **Contexto:** decisões D-108, D-118 e D-125.
- **Tarefas:**
  1. Criar `nucleo/servicos/arquivos.py::receber_svg(revista, arquivo)`. Ele:
     - recusa arquivos acima de 3 MB;
     - lê com `defusedxml`;
     - aplica uma lista fixa de tags e atributos, removendo `on*`, `script`, `foreignObject` e `href` externo;
     - prefixa `f2-` em ids e classes, inclusive dentro do `<style>` e de `url(#…)`;
     - grava com nome uuid;
     - preenche `svg_sha256` e `svg_ids`, guardados **sem o prefixo**.
  2. Criar `receber_capa`: PNG, JPG ou WebP, até 5 MB, com sha.
  3. Criar `ids_faltando(revista)`. Compara as seções efetivas do F2 (`passoN` → id `passoN`; `dlg-xx` → id `btn-action-xx`) com `svg_ids`, sem prefixo.
- **Verificação:**
  - Copiar o SVG real de `svg-tour/avaliacao-e-curriculo/infografico-atual/*NOMEADO.svg` para `app/nucleo/tests/fixtures/f2-lp.svg`.
  - Testes:
    - o SVG passa e a contagem de `<path>` se mantém;
    - `btn-action-p2` e `passo1` aparecem em `svg_ids`;
    - `<image onerror>` é removido;
    - billion laughs dá erro;
    - arquivo acima de 3 MB é recusado.
  - Revisão pelo `ecc:security-reviewer`.
- **Depende de:** S03. **Modelo:** padrão. **Estimativa:** 3 h.

#### S10: Bloqueio: serviço, rota, JS e mixin
- **Contexto:** decisões D-080, D-081, D-109 e D-121. Bloqueio de 30 s com renovação a cada 10 s, usando o `now()` do banco.
- **Tarefas:**
  1. Criar `nucleo/servicos/bloqueio.py` com:
     - `adquirir`: `INSERT … ON CONFLICT … DO UPDATE … WHERE expira_em < now() OR mesma sessão … RETURNING id`;
     - `renovar` e `liberar`;
     - `conferir_na_transacao(alvo, sessao)`: `SELECT … FOR SHARE`.
  2. Criar `nucleo/urls/bloqueio.py` com `POST /bloqueio/renovar`.
  3. Criar `static/nucleo/bloqueio.js`, portado de `useBloqueio.ts`. Ele gera a sessão da aba, renova a cada 10 s e desliga o formulário quando perde o bloqueio.
  4. Criar `BloqueioAdminMixin`, testado com um ModelAdmin **de teste**. Os admins reais usam o mixin em S11a, S11b1 e S11c.
- **Verificação:** testes com `TransactionTestCase` para:
  - duas sessões concorrentes: só uma adquire;
  - bloqueio expirado é tomado;
  - a mesma sessão renova;
  - escrita com bloqueio de outra sessão é recusada.
- **Depende de:** S03. **Modelo:** padrão. **Estimativa:** 3 h.

#### S14: Perfis e permissões
- **Contexto:** decisões D-073, D-079, D-083 e D-102.
- **Tarefas:**
  1. Migração de dados com 4 `Group`: Admin, Pedagógica, Impresso e Mídias Digitais. Mídias tem o mesmo que Pedagógica.
  2. Permissões customizadas: `validar_revista`, `marcar_impressa` e `abrir_ano`.
  3. Tabela de papel × ação em `nucleo/permissoes.py`. Admin tem tudo o que a Pedagógica tem, mais usuários.
  4. Padrão proposto: admin **não** marca impressa (pergunta em aberto).
- **Verificação:** um teste por perfil com `user.has_perm`. Os testes de tela por perfil ficam em S11 a S13.
- **Depende de:** S03. **Única migração da Fase B.** **Modelo:** padrão. **Estimativa:** 2 h.

---

### Fase C: Montagem da revista

#### S07: Resolver, foto, hash e pendências
- **Contexto:** é o núcleo que o preview, o hash, a foto, o zip e o painel consomem. Não grava nada, exceto pela função `fotografar`.
- **Tarefas:**
  1. Criar `nucleo/servicos/resolver.py::resolver(revista) -> dict`.

     **F1**, no formato que o JS de S03b lê:
     - etapas do componente que têm cortes, com chave em minúsculas;
     - descritores e tarefas da matriz escolhida, **distribuídos por padrão pela âncora maior** (D-058);
     - **linhas vazias geradas a partir do passo efetivo**, que vem de `ProjetoPasso` ou do MEC (D-053, D-091). Para isso, portar `niveisDoPasso` e `linhasVaziasDoPasso` de `contrato/schemas.ts`, generalizados para N padrões;
     - cores efetivas, de `ProjetoCor` ou `CorPadrao` (D-060, D-064);
     - textos efetivos das seções (cópia ou última versão) renderizados com `texto.renderizar`.

     **F2**: título e corpo de cada seção e os metadados do SVG.

     **Lacunas**: template ausente e variável vazia, com o marcador da faixa vermelha (D-116).

     **Revista arquivada**: devolve o conteúdo da própria foto de arquivamento (D-117).
  2. Criar `hash_validado(revista)`: sha256 do JSON canônico do resolvido, mais `svg_sha256` e `capa_sha256` (D-118).
  3. Criar `conteudo_impresso(revista)`. Inclui as **escalas do F1** (por etapa: cortes e descritores/tarefas por padrão) e os **textos** de F1 e F2. **Exclui** SVG e capa (D-066, D-072, D-077, D-112).
  4. Substituir o stub de `foto.fotografar` pela versão real: monta, calcula o hash e grava numa transação REPEATABLE READ. Atualizar o teste de arquivamento de S06.
  5. Criar `pendencias(revista) -> list[Pendencia(codigo, mensagem, link)]`. Bloqueia por: matriz ausente; corte sem MEC; template F1 ou F2 ausente; SVG ou capa ausente; `ids_faltando`; variável usada vazia; nome padrão.
  6. Criar `secoes_desatualizadas(revista)` (D-115).
- **Verificação:**
  - Testes:
    - mudar uma variável usada só no F2 da LP muda o hash da LP e não o da MT;
    - trocar o SVG muda o hash e não muda `conteudo_impresso`;
    - mudar o corte do PE muda só o conteúdo do PE;
    - editar uma tarefa da comunitária muda o conteúdo de todas as revistas que a usam;
    - passo 25 gera as linhas vazias esperadas (casos de `contrato/schemas.ts`);
    - sem template, a pendência e o marcador aparecem.
  - O JSON gerado pelo resolver para um caso de 4 cortes entra no Playwright `f1-fixture` de S03b: 0 erros e 5 faixas.
- **Depende de:** S03b, S05, S06, S09. **Modelo:** forte. **Estimativa:** 8 h.

#### S08: Página única F1 + F2 (preview)
- **Tarefas:**
  1. Copiar para `static/revista/f2/`, com cabeçalho de origem, os arquivos `svg-tour/common/{svg-tour.js,svg-tour-modal.js}` e `avaliacao-e-curriculo/revista.css`.
  2. Portar `escala.hbs` para `templates/revista/index.html`:
     - hero e capa;
     - `introducao` antes das escalas e `fechamento` depois;
     - menu de capítulos F1/F2;
     - `#f2` com o SVG inline;
     - JSON do tour gerado das seções `abertura` e `passoN`, com a config do tour como constantes;
     - `<dialog>` gerados das seções `dlg-*`.
  3. Portar `jsonSeguro` e `cssDasCores` (N padrões) para `nucleo/servicos/html.py`.
  4. Criar `static/revista/f2/f2-init.js`. Ele lê os dados inline, sem `fetch` (para funcionar em `file://`), monta o `BOTOES_MODAL` a partir das seções e busca os ids no DOM com o prefixo `f2-`.
  5. Na cópia `static/revista/f1/script.js`, o `Ctrl+setas` só age quando `!e.target.closest('#f2') && !document.querySelector('dialog[open]')`.
  6. Criar a view `nucleo/urls/preview.py`: `preview/<revista_id>/`, só leitura, protegida por login.
- **Verificação:**
  - Testes de view: 200, faixa vermelha quando falta template, foto quando a revista está arquivada.
  - Playwright:
    - troca a etapa do F1;
    - vai ao F2, faz o tour completo e abre `dlg-p2`;
    - `Ctrl+→` dentro do F2 não muda o descritor do F1;
    - screenshots em 1280px e 390px.
  - Revisão pelo `ecc:a11y-architect`.
- **Depende de:** S07. **Modelo:** padrão. **Estimativa:** 6 h.

#### S15: Zip por revista
- **Tarefas:**
  1. Criar `nucleo/servicos/empacotar.py::zip_revista(revista)`. Ele contém:
     - `index.html` (sem faixas);
     - `revista/f1/*` e `revista/f2/*`;
     - `arquivos/capa.*`.

     SVG, tour e modais vão embutidos. O nome é `<parceiro>-<cc>-<ano>.zip`, sem acento.
  2. Criar a ação de admin "Baixar zip", que só funciona sem pendências.
- **Verificação:** testes que conferem a lista de arquivos e a ausência de `fetch(`. No Playwright, `file:///…/index.html` abre o F1 e o F2.
- **Depende de:** S08. **Modelo:** padrão. **Estimativa:** 2 h.

---

### Fase D: Interface (Django admin)

#### S11a: Admin de cadastros, cortes e matriz (`nucleo/admin/cadastro.py`, `matriz.py`, `cortes.py`)
- **Tarefas:**
  1. Admins de Ano, Parceiro, Etapa, Componente e CorPadrao.
  2. Admin de Matriz com:
     - "Duplicar matriz" de qualquer ano (D-101, D-124), com diff contra a origem só para consulta (D-113);
     - "Reimportar" com confirmação forte (D-071).
  3. Edição de MEC (incluindo o passo), Descritor e Tarefa com o aviso "afeta N revistas" antes de salvar (D-076). Usa o `BloqueioAdminMixin` por MEC.
  4. Tela de cortes por ano: grade parceiro × (etapa × CC), validação da D-055, gravação por `gravar_cortes`.
  5. Exportação da planilha de grupos de corte (D-056).
  6. Ação "Abrir ano", que chama o serviço de S16 e exige a permissão `abrir_ano` (D-079).
- **Verificação:**
  - Testes do client:
    - duplicar matriz;
    - aviso de impacto;
    - a grade dispara a cascata;
    - grupos batem com o `state.md` (9EF-MT: SE grupo 6, SALVADOR grupo 7; 5EF-MT: SALVADOR grupo 6);
    - permissões por perfil.
  - Playwright: preencher os cortes de 2 parceiros.
- **Depende de:** S04, S06, S10, S14 (e o serviço de S16 para a ação). **Modelo:** padrão. **Estimativa:** 7 h.

#### S11b1: Admin de templates (`nucleo/admin/templates.py`)
- **Tarefas:**
  1. Página "Templates" com abas Textos F1, Textos F2, Matrizes e Variáveis (D-102). A lista mostra "usado por N (M com cópia)", com link para o painel filtrado.
  2. Widget de edição: textarea Markdown, botão "Inserir variável" e preview ao vivo com as variáveis coloridas (D-123).
  3. Ao salvar:
     - roda `validar`;
     - mostra uma tela de impacto com as revistas afetadas, as que já têm foto do impresso e os SVGs que ficariam com `ids_faltando`;
     - cria uma nova `TemplateVersao`.

     Usa o `BloqueioAdminMixin` por template (D-099, D-109, D-125).
- **Verificação:** testes para `{{x}}` inválido recusado, nova versão criada (versão antiga intacta), a tela de impacto listando um SVG incompleto e as permissões.
- **Depende de:** S05, S07, S09, S10, S14. **Modelo:** forte. **Estimativa:** 5 h.

#### S11b2: Cópia por seção na revista (`nucleo/admin/revista.py`, parte de texto)
- **Tarefas:**
  1. Na revista, editar o texto seção por seção. O título da seção não é editável. A cópia nasce ao salvar a seção (D-104, D-115).
  2. Seção desatualizada mostra "seu texto | template novo com diff" (`difflib`), com as opções salvar ou "descartar cópia".
  3. Trocar o template com cópias exige confirmação forte e descarta as cópias numa transação (D-104).
- **Verificação:**
  - Testes:
    - a cópia é criada só na seção editada;
    - o aviso aparece depois de nova versão do template;
    - descartar volta ao template ao vivo;
    - a troca sem confirmação é recusada.
  - Playwright do fluxo completo.
- **Depende de:** S11b1. **Modelo:** forte. **Estimativa:** 4 h.

#### S11c: Admin de projeto, variáveis, arquivos e lote (`nucleo/admin/projeto.py`, `variaveis.py`, `lote.py`)
- **Tarefas:**
  1. Admin de Projeto com o `BloqueioAdminMixin`, o nome do projeto e os inlines de ProjetoPasso e ProjetoCor (D-053, D-060, D-091).
  2. Na revista: campos de upload de SVG e capa usando `receber_svg` e `receber_capa`. Erros de id aparecem com a lista de ids esperados e o botão "Baixar gabarito de ids".
  3. Aba Variáveis:
     - lista de projetos do ano com `list_editable` das colunas;
     - descrição e templates onde cada variável aparece;
     - automáticas só para leitura;
     - ação "Copiar valores do ano anterior" por projeto, que preenche só as colunas vazias (D-107, D-119).
  4. Lote "Escolher matriz" (ParceiroAno) e "Escolher template F1/F2" (Revista, filtrado por componente). Pula os alvos travados e lista os pulados (D-102, D-121).
- **Verificação:** testes para:
  - lote com um projeto travado: é pulado e listado;
  - template de outro componente: não é oferecido e o banco recusa;
  - copiar do ano anterior não sobrescreve o que já tem valor;
  - upload de SVG sem um id mostra o erro;
  - permissões.
- **Depende de:** S07, S09, S10, S14. **Modelo:** padrão. **Estimativa:** 6 h.

#### S12: Painel da temporada e "Validado"
- **Tarefas:**
  1. `painel/<ano>/`: uma linha por revista ativa, com colunas Matriz, Template F1, Template F2, Variáveis, SVG, Capa, Validado e Impresso. Cada célula mostra ✓ ou "falta" com link (de `pendencias`). Filtros por pendência e por parceiro (D-120).
  2. "Validado" na revista: envia o hash exibido. O servidor recusa quando o hash mudou ou há pendência; senão grava `hash_validado`, `validado_em` e `validado_por` (D-074, D-089).
  3. Validação em lote: mostra o diff de cada revista e envia pares (revista, hash). Cada par é recusado individualmente (D-078, D-120).
  4. O estado "validado" é sempre calculado na hora, então desfazer uma mudança faz o "Validado" voltar (D-094).
  5. Seção desatualizada só avisa e não bloqueia (D-087).
- **Verificação:** testes para:
  - hash velho é recusado;
  - lote com 1 de 3 alterado no meio grava 2;
  - trocar o SVG derruba o "Validado";
  - desfazer a mudança faz o "Validado" voltar;
  - permissões.
- **Depende de:** S08, S11b2, S11c. **Modelo:** padrão. **Estimativa:** 5 h.

#### S13: Impresso: "o que mudou", confirmação e planilhas
- **Tarefas:**
  1. Tela do impresso: diff entre `conteudo_impresso(revista)` e a última foto `impresso` (ou a herdada). Organização:
     - agrupado por fascículo e depois por etapa ou seção;
     - itens na ordem das páginas;
     - antes → depois;
     - botão "copiar texto novo".
  2. "Revista Impressa Atualizada": só aparece com "Validado", envia o hash e chama `fotografar(revista, 'impresso')` (D-072, D-089).
  3. Planilhas:
     - portar `planilhas/layout.ts` e `service.ts` para `openpyxl`, generalizando para N padrões;
     - criar uma planilha F2 com as colunas seção, título e texto.
  4. Ação "Baixar planilhas": zip com F1 e F2.
- **Verificação:**
  - Testes:
    - primeira entrega mostra tudo como novo;
    - variável alterada aparece em todas as seções que a usam;
    - corte alterado aparece só na etapa;
    - hash velho é recusado;
    - revista readicionada faz o diff a partir da foto herdada;
    - permissões (impresso só depois do validado).
  - Gabarito da planilha: rodar o `service.ts` antigo uma vez sobre o JSON `revista-3cortes.json` de S03b, guardar o xlsx em `tests/fixtures/` e comparar célula a célula com o `openpyxl`, carregando os mesmos dados no Postgres.
- **Depende de:** S12. **Modelo:** forte. **Estimativa:** 7 h.

---

### Fase E: Ano e virada

#### S16: Serviço e comando abrir_ano
- **Tarefas:**
  1. Criar `nucleo/servicos/abrir_ano.py` e o comando `abrir_ano 2027`. Tudo roda em `transaction.atomic()` e começa por `Ano.objects.create` (o UNIQUE barra a repetição). Com um mapa de ids, copia:
     - Etapa, Componente e CorPadrao;
     - Matriz (com MEC, Descritor e Tarefa), com `duplicada_de` apontando para a origem;
     - Template, com a última versão como versão 1.

     Usa `bulk_create_with_history`.
  2. Não copia cortes, parceiro_ano, projetos nem escolhas (D-054, D-106, D-119).
- **Verificação:** testes para:
  - contagens iguais por tabela;
  - a 2ª execução falha sem efeito;
  - nenhum projeto em 2027;
  - FKs compostas válidas.
- **Depende de:** S03, S05. **Paralelo com:** a Fase C e a Fase D. **Modelo:** padrão. **Estimativa:** 3 h.

#### S17: Carga de 2026 e desligamento do sistema antigo
- **Tarefas:**
  1. `carregar_cadastros --ano 2026`.
  2. `importar_matriz` com os 3 PDFs SAEGO 2025 como Comunitária 2026 (D-076).
  3. `carregar_templates --ano 2026`.
  4. Recriar usuários nos grupos.
  5. A Pedagógica preenche os cortes pela tela (D-119).
  6. Ações destrutivas, **uma confirmação explícita do usuário para cada**:
     - criar a tag `legado-express`;
     - retirar `mongo`, `api` e `editor` do compose;
     - apagar `api/`, `editor/`, `revista/` e `scripts/`;
     - `gh repo archive` do svg-tour.
  7. Atualizar README e CLAUDE.md.
- **Verificação:** o painel de 2026 lista as revistas esperadas, e um zip de LP e um de MT abrem por duplo clique.
- **Depende de:** todos. **Modelo:** padrão. **Estimativa:** 3 h de código, mais o trabalho da equipe.

#### S18: E2E da temporada
- **Tarefas:** suíte Playwright (via `ecc:e2e-runner`) cobrindo:
  1. abrir o ano;
  2. preencher os cortes;
  3. escolher matriz e templates em lote;
  4. preencher as variáveis;
  5. subir o SVG e a capa;
  6. validar;
  7. o impresso atualiza;
  8. editar o template;
  9. ver o aviso na seção copiada;
  10. revalidar;
  11. o diff aparece para o impresso;
  12. baixar o zip.
- **Depende de:** S17 (ou fixtures). **Modelo:** padrão. **Estimativa:** 4 h.

## Totais

| Fase | Passos | Estimativa |
|---|---|---|
| A | S01, S02, S03, S03b | 13 a 16 h |
| B (paralelos) | S04, S05, S06, S09, S10, S14 | 21 h em série / cerca de 7 h com 3 agentes |
| C | S07, S08, S15 | 16 h |
| D | S11a, S11b1, S11b2, S11c, S12, S13 | 34 h |
| E | S16, S17, S18 | 10 h, mais a equipe |

Total: cerca de 95 h em série; cerca de 65 h com paralelização.

## Perguntas abertas (não bloqueiam até S10)

1. Lista completa de variáveis (D-107). S03 cria só os 4 gentílicos; cada variável nova é um `ADD COLUMN`.
2. Admin pode marcar "Revista Impressa Atualizada"? O padrão em S14 é não.
3. A Pedagógica precisa revisar os seeds de 2026, em especial o `f2-mt.hbs` (cópia do LP).

## Verificação ponta a ponta

- `docker compose run --rm app python manage.py test` e `makemigrations --check`.
- `cd app/e2e && npx playwright test`.
- `node app/nucleo/static/revista/f1/regua.test.mjs`.
- Manual: painel de 2026 → validar uma revista → marcar impressa → editar o template → ver o diff do impresso → baixar o zip e abrir por duplo clique.

## Registro (depois da aprovação, ainda sem commit)

1. Copiar este plano para `plans/revista-express-django.md` no repositório.
2. Registrar a D-126 no `state.md`. Ela traz:
   - o plano S01–S18;
   - o app em `app/`;
   - F1 copiado e generalizado para 2 a 5 padrões;
   - foto do impresso com escalas e textos (sem SVG e capa);
   - variáveis como colunas;
   - convenção de título do F2;
   - `svg_ids` sem prefixo.
3. Substituir a seção "Plano" do `state.md` por S01–S18, com S01 marcado como "agora".
4. Regerar `docs/Modelo_ER_Revista.pdf` a partir do ER novo, validando o Mermaid.
