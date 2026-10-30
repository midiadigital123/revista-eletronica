# Telas B: o que já está fora do admin

Telas do dia a dia como páginas próprias no Django, com o visual do editor React (D-183) e HTMX local (D-186). Branch `feat/ui-b`. Convenções e componentes: [`design-system.md`](design-system.md). Requisitos de origem: [`inventario.md`](inventario.md) (ids T01–T28).

Todas: login obrigatório (anônimo vai ao login do admin), mesmas permissões do admin equivalente, só leitura sem permissão de escrita (POST → 403), bloqueio de edição onde o admin usa `BloqueioAdminMixin` (`nucleo/ui_bloqueio.py`) e mensagens no padrão causa + correção. O admin continua funcionando para tudo.

## 1. Telas integradas

Revisão = resultado da supervisão por tela. "Correções integradas" = a branch `-fix` da tela entrou no merge, sem uma segunda revisão.

| Tela | Inventário | URL | Rota | Ficha | Revisão |
|---|---|---|---|---|---|
| Cortes (protótipo) | T08 | `/cortes/<ano>/` | `cortes` | — (protótipo, `templates/ui/cortes.html`) | referência do time |
| Painel da temporada | T23 | `/painel/<ano>/` | `painel` | [`fichas/painel.md`](fichas/painel.md) | não aprovada (6 achados); correções integradas (`feat/ui-b-painel-fix`) |
| Validar revistas | T24, Validado de T21 | `/ui/validar/<ano>/?revista=…` | `ui_validar` | [`fichas/validar.md`](fichas/validar.md) | aprovada (6 achados menores) |
| Variáveis | T17 | `/ui/variaveis/<ano>/` | `ui_variaveis` | [`fichas/variaveis.md`](fichas/variaveis.md) | não aprovada (6 achados); correções integradas (`feat/ui-b-variaveis-fix`) |
| Projetos e projeto | T15, T16 | `/ui/projeto/ano/<ano>/`, `/ui/projeto/<pk>/` | `ui_projeto_lista`, `ui_projeto` | [`fichas/projeto.md`](fichas/projeto.md) | não aprovada (7 achados); correções integradas (`feat/ui-b-projeto-fix`) |
| Templates (lista, editor, impacto) | T12, T13, T14 | `/ui/templates/<ano>/`, `/ui/templates/editar/<pk>/` | `ui_templates`, `ui_templates_editar` | [`fichas/templates.md`](fichas/templates.md) | aprovada (6 achados menores) |
| Matrizes e descritores | T09, T10, T11 (+ arquivo do item D-180, exclusão D-181) | `/ui/matriz/<ano>/`, `/ui/matriz/m/<pk>/`, `/ui/matriz/mec/<pk>/` | `ui_matriz`, `ui_matriz_detalhe`, `ui_matriz_mec` | [`fichas/matriz.md`](fichas/matriz.md) | não aprovada (5 achados); correções integradas (`feat/ui-b-matriz-fix`) |
| Revistas e revista | T20, T21 | `/ui/revista/<ano>/`, `/ui/revista/<ano>/<pk>/` | `ui_revista`, `ui_revista_editar` | [`fichas/revista.md`](fichas/revista.md) | aprovada (6 achados menores) |
| Impresso (+ planilhas) | T26, T27 | `/ui/impresso/<ano>/` | `ui_impresso` | [`fichas/impresso.md`](fichas/impresso.md) | não aprovada (5 achados); correções integradas (`feat/ui-b-impresso-fix`) |
| Lotes (Escolher matriz, Escolher template F1/F2) | T18, T19 | `/ui/lotes/<ano>/matriz/`, `/ui/lotes/<ano>/template/` | `ui_lotes_matriz`, `ui_lotes_template` | [`fichas/lotes.md`](fichas/lotes.md) | aprovada (7 achados menores) |

O painel no estilo do admin saiu: `/painel/<ano>/` é a tela B (cobre filtros falta/parceiro/template, contagem por coluna, links de correção, preview e o lote, que vai a `ui_validar`). `/painel/<ano>/validar/` (`painel_validar`, estilo admin) continua para quem chega pelo admin.

## 2. O que ainda é só admin

| O quê | Inventário | Onde fica |
|---|---|---|
| Login, índice | T01, T02 | `/admin/login/`, `/admin/` (a navegação B tem "Admin" e "Sair") |
| Anos e Abrir ano | T03 | `/admin/nucleo/ano/`, `/admin/nucleo/ano/abrir/` |
| Parceiros, etapas, componentes | T04, T05, T06 | `/admin/nucleo/parceiro/`, `/etapa/`, `/componente/` |
| Padrões do ano (cor e nome) | T07 | `/admin/nucleo/corpadrao/` |
| Planilha de grupos de corte | T08b | `/admin/nucleo/corte/exportar/` (o botão da tela Cortes leva para lá) |
| Criar template | parte de T13 | `/admin/nucleo/template/add/` ("Novo template" da tela Templates leva para lá) |
| Gabarito de ids do SVG (CSV) | T21b | `/admin/nucleo/revista/<pk>/gabarito-ids/` (link na revista B) |
| Usuários | T25 | `/admin/auth/user/` |
| Histórico por registro | T28 | não existe (falta também no admin) |

Preview (T22) não é admin nem tela B: é a página da revista em `/preview/<id>/`.

## 3. Pendências

- Os links "falta" do painel e do validar (`urls/painel.py: link`) ainda levam ao admin (escolher matriz, cortes do admin, projeto, revista). Telas B equivalentes já existem (`ui_lotes_matriz`, `cortes`, `ui_projeto`, `ui_revista_editar`); trocar pede ajustar os testes do painel e do validar.
- As revisões não aprovadas (painel, variáveis, projeto, matriz, impresso) tiveram as correções integradas, mas não passaram por uma segunda revisão.
