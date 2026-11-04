# Ficha: Painel da temporada (T23)

Endereço: `/painel/<ano>/` (rota `painel`). Visual do editor React; mesma regra do painel do admin. Redesenhado no U8: agrupado por parceiro, sem o card "Próxima tarefa".

## Objetivo

Responder em uma tela "o que falta para cada revista do ano sair completa, e onde eu resolvo". As revistas ativas vêm agrupadas por projeto (um por parceiro); cada etapa da montagem é uma coluna com ✓ ou "falta". A "falta" leva direto ao lugar da correção.

## Quem usa

| Perfil | O que faz aqui |
|---|---|
| Pedagógica, Mídias, Admin | acompanham a montagem, filtram o que falta, selecionam revistas para validar em lote |
| Impresso | vê quais revistas mudaram desde a última impressão e abre a tela do impresso de cada uma |
| Qualquer pessoa com acesso às revistas | consulta, sem validar |

## Na jornada

- **Antes:** projeto (matriz, cortes, variáveis), revista (templates, SVG, capa, textos) e preview.
- **Depois:** validar em lote (T24), tela do impresso (T26), página do projeto e da revista.
- É a primeira tela depois do login (o endereço `/` leva ao painel do maior ano).

## Dados mostrados

- Título "Painel da temporada <ano>". O ano troca pelo seletor do cabeçalho, mantendo os filtros.
- Filtros: Parceiro, Componente, Template, Matriz e Situação (Completas, Incompletas, Validadas), cada um com "Todos/Todas". "Limpar filtros" aparece com qualquer filtro ativo.
- Resumo: "<N> de <M> revistas completas" (e, com uma coluna ativa, "· <K> sem <coluna>"). Abaixo, um contador por coluna: com pendência, um botão com o número e o nome da coluna, que filtra por ela; sem pendência, o ✓ com o nome. O contador ativo fica destacado (`aria-pressed`) e clicar de novo desliga o filtro. Com uma coluna ativa, aparece "Limpar filtro".
- Tabela, cabeçalho e coluna Revista fixos:
  - Uma linha de grupo por projeto: nome do projeto (link para o projeto), parceiro em cinza e "N de M revistas completas".
  - Abaixo, uma sublinha por revista, na ordem dos componentes: selo LP/MT com o nome do componente (link para a revista) e "Preview" (nova aba; abre mesmo com pendências).
  - Colunas Matriz, Template F1, Template F2, Variáveis, SVG, Capa, Validado, Impresso. A coluna ativa fica destacada.
  - Célula: ✓ ou "falta" com a explicação no `title` e o link de correção. Impresso com ✓ também é link (mostra a última versão impressa).
- "Validado" e "Impresso" são calculados na hora: o "Validado" vale para a versão atual; o "Impresso" compara com a última foto impressa (só textos e escalas; SVG e capa não contam).
- Revistas arquivadas ficam de fora.

## Dados gravados

Nenhum. O painel só lê. "Validar selecionadas" leva à tela de validação em lote (T24) com as revistas marcadas; quem grava é ela.

## Ações

| Ação | Quem | Resultado |
|---|---|---|
| Trocar ano (seletor do cabeçalho) | todos | o mesmo painel no outro ano, com a mesma query |
| Mudar um filtro | todos | o corpo da tela troca sem recarregar; a URL muda (dá para recarregar e compartilhar) |
| Clicar num contador | todos | filtra pela coluna (`?falta=`), mantendo os outros filtros; clicar no ativo desliga |
| Limpar filtro / Limpar filtros | todos | tira só a coluna / tira tudo |
| Clicar em "falta" | todos | abre onde se corrige, sempre numa tela B (aba Matriz do projeto, grade de Cortes, matriz, projeto, revista, impresso) |
| Preview | todos | nova aba com o preview |
| Marcar revistas (uma, as do projeto ou todas) + "Validar selecionadas" | quem valida | abre a validação em lote com as marcadas |

## Estados

- **Vazio (ano sem revistas ativas):** "Nenhuma revista ativa neste ano" · "As revistas nascem quando os cortes do parceiro são lançados. Lance os cortes do ano para ver as revistas aqui." · botão "Abrir cortes".
- **Vazio (filtro sem resultado):** "Nenhuma revista com esse filtro" · com uma coluna ativa: "Nenhuma revista deste recorte está sem <coluna>: a coluna está em dia. Limpe o filtro para ver todas."; sem ela: "Este recorte ainda não tem revistas ativas. Lance os cortes do parceiro para criar as revistas, ou limpe os filtros." · botão "Limpar filtro".
- **Erro:** ano inexistente: 404. Filtro inválido, de outro ano ou mal formado: ignorado (a tela mostra tudo). Falha de rede ou do servidor ao filtrar: aviso flutuante da base e a tabela anterior continua.
- **Só leitura (sem permissão de validar):** aviso "Só leitura: seu perfil vê o painel, mas não valida revistas. Para validar, peça a permissão de validação a um administrador."; sem caixas de seleção e sem "Validar selecionadas".
- **Bloqueio:** não se aplica (a tela não grava).
- **Seleção:** a barra fixa mostra "Nenhuma selecionada" ou "N selecionada(s)"; "Validar selecionadas" só fica ativo com ao menos uma marcada. A caixa do projeto marca as revistas dele e fica indeterminada quando só parte está marcada.

## Permissões

- Sem login: vai ao login do admin e volta ao painel.
- Ver: `view_revista`; sem ela, 403.
- Seleção e "Validar selecionadas": `validar_revista`.
- POST: 405 (a tela não aceita gravação).

## Interações com HTMX

- O formulário de filtros faz `hx-get` ao mudar qualquer select (`hx-sync="this:replace"`); alvo `#painel-corpo` (filtros + resumo + tabela), `hx-push-url`. Os contadores e os "Limpar" fazem o mesmo; os links funcionam sem JS.
- A mesma view devolve só o corpo quando o pedido é HTMX; senão a página inteira (`pagina_ou_parcial`, com `Vary: HX-Request`). A restauração de histórico do htmx recebe a página inteira.
- O resumo é anunciado ao leitor de tela por uma região viva fixa fora de `#painel-corpo`, atualizada no `htmx:afterSwap`.
- Sem JS: um botão "Filtrar" aparece (`<noscript>`).
- Seleção: JS pequeno e delegado no documento (sobrevive à troca do corpo): todas, por projeto ou uma a uma, contador e botão ativo/inativo. A sombra da borda dos fixos liga só quando a tabela rolou.

## Wireframe (1440 px)

```
┌ Revista Eletrônica  [2026 ▾]  [Painel] Projetos Matrizes Templates Impresso             Ana  Admin  Sair ┐
Painel da temporada 2026
As revistas ativas, por parceiro: o que falta para cada uma sair completa, e onde resolver.
Parceiro [Todos ▾]  Componente [Todos ▾]  Template [Todos ▾]  Matriz [Todas ▾]  Situação [Todas ▾]  Limpar filtros

3 de 12 revistas completas
(✓ Matriz) (✓ Template F1) (2 Template F2) (✓ Variáveis) (6 SVG) (6 Capa) [10 Validado] (12 Impresso)   Limpar filtro

┌ tabela-densa (cabeçalho fixo, coluna Revista fixa) ───────────────────────────────────────────────────┐
│ [■] Revista                  │ Matriz │ Templ.F1 │ Templ.F2 │ Variáveis │ SVG │ Capa │ Validado │ Impresso │
│ [■] Projeto GO  GO  1 de 2 revistas completas                                                        │
│   [ ] LP Língua Portuguesa ↗Preview │ ✓ │ ✓ │ ✓ │ ✓ │ ✓ │ ✓ │ ✓ │ falta │
│   [x] MT Matemática ↗Preview         │ ✓ │ ✓ │ ✓ │ ✓ │falta│falta│ falta │ falta │
└───────────────────────────────────────────────────────────────────────────────────────────────────────┘
──────────────────────────────────────────────────────────────────── barra fixa no rodapé ───
1 selecionada(s)                                                           [Validar selecionadas]
```

Em 390 px: filtros empilhados em largura total; contadores quebram linha; a tabela rola na horizontal com a coluna Revista fixa.

## Critérios de aceite

1. Pedagógica abre `/painel/2026/`: 200, um grupo por projeto com "N de M revistas completas" e as revistas na ordem dos componentes, caixas de seleção, "Validar selecionadas" apontando para a validação em lote, preview em nova aba, coluna Impresso com link para a tela do impresso.
2. Não há card "Próxima tarefa".
3. Clicar no contador "Validado" filtra `?falta=validado` mantendo os outros filtros; clicar de novo volta a todas.
4. Célula "falta" tem a dica no `title` e o link de correção numa tela B.
5. Filtros dão o mesmo resultado do painel do admin; inválidos são ignorados.
6. Pedido HTMX devolve só o corpo (sem `<html>`); a resposta tem `Vary: HX-Request`; pedido de restauração de histórico recebe a página inteira.
7. Impresso: aviso de só leitura, sem seleção nem botão; POST 405.
8. Sem `view_revista`: 403. Anônimo: login do admin com `next`. Ano inexistente: 404.
9. Estados vazios com as mensagens exatas acima.
10. Em 1440 px e 390 px a tela não tem rolagem horizontal da página (só a da tabela).

## Referências técnicas

- Regra: `app/nucleo/urls/painel.py` (`filtrar`, `linha`, `COLUNAS`, `SITUACOES`, `link`, `completa`). View B: `app/nucleo/urls/ui_painel.py` (`painel`, `agrupar`).
- Templates: `templates/ui/painel/painel.html`, `templates/ui/parciais/painel_corpo.html`; CSS `static/ui/telas/painel.css`.
- Testes: `app/nucleo/tests/test_ui_painel.py`; `app/e2e/tests/painel.spec.ts`.
- Decisões: D-078, D-094, D-118, D-120, D-174, D-183, D-186 e as do plano de UX (D-195 em diante); rascunho-ui itens 1, 3 e 4.
