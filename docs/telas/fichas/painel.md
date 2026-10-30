# Ficha: Painel da temporada (T23)

Endereço: `/ui/painel/<ano>/`. Visual do editor React; mesma regra do painel do admin.

## Objetivo

Responder em uma tela "o que falta para cada revista do ano sair completa, e onde eu resolvo". Cada revista ativa é uma linha; cada etapa da montagem é uma coluna com ✓ ou "falta". A "falta" leva direto ao lugar da correção.

## Quem usa

| Perfil | O que faz aqui |
|---|---|
| Pedagógica, Mídias, Admin | acompanham a montagem, filtram o que falta, selecionam revistas para validar em lote |
| Impresso | vê quais revistas mudaram desde a última impressão e abre a tela do impresso de cada uma |
| Qualquer pessoa com acesso às revistas | consulta, sem validar |

## Na jornada

- **Antes:** revista (SVG, capa, template por fascículo, textos) e preview.
- **Depois:** validar em lote (T24), tela do impresso (T26), lista de revistas para baixar o zip.
- É a primeira tela depois do login (o endereço `/` leva ao painel do maior ano).

## Dados mostrados

- Seletor de ano (todos os anos abertos).
- Bloco "Próxima tarefa", conforme a permissão (nunca pelo nome do grupo):
  - quem marca impressão: "N revista(s) para atualizar no impresso", com link para o filtro Impresso;
  - quem valida: "N revista(s) sem “Validado” nesta versão", com link para o filtro Validado;
  - os demais: "N de M revista(s) completas".
  - Atalhos de montagem, cada um só com a permissão: Cortes, Variáveis, Escolher matriz, Escolher template F1/F2.
- Filtros: Falta (Tudo ou uma das 8 colunas), Parceiro (Todos ou um parceiro do ano) e Template (só aparece quando se chega pelo "usado por" da lista de templates, com "Limpar").
- Resumo: "X de Y revista(s) · Z completa(s)".
- Tabela, uma linha por revista ativa (arquivadas ficam de fora):
  - Revista: parceiro (link para a revista), componente, "Preview" (nova aba; abre mesmo com pendências).
  - Colunas Matriz, Template F1, Template F2, Variáveis, SVG, Capa, Validado, Impresso.
  - Cabeçalho de cada coluna: quantas revistas do recorte têm "falta" nela; o número filtra por ela.
  - Célula: ✓ ou "falta" com a explicação no `title` e o link de correção. Impresso com ✓ também é link (mostra a última versão impressa).
- "Validado" e "Impresso" são calculados na hora: o "Validado" vale para a versão atual; o "Impresso" compara com a última foto impressa (só textos e escalas; SVG e capa não contam).

## Dados gravados

Nenhum. O painel só lê. "Validar selecionadas" leva à tela de validação em lote (T24) com as revistas marcadas; quem grava é ela.

## Ações

| Ação | Quem | Resultado |
|---|---|---|
| Trocar ano | todos | página do ano escolhido |
| Mudar Falta ou Parceiro | todos | o corpo da tela troca sem recarregar; a URL muda (dá para recarregar e compartilhar) |
| Clicar no número de uma coluna | todos | mesmo que escolher a coluna em Falta, mantendo parceiro e template |
| Limpar template | todos | remove só o filtro de template |
| Clicar em "falta" | todos | abre onde se corrige (escolher matriz, cortes, projeto, revista, impresso) |
| Preview | todos | nova aba com o preview |
| Marcar revistas + "Validar selecionadas" | quem valida | abre a validação em lote com as marcadas |

## Estados

- **Vazio (ano sem revistas ativas):** "Nenhuma revista ativa neste ano" · "As revistas nascem quando os cortes do parceiro são lançados. Lance os cortes do ano para ver as revistas aqui." · botão "Abrir cortes".
- **Vazio (filtro sem resultado):** "Nenhuma revista com esse filtro" · "Nenhuma revista ativa tem essa pendência neste recorte. Limpe o filtro de falta para ver todas." · botão "Limpar filtro de falta".
- **Erro:** ano inexistente: página 404. Falta, parceiro ou template inválidos: ignorados (a tela mostra tudo). Falha de rede ou do servidor ao filtrar: aviso flutuante da base ("Não feito: …. Recarregue a página e tente de novo.") e a tabela anterior continua.
- **Só leitura (sem permissão de validar):** aviso "Só leitura: seu perfil vê o painel, mas não valida revistas. Para validar, peça a permissão de validação a um administrador."; sem caixas de seleção e sem "Validar selecionadas".
- **Arquivado:** revista arquivada não aparece. **Bloqueio:** não se aplica (a tela não grava).
- **Sucesso:** "Validar selecionadas" só fica ativo com ao menos uma marcada; a barra mostra "N revista(s) selecionada(s)."; "Próxima tarefa" sem pendência mostra "Tudo validado: nenhuma revista mudou desde o último “Validado”." ou "Impresso em dia: nenhuma revista mudou desde a última impressão."

## Permissões

- Sem login: vai ao login do admin e volta ao painel.
- Ver: permissão de ver revistas; sem ela, 403.
- Seleção e "Validar selecionadas": permissão de validar revista.
- POST: 405 (a tela não aceita gravação).

## Interações com HTMX

- O formulário de filtros faz `hx-get` ao mudar qualquer select; alvo `#painel-corpo` (tarefa + filtros + tabela), `hx-push-url`. Os números do cabeçalho fazem o mesmo, com `href` normal para funcionar sem JS.
- A mesma view devolve só o corpo quando o pedido é HTMX; senão a página inteira.
- Sem JS: um botão "Filtrar" aparece (`<noscript>`), os links funcionam.
- Seleção: JS pequeno e delegado (sobrevive à troca do corpo): marcar todas, contador, botão ativo/inativo.

## Wireframe

```
┌ Revista Eletrônica   [Painel] Cortes Variáveis Matrizes Templates Revistas Impresso     Ana  Admin [Sair] ┐
Painel da temporada 2026
Uma linha por revista ativa: o que falta para cada uma sair completa, e onde resolver.
( 2026 | 2025 )                                                      ← segmentos

┌ card ─────────────────────────────────────────────────────────────────────────────────────────────┐
│ Próxima tarefa                                          Cortes  Variáveis  Escolher matriz  Escolher template F1/F2 │
│ 10 revista(s) sem “Validado” nesta versão  (link)                                                  │
└────────────────────────────────────────────────────────────────────────────────────────────────────┘
Falta [Tudo ▾]  Parceiro [Todos ▾]  (Template [LP · Padrão  Limpar])         12 de 12 revista(s) · 0 completa(s)

┌ tabela-densa (cabeçalho fixo, 1ª coluna fixa) ─────────────────────────────────────────────────────┐
│ [■] Revista              │ Matriz │ Templ.F1 │ Templ.F2 │ Variáveis │ SVG │ Capa │ Validado │ Impresso │
│                          │   0    │    0     │    0     │     0     │ (6) │ (6)  │  (10)    │  (12)    │
│ [ ] Alagoas  LP  ↗Preview │   ✓    │    ✓     │    ✓     │     ✓     │  ✓  │  ✓   │    ✓     │  falta   │
│ [x] Alagoas  MT  ↗Preview │   ✓    │    ✓     │    ✓     │     ✓     │falta│falta │  falta   │  falta   │
└────────────────────────────────────────────────────────────────────────────────────────────────────┘
──────────────────────────────────────────────────────────────────── barra fixa no rodapé ───
1 revista(s) selecionada(s).                                               [Validar selecionadas]
```

Em 390 px: filtros empilhados em largura total; atalhos de montagem quebram linha; a tabela rola na horizontal com a coluna Revista fixa e "Preview" só como ícone.

## Critérios de aceite

1. Pedagógica abre `/ui/painel/2026/`: 200, visual da base B, uma linha por revista ativa, caixas de seleção, "Validar selecionadas" apontando para a validação em lote, link de preview em nova aba, link da coluna Impresso para a tela do impresso.
2. "Próxima tarefa" da Pedagógica mostra a contagem de revistas sem "Validado" e linka `?falta=validado`; a do Impresso linka `?falta=impresso`.
3. Célula "falta" tem a dica no `title` e o link de correção; o cabeçalho mostra quantas faltam por coluna e linka o filtro mantendo parceiro e template.
4. Filtros dão o mesmo resultado do painel do admin (falta, parceiro, template; inválidos ignorados).
5. Pedido HTMX devolve só o corpo (sem `<html>`).
6. Impresso: aviso de só leitura, sem seleção nem botão; POST 405.
7. Sem `view_revista`: 403. Anônimo: login do admin com `next`. Ano inexistente: 404.
8. Estados vazios com as mensagens exatas acima.
9. Em 1440 px e 390 px a tela não tem rolagem horizontal da página (só a da tabela).

## Referências técnicas

- Regra: `app/nucleo/urls/painel.py` (`filtrar`, extraída da view do admin; `linha`, `COLUNAS`, `link`). View B: `app/nucleo/urls/ui_painel.py`.
- Templates: `templates/ui/painel/painel.html`, `templates/ui/parciais/painel_corpo.html`, `templates/ui/_componentes/painel_tarefa.html`; CSS `static/ui/telas/painel.css`.
- Testes: `app/nucleo/tests/test_ui_painel.py`.
- Decisões: D-078, D-094, D-118, D-120, D-174, D-183, D-186; rascunho-ui itens 1, 3 e 4.
