# Design system das telas B (referência obrigatória do time)

Telas do dia a dia como páginas próprias no Django, com o visual do editor React (D-183), HTMX servido localmente (D-186). Base: branch `feat/ui-b`. Protótipo de referência: grade de cortes (`app/nucleo/cortes.py`, `urls/cortes.py`, `templates/ui/cortes.html`, `tests/test_ui_cortes.py`).

Caminhos abaixo relativos a `app/nucleo/`, salvo `editor/` (só leitura).

## 1. Arquivos por tela

| O quê | Onde |
|---|---|
| Rotas | `urls/ui_<tela>.py` (já existe, vazio, já incluído em `urls/__init__.py` sob `/ui/<tela>/`). **Não edite `urls/__init__.py`.** |
| Regra reaproveitada | módulo comum fora do admin (ex.: `cortes.py`) ou `servicos/`; o admin passa a importar dele. Nunca copie a regra. |
| Templates | `templates/ui/<tela>/*.html` (página) e `templates/ui/parciais/<tela>_*.html` (fragmentos HTMX) |
| Testes | `tests/test_ui_<tela>.py` |
| Ficha da tela | `docs/telas/fichas/<tela>.md` |
| CSS só da tela | evite; se inevitável, `<style>` curto no `{% block cabeca %}`. Componente novo que serve a 2+ telas vai para `static/ui/ui.css` em commit separado e avisado ao supervisor. |

Telas e rotas (nomes `ui_<tela>`; ações `ui_<tela>_<acao>`):

| Tela | Módulo | URL | Rota principal |
|---|---|---|---|
| Painel (T23) | `ui_painel` | `/ui/painel/<ano>/` | `ui_painel` |
| Validar (T24, Validado de T21) | `ui_validar` | `/ui/validar/<ano>/` | `ui_validar` |
| Variáveis (T17) | `ui_variaveis` | `/ui/variaveis/<ano>/` | `ui_variaveis` |
| Projeto (T15/T16) | `ui_projeto` | `/ui/projeto/<pk>/` | `ui_projeto` |
| Templates (T12–T14) | `ui_templates` | `/ui/templates/<ano>/` | `ui_templates` |
| Matrizes (T09–T11) | `ui_matriz` | `/ui/matriz/<ano>/` | `ui_matriz` |
| Revistas (T20/T21) | `ui_revista` | `/ui/revista/<ano>/` | `ui_revista` |
| Impresso (T26/T27) | `ui_impresso` | `/ui/impresso/<ano>/` | `ui_impresso` |
| Lotes (T18/T19) | `ui_lotes` | `/ui/lotes/<ano>/matriz/`, `.../template/` | `ui_lotes_matriz`, `ui_lotes_template` |

- Cortes já é B e fica em `/cortes/<ano>/` (rota `cortes`).
- O Painel B entra em `/ui/painel/<ano>/`; trocar `/painel/<ano>/` (rota `painel`) pela B é o último passo, depois de tudo migrado.
- A rota principal recebe o ano (`<int:ano>/`) quando a tela é por ano. A navegação usa `{% rota_b "ui_<tela>" ano.ano %}`: tenta com o ano, depois sem args; vazio = cai no admin equivalente. Por isso a navegação funciona em qualquer ordem de merge: basta registrar a rota com o nome da tabela.

## 2. Casca e contexto

- `{% extends "ui/base.html" %}`, blocos `titulo`, `cabeca`, `conteudo`.
- Contexto: `secao` (`painel`, `cortes`, `variaveis`, `matrizes`, `templates`, `revistas`, `impresso`) marca a navegação; `ano` (instância `Ano`) leva o ano aos links; `anos` para o seletor.
- Cabeçalho de página: `<header class="pagina-cab"><div><h1>…</h1><p class="mudo">…</p></div><div class="acoes">…</div></header>` (`editor/src/projetos/ListaProjetos.tsx:31-34`).
- Já carregados pela base: `ui/ui.css`, `ui/htmx.min.js` (2.0.4, `defer`), `ui/ui.js` (`defer`), fonte Inter local. Nada de CDN.

## 3. Tokens (copiados do editor)

Todos em `static/ui/ui.css` `:root`. Origem:

| Token | Editor |
|---|---|
| `--background`, `--foreground`, `--card`, `--primary(-foreground)`, `--secondary(-foreground)`, `--muted(-foreground)`, `--destructive`, `--warning`, `--warning-bg`, `--border`, `--input`, `--ring` | `editor/src/index.css:134-156` |
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
| Seletor de ano | telas por ano | `{% include "ui/_componentes/anos.html" with rota="ui_<tela>" %}` |
| Abas | partes da mesma tela (Templates F1/F2/Matrizes/Variáveis) | `<nav class="abas"><a aria-current="page">`; a aba é a URL (`?aba=`), não estado em JS |
| Tabela | listas curtas | `.tabela-caixa > table.tabela` |
| Tabela densa | painel, listas longas: cabeçalho fixo, 1ª coluna `.fixa` (é `position: relative`, para o `.sr-only` não vazar e criar rolagem na página) | `.tabela-densa > table.tabela`; `.num` alinha números; `.quebra` deixa quebrar |
| Grade editável | planilha de células (cortes, variáveis) | `form.grade > .grade-caixa > table.tabela` + `.barra-salvar` (ver `cortes.html`) |
| Lista + detalhe | navegar itens e editar um (matriz → descritores, revista → seções) | `.lado-a-lado > nav.lista + section.detalhe`; o item ativo com `aria-current`; o detalhe vem por HTMX |
| Duas colunas | editor + preview ao vivo | `.duas-colunas` |
| Modal | confirmação curta, formulário pequeno sem sair da tela | `<dialog class="dialogo" id="x"><header><h2>…</h2><p class="mudo">…</p></header>…<footer><button data-fechar class="btn btn-outline">Cancelar</button>…</footer></dialog>` + `<button data-abrir="x">`; `.dialogo-largo` para diff |
| Diff antes/depois | o que mudou (impresso, seção desatualizada, validar) | `difflib.HtmlDiff(...).make_table` → `table.diff` (já estilizado); ou `.diff-lado` com `<div><h3>Antes</h3>…</div><div><h3>Depois</h3>…</div>`, trechos em `.diff-velho`/`.diff-novo` |
| Faixa vermelha | lacuna que impede a revista de sair completa (D-116) | `{% include "ui/_componentes/faixa.html" with texto=… url=… rotulo=… %}` |
| Variável vazia | `{{nome}}` sem valor no texto | `<span class="variavel-vazia">{{nome}}</span>` (o `texto.renderizar` já gera); variável preenchida: `.variavel` |
| Status ✓/falta | célula de pendência | `{% include "ui/_componentes/status.html" with ok=… url=… titulo=… %}` |
| Barra de salvar | form longo: contador de alterações à esquerda, ações à direita, fixa no rodapé | `.barra-salvar > span.mudo + .btn` |
| Confirmação forte | ação irreversível ou de grande impacto (reimportar matriz, descartar cópias) | `{% include "ui/_componentes/confirmar.html" with nome=… codigo=… texto=… erro=… %}` + botão `data-confirmado`; o form no servidor confere o texto |
| Só leitura | perfil sem permissão de escrita | `{% include "ui/_componentes/so_leitura.html" with texto="Só leitura: … Para editar, peça …" %}` |
| Mensagens | resultado de ação (Django `messages`) | já na base (`#mensagens`); fragmento HTMX que grava inclui `{% include "ui/_componentes/mensagens.html" with oob=True %}` |
| Toast | erro de rede/servidor do HTMX (automático) ou aviso efêmero | `uiToast("texto", "erro")` (`static/ui/ui.js`) |
| Estado vazio | lista sem itens | `{% include "ui/_componentes/vazio.html" with titulo=… texto=… url=… rotulo=… %}` |
| Badge | contagem, rótulo curto | `.badge`, `.badge-secundario`, `.badge-contorno`, `.badge-alerta`, `.badge-erro` |
| Carregando | pedido HTMX demorado | `hx-indicator` + `.htmx-indicator`; `svg.girando`; o alvo com `.alvo-htmx` (ou `.detalhe`) e `hx-indicator` nele esmaece |
| Link da linha | nome na 1ª coluna que abre o item | `a.link-linha` (sublinha no hover) |

## 5. HTMX

- Página inteira = GET normal. HTMX só para trocar um pedaço: detalhe da lista, preview, linha salva, filtro.
- Fragmentos em `templates/ui/parciais/<tela>_<pedaco>.html`; a mesma view devolve o fragmento ao HTMX e a página inteira ao resto (o link funciona sem JS e ao recarregar): `return pagina_ou_parcial(request, "ui/<tela>/x.html", "ui/parciais/<tela>_y.html", ctx)` (`nucleo.ui_bloqueio`). Ela põe `Vary: HX-Request` (sem isso o Voltar do navegador mostra só o fragmento de uma URL empurrada) e `e_htmx` trata a restauração de histórico do htmx (`HX-History-Restore-Request`) como página inteira.
- Região viva (`aria-live`) fica fora do `hx-target`: uma região recém-inserida não é anunciada. Copie o texto para ela no `htmx:afterSwap` (ver `ui/painel/painel.html`).
- Atributos: `hx-get`/`hx-post` + `hx-target="#id"` + `hx-swap="innerHTML"` (padrão) ou `outerHTML` para trocar o próprio elemento; `hx-push-url="true"` quando o fragmento muda o "onde estou" (item da lista ativo); `hx-trigger="input changed delay:400ms"` para preview ao vivo (o mesmo debounce do admin).
- CSRF: a base põe `hx-headers='{"X-CSRFToken": …}'` no `<body>`; todo `hx-post` já vai com o token. Forms comuns seguem com `{% csrf_token %}`.
- Erro 4xx/5xx: o HTMX não troca o alvo; `ui.js` mostra um toast. Erro de validação esperado: responda 200 com o fragmento e os erros nele.
- Depois de gravar: página inteira → `redirect` (PRG). Fragmento → 200 com o fragmento novo + mensagens `oob`; para ir a outra página use o header `HX-Redirect`.

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
