# Ficha: Validar revistas (T24, validação em lote)

## Objetivo

Dar o "Validado" a várias revistas de uma vez, depois de conferir o que mudou em cada uma desde a última versão impressa. O "Validado" vale para a versão exata que a pessoa viu: se a revista mudar antes do envio, ela é recusada e listada; as outras são gravadas.

## Quem usa

| Perfil | O que faz |
|---|---|
| Pedagógica, Mídias, Administrador (permissão de validar revista) | confere e valida |
| Impresso e quem só vê revistas | confere em só leitura (vê pendências e mudanças, não valida) |
| Sem permissão de ver revistas | não entra (acesso negado) |
| Anônimo | vai ao login do admin e volta depois |

## Jornada

- **Antes:** Painel da temporada. A pessoa filtra "Falta: Validado", marca as revistas e clica "Validar selecionadas". O link traz as revistas na URL (`?revista=…`), então também funciona salvo ou colado.
- **Depois:** Painel (coluna Validado com ✓) e o Impresso (marcar "Revista Impressa Atualizada" das validadas).

## Dados mostrados (por revista)

- Nome da revista (projeto · componente).
- Estado: **Pronta para validar**, **Validada nesta versão** (com quem e quando), **N pendência(s)** e, à parte, **Em edição por <nome>** (será pulada).
- Pendências que impedem o "Validado", cada uma com o link para onde se resolve.
- Seções desatualizadas em relação ao template (só aviso; não impede).
- Mudanças desde a última versão impressa (diff "Última impressa" × "Agora", só os trechos alterados), recolhidas por padrão. Sem foto do impresso: "Primeira impressão: não há versão impressa para comparar." Sem diferença: "Sem mudanças desde a última impressa."

Topo: o ano, quantas revistas estão na tela e, se alguma pedida não aparece, quantas ficaram de fora (arquivadas ou de outro ano).

## Dados gravados

Por revista marcada: o "Validado" (versão validada, quem, quando). Nada mais. Revista já validada nesta versão não regrava quem e quando.

## Ações

| Ação | Onde | Resultado |
|---|---|---|
| Marcar/desmarcar revista | caixa no cabeçalho do cartão | contador da barra inferior muda |
| **Validar marcadas** (principal) | barra inferior fixa | grava cada marcada; volta à mesma tela com o resultado |
| **Validar esta** (secundária) | cabeçalho do cartão | grava só aquela revista; o cartão se atualiza sem recarregar a página |
| Ver mudanças | "Mudanças desde a última impressa" (abre/fecha) | mostra o diff |
| Resolver pendência | link em cada pendência | abre onde se corrige |
| Voltar ao painel | cabeçalho da página | Painel do ano |

Pré-marcadas: só as prontas (sem pendência e ainda não validadas). Com pendência: caixa e "Validar esta" desabilitadas (o servidor também recusa).

## Estados

| Estado | O que aparece |
|---|---|
| Vazio (nenhuma revista na URL ou nenhuma encontrada) | "Nenhuma revista para validar" + "Marque as revistas no Painel e clique em Validar selecionadas." + botão "Abrir painel" (filtrado por "Falta: Validado") |
| Só leitura (sem permissão de validar) | aviso "Só leitura: seu perfil confere as revistas, mas não valida. Para validar, peça a permissão de validar revista a um administrador." Sem caixas nem botões de validar |
| Em edição por outra pessoa | selo "Em edição por Ana: será pulada" no cartão (pode marcar; o servidor pula e lista) |
| Revista arquivada ou de outro ano na URL | some da lista; aviso "1 revista(s) pedida(s) não aparecem: arquivadas ou de outro ano." |
| Sucesso | "Validadas 3 revista(s)." |
| Recusa parcial | "Pulados: Projeto PE · LP (a revista mudou depois que a página abriu; confira de novo)." / "(projeto em edição por Ana)" / "(pendências: …)" / "revista 99 (não encontrada ou arquivada)" |
| Nada marcado | "Nada foi validado: nenhuma revista marcada. Marque ao menos uma e envie de novo." |
| Erro de rede/servidor no "Validar esta" | toast da base ("Não feito: …") e o cartão fica como estava |

## Regras de permissão

- Login obrigatório (anônimo → login do admin).
- Ver: permissão de ver revista. Sem ela: 403.
- Validar: permissão de validar revista. Sem ela: só leitura, e o envio dá 403.
- Bloqueio: a tela não trava projetos ao abrir (é um lote). Ao gravar, cada revista trava o seu projeto só durante a gravação; projeto aberto por outra sessão é pulado e listado.

## HTMX

- "Validar esta": `hx-post` para a mesma URL da tela com o par daquela revista, `hx-target` no próprio cartão, `outerHTML`. Resposta: o cartão novo + mensagens fora do alvo (`oob`).
- O resto é HTML comum: "Validar marcadas" é um POST de formulário que volta à mesma tela (PRG); o diff usa `<details>` nativo. Sem JS, tudo funciona: "Validar esta" vira um envio comum que grava só aquela revista.

## Wireframe

1440 px:

```
┌ Revista Eletrônica   Painel* Cortes Variáveis Matrizes Templates Revistas Impresso     Ana [Admin] [Sair] ┐
│                                                                                                         │
│ Validar revistas                                                               [Voltar ao painel]       │
│ 2026: 3 revista(s). Cada uma é validada na versão mostrada aqui; se mudar antes do envio, é recusada.   │
│                                                                                                         │
│ ┃ [x] Projeto GO · LP          (Pronta para validar)                              [Validar esta]        │
│ ┃ ▸ Mudanças desde a última impressa                                                                    │
│                                                                                                         │
│ ┃ [ ] Projeto GO · MT          (✓ Validada nesta versão) por Ana em 30/10/2026 14:02                    │
│ ┃ Primeira impressão: não há versão impressa para comparar.                                             │
│                                                                                                         │
│ ┃ [–] Projeto PE · LP          (2 pendência(s))                                   [Validar esta] desab. │
│ ┃ ██ Falta o SVG do F2.  Resolver                                                                       │
│ ┃ ██ Falta a imagem de capa.  Resolver                                                                  │
│ ┃ ⚠ Seções desatualizadas: F1 fechamento. Não impede o “Validado”.                                      │
│                                                                                                         │
│ ─────────────────────────────────────────────────────────────────────────────────────────────────────── │
│ 1 de 3 marcada(s). Projetos em edição por outra sessão são pulados.             [Validar marcadas]     │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

390 px: cartões em coluna única; o botão "Validar esta" desce para baixo do nome; a barra inferior empilha texto e botão (botão na largura toda); o diff rola na horizontal dentro do cartão.

Componentes do design system: cabeçalho de página, card, badge (`badge-secundario` pronta, verde validada, `badge-erro` pendências, `badge-alerta` em edição), faixa vermelha (pendência), aviso alerta (seções desatualizadas, só leitura), diff do difflib (`table.diff`), barra de salvar, estado vazio, mensagens. Único detalhe próprio: a borda esquerda do cartão na cor do estado (verde validada, vermelho pendência, neutra pronta), para ler o lote de relance.

## Critérios de aceite

1. Com permissão de validar, `GET /ui/validar/2026/?revista=…` mostra um cartão por revista ativa pedida, pré-marca só as prontas e não validadas, e mostra o diff ou o texto de primeira impressão.
2. Sem permissão de validar (com permissão de ver): mesma lista, aviso de só leitura, nenhuma caixa nem botão de validar; POST → 403. Sem permissão de ver: 403. Anônimo: login do admin.
3. "Validar marcadas" grava pela mesma regra do admin (versão vista, pendências, bloqueio por projeto) e volta à mesma tela com "Validadas N revista(s)."; a revista que mudou no meio é recusada e listada em "Pulados".
4. Projeto aberto por outra sessão: o cartão mostra "Em edição por …" e o envio pula essa revista, listando o motivo.
5. "Validar esta" via HTMX devolve só o cartão atualizado (estado "Validada nesta versão") com as mensagens fora do alvo.
6. Sem revistas: estado vazio com link para o Painel filtrado. Envio sem nada marcado: mensagem "Nada foi validado: …".
7. A tela do admin (`/painel/2026/validar/`) continua funcionando igual.

## Referências técnicas

- Regra: `app/nucleo/urls/painel.py` (`itens_validar`, `validar_pares`, extraídas da view do admin `validar_lote`), `servicos/validacao.py`, `admin/lote.py` (`aplicar`, `escrever_travado`, `quem_edita`).
- Tela B: `app/nucleo/urls/ui_validar.py`, `templates/ui/validar/pagina.html`, `templates/ui/parciais/validar_cartao.html`, `static/ui/telas/validar.css`, `tests/test_ui_validar.py`.
- Decisões: D-074, D-078, D-087, D-089, D-094, D-120, D-121, D-174, D-183, D-186.
