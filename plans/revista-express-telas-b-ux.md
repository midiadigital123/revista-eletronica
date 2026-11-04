# Plano de implementação: Reforma de UX das telas B

> **Para agentes:** sub-skill obrigatória: superpowers:subagent-driven-development (recomendado) ou superpowers:executing-plans. Cada passo usa checkbox (`- [ ]`). Na execução, copie este arquivo para `plans/revista-express-telas-b-ux.md`, seguindo a convenção do repositório.

**Objetivo:** aplicar os 18 comentários do docx "Comentários Revista Eletrônica". O menu passa de 9 para 5 itens, cada dado tem uma única tela onde é editado, a confirmação de impacto vira modal, o autosave segue a regra de impacto, linhas novas nascem de um botão e o acabamento visual fica no nível do editor React.

**Arquitetura:** o Django continua renderizando HTML. O HTMX 2.0.4, já vendorizado, fica onde já funciona. Entra o **Alpine.js no build CSP**, que cuida só do estado local: modal, edição inline, linha nova, status do salvamento e aviso de saída. Para o autosave por campo, o cliente usa `fetch` e um protocolo JSON único. O SortableJS cuida da reordenação. Toda gravação com impacto no "Validado" passa por um único serviço, que simula a mudança e lista as revistas afetadas.

**Stack:** Django 6.1, HTMX 2.0.4 (já em uso), Alpine.js `@alpinejs/csp` 3.14.9 (novo), SortableJS 1.15.6 (novo), Playwright e `django.test.TestCase`.

**Spec:** este plano e a revisão de UX feita na sessão de 03/11. Os prints e comentários estão em `~/Downloads/Comentários Revista Eletrônica.docx`. As learnings ativas são "Confirmação… é um modal, não um checkbox…" (`.trail/learnings/2026-11-03-confirmac-a-o-de-ac-a-otavio.md`) e "Toda função do back precisa de botão na tela nova".

## Decisões já tomadas (registrar no `state.md` como D-195 em diante, no U0)

| # | Decisão | Descartado |
|---|---|---|
| a | Alpine.js no build CSP + `fetch`; o HTMX continua nas telas que já o usam | Migrar tudo para Alpine (soma 2 a 3 dias e não traz ganho para o usuário); só JS puro (código demais por tela) |
| b | Campo sem impacto salva sozinho. Campo com impacto abre o modal antes de gravar. O impacto é calculado **na hora, pelo servidor**, porque a mesma variável pode ou não tirar um "Validado" | Tudo sozinho com desfazer (o impacto só apareceria depois de gravado); manter o "Salvar" |
| c | A grade de Cortes passa a ser a visão "Cortes" de Projetos. Cada projeto também ganha uma aba Cortes | Só a aba no projeto (lançar 30 parceiros viraria 30 páginas) |
| d | Esta reforma roda **antes** de S6–S9, que já nascem no padrão novo | Fazer S6–S9 antes e adaptar depois |
| e | O menu fica com Painel, Projetos, Matrizes, Templates e Impresso. O seletor de ano vai para o cabeçalho e traz "Configurar <ano>" e "Abrir novo ano" | O seletor "+ Abrir ano" dentro de cada página |

## Modo de execução: worktrees em paralelo (D-201)

- **Branch de integração:** `feat/telas-b-ux`, criada a partir de `feat/telas-b-lacunas` logo depois do commit do U2. Cada passo roda num subagente com `isolation: "worktree"`, na branch `feat/ux-<passo>-<nome>` (ex.: `feat/ux-u3-autosave`), criada do topo da integração. O subagente faz o commit na própria branch, sem push e sem tocar no `state.md`.
- **Ambiente por worktree:** copie o `.env` da raiz **e apague a linha `COMPOSE_PROJECT_NAME`** (ela aponta para o projeto do dev do usuário; sem apagar, o `up` recria o app do dev e o `migrate`/`criar_demo` caem no banco de dev — incidente de 03/11). Exporte `COMPOSE_PROJECT_NAME=ux-<passo>` em todo comando e use um `APP_PORT` único (U3 8021, U6 8022, U8 8023, U9b 8024; as ondas seguintes reaproveitam). O compose do worktree tem banco e volume próprios, porque o nome do projeto vem da pasta. Preparo: `docker compose up -d db app`, `migrate`, `criar_demo --ano 2026` e os usuários `e2e` e `imp-e2e` (senhas aleatórias num arquivo fora do repo). No fim, `docker compose down -v`. Com isso, **nada de teste toca o banco de dev do usuário**.
- **Integração (eu, na raiz):** `git merge --no-ff` de cada branch na ordem da onda. Depois de cada onda: suíte Django, `makemigrations --check` e Playwright completo no resultado mesclado. Conflitos (o mais comum é a linha do include `_componentes/anos.html`, que o U6 remove) são resolvidos na integração e entram na mensagem de merge.
- **Ondas:**

| Onda | Passos em paralelo | Depende de |
|---|---|---|
| 1 | U2 (na raiz, já em curso) | U1 |
| 2 | U3 autosave · U6 menu e ano · U8 painel · U9b editor de template | U2 |
| 3 | U4 → U9 (mesmo agente: os dois mexem na MEC) · U5 → U8b (mesmo agente: os dois mexem na revista) | U3 |
| 4 | U7 hub Projetos | U3, U4, U6 |
| 5 | U10 acabamento | todas |

- **Tempo:** cerca de 12,5 dias em série, cerca de 6 dias com as ondas (o caminho crítico é U2 → U3 → U4/U9 → U7 → U10).

## Restrições globais

- CDN liberada pelo usuário (03/11). As libs novas vêm do jsDelivr com versão exata e `integrity` (SRI) + `crossorigin="anonymous"`, registradas em `docs/telas/design-system.md`. O HTMX vendorizado fica como está.
- Alpine **só no build CSP**: cada `x-data` aponta para um componente registrado com `Alpine.data(...)` em `static/ui/componentes.js`, e as expressões são acesso a propriedade ou chamada de método, sem lógica inline.
- O mundo visual é o do `DESIGN.md` ("A Bancada Neutra"): Inter, neutros, cor só nos Padrões 01–04, âmbar de aviso e destructive, movimento de 120/180 ms com `--ease-saida`, `prefers-reduced-motion` e foco de 2px. Componentes compartilhados vão para `static/ui/ui.css` e `templates/ui/_componentes/`.
- Valem os invariantes de `plans/revista-express-telas-b-lacunas.md`, que entram em todo passo: suíte verde, `makemigrations --check` limpo, Playwright verde (**rodando de verdade, não pulando**), permissão checada no template e na view, teste cobrindo o perfil que grava e o Impresso recebendo 403, e o `grep "admin:"` nas telas B só diminuindo.
- Bloqueio: todo endpoint novo de gravação numa tela com bloqueio usa `com_bloqueio` (`app/nucleo/ui_bloqueio.py:63`) e a mesma sessão do GET. O `fetch` manda o campo da sessão, como o `bloqueio.js` já faz no HTMX.
- Nenhuma função do back pode sumir da tela ao fundir páginas. Antes de apagar qualquer rota, liste as ações dela e aponte a tela que passa a ter cada uma.
- URLs antigas (`/ui/lotes/…`, `/ui/revista/<ano>/`, `/ui/variaveis/<ano>/`, `/cortes/<ano>/`) **redirecionam** para a tela nova, sem quebrar favoritos nem specs.
- Textos de interface em PT-BR, no formato "causa + correção" que as mensagens já usam.

## Foco da revisão (falhas que nenhum caso feliz testa)

1. **Bloqueio perdido no meio do autosave** (resposta 409): o campo não pode aparecer como "Salvo". A tela inteira vira só leitura com o nome de quem edita. Teste no U3.
2. **Duas pessoas na grade de Cortes**, que não tem bloqueio e usa conflito otimista pelo campo `o-`: o autosave por célula manda o valor original e recebe um conflito explícito, sem gravar por cima. Teste no U3.
3. **Rede caiu durante o autosave:** o status mostra "Não salvo: sem conexão · Tentar de novo" e o aviso de saída só dispara nesse caso. Teste Playwright com `page.route` abortando a requisição, no U3.
4. **Modal de impacto só no teclado:** o foco entra no modal, Esc cancela **e devolve o valor anterior ao campo**, e o foco volta ao campo. Teste Playwright no U2.
5. **Trocar de ano numa página de detalhe sem ano na URL** (`/ui/projeto/<pk>/`): leva ao projeto do mesmo parceiro no outro ano, se existir, ou à lista de projetos desse ano. Nunca dá 404. Teste no U6.

---

## Mapa de arquivos

| Arquivo | Responsabilidade | Passo |
|---|---|---|
| `static/ui/componentes.js` (novo) | Registro de `Alpine.data`: `impacto`, `campoAuto`, `linhaNova`, `nomeInline`, `ordenavel`, `seletorAno`, `saida` | U1 a U6 |
| `templates/ui/base.html` | Ordem de carga, menu de 5 itens, seletor de ano no cabeçalho | U1, U6 |
| `servicos/impacto.py` (novo) | `perdem_validado(gravar, revistas)`, extraído de `urls/cortes.py:55` | U2 |
| `templates/ui/_componentes/impacto.html` (novo) | `<dialog>` com a lista de revistas que perdem o "Validado" | U2 |
| `ui_autosave.py` (novo) | `responder_campo(...)`: protocolo JSON do autosave | U3 |
| `templates/ui/_componentes/status_salvo.html` (novo) | "Salvando… / Salvo às HH:MM / Não salvo · Tentar de novo" | U3 |
| `contexto.py` (novo) + `sistema/settings.py` | Context processor com o ano atual, os links de troca de ano e o ano guardado na sessão | U6 |
| `urls/ui_projeto.py`, `templates/ui/projeto/*` | Hub Projetos (visões e ações em massa) e página do projeto com abas | U7 |
| `urls/painel.py`, `templates/ui/parciais/painel_corpo.html` | Painel agrupado por parceiro | U8 |

Os caminhos são relativos a `app/nucleo/`.

---

### U0: Bug do contador eterno em Cortes + registro (~20 min)

**Arquivos:** `templates/ui/cortes.html:105`; `app/e2e/tests/cortes.spec.ts`; `state.md`; `plans/revista-express-telas-b-ux.md`.

- [x] Teste Playwright `cortes sem edição não acusa alteração`: abre `/cortes/2026/`, espera o texto `Nenhuma alteração.` e que nenhuma célula tenha `[data-alterada]`. Depois recarrega, e o recarregamento não pode abrir diálogo (`page.on('dialog')` falha o teste).
- [x] Rode o teste e confira que **falha**.
- [x] Correção: `tr.querySelectorAll("td input.input")`. O seletor atual pega também o campo do "Renomear" e desloca a comparação.
- [x] Confira o mesmo tipo de seletor em `variaveis/pagina.html` (perto da `:112`) e em `templates/editar.html` (perto da `:94`). Corrija se houver.
- [x] Rode de novo e confira que passa. Registre D-195 a D-199 (decisões a–e) no `state.md`.
- [x] Commit `fix(ui-b): contador de alteração não salva em Cortes`.

### U1: Fundação Alpine + SortableJS (~45 min)

**Arquivos:** `static/ui/componentes.js`, `templates/ui/base.html:14-16`, `docs/telas/design-system.md` §2, `app/e2e/tests/fumaca.spec.ts`.

**Produz:** `window.Alpine` iniciado em toda tela B, e `componentes.js` registrando componentes no evento `alpine:init`.

- [x] Teste de fumaça: numa tela B, `await page.evaluate(() => !!window.Alpine && !!window.Sortable)` é `true`, e o console não mostra erro.
- [x] Carregue do jsDelivr com SRI: `https://cdn.jsdelivr.net/npm/@alpinejs/csp@3.14.9/dist/cdn.min.js` e `https://cdn.jsdelivr.net/npm/sortablejs@1.15.6/Sortable.min.js`. Calcule o `integrity` com `curl -s URL | openssl dgst -sha384 -binary | openssl base64 -A`.
- [x] Ordem na base, toda com `defer`: `htmx.min.js` → `ui.js` → Sortable (CDN) → `componentes.js` → Alpine CSP (CDN). O Alpine fica por último para que o `alpine:init` encontre os registros.
- [x] Teste da fumaça passa. Na suíte Django, `test_ui_base` confere os 5 `<script>`. Commit.

### U2: Modal de impacto no lugar de todo checkbox "Confirmo" (~1 dia)

**Arquivos:** `servicos/impacto.py` (novo); `urls/cortes.py:55-95`; `matriz.py:130-152` (`ImpactoForm`); `paleta.py:51-89`; `templates/ui/_componentes/impacto.html` (novo); `parciais/matriz_painel.html:78`; `matriz_intervalo.html:15`; `anos/ano.html:85`; `cortes.html:54`; `lotes.py:139,184`; testes `test_ui_cortes`, `test_ui_matriz`, `test_ui_anos`, `test_ui_lotes`; `app/e2e/tests/impacto.spec.ts` (novo).

**Interfaces produzidas:**
- `perdem_validado(gravar: Callable[[], None], revistas: Iterable[Revista]) -> list[Revista]` em `servicos/impacto.py`. Roda `gravar()` num savepoint desfeito e devolve as revistas validadas cujo `hash_validado` muda (`servicos/resolver.py:293`, `servicos/validacao.py:20`). A função atual de `urls/cortes.py:55` passa a chamar esta.
- O `ImpactoForm` ganha `precisa_confirmar: bool` e `perdem: list[Revista]`. O campo `confirmar_impacto` vira **sempre** `HiddenInput`.
- Include: `{% include "ui/_componentes/impacto.html" with form_id=… titulo=… perdem=… afetadas=… %}`, que renderiza um `<dialog x-data="impacto" data-abrir-ao-carregar>` com o título "<Ação> tira o “Validado” de N revista(s)", a lista de revistas e os botões "Cancelar" (outline) e "<Ação> e tirar Validado" (destructive).
- Componente Alpine `impacto`: abre com `showModal()` ao carregar ou depois de uma troca HTMX. "Confirmar" põe `confirmar_impacto=on` no form e chama `requestSubmit()`. "Cancelar" e Esc fecham o modal e restauram os valores do form a partir de `data-original`.

Passos:
- [x] Testes Django, um por lugar (renomear parceiro, intervalo, descritor, novo descritor, item, paleta):
  - `test_sem_confirmar_abre_modal_e_nao_grava`: `assertContains(r, 'role="dialog"')`, o nome da revista validada aparece, o dado continua igual e `esta_validada(...)` segue `True`.
  - `test_confirmado_grava_e_tira_validado`.
- [x] Testes novos de impacto onde hoje não existe: **grade de Cortes** (`cortes.gravar`) e **lote de matriz e de template** (`lotes.gravar_matriz` / `gravar_template`), com os mesmos dois casos.
- [x] Teste de regressão `test_nenhum_checkbox_confirmo`: percorre `templates/ui/**/*.html` e falha se aparecer `Confirmo:` ou `name="confirmar"` em `type="checkbox"`.
- [x] Implemente o serviço, o include e o componente. Troque cada checkbox pelo include.
- [x] Playwright `impacto.spec.ts`: renomear um parceiro validado abre o modal; Esc volta o nome antigo e devolve o foco; confirmar grava. Commit.

### U3: Autosave por campo com regra de impacto (~2 dias, em dois commits)

**Arquivos:** `ui_autosave.py` (novo); `templates/ui/_componentes/status_salvo.html` (novo); rotas `ui_projeto_campo` (`urls/ui_projeto.py`), `cortes_celula` (`urls/cortes.py`), `ui_ano_campo` (`urls/ui_anos.py`) e `ui_matriz_campo` (`urls/ui_matriz.py`); templates `projeto/projeto.html`, `variaveis/pagina.html`, `cortes.html`, `anos/ano.html`, `parciais/matriz_painel.html`; testes `test_ui_autosave.py` (novo) e `app/e2e/tests/autosave.spec.ts` (novo).

**Protocolo** (único, documentado em `design-system.md`). O POST manda `campo`, `valor`, `confirmar_impacto?`, `original?` e a sessão de bloqueio. As respostas:
- `200 {"ok": true, "salvo_em": "10:15"}`
- `200 {"ok": false, "impacto": {"titulo": str, "perdem": [str], "afetadas": int}}`: **não grava**.
- `422 {"ok": false, "erros": [str]}`
- `409 {"ok": false, "conflito": str}`: bloqueio perdido, ou o valor `original` difere do que está no banco.
- `403`, como hoje.

**Interface:** `responder_campo(request, *, form: Form, gravar: Callable[[dict], None], revistas: Callable[[], Iterable[Revista]]) -> JsonResponse` em `ui_autosave.py`. Valida o form de um campo só, chama `perdem_validado` (U2) e grava ou devolve o impacto.

**Componente Alpine `campoAuto`**, no form:
- Escuta `change` (o texto dispara ao sair do campo) e envia **um campo por vez**, com fila por campo.
- Atualiza o `status_salvo` do cabeçalho.
- Quando a resposta traz `impacto`, abre o mesmo modal do U2 e reenvia com a confirmação.
- No 409, desliga o form como o `bloqueio.js` faz.
- Componente global `saida`: só faz `beforeunload` se houver envio pendente ou com erro.

Passos:
- [x] **U3a: infra + Projeto + Variáveis.** Testes em `test_ui_autosave.py`, um caso por resposta do protocolo (200, impacto, 422, 409 de bloqueio, 403 para o Impresso). A planilha de Variáveis e a página do projeto usam **a mesma rota** `ui_projeto_campo`, assim o dado tem um único ponto de escrita.
  - Implemente.
  - Tire o "Salvar projeto" e o "Salvar variáveis". Passos e cores continuam formsets, mas cada linha salva sozinha pela mesma rota.
  - Playwright: digitar uma variável, sair do campo, ver "Salvo às" e recarregar sem diálogo. Com a rede abortada, ver "Não salvo · Tentar de novo" e o diálogo ao sair.
  - Commit.
- [x] **U3b: Cortes + Ano + descritor.** Testes, incluindo o `409` de Cortes quando `original` não bate (duas abas).
  - Implemente.
  - Tire "Salvar cortes", "Salvar etapas", "Salvar componentes" e "Salvar descritor". O editor de Templates **mantém** o salvar explícito, porque gera uma versão assinada.
  - Apague o contador "N parceiro(s) com alteração não salva" e o `beforeunload` inline das três páginas, que passam a usar o componente `saida`.
  - Commit.

### U4: Linha nova por botão, ordem automática e reordenar (~1 dia)

**Arquivos:**
- `urls/ui_anos.py:79-83,119-120` (`EtapaForm`, formsets com `extra=1`)
- `urls/ui_matriz.py:230,250,257-272` (descritor e tarefas)
- `anos/ano.html:22-55`, `parciais/matriz_painel.html:51-56`
- Rotas novas `ui_ano_linha`, `ui_ano_reordenar` e `ui_matriz_reordenar`
- Testes em `test_ui_anos` e `test_ui_matriz`, e `app/e2e/tests/linhas.spec.ts`

**Reuso:** o padrão de linha por botão via HTMX que o Projeto já tem (`ui_projeto_linha`, `parciais/projeto_linha.html`).

**Interfaces:**
- `proxima_ordem(qs) -> int`, que é `max(ordem) + 1` (1 quando vazio).
- `POST …/reordenar/` com `ids=[pk,…]`, que grava a ordem 1…N numa transação. Responde 422 se a lista não for exatamente o conjunto atual.
- Componente `ordenavel`: alça de arrastar (SortableJS, `handle: ".alca"`) e botões "Mover para cima/baixo" para o teclado. Os dois disparam o POST de reordenação.

Passos:
- [x] Testes:
  - `test_form_sem_campo_ordem` (etapa, descritor, tarefa).
  - `test_nova_etapa_vai_para_o_fim`.
  - `test_reordenar_grava_1_a_n`.
  - `test_reordenar_lista_incompleta_422`.
  - `test_sem_linha_vazia` (o texto "Preencha a última linha" não aparece, e o formset usa `extra=0`).
- [x] Implemente nas etapas, componentes, descritores (lista da MEC) e tarefas. Na grade de Cortes, o form "Nova linha" sai e entra o botão "+ Adicionar parceiro" **logo abaixo da tabela**, que abre a linha com o foco no nome.
- [x] Playwright: clicar em "+ Adicionar etapa" faz a linha aparecer com foco; Enter grava; Esc descarta; arrastar troca a ordem. Commit.

### U5: Renomear inline (~0,5 dia)

**Arquivos:** `cortes.html:51-56` (o `<details>`), `matriz/matriz.html:16,66-71` (diálogo), `revista/revista.html:17-26` (o "Editar nome", que **sai**: o nome do projeto passa a ser editado só no Projeto, e a revista mostra um link "Editar no projeto"), e as rotas `cortes_renomear_parceiro` e `ui_matriz_renomear`, que passam a falar o protocolo do U3.

**Componente `nomeInline`:** o nome aparece como texto com um botão-lápis acessível ("Renomear <nome>"). O clique troca para um input já com foco; Enter salva; Esc cancela; ao sair do campo, salva. Se houver impacto, abre o modal do U2.

- [x] Testes: o renomear com o protocolo JSON (200, impacto, 422 para nome vazio ou repetido, 403); `ui_revista_editar` com `acao=nome` responde 400; o texto `Editar nome` não aparece em `revista.html`.
- [x] Implemente. Playwright: renomear o parceiro pela grade. Commit.

### U6: Menu de 5 itens + seletor de ano global (~1 dia)

**Arquivos:** `templates/ui/base.html:24-39`; `contexto.py` (novo); `sistema/settings.py` (registrar o context processor); `templates/ui/_componentes/anos.html` (vira o seletor do cabeçalho); remover o include desse componente das 9 páginas listadas no mapa (`painel/painel.html:15`, `cortes.html:29`, `projeto/lista.html:18`…); testes em `test_ui_base.py` e `test_ui_links.py`.

**Interface:** `ano_atual(request) -> dict` é o context processor e devolve:
- `ano_ctx`: o `Ano` atual, que vem do kwarg `ano`, ou do objeto da página, ou da sessão, ou do ano mais recente.
- `trocas_ano`: lista de `(ano: int, url: str)`. A URL usa `request.resolver_match.url_name` com o kwarg `ano` trocado e preserva a query string. Em páginas sem kwarg `ano`, aplica a regra do Foco da revisão, item 5.
- Grava `request.session["ano"]`. As rotas `_inicio` passam a redirecionar para o ano da sessão.

Detalhes:
- `secao`: Cortes, Variáveis, Revistas e Lotes passam a marcar `projetos`; a página do ano marca nenhum item, mas destaca o seletor.
- O seletor é um botão "2026 ▾" que abre um popover (`popover` nativo + `x-data="seletorAno"`). Ele lista os anos, "Configurar 2026" (`ui_ano`) e, com `perms.nucleo.abrir_ano`, "Abrir novo ano" (`ui_anos`).

Passos:
- [x] Testes:
  - `test_menu_tem_5_itens` (os nomes exatos).
  - `test_troca_de_ano_mantem_rota_e_query` (`/painel/2026/?falta=validado` vai para `/painel/2025/?falta=validado`).
  - `test_troca_em_projeto_vai_ao_mesmo_parceiro`.
  - `test_abrir_ano_so_com_permissao`.
  - `test_nenhuma_pagina_inclui_abrir_ano`.
- [x] Implemente. Rode o `test_ui_links` completo. Commit.

### U7: Hub Projetos (~2 dias, em dois commits)

**Arquivos:** `urls/ui_projeto.py:52-169`; `templates/ui/projeto/lista.html` e `projeto.html`; `cortes.html`; `variaveis/pagina.html`; `urls/ui_lotes.py`; `lotes.py`; `urls/ui_revista.py:67` (a lista); redirects em `urls/cortes.py`, `urls/ui_variaveis.py`, `urls/ui_lotes.py` e `urls/ui_revista.py`.

**U7a: lista com visões e ações em massa**
- Abas "Lista · Cortes · Variáveis" (`_componentes/projetos_abas.html`).
  - "Lista": uma linha por projeto, com o parceiro, a matriz e as revistas como selos (LP, MT) mostrando situação, Preview e zip. Isso **substitui a lista de Revistas**.
  - "Cortes": a grade atual, agora com a coluna Parceiro e o cabeçalho fixos.
  - "Variáveis": a planilha atual.
- Ações em massa na "Lista": checkbox por projeto e uma barra fixa embaixo com "Atribuir matriz…" e "Atribuir template…". Cada uma abre um diálogo com o select (no template, também o componente e F1/F2), reaproveita `lotes.gravar_matriz` e `gravar_template` e passa pelo modal de impacto do U2. Isso **substitui Lotes**. O aviso "em edição por X: será pulado" continua.
- GET em `/ui/lotes/…`, `/ui/revista/<ano>/`, `/ui/variaveis/<ano>/` e `/cortes/<ano>/` redireciona (302) para a aba equivalente. Os POSTs antigos continuam funcionando até o fim do U7.

**U7b: página do projeto com abas**
- Abas: **Dados** (nome e variáveis), **Matriz** (select com autosave e impacto; é o único lugar da tela B que grava a matriz de um projeto, além da ação em massa, e as duas chamam o mesmo serviço), **Cortes** (a linha deste parceiro, usando `cortes.grade` filtrada), **Passos e cores** (as sobrescritas) e **Revistas** (um cartão por componente com templates F1/F2, SVG e capa, Preview, Validado e o link para a página da revista, que continua sendo o detalhe das seções).
- **Interface:** `atribuir_matriz(parceiro_ano, matriz, usuario) -> None` em `servicos/`. É usada por `_gravar_matriz` (`ui_projeto.py:151`) e por `lotes.gravar_matriz`.

Passos:
- [x] Testes:
  - Inventário `test_nenhuma_acao_perdida`: para cada rota antiga, a ação continua alcançável na tela nova (nomes de botão exatos).
  - Os redirects.
  - A ação em massa com e sem impacto.
  - A aba Matriz e a ação em massa chamam `atribuir_matriz` (`mock.patch`).
  - O Impresso não vê a barra de ações e recebe 403.
- [x] Implemente o U7a, rode o Playwright completo (`cortes`, `painel` e `lotes` atualizados) e faça o commit. Depois implemente o U7b e faça o commit.

### U8: Painel redesenhado (~1 dia)

**Arquivos:** `urls/painel.py:68-101`, `urls/ui_painel.py:20`, `templates/ui/painel/painel.html`, `parciais/painel_corpo.html`, `_componentes/painel_tarefa.html` (**apagar**) e `static/ui/telas/painel.css`.

- As linhas ficam agrupadas por parceiro: uma linha de grupo com o nome, o link do projeto e "N de M revistas completas", e abaixo uma sublinha por componente (o selo LP/MT, Preview e o status por coluna).
- O card "Próxima tarefa" e a nav "Montagem" saem. Os contadores por coluna, que já são links-filtro, viram o resumo principal: um contador ativo fica destacado e há um "Limpar filtro".
- Cabeçalho e coluna Revista ficam fixos. A barra "Validar selecionadas" também é fixa e mostra "N selecionada(s)".
- [x] Testes:
  - `test_agrupa_por_parceiro` (uma linha de grupo por parceiro, com as revistas na ordem dos componentes).
  - `test_sem_card_proxima_tarefa`.
  - `test_filtro_por_contador`.
  - Os testes atuais de seleção e validação continuam verdes.
- [x] Implemente e atualize o `painel.spec.ts`. Commit.

### U8b: Página da revista reorganizada (~1 dia)

**Problema (print de 03/11, revista SAESE MT):** as mesmas 4 pendências aparecem três vezes (caixa rosa no card de validação, duas faixas vermelhas cheias em "Textos" e "Sem template" nos selects). O vermelho cheio (`#b00020`) é usado para algo que é tarefa a fazer, não erro. A ordem está invertida: a validação, que é o último passo, vem primeiro, e templates e arquivos, que são pré-requisitos, ficam no fim. "✓ Validado" cinza parece um estado, e não um botão desabilitado. Há dois "Salvar" (templates, arquivos). Os inputs de arquivo são os nativos ("Procurar…"), e há rótulos duplicados ("SVG do F2" e "Trocar SVG do F2"). O "Editar nome" é um `<details>`. As três ações do cabeçalho têm o mesmo peso.

**Arquivos:** `templates/ui/revista/revista.html`, `parciais/revista_secao.html`, `revista_secoes.html`, `revista_validado.html`, `urls/ui_revista.py:134-193` (despacho por `acao`), `static/ui/telas/revista.css`, `tests/test_ui_revista.py`, `app/e2e/tests/revista-textos.spec.ts`.

**Layout novo:**
```
‹ Projetos 2026 › SAESE
SAESE · Matemática 2026                    [Abrir preview]  Baixar zip  ⋯ (Tela do impresso)
┌ coluna principal ─────────────────────────┐ ┌ Situação (fixa ao rolar) ──────┐
│ 1 Templates   F1 [select]  F2 [select]    │ │ 2 de 6 prontos  ▓▓░░░░          │
│               salva ao escolher           │ │ ✓ Matriz                        │
│ 2 Arquivos    SVG do F2 [área de soltar]  │ │ ○ Template F1 → ir              │
│               Baixar gabarito de ids      │ │ ○ Template F2 → ir              │
│               Capa [área + miniatura]     │ │ ○ SVG do F2 → ir                │
│ 3 Textos      (só com templates escolhidos;│ │ ○ Capa → ir                     │
│               senão, estado vazio neutro  │ │ [Validar revista] (desabilitado │
│               "Escolha os templates acima")│ │  com o motivo, ou primário)     │
└───────────────────────────────────────────┘ │ O que mudou para o impresso     │
                                              └─────────────────────────────────┘
```

Regras:
- **Uma única lista de pendências**, a da coluna Situação. Cada item é um link-âncora para o passo que o resolve. As faixas vermelhas e a caixa rosa saem. A cor de tarefa pendente é neutra (○ em muted-foreground); o vermelho fica só para erro de verdade (upload recusado, falha de gravação).
- Selects de template com autosave e impacto (protocolo do U3, `acao=templates`). A confirmação digitada "descartar N cópia(s)" continua, agora dentro do modal do U2.
- Arquivos: componente Alpine `arquivoSoltar` com área de soltar e clique, miniatura da capa, nome e tamanho do SVG atual, "Substituir" e "Remover". O envio acontece ao escolher o arquivo, com barra de progresso via `fetch` e o erro inline ("SVG maior que 3 MB: reduza e envie de novo"). O "Salvar arquivos" sai.
- Validação: o botão "Validar revista" fica na coluna Situação. Está desabilitado, com o motivo por escrito, até não sobrar pendência, e passa a primário quando a revista está pronta. Depois de validada, a coluna mostra "Validada por X em DD/MM HH:MM". O aviso "texto não salvo não entra" sai, porque o autosave cobre isso.
- O nome não se edita aqui (U5): o link "Editar no projeto" vai para a aba Dados.

Passos:
- [x] Testes:
  - `test_pendencias_aparecem_uma_vez`: cada texto de pendência aparece exatamente 1 vez no HTML.
  - `test_textos_sem_template_mostra_estado_vazio` (sem `class="faixa"`).
  - `test_validar_desabilitado_com_motivo`.
  - `test_upload_svg_grande_422_com_mensagem`.
  - `test_trocar_template_com_copias_pede_modal`.
  - Os testes atuais de seção, validado e permissão continuam verdes.
- [x] Implemente. Playwright: soltar uma capa mostra a miniatura e "Salvo às"; escolher os dois templates libera "Textos"; validar. Commit.

### U9b: Editor de template com seções travadas (~1,5 dia)

**Problema (print de 03/11, template F2 "Padrão"):** o texto inteiro é um textarea em markdown, e os marcadores `## abertura`, `## passo1`, `## dlg-p2`… ficam editáveis. Apagar um `#` ou trocar o id quebra a seção, e o usuário não tem como saber qual era o nome. Os ids não são conteúdo, são a estrutura do fascículo (`texto.SECOES_F1` e `texto.ID_F2`, `app/nucleo/texto.py:34-35`). A pré-visualização ainda mostra `## passo1`, que é ruído técnico.

**Decisão:** o editor passa a ser **estruturado por seção**. O **formato gravado não muda**: o servidor continua recebendo e validando o mesmo markdown `## id\ntítulo\n\ncorpo`, com `texto.validar`, `templates_texto.impacto` e `criar_versao`. Não há migração, e o admin segue igual.

**Arquivos:** `templates/ui/templates/editar.html`, `urls/ui_templates.py:95-158`, `templates_texto.py`, `static/ui/telas/templates.css`, `static/ui/componentes.js` (componente `editorSecoes`), `tests/test_ui_templates.py`, `app/e2e/tests/templates-editor.spec.ts` (novo).

**Interfaces:**
- `secoes_para_form(corpo: str) -> list[dict(id, titulo, corpo)]`, que usa `texto.secoes`.
- `form_para_corpo(secoes: list[dict]) -> str` em `templates_texto.py`, que é a inversa. A ida e a volta preservam o texto byte a byte para os seeds de 2026.
- `secoes_permitidas(fasciculo) -> dict`: no F1, `fixas=["introducao","fechamento"]`; no F2, `fixas=["abertura"]`, `repetiveis={"passo": "passoN", "dlg": "dlg-<passo>"}`.
- O POST manda `secao-N-id`, que fica oculto e é conferido no servidor contra `secoes_permitidas` (id inválido responde 422), `secao-N-titulo` e `secao-N-corpo`. A view monta o corpo com `form_para_corpo` e segue o fluxo atual (impacto e versão assinada).

**UI:**
- Cada seção é um bloco com o rótulo legível do id ("Abertura", "Passo 1", "Diálogo do passo 2"), num chip **não editável**, um campo "Título" (uma linha) e um campo "Texto" (textarea que cresce com o conteúdo).
- Mini-barra por campo: **N** (negrito), *I* (itálico), lista e "{ } Variável". O select de variáveis que hoje fica no topo passa para dentro dessa barra e insere no campo que está com o foco.
- F1: as duas seções são fixas, sem adicionar nem remover.
- F2: "+ Adicionar passo" cria o `passo<N+1>`, e "+ Adicionar diálogo" escolhe o passo e cria o `dlg-pN`. Seções opcionais têm "Remover seção", que pede o modal do U2 quando o template está em uso. A ordem segue a regra do fascículo, sem arrastar.
- A lista lateral de seções serve como índice e mostra o status de validade de cada uma: o erro de `texto.validar` vai para a seção certa, porque o prefixo `Seção {id}:` já existe nas mensagens.
- A pré-visualização mostra só o título e o texto renderizados, sem `## id`. A prévia continua HTMX, mandando o corpo montado.
- O "Salvar" explícito continua, porque cria uma versão assinada (decisão do U3). A barra mostra "Alterações não salvas", e o aviso de saída só aparece quando há alteração de verdade.

Passos:
- [x] Testes:
  - `test_ida_e_volta_preserva_seeds`: para cada template seed de 2026, `form_para_corpo(secoes_para_form(t)) == t`.
  - `test_id_fora_do_permitido_422`.
  - `test_id_nao_aparece_como_campo_editavel` (nenhum `input`/`textarea` com o valor `## `).
  - `test_adicionar_passo_numera_sequencial`.
  - `test_erro_de_validacao_aparece_na_secao_certa`.
  - Os testes atuais de impacto e versão continuam verdes.
- [x] Implemente. Playwright: editar o título do Passo 1, inserir `{{nome_parceiro}}` pelo botão, salvar, ver a tela de impacto e criar a versão 2. Commit.

### U9: Hierarquia do editor de matriz (~0,5 dia)

**Arquivos:** `matriz/mec.html`, `parciais/matriz_intervalo.html`, `parciais/matriz_painel.html` e `static/ui/telas/matriz.css`.

- Cabeçalho com o título "2EF Língua Portuguesa", a linha de contexto e o status de salvamento. À direita, um botão outline "Configurações" que abre um popover com o "Intervalo mínimo" (autosave com impacto).
- "+ Novo descritor" sai do cabeçalho e vai para o topo da lista de descritores, como botão outline.
- "Excluir descritor" vai para o fim do painel, numa zona de perigo separada e com o destructive suave. O fluxo de digitar o código para excluir continua.
- [x] Testes: os rótulos e papéis novos; a exclusão continua exigindo o código. Playwright do fluxo da MEC. Commit.

### U10: Acabamento visual e documentação (~1 dia)

- Tabelas largas: coluna-chave e cabeçalho fixos (`position: sticky`) e uma sombra na borda enquanto houver rolagem. Componente `.tabela-rolavel` em `ui.css` com um observer pequeno em `componentes.js`.
- Estados vazios que ensinam o próximo passo; estados de foco, hover, desabilitado e carregando em todo controle novo; entrada de linha nova com `animate-entra` (120 ms) e transição do status em 180 ms.
- Rode `impeccable critique` e `audit` nas telas alteradas. Corrija tudo num lote só. Rode `impeccable detect --json` uma vez sobre os templates e CSS alterados.
- Atualize `docs/telas/design-system.md` (componentes Alpine, protocolo do autosave, modal de impacto, linha nova, seletor de ano, libs e sha256) e as fichas em `docs/telas/fichas/` (crie `cortes.md` e `anos.md`, que faltam, e corrija o `telas-b.md:31-33`).
- [x] Rode o Playwright completo em desktop (1440px) e 1280px. Commit.
- [x] Último commit da leva: só o `state.md` (`docs: atualiza state.md`).

**Depois do U10:** retomar S6–S9 de `plans/revista-express-telas-b-lacunas.md`. "Nova matriz" (S6) e "Novo template" (S7) já nascem com linha nova, modal e autosave. S8 coloca os downloads nas abas do projeto e da revista.

---

## Verificação de ponta a ponta

1. `docker compose exec -T app python manage.py test nucleo`: tudo OK (hoje são 554).
2. `docker compose exec -T app python manage.py makemigrations --check --dry-run`: sem migração.
3. Prepare o E2E conforme `app/e2e/tests/painel.spec.ts:2-9`. Depois rode `cd app/e2e && E2E_BASE_URL=… E2E_ADMIN_USUARIO=… E2E_ADMIN_SENHA=… E2E_IMPRESSO_USUARIO=… E2E_IMPRESSO_SENHA=… npx playwright test`, com **0 pulados** nos specs novos. Pré-requisito: credenciais E2E, que hoje faltam (o `state.md` registra 11 pulados).
4. Roteiro manual com os prints do docx, um por comentário, conferindo que os 18 foram resolvidos:
   - Cortes sem contador falso e sem aviso ao sair.
   - Etapa nova por botão e sem campo de ordem.
   - Menu com 5 itens.
   - Lotes dentro de Projetos.
   - Painel agrupado e sem card.
   - Variáveis e matriz com um único lugar de edição.
   - Matriz com hierarquia e modal.
   - Ano acessível pelo seletor.
   - Revista com uma única lista de pendências, sem faixas vermelhas e com upload por área de soltar.
   - Template com os ids de seção travados.
5. `grep -rn "Confirmo:" app/nucleo/templates/ui` não retorna nada.

## Estimativa total
Cerca de 12,5 dias de execução: U0 20 min, U1 45 min, U2 1 dia, U3 2 dias, U4 1 dia, U5 0,5 dia, U6 1 dia, U7 2 dias, U8 1 dia, U8b 1 dia, U9 0,5 dia, U9b 1,5 dia, U10 1 dia. U8b depende de U2, U3 e U5. U9b depende de U2 e pode rodar em paralelo com U4 a U8.

**Pré-requisito do E2E (pendente do usuário):** credenciais dos usuários `E2E_ADMIN_*` e `E2E_IMPRESSO_*`, ou autorização para criá-los no banco de dev. A criação foi recusada em 03/11. U4 e U5 podem rodar em paralelo depois do U3, porque mexem em arquivos diferentes, exceto `cortes.html`: nesse arquivo, faça U4 antes de U5.
