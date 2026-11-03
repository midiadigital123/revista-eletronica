# Design system das telas B (referência obrigatória do time)

Telas do dia a dia como páginas próprias no Django, com o visual do editor React (D-183), HTMX servido localmente (D-186). Base: branch `feat/ui-b` (as 10 telas já integradas; lista e status em `docs/telas/telas-b.md`). Protótipo de referência: grade de cortes (`app/nucleo/cortes.py`, `urls/cortes.py`, `templates/ui/cortes.html`, `tests/test_ui_cortes.py`).

Caminhos abaixo relativos a `app/nucleo/`, salvo `editor/` (só leitura).

## 1. Arquivos por tela

| O quê | Onde |
|---|---|
| Rotas | `urls/ui_<tela>.py` (já existe, vazio, já incluído em `urls/__init__.py` sob `/ui/<tela>/`). **Não edite `urls/__init__.py`.** |
| Regra reaproveitada | módulo comum fora do admin (ex.: `cortes.py`) ou `servicos/`; o admin passa a importar dele. Nunca copie a regra. |
| Templates | `templates/ui/<tela>/*.html` (página) e `templates/ui/parciais/<tela>_*.html` (fragmentos HTMX) |
| Testes | `tests/test_ui_<tela>.py` |
| Ficha da tela | `docs/telas/fichas/<tela>.md` |
| CSS só da tela | `static/ui/telas/<tela>.css`, carregado no `{% block cabeca %}`; só o que é da tela. Componente que serve a 2+ telas vai para `static/ui/ui.css` (e o include para `templates/ui/_componentes/`). |

Telas e rotas (nomes `ui_<tela>`; ações `ui_<tela>_<acao>`):

| Tela | Módulo | URL | Rota principal |
|---|---|---|---|
| Painel (T23) | `ui_painel` | `/painel/<ano>/` | `painel` |
| Validar (T24, Validado de T21) | `ui_validar` | `/ui/validar/<ano>/` | `ui_validar` |
| Variáveis (T17) | `ui_variaveis` | `/ui/variaveis/<ano>/` | `ui_variaveis` |
| Projeto (T15/T16) | `ui_projeto` | `/ui/projeto/ano/<ano>/` (lista), `/ui/projeto/<pk>/` | `ui_projeto_lista`, `ui_projeto` |
| Templates (T12–T14) | `ui_templates` | `/ui/templates/<ano>/` | `ui_templates` |
| Matrizes (T09–T11) | `ui_matriz` | `/ui/matriz/<ano>/` | `ui_matriz` |
| Revistas (T20/T21) | `ui_revista` | `/ui/revista/<ano>/` | `ui_revista` |
| Impresso (T26/T27) | `ui_impresso` | `/ui/impresso/<ano>/` | `ui_impresso` |
| Lotes (T18/T19) | `ui_lotes` | `/ui/lotes/<ano>/matriz/`, `.../template/` | `ui_lotes_matriz`, `ui_lotes_template` |

- Cortes já é B e fica em `/cortes/<ano>/` (rota `cortes`).
- O Painel B ocupa `/painel/<ano>/` (rota `painel`; `urls/ui_painel.py` é incluído em `painel/` antes de `urls/painel.py`). O painel no estilo do admin saiu; `/painel/<ano>/validar/` (`painel_validar`) continua para quem chega pelo admin. O lote do painel B vai a `ui_validar`.
- A rota principal recebe o ano (`<int:ano>/`) quando a tela é por ano. A navegação usa `{% if ano %}{% url "ui_<tela>" ano.ano %}{% else %}{% url "ui_<tela>_inicio" %}{% endif %}`; a rota `_inicio` redireciona ao ano mais recente. Nenhum link de navegação cai no admin.

## 2. Casca e contexto

- `{% extends "ui/base.html" %}`, blocos `titulo`, `cabeca`, `conteudo`.
- Menu de 5 itens (U6): Painel, Projetos, Matrizes, Templates, Impresso. `secao` marca o item: Validar marca Painel; `cortes`, `variaveis`, `revistas` e `lotes` marcam Projetos; `anos` não marca nenhum e destaca o seletor.
- Ano: o context processor `nucleo/contexto.py:ano_atual` dá `ano_ctx` (kwarg `ano`, objeto da página, sessão ou o mais recente) e `trocas_ano` (mesma rota e query no outro ano; em detalhe, o equivalente do mesmo parceiro ou a lista do ano). Grava `request.session["ano"]`; as rotas `_inicio` usam `ano_da_sessao`.
- Cabeçalho de página: `<header class="pagina-cab"><div><h1>…</h1><p class="mudo">…</p></div><div class="acoes">…</div></header>` (`editor/src/projetos/ListaProjetos.tsx:31-34`).
- Página de detalhe (um item de uma lista): o caminho de volta é `<a class="mudo voltar" href="…">‹ Lista</a>` logo acima do cabeçalho, não um botão nas ações (matriz, MEC, revista, projeto, editor de template).
- Ações do cabeçalho: ir a outra tela = `.btn-ghost` ("Ver painel de 2026"); ação desta tela = `.btn-outline`; a principal = `.btn`.
- Já carregados pela base, nesta ordem e todos com `defer`: `ui/ui.css`, `ui/htmx.min.js` (2.0.4, local), `ui/ui.js`, SortableJS 1.15.6 (jsDelivr), `ui/componentes.js`, `ui/componentes/autosave.js` (U3) e Alpine.js `@alpinejs/csp` 3.14.9 (jsDelivr). Fonte Inter local.
- **CDN (D-199):** liberada para libs novas, sempre com versão exata, `integrity` (SRI sha384) e `crossorigin="anonymous"`. Hash: `curl -sL URL | openssl dgst -sha384 -binary | openssl base64 -A`.
  - `sortablejs@1.15.6/Sortable.min.js`: `sha384-HZZ/fukV+9G8gwTNjN7zQDG0Sp7MsZy5DDN6VfY3Be7V9dvQpEpR2jF2HlyFUUjU`
  - `@alpinejs/csp@3.14.9/dist/cdn.min.js`: `sha384-zaqGaLZBjCeXCLnYyKyAJrDaZcsW8AqZN7iDmFDw3TzHJvhjMckT1H52jWWza0w8`
- **Alpine (D-195):** só o build CSP. Todo `x-data` aponta para um componente registrado com `Alpine.data` em `static/ui/componentes.js`, no evento `alpine:init`; no HTML, só propriedade ou chamada de método (sem expressão inline). O HTMX continua nas telas que já o usam; o Alpine cuida só de estado local (modal, linha nova, edição inline, status do salvamento).

## 3. Tokens (copiados do editor)

Todos em `static/ui/ui.css` `:root`. Origem:

| Token | Editor |
|---|---|
| `--background`, `--foreground`, `--card`, `--primary(-foreground)`, `--secondary(-foreground)`, `--muted(-foreground)`, `--destructive`, `--warning`, `--warning-bg`, `--border`, `--input`, `--ring` | `editor/src/index.css:134-156` |
| `--sucesso` (o verde do ✓: status ok, validado, copiado) | o `text-green-700` dos selos do editor |
| `--radius` e derivados (`-md`, `-lg`, `-xl`) | `editor/src/index.css:123-129`, `:162` |
| `--padrao-1..4` (cores dos padrões) | `editor/src/index.css:15-18` |
| `--ease-saida`, animação `entra` | `editor/src/index.css:25-37` |
| `--font-sans` (Inter Variable) | `editor/src/index.css:88-89`; arquivos em `static/ui/fontes/` (de `@fontsource-variable/inter` 5.3.0) |
| `--font-mono` | pilha do sistema (o editor usa a do Tailwind) |

Cores fora dos tokens só onde o admin/preview já fixou: faixa vermelha `#b00020`, variável vazia `#fde68a`/`#713f12`, diff verde/amarelo/vermelho.

## 4. Componentes (classes em `ui.css`; includes em `templates/ui/_componentes/`)

| Componente | Quando usar | Como |
|---|---|---|
| Botão | ação principal (1 por área) / secundária / terciária / destrutiva | `.btn`, `.btn-outline`, `.btn-ghost`, `.btn-destrutivo`; tamanhos `.btn-sm`, `.btn-lg` (`components/ui/button.tsx`) |
| Campo | rótulo + controle + ajuda/erro | `.campo > label + .input/.textarea/.select + .ajuda/.erro`; erro também em `aria-invalid="true"` |
| Seletor de ano | cabeçalho da base (só ela inclui) | `_componentes/anos.html`: popover nativo + Alpine `seletorAno` (`static/ui/componentes/seletor-ano.js`) |
| Abas | partes da mesma tela (Templates F1/F2/Matrizes/Variáveis) | `<nav class="abas"><a aria-current="page">`; a aba é a URL (`?aba=`), não estado em JS |
| Tabela | listas curtas | `.tabela-caixa > table.tabela` |
| Tabela densa | painel, listas longas: cabeçalho fixo, 1ª coluna `.fixa` (é `position: relative`, para o `.sr-only` não vazar e criar rolagem na página) | `.tabela-densa > table.tabela`; `.num` alinha números; `.quebra` deixa quebrar |
| Grade editável | planilha de células (cortes, variáveis) | `form.grade > .grade-caixa > table.tabela` + `.barra-salvar` (ver `cortes.html`) |
| Lista + detalhe | navegar itens e editar um (matriz → descritores, revista → seções) | `.lado-a-lado > nav.lista + section.detalhe`; o item ativo com `aria-current`; o detalhe vem por HTMX |
| Duas colunas | editor + preview ao vivo | `.duas-colunas` |
| Modal | confirmação curta, formulário pequeno sem sair da tela | `<dialog class="dialogo" id="x"><header><h2>…</h2><p class="mudo">…</p></header>…<footer><button data-fechar class="btn btn-outline">Cancelar</button>…</footer></dialog>` + `<button data-abrir="x">`; `.dialogo-largo` para diff |
| Modal de impacto (U2) | gravação que tira o “Validado” de revistas; nunca checkbox "Confirmo" | O form sem `confirmar_impacto` não grava e volta com `{% include "ui/_componentes/impacto.html" with form_id=… acao=… perdem=… %}` (componente Alpine `impacto`): abre sozinho, lista as revistas, "<Ação> e tirar Validado" (`.btn-destrutivo`) reenvia com `confirmar_impacto=on`; Cancelar/Esc volta os campos com `data-original` e o foco. Na view: `form.pedir_confirmacao(perdem)` (`ImpactoForm.modal = True`) ou `servicos/impacto.perdem_validado(gravar, revistas)` |
| Renomear inline (U5) | nome de parceiro (grade de Cortes) e de matriz; nunca `<details>` nem modal | `{% url … as url %}{% include "ui/_componentes/nome_inline.html" with nome=… %}` dentro de um form `campoAuto` (o `data-url` do componente troca a rota). Texto + lápis "Renomear <nome>"; Enter ou sair do campo salva pelo protocolo do autosave (impacto, 422), Esc volta o nome. Na view: `responder_campo(request, form=form_de_um_campo(Form, "nome", …), …)` |
| Diff antes/depois | o que mudou (impresso, seção desatualizada, validar) | `difflib.HtmlDiff(...).make_table` → `table.diff` (já estilizado); ou `.diff-lado` com `<div><h3>Antes</h3>…</div><div><h3>Depois</h3>…</div>`, trechos em `.diff-velho`/`.diff-novo` |
| Faixa vermelha | lacuna que impede a revista de sair completa (D-116). Na página da revista (U8b) não: lá a única lista é a coluna Situação, com ○ neutro | `{% include "ui/_componentes/faixa.html" with texto=… url=… rotulo=… %}` |
| Variável vazia | `{{nome}}` sem valor no texto | `<span class="variavel-vazia">{{nome}}</span>` (o `texto.renderizar` já gera); variável preenchida: `.variavel` |
| Status ✓/falta | célula de pendência | `{% include "ui/_componentes/status.html" with ok=… url=… titulo=… %}` |
| Barra de salvar | form longo: contador de alterações à esquerda, ações à direita, fixa no rodapé | `.barra-salvar > span.mudo + .btn` |
| Confirmação forte | ação irreversível ou de grande impacto (reimportar matriz, descartar cópias) | `{% include "ui/_componentes/confirmar.html" with nome=… codigo=… texto=… erro=… %}` + botão `data-confirmado`; o form no servidor confere o texto |
| Só leitura | perfil sem permissão de escrita | `{% include "ui/_componentes/so_leitura.html" with texto="Só leitura: … Para editar, peça …" %}` |
| Mensagens | resultado de ação (Django `messages`) | já na base (`#mensagens`); fragmento HTMX que grava inclui `{% include "ui/_componentes/mensagens.html" with oob=True %}` |
| Toast | erro de rede/servidor do HTMX (automático) ou aviso efêmero | `uiToast("texto", "erro")` (`static/ui/ui.js`) |
| Estado vazio | lista sem itens | `{% include "ui/_componentes/vazio.html" with titulo=… texto=… url=… rotulo=… %}` |
| Badge | contagem, rótulo curto | `.badge`, `.badge-secundario`, `.badge-contorno`, `.badge-alerta`, `.badge-erro` |
| Carregando | pedido HTMX demorado | `hx-indicator` + `{% include "ui/_componentes/girando.html" with id=… %}` (`svg.girando.htmx-indicator`); o alvo com `.alvo-htmx` (ou `.detalhe`) e `hx-indicator` nele esmaece |
| Link da linha | nome na 1ª coluna que abre o item (painel, matrizes, templates, revistas, variáveis) | `a.link-linha` (sublinhado discreto que escurece no hover) |
| Link de texto | link no meio de uma frase ("usado por 2", "Limpar", "O que mudou") | `a.link` |
| Voltar | detalhe → lista de cima | `a.mudo.voltar` acima do `.pagina-cab` |
| Recolhível | conteúdo secundário longo (diff do validar, legenda das variáveis) | `<details class="recolhivel"><summary>…</summary>…</details>` |
| Caixa de erro | lista de pendências/erros dentro de um card (pendências da revista, prévia do template) | `.caixa-erro` com `<ul>` |
| Só leitura nativo | form inteiro sem permissão | `<fieldset disabled>`: os campos ganham o fundo de só leitura |
| Modal com form | o HTMX troca o form inteiro do modal | `<dialog class="dialogo"><form>…</form></dialog>` (o `form` vira a coluna do modal) |

## 5. HTMX

- Página inteira = GET normal. HTMX só para trocar um pedaço: detalhe da lista, preview, linha salva, filtro.
- Fragmentos em `templates/ui/parciais/<tela>_<pedaco>.html`; a mesma view devolve o fragmento ao HTMX e a página inteira ao resto (o link funciona sem JS e ao recarregar): `return pagina_ou_parcial(request, "ui/<tela>/x.html", "ui/parciais/<tela>_y.html", ctx)` (`nucleo.ui_bloqueio`). Ela põe `Vary: HX-Request` (sem isso o Voltar do navegador mostra só o fragmento de uma URL empurrada) e `e_htmx` trata a restauração de histórico do htmx (`HX-History-Restore-Request`) como página inteira.
- Região viva (`aria-live`) fica fora do `hx-target`: uma região recém-inserida não é anunciada. Copie o texto para ela no `htmx:afterSwap` (ver `ui/painel/painel.html`).
- Filtro que troca o corpo a cada `change`: `hx-sync="this:replace"` no form (a resposta velha não sobrescreve a nova).
- Atributos: `hx-get`/`hx-post` + `hx-target="#id"` + `hx-swap="innerHTML"` (padrão) ou `outerHTML` para trocar o próprio elemento; `hx-push-url="true"` quando o fragmento muda o "onde estou" (item da lista ativo); a lista leva `data-lista` e `ui.js` marca o link ativo (`aria-current`) e põe o foco no título do detalhe novo (sem `aria-live` no detalhe inteiro); `hx-trigger="input changed delay:400ms"` para preview ao vivo (o mesmo debounce do admin).
- CSRF: a base põe `hx-headers='{"X-CSRFToken": …}'` no `<body>`; todo `hx-post` já vai com o token. Forms comuns seguem com `{% csrf_token %}`.
- Erro 4xx/5xx: o HTMX não troca o alvo; `ui.js` mostra um toast. Erro de validação esperado: responda 200 com o fragmento e os erros nele.
- Depois de gravar: página inteira → `redirect` (PRG). Fragmento → 200 com o fragmento novo + mensagens `oob`; para ir a outra página use o header `HX-Redirect`.

### Autosave por campo (U3)

Campo sem impacto salva sozinho; com impacto, o modal do U2 abre antes de gravar. Servidor: `nucleo/ui_autosave.py`, `responder_campo(request, *, form, gravar, revistas, titulo)` (valida, simula com `perdem_validado` e grava ou devolve o impacto). `form_de_um_campo(Form, campo, valor, instance=…)` reaproveita o form inteiro trocando um campo só. Cliente: `static/ui/componentes/autosave.js` (`campoAuto` no `<form>`, `saida` em `_componentes/status_salvo.html`, no cabeçalho).

- POST: `campo`, `valor`, `original` (o que a tela tinha), `confirmar_impacto`, `form_id` e a sessão de bloqueio; `[data-linha]` manda também a linha inteira (passo, cor, tarefa); `Accept: application/json`.
- `200 {"ok": true, "salvo_em": "10:15"}` (+ `valor` normalizado, `id` da linha criada, `removida`).
- `200 {"ok": false, "impacto": {"titulo", "perdem": [str], "afetadas": int, "html"}}`: não gravou; `html` é o `_componentes/impacto.html`, inserido no form. Confirmar reenvia o campo com `confirmar_impacto=on`; Cancelar/Esc volta o valor gravado e o foco.
- `422 {"ok": false, "erros": [str]}`: erro embaixo do campo, status "Não salvo: corrija o campo marcado".
- `409 {"ok": false, "conflito": str}`: bloqueio perdido (o `com_bloqueio` responde JSON a quem pede JSON) → o form inteiro vira só leitura com o nome de quem edita. Com `atual` (Cortes, conflito otimista pelo `original`): mostra o conflito e "Tentar de novo" sobrescreve de propósito.
- `403`: sem permissão (só leitura, como no 409 de bloqueio).
- Marcação: `<form x-data="campoAuto" id="…" data-url="…">`; ancestral com `data-url`/`data-prefixo` troca a rota e tira o prefixo do formset; `[data-manual]` fica de fora (linha nova que ainda grava pelo botão). O aviso ao sair (`beforeunload`) só dispara com envio pendente ou com erro.
- U8b: `200` pode trazer `trocar: {id: html}` (o cliente troca essas partes da página: o que a gravação mudou fora do campo, como a Situação da revista). `responder_campo(…, simular=, modal=)`: `simular` roda na simulação no lugar do `gravar` (ex.: arquivo, só o sha256); `modal` é contexto extra do modal e o torna obrigatório (ex.: `copias`/`frase` de "descartar N cópia(s)"); os campos com `name` dentro do modal vão junto ao confirmar.
- Arquivo: `<div x-data="arquivoSoltar" data-soltar data-max="<bytes>" data-tipo="SVG">` com `label.soltar-area > input[type=file].sr-only` dentro do form `campoAuto`: soltar ou clicar envia o arquivo em `valor`; acima de `data-max` o erro aparece sem enviar. Ver `parciais/revista_arquivos.html`.
- Eventos no campo: `autosave:salvo` (`detail.valor`), `autosave:falhou`, `autosave:cancelado` (para `nomeInline` e `arquivoSoltar`).

### Linha nova e ordem (U4)

- Tabela editável não termina em linha vazia (formset com `extra=0`). `linhaNova` (`static/ui/componentes.js`): `<div x-data="linhaNova" data-total="id_<prefixo>-TOTAL_FORMS">` com `<template data-molde>` (o `empty_form`, com `__prefix__`), o alvo `[data-linhas]` e o botão `[data-abrir-linha]` "+ Adicionar <coisa>". A linha nasce no fim com o foco no 1º campo; o botão "Incluir <coisa>" da linha (ou Enter) grava pelo POST da página; Esc ou "Descartar" tira a linha e devolve o foco ao botão. Sem `data-total` (Cortes), o molde é um form próprio.
- Ordem não se digita. Linha nova vai para o fim: `proxima_ordem(qs)` (`ui_autosave.py`). Etapa segue a lógica escolar (`ordem_escolar` em `urls/ui_anos.py`: todo EF antes do EM; no mesmo ensino, pela série) e não se arrasta; componente segue o código.
- Reordenar (descritores da MEC, tarefas): `ordenavel` (`static/ui/componentes/autosave.js`) em `<ul|ol x-data="ordenavel" id="…" data-ordem-url="…/reordenar/">` com filhos `[data-id]` e `_componentes/ordem.html` (alça `.alca` do SortableJS + "Mover para cima/baixo" para o teclado). Servidor: `reordenar(request, qs, revistas=…, titulo=…)` grava 1…N pelo protocolo do autosave (impacto, 409 do bloqueio); 422 se `ids` não for exatamente o conjunto atual. Erro ou Cancelar no modal voltam a ordem gravada.

### Configurações e zona de perigo (U9)

- Ajuste raro da página (ex.: intervalo mínimo da MEC) fica num popover nativo atrás de um botão outline "Configurações" no cabeçalho: `<div x-data="popoverSob">` com `popovertarget` no botão (`x-ref="botao"`) e o painel `.popover-config` (`popover`, `x-ref="painel"`, `@toggle="alternou"`). O campo dentro salva sozinho (`campoAuto`); o modal de impacto abre por cima do popover.
- Ação destrutiva sai do topo e vai para o fim, em `.zona-perigo` (título, o que se perde e o botão `btn-destrutivo` suave). A confirmação forte (digitar o código, D-181) continua na página seguinte.

## 6. Bloqueio de edição (onde o admin usa `BloqueioAdminMixin`)

`nucleo/ui_bloqueio.py`, mesma regra e mesmo serviço do admin (`servicos/bloqueio.py`, D-080, D-081, D-121):

```python
@require_http_methods(["GET", "POST"])
@login_required(login_url="admin:login")
@com_bloqueio(lambda request, pk: get_object_or_404(Projeto, pk=pk), lambda u: u.has_perm("nucleo.change_projeto"))
def projeto(request, pk): ...   # usa request.pode_gravar
```

- `obter_alvo` devolve o objeto travado (Projeto, Template ou MatrizEtapaCC; revista trava o projeto) ou `None` para não travar (arquivado: a view mostra só leitura).
- GET de página: quem pode gravar adquire; quem não consegue vê o aviso "Somente leitura: Ana está editando…" e `request.pode_gravar = False`.
- GET HTMX: não adquire; vale a sessão que o `bloqueio.js` manda em todo pedido HTMX.
- POST: sem permissão → 403; confere com `conferir_na_transacao` e roda a view na mesma transação; perdeu → "Não salvo: você perdeu o bloqueio…" e recarrega. Redirect (ou `HX-Redirect`) libera.
- Template: `{% include "ui/_componentes/bloqueio.html" %}` dentro do `<form>` que grava, depois do `{% csrf_token %}`, fora de qualquer `hx-target`.
- Lotes (várias entidades por POST) não usam o decorador: pulam os travados com `bloqueio.quem_bloqueia` e listam os pulados (D-121), como `admin/lote.py`.
- Teste com `TransactionTestCase` e dois `Client` (ver `tests/test_ui_base.py`).

## 7. Permissões e mensagens

- Login obrigatório: `@login_required(login_url="admin:login")` (anônimo vai ao login do admin).
- Mesmas permissões do admin equivalente: ver sem permissão → 403; sem permissão de escrita → só leitura (campos `readonly`/`disabled`, sem botão de salvar) e POST → 403.
- Mensagens em PT-BR, causa + correção, sem "Opa": "Não salvo: <causa>. <o que fazer>." / "Nada foi gravado: corrija os erros marcados." / "Só leitura: <por quê>. Para editar, <como>."
- Ícones: SVG inline do Lucide (o mesmo do editor), `aria-hidden="true"`, sempre com texto ao lado.
