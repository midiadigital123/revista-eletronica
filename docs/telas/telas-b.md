# Telas B: o que já está fora do admin

Telas do dia a dia como páginas próprias no Django, com o visual do editor React (D-183) e HTMX local (D-186). Branch `feat/ui-b`. Convenções e componentes: [`design-system.md`](design-system.md). Requisitos de origem: [`inventario.md`](inventario.md) (ids T01–T28).

Todas: login obrigatório (anônimo vai ao login das telas B (`/conta/entrar/`)), mesmas permissões do admin equivalente, só leitura sem permissão de escrita (POST → 403), bloqueio de edição onde o admin usa `BloqueioAdminMixin` (`nucleo/ui_bloqueio.py`) e mensagens no padrão causa + correção. O admin continua funcionando para tudo.

## 1. Telas integradas

Revisão = resultado da supervisão por tela. "Correções integradas" = a branch `-fix` da tela entrou no merge, sem uma segunda revisão. Desde a reforma de UX (`plans/revista-express-telas-b-ux.md`, U0–U9b), o menu tem 5 itens (Painel, Projetos, Matrizes, Templates, Impresso) e o ano fica no seletor do cabeçalho.

| Tela | Inventário | URL | Rota | Ficha | Revisão |
|---|---|---|---|---|---|
| Painel da temporada | T23 | `/painel/<ano>/` | `painel` | [`fichas/painel.md`](fichas/painel.md) | não aprovada (6 achados); correções integradas (`feat/ui-b-painel-fix`); refeito no U8 (agrupado por parceiro) |
| Validar revistas | T24, Validado de T21 | `/ui/validar/<ano>/?revista=…` | `ui_validar` | [`fichas/validar.md`](fichas/validar.md) | aprovada (6 achados menores) |
| Projetos, aba Lista (revistas e ações em massa) | T15, T18, T19, T20 | `/ui/projeto/ano/<ano>/` | `ui_projeto_lista` | [`fichas/projeto.md`](fichas/projeto.md), [`fichas/lotes.md`](fichas/lotes.md) | não aprovada (7 achados); correções integradas (`feat/ui-b-projeto-fix`); refeita no U7a |
| Projetos, aba Cortes (+ criar e renomear parceiro) | T08, T04 | `/ui/projeto/ano/<ano>/cortes/` | `cortes` | [`fichas/cortes.md`](fichas/cortes.md) | referência do time (protótipo); autosave no U3 |
| Projetos, aba Variáveis | T17 | `/ui/projeto/ano/<ano>/variaveis/` | `ui_variaveis` | [`fichas/variaveis.md`](fichas/variaveis.md) | não aprovada (6 achados); correções integradas (`feat/ui-b-variaveis-fix`) |
| Projeto (abas Dados, Matriz, Cortes, Passos e cores, Revistas) | T16 | `/ui/projeto/<pk>/?aba=…` | `ui_projeto` | [`fichas/projeto.md`](fichas/projeto.md) | refeito no U7b |
| Revista | T21 | `/ui/revista/<ano>/<pk>/` | `ui_revista_editar` | [`fichas/revista.md`](fichas/revista.md) | aprovada (6 achados menores); refeita no U8b |
| Templates (lista, editor, impacto) | T12, T13, T14 | `/ui/templates/<ano>/`, `/ui/templates/editar/<pk>/` | `ui_templates`, `ui_templates_editar` | [`fichas/templates.md`](fichas/templates.md) | aprovada (6 achados menores); editor por seção no U9b |
| Matrizes e descritores | T09, T10, T11 (+ arquivo do item D-180, exclusão D-181) | `/ui/matriz/<ano>/`, `/ui/matriz/m/<pk>/`, `/ui/matriz/mec/<pk>/` | `ui_matriz`, `ui_matriz_detalhe`, `ui_matriz_mec` | [`fichas/matriz.md`](fichas/matriz.md) | não aprovada (5 achados); correções integradas (`feat/ui-b-matriz-fix`) |
| Impresso (+ planilhas) | T26, T27 | `/ui/impresso/<ano>/` | `ui_impresso` | [`fichas/impresso.md`](fichas/impresso.md) | não aprovada (5 achados); correções integradas (`feat/ui-b-impresso-fix`) |
| Anos e Abrir ano | T03 | `/ui/anos/` ("Abrir novo ano" no seletor de ano) | `ui_anos` | [`fichas/anos.md`](fichas/anos.md) | sem revisão de tela (S3 de D-190) |
| Configurar o ano: etapas, componentes, Padrões do ano | T05, T06, T07 | `/ui/anos/<ano>/` ("Configurar <ano>" no seletor; padrões em `#padroes`) | `ui_ano` | [`fichas/anos.md`](fichas/anos.md) | sem revisão de tela (S4 e S5 de D-190) |
| Excluir e desativar (D-205 a D-208) | — | `/ui/excluir/<modelo>/<pk>/`, `/ui/excluir/parceiro/<pk>/ativo/` | `ui_excluir`, `ui_parceiro_ativo` | [`fichas/anos.md`](fichas/anos.md), [`fichas/cortes.md`](fichas/cortes.md), [`fichas/matriz.md`](fichas/matriz.md), [`fichas/templates.md`](fichas/templates.md) | sem revisão de tela (E0–E5) |

Endereços antigos que redirecionam (302) para a aba equivalente de Projetos: `/cortes/<ano>/`, `/ui/variaveis/<ano>/`, `/ui/revista/<ano>/` (a lista de revistas virou a aba Lista) e `/ui/lotes/<ano>/matriz/` e `.../template/` (os lotes viraram "Atribuir matriz…" e "Atribuir template…" na barra da Lista). O POST antigo de Variáveis e Lotes continua gravando.

O painel no estilo do admin saiu: `/painel/<ano>/` é a tela B (filtros parceiro, componente, template, matriz e situação, contadores por coluna, links de correção, preview e o lote, que vai a `ui_validar`). `/painel/<ano>/validar/` (`painel_validar`, estilo admin) continua para quem chega pelo admin.

## 2. O que ainda é só admin

Anos, Abrir ano, etapas, componentes, Padrões do ano e parceiros (criar e renomear) saíram desta lista: ver a tabela 1. Também saíram, com S6–S9 (D-210): criar matriz (`/ui/matriz/<ano>/nova/`, `ui_matriz_nova`), criar template (`/ui/templates/<ano>/novo/`, `ui_templates_novo`), planilha de grupos de corte (`cortes_exportar`), gabarito de ids do SVG (`ui_revista_gabarito`), baixar o arquivo do item (`ui_matriz_item_baixar`), planilhas F1/F2 na ficha da revista (`impresso_planilhas`) e usuários (`/ui/usuarios/`, `ui_usuarios`, link "Usuários" no cabeçalho com `auth.change_user`). Os links que saem das telas B para o admin são os da coluna "Onde fica" (`grep "admin:" app/nucleo/templates/ui`).

| O quê | Inventário | Onde fica |
|---|---|---|
| Índice | T02 | `/admin/` (a navegação B tem "Admin", só para superusuário). O login e o "Sair" são das telas B (`/conta/entrar/`, `/conta/sair/`, D-212); `/admin/login/` redireciona para o login B com o `next` |
| Histórico por registro | T28 | não existe (falta também no admin) |

Preview (T22) não é admin nem tela B: é a página da revista em `/preview/<id>/`.

## 3. Pendências

- As revisões não aprovadas (painel, variáveis, projeto, matriz, impresso) tiveram as correções integradas, mas não passaram por uma segunda revisão.
- Os links "falta" do painel, do validar e da coluna Situação da revista já levam só a telas B (`urls/painel.py: link`).
