# Testes de navegador (Playwright)

Os testes ponta a ponta do sistema atual ficam em `app/e2e/` e rodam contra o `app` Django. O roteiro manual do sistema antigo (editor React, API e Mongo) foi aposentado junto com ele (D-187).

## Rodar

```bash
docker compose up -d app
cd app/e2e
npm ci
E2E_ADMIN_USUARIO=<superusuário> E2E_ADMIN_SENHA=<senha> npx playwright test
```

- `baseURL`: `http://localhost:8000` (mude com `E2E_BASE_URL`) (`app/e2e/playwright.config.ts:8`).
- Todo spec roda em dois projetos, `chromium` (1280×720) e `desktop-1440` (1440×900), com `workers: 1`: todos entram com o mesmo usuário, que toma o bloqueio da própria outra aba (D-191), e o `anos.spec` abre e apaga 2027, o ano mais recente que outro spec veria no meio (D-234).
- Sem `E2E_ADMIN_USUARIO` e `E2E_ADMIN_SENHA`, os specs **pulam em silêncio**. A regra é 0 pulados.
- Os specs gravam no banco apontado. Rode contra o banco de desenvolvimento ou uma [stack isolada](#stack-isolada), nunca contra dados reais.
- Convenções de espera (`alpinePronto`, "Salvo às…") em [`telas/design-system.md`](telas/design-system.md), seção 8.

## Preparo do banco

A suíte inteira precisa disto (o cabeçalho de cada spec diz o que ele usa):

1. A demonstração: `docker compose run --rm app python manage.py criar_demo --ano 2026` (só com DEBUG). Os specs de matriz e de revista partem dela, para copiá-la ou só lê-la.
2. Um ano 2025 vazio: `docker compose run --rm app python manage.py shell -c "from nucleo.models import Ano; Ano.objects.create(ano=2025)"`. Não use `abrir_ano 2027`: ele copia os descritores, e o `item.spec` passa a achar dois "D01" (`ano.spec.ts`).
3. O superusuário `e2e` (`createsuperuser`), passado em `E2E_ADMIN_USUARIO` e `E2E_ADMIN_SENHA`.
4. Um usuário do grupo Impresso (`imp-e2e`), passado em `E2E_IMPRESSO_USUARIO` e `E2E_IMPRESSO_SENHA` (comando no cabeçalho de `impresso.spec.ts`). Sem eles, os testes do Impresso pulam.

## Stack isolada

O banco de dev normalmente não tem a demonstração. Para rodar a suíte inteira sem tocar nele, suba uma stack compose própria (banco e volume novos) e derrube no fim:

```bash
export COMPOSE_PROJECT_NAME=e2e-suite   # se o .env da raiz fixa o nome, só o -p sobe em cima do dev
docker compose -p e2e-suite up -d --wait db
docker compose -p e2e-suite run --rm app python manage.py migrate
# preparo da seção anterior, sempre com -p e2e-suite
APP_PORT=8040 docker compose -p e2e-suite up -d app
cd app/e2e && E2E_BASE_URL=http://localhost:8040 E2E_COMPOSE_PROJECT=e2e-suite \
  E2E_ADMIN_USUARIO=e2e E2E_ADMIN_SENHA=<senha> npx playwright test
cd ../.. && docker compose -p e2e-suite down -v
```

`E2E_COMPOSE_PROJECT` diz à limpeza qual stack limpar. Sem ela, a limpeza roda no banco do dev.

## Limpeza no fim (D-224)

O `globalTeardown` (`app/e2e/limpar.ts`) roda `manage.py limpar_e2e --usuario <E2E_ADMIN_USUARIO>` por `docker compose exec` no fim de toda execução, mesmo quando um spec para no meio.

- Apaga os parceiros "E2E …" (com parceiro-ano, cortes, projetos e revistas que a cascata criou), as matrizes "E2E …" e os templates "E2E …". Só os que o usuário de teste criou: o registro de criação no histórico é dele.
- Matriz e template saem pela regra da tela (D-205, D-207). Em uso, ficam, e o comando avisa.
- Cópias de etapa do projeto (D-280): as dos projetos dos parceiros "E2E …" saem com descritores e tarefas, antes do projeto e antes das matrizes; assim a matriz "E2E …" que serviu de base fica livre e sai em seguida.
- Risco conhecido (D-283, item 4c): matriz "E2E …" usada de base por projeto que não é "E2E …". Com o projeto ativo, a matriz fica ("Em uso, ficaram: …"), mas a dica da mensagem só fala em template da revista e matriz do parceiro: a saída é desfazer a cópia naquele projeto. Com o projeto arquivado, a matriz sai e a cópia dele fica sem base (`ON DELETE SET NULL`). Por isso o spec só cria cópia em projeto "E2E …".
- Só roda com DEBUG. Se a limpeza falhar, a execução só avisa. À mão: `docker compose exec app python manage.py limpar_e2e` (`--simular` lista o que sairia).

## Spec só edita o que criou (D-225)

Um spec nunca edita revista que ele mesmo não criou, nem o que alimenta a revista (projeto, variáveis, cortes, textos, arquivos, template escolhido). "Volto o valor original no fim" não vale: se o teste falha no meio, o dado real fica alterado.

O spec cria o próprio parceiro "E2E …", e a cascata gera o projeto e a revista dele. Helpers em `app/e2e/tests/helpers.ts`:

- `parceiroComProjeto`: parceiro "E2E …" com cortes, projeto e revista LP de 2026.
- `revistaPropria`: o mesmo, com matriz, templates, infográfico e capa, pronta para validar (6 de 6).
- `matrizPropria`: cópia "E2E …" da matriz Demonstração, para os specs que editam matriz.
- `revistaDemo`: a revista LP da demonstração, só para os specs que leem.

## Etapa do projeto (`etapa-projeto.spec.ts`)

Cobre o fluxo da cópia local na aba Matriz do projeto. Cada teste cria a própria matriz (`matrizPropria`) e a própria revista com ela (`revistaPropria`); nunca a Demonstração, porque a cópia derivada dela faria o aviso do editor aparecer nos outros specs. A cópia se edita sempre pela tela B.

1. **Cópia local, edição isolada e desfazer:** "Editar só neste projeto" abre o editor da cópia; o texto mudado aparece no preview da revista e não na etapa da matriz, cujo editor mostra "1 projeto(s) têm cópia a partir desta etapa: …"; "Desfazer a cópia", digitando a etapa e o componente, volta a linha a "usa a matriz".
2. **A base mudou:** com a matriz mudada depois da cópia, a aba Matriz mostra "A base mudou" e o "Validado" é recusado (pendência `base`); "Revisar mudanças da base" → escolha → "Concluir revisão" tira o selo e a revista valida.
3. **Modal de impacto e impresso:** com a revista validada e impressa, mudar a matriz abre o modal com "Abre revisão em 1 projeto(s) com cópia desta etapa: …"; depois da revisão e de um descritor novo na cópia, o Impresso vê os dois em "o que mudou".

Fora do E2E, cobertos por teste Django: "Apontar" (pede etapa não canônica fixa no banco, que viraria coluna em todos os specs de cortes), item com imagem trocada e o modal de impacto ao concluir a revisão.
