# Ficha da tela: Matrizes e descritores (T09, T10, T11)

## Objetivo

Cuidar da matriz de referência do ano: ver quais matrizes existem, criar uma a partir de outra (Duplicar), trocar o conteúdo pelo PDF ou planilha do SAEGO (Reimportar), ver o que mudou numa cópia (Diferenças), ajustar o intervalo mínimo de cada etapa × componente e editar descritores, tarefas e o arquivo do item. Tudo o que muda aqui muda as revistas ativas que usam a matriz. Campos simples salvam sozinhos; quando a gravação tira o "Validado" de revistas, o modal de impacto lista as revistas antes de gravar.

## Quem usa

| Perfil | O que faz |
|---|---|
| Pedagógica, Mídias Digitais, Admin | tudo: duplicar, reimportar, renomear, intervalo mínimo, descritores, tarefas, arquivo do item, excluir tarefa e descritor |
| Impresso | só vê (aviso de só leitura; nenhum botão de gravar) |
| Sem permissão de ver matriz | recebe "acesso negado" (403) |
| Não logado | vai para o login do admin e volta depois |

## Jornada

- **Antes:** abrir o ano e conferir os cadastros (etapas, componentes, padrões). A matriz do ano nasce pela importação (comando da carga) ou pela duplicação de uma matriz de outro ano.
- **Depois:** escolher a matriz de cada parceiro ("Atribuir matriz…" na Lista de Projetos, ou a aba Matriz do projeto) e conferir as revistas no Painel.

## Páginas

1. **Matrizes do ano** — lista das matrizes do ano escolhido.
2. **Matriz** — etapas × componente da matriz; nome renomeável no título (lápis); ações Duplicar, Reimportar e Diferenças da origem.
3. **Reimportar** — envio do arquivo com confirmação forte.
4. **Diferenças** — o que a cópia tem de diferente da origem (só consulta).
5. **Etapa × componente** — cabeçalho com o título ("5EF Língua Portuguesa"), a linha de contexto (matriz, escala, revistas afetadas), o status do salvamento e o botão "Configurações" (popover com o intervalo mínimo); lista de descritores com "+ Novo descritor" e busca à esquerda; painel do descritor à direita (campos, tarefas, arquivo do item e, no fim, a zona de perigo "Excluir descritor").
6. **Excluir tarefa / Excluir descritor** — confirmação forte com as revistas afetadas.

## Dados mostrados

- Matrizes do ano: nome, de onde foi duplicada, quantas etapas × componente e quantos descritores.
- Matriz: ano, origem; por etapa × componente: intervalo mínimo, descritores, revistas ativas afetadas.
- Etapa × componente: intervalo mínimo; descritores (código, descrição); contagem "N de M descritores" na busca.
- Descritor: código, descrição, pré-requisitos (um por linha), práticas, conhecimento, habilidades relacionadas e correspondente; tarefas (início, fim, texto) com a faixa da tarefa desenhada na escala da etapa e o tipo do arquivo do item quando houver. A ordem não é campo: descritores e tarefas se reordenam pela alça.
- Impacto: "Afeta N revista(s) ativa(s)"; no arquivo do item e na exclusão, também quantas perdem o "Validado".
- Diferenças: onde, o quê, na origem, nesta matriz.

## Dados gravados (pela mesma regra do admin)

- Matriz: nome (único no ano); cópia nova com origem guardada (Duplicar); etapas × componente, descritores e tarefas recriados pelo arquivo (Reimportar).
- Etapa × componente: intervalo mínimo (vazio = sem linhas vazias).
- Descritor: cada campo acima, um por vez; descritor novo (código e descrição; entra no fim da lista).
- Tarefa: início, fim e texto de uma tarefa gravada, linha a linha; tarefa nova pelo "+ Adicionar tarefa" (entra no fim); arquivo do item e texto alternativo (enviar, trocar, remover).
- Ordem de descritores e de tarefas: 1…N, pelo arrastar ou pelos botões "Mover para cima/baixo".
- Exclusão: tarefa ou descritor (com as tarefas dele).

## Ações

| Ação | Onde | Permissão | Resultado |
|---|---|---|---|
| Duplicar | Matriz (modal) | criar matriz | vai para a matriz nova; "Matriz X criada como cópia de Y." |
| Renomear | Matriz (lápis no título) | alterar matriz | Enter ou sair do campo salva (autosave, com modal de impacto); Esc cancela |
| Reimportar | página própria | alterar matriz | volta à matriz; "Importado em X: LP 5EF: 12 descritores, …" |
| Diferenças da origem | página própria (só em cópia) | ver matriz | tabela ou "Nenhuma diferença para X." |
| Intervalo mínimo | popover "Configurações" | editar matriz + bloqueio | salva sozinho; com impacto, o modal abre por cima do popover |
| Buscar descritor | Etapa × CC (HTMX) | ver | lista filtrada por código ou texto |
| Abrir descritor | Etapa × CC (HTMX, muda a URL) | ver | painel troca sem recarregar |
| Editar campo do descritor ou de tarefa gravada | painel | editar matriz + bloqueio | salva sozinho ao sair do campo (status "Salvo às HH:MM") |
| + Adicionar tarefa | painel | editar matriz + bloqueio | linha nova com foco; "Incluir tarefa" (ou Enter) grava; "Descartar" (ou Esc) tira |
| Reordenar descritores / tarefas | lista / painel | editar matriz + bloqueio | alça (arrastar) ou "Mover para cima/baixo"; grava 1…N, com impacto. Sem reordenar enquanto há busca |
| + Novo descritor | topo da lista (modal) | editar matriz + bloqueio | abre o descritor novo; "Descritor D09 criado." |
| Arquivo do item | painel (modal por tarefa) | editar matriz + bloqueio | "Arquivo do item enviado para a tarefa D01 100-150." / removido / texto alternativo salvo |
| Excluir tarefa / descritor | ícone da tarefa / zona de perigo no fim do painel → página de confirmação | excluir tarefa / descritor + bloqueio | volta ao descritor / à etapa × CC; "Tarefa D01 100-150 excluída." |

## Estados

- **Vazio:** ano sem matriz → "Nenhuma matriz em 2027" com o caminho (duplicar de outro ano). Etapa × CC sem descritor → "Nenhum descritor" com "Novo descritor". Busca sem resultado → "Nenhum descritor com “<busca>” no código ou no texto." Sem ano aberto → aviso com o link "Abra um ano" (`/ui/anos/`, com `abrir_ano`).
- **Erro de validação:** a página/painel volta com os erros no campo e a mensagem "Nada foi gravado: corrija os erros marcados."
- **Impacto:** a gravação que tira o "Validado" não grava: abre o modal "<Ação> tira o “Validado” de N revista(s)" com a lista. Confirmar grava; Cancelar ou Esc volta o valor anterior e o foco. No arquivo do item, a lista aparece dentro do próprio modal do item, e o botão vira "Enviar e tirar Validado".
- **Só leitura (perfil):** "Só leitura: seu perfil vê a matriz, mas não altera. Para editar, peça a permissão de matriz a um administrador." Campos desabilitados, sem botões de gravar.
- **Só leitura (bloqueio):** "Somente leitura: Ana está editando (bloqueio até 14:32:10, …). Recarregue para tentar editar." Perdeu o bloqueio no meio: o formulário para de enviar e avisa.
- **Sucesso:** mensagem no topo (lista de mensagens), painel atualizado no lugar.

## Mensagens exatas (novas desta tela; as demais vêm da regra do admin)

- "Só leitura: seu perfil vê a matriz, mas não altera. Para editar, peça a permissão de matriz a um administrador."
- "Nada foi gravado: corrija os erros marcados."
- "Descritor {código} criado." · "Matriz {nova} criada como cópia de {origem}." (o autosave não põe mensagem: o status do cabeçalho diz "Salvo às HH:MM")
- Tarefa nova pelo autosave: "Tarefa nova: preencha a linha e use Incluir tarefa."
- Reordenar com a lista velha: "A lista mudou depois que a página abriu (linha criada ou excluída). Recarregue a página e reordene de novo."
- "Nada foi excluído: o código não confere. Digite {código} exatamente." (da regra existente)

## Regras de permissão

- Ver: `view_matriz` (matrizes) e `view_matrizetapacc` (etapa × CC).
- Duplicar: `add_matriz`. Renomear e reimportar: `change_matriz`.
- Editar etapa × CC, descritor e tarefas: as permissões de alterar/criar de etapa × CC, descritor e tarefa (o pacote "editar matriz" dos perfis).
- Excluir: `delete_tarefa` / `delete_descritor`.
- Gravar na etapa × CC (campos, tarefas, ordem, intervalo, item, novo descritor) exige o bloqueio dela (um editor por vez); POST sem permissão é 403; sem o bloqueio, 409 e a página vira só leitura.
- A permissão de ver a etapa × CC é conferida antes de pegar o bloqueio: quem só tem `delete_*` recebe 403 sem travar a etapa × CC.

## Interações com HTMX e Alpine

- Busca: `input` com atraso de 300 ms troca só a lista; Enter também (o campo fica num `<form method=get>`, que sem JS recarrega a página filtrada).
- Clique num descritor: troca o painel e a URL (`hx-push-url`); a lista volta junto (fora do alvo) para marcar o ativo, mantendo a busca.
- Campos do descritor e tarefas gravadas: form `campoAuto` (rota `ui_matriz_campo`); a tarefa manda a linha inteira (`data-linha`). Intervalo mínimo: `campoAuto` no popover (rota `ui_matriz_intervalo`, componente `popoverSob`). Renomear: `nomeInline` (rota `ui_matriz_renomear`). Protocolo em [`design-system.md`](../design-system.md) §5.
- Tarefa nova: componente `linhaNova`, que grava pelo POST do painel ("Incluir tarefa"). Reordenar: componente `ordenavel` (SortableJS) → `ui_matriz_reordenar`.
- Arquivo do item: `hx-post` do modal; a resposta é o painel novo + mensagens.
- Novo descritor e Duplicar: modal com `hx-post`; erro volta dentro do modal; sucesso leva à página nova (`HX-Redirect`).
- Reimportar e Excluir: página inteira (formulário comum), porque são irreversíveis e pedem confirmação forte.

## Wireframe

```
Matrizes do ano
┌─────────────────────────────────────────────────────────────────────────┐
│ Matrizes                                                                │
│ Descritores e tarefas que as revistas usam.  [Ver painel de 2026]       │
│ ┌──────────────────┬──────────────────┬───────────────┬─────────────┐   │
│ │ Matriz           │ Duplicada de     │ Etapa × CC    │ Descritores │   │
│ │ Comunitária  ›   │ —                │ 8             │ 112         │   │
│ └──────────────────┴──────────────────┴───────────────┴─────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘

Matriz
┌─────────────────────────────────────────────────────────────────────────┐
│ ‹ Matrizes de 2026                                                      │
│ Comunitária ✎          [Diferenças da origem][Reimportar][Duplicar]     │
│ Matriz de 2026 · cópia de Comunitária (2025)                            │
│ ┌──────────┬──────┬──────────────────┬────────────┬──────────────────┐  │
│ │ Etapa    │ CC   │ Intervalo mínimo │ Descritores│ Revistas ativas  │  │
│ │ 5EF  ›   │ LP   │ 25               │ 14         │ 23               │  │
│ └──────────┴──────┴──────────────────┴────────────┴──────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘

Etapa × componente (lista + detalhe)
┌─────────────────────────────────────────────────────────────────────────┐
│ ‹ Comunitária (2026)                                                    │
│ 5EF Língua Portuguesa               ✓ Salvo às 10:15 [⚙ Configurações] │
│ Comunitária · escala até 500 · afeta 23 revista(s) ativa(s)             │
│ ┌───────────────────┐ ┌───────────────────────────────────────────────┐ │
│ │ [+ Novo descritor] │ │ D01  5EF LP                                   │ │
│ │ [🔍 Código ou texto]│ │ Identificação: Código [D01]                   │ │
│ │ 14 de 14 descritores│ │ Descrição [....................]             │ │
│ │ ⋮⋮ ▌D01 Localizar… │ │ Pré-requisitos (um por linha) [....]          │ │
│ │ ⋮⋮  D02 Inferir…   │ │ BNCC: Práticas [..] Conhecimento [..] …       │ │
│ │ ⋮⋮  D03 …          │ │ Tarefas na escala de 0 a 500                  │ │
│ │                    │ │ ⋮⋮ 0 ├──██──┤ 500 [≥100][<150][texto] 📎 ✕    │ │
│ │                    │ │ [+ Adicionar tarefa]                          │ │
│ │                    │ │ ┌ Excluir descritor ─────────────── [Excluir] ┐│ │
│ │                    │ │ └ Na próxima tela, digite o código. ─────────┘│ │
│ └───────────────────┘ └───────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
No celular (< 800 px): a lista vira bloco acima do painel (altura limitada).
```

O elemento que marca a tela: a **faixa da tarefa na escala** (barra fina de 0 ao máximo da etapa, com o trecho início–fim preenchido na cor primária), para ver de relance onde cada tarefa cai, como no editor de escala do React.

## Critérios de aceite

1. Com perfil Pedagógica: as páginas abrem (200), com botões de gravar; anônimo vai ao login do admin; sem `view_matriz` → 403.
2. Impresso vê tudo em só leitura (aviso, campos desabilitados, sem "Salvar") e todo POST dá 403.
3. Duplicar cria a cópia com a origem e leva a ela; nome repetido no ano mostra o erro no modal. Renomear pelo lápis grava pelo autosave; nome vazio ou repetido dá 422.
4. Reimportar grava pela regra do admin; com etapas × CC existentes, exige digitar o nome da matriz.
5. Diferenças lista o que mudou ou "Nenhuma diferença para X."
6. Intervalo mínimo, campos do descritor, tarefas e ordem salvam sozinhos; quando tiram o "Validado" de revistas, o modal abre e nada grava até confirmar. Nenhum checkbox "Confirmo". Não há linha de tarefa em branco: a nova só aparece com "+ Adicionar tarefa".
7. Busca filtra por código ou descrição; abrir descritor por HTMX devolve só o painel (com a lista fora do alvo).
8. Arquivo do item envia, troca e remove pela mesma regra do admin (tipo pelos bytes, 5 MB).
9. Excluir tarefa/descritor pede o código digitado; código errado não exclui; certo exclui e volta com a mensagem.
10. Outra pessoa com a etapa × CC aberta: segunda pessoa vê "Somente leitura: … está editando" e não grava.

## Referências técnicas

- Regra: `app/nucleo/admin/matriz.py` (formulários, impacto, exclusão), `app/nucleo/matriz.py` (reimportar, arquivo do item, `com_afetadas` e `excluir`, extraídos do admin), `app/nucleo/servicos/matriz.py`, `app/nucleo/servicos/arquivos.py`.
- Bloqueio: `app/nucleo/ui_bloqueio.py` (`com_bloqueio`, alvo = etapa × CC).
- Visual: `editor/src/projetos/ano/TelaAno.tsx`, `ListaDescritores.tsx`, `TelaDescritor.tsx`.
- Decisões: D-053, D-071, D-076, D-081, D-091, D-101, D-113, D-155, D-180, D-181, D-183, D-185, D-186.
