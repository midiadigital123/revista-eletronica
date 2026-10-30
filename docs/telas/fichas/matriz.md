# Ficha da tela: Matrizes e descritores (T09, T10, T11)

## Objetivo

Cuidar da matriz de referência do ano: ver quais matrizes existem, criar uma a partir de outra (Duplicar), trocar o conteúdo pelo PDF ou planilha do SAEGO (Reimportar), ver o que mudou numa cópia (Diferenças), ajustar o intervalo mínimo de cada etapa × componente e editar descritores, tarefas e o arquivo do item. Tudo o que muda aqui muda as revistas ativas que usam a matriz, então cada gravação mostra quantas revistas são afetadas e pede confirmação.

## Quem usa

| Perfil | O que faz |
|---|---|
| Pedagógica, Mídias Digitais, Admin | tudo: duplicar, reimportar, renomear, intervalo mínimo, descritores, tarefas, arquivo do item, excluir tarefa e descritor |
| Impresso | só vê (aviso de só leitura; nenhum botão de gravar) |
| Sem permissão de ver matriz | recebe "acesso negado" (403) |
| Não logado | vai para o login do admin e volta depois |

## Jornada

- **Antes:** abrir o ano e conferir os cadastros (etapas, componentes, padrões). A matriz do ano nasce pela importação (comando da carga) ou pela duplicação de uma matriz de outro ano.
- **Depois:** escolher a matriz de cada parceiro (lote "Escolher matriz") e conferir as revistas no Painel.

## Páginas

1. **Matrizes do ano** — lista das matrizes do ano escolhido.
2. **Matriz** — etapas × componente da matriz, com as ações Renomear, Duplicar, Reimportar e Diferenças.
3. **Reimportar** — envio do arquivo com confirmação forte.
4. **Diferenças** — o que a cópia tem de diferente da origem (só consulta).
5. **Etapa × componente** — intervalo mínimo no topo; lista de descritores com busca à esquerda; painel do descritor à direita (campos, tarefas, arquivo do item).
6. **Excluir tarefa / Excluir descritor** — confirmação forte com as revistas afetadas.

## Dados mostrados

- Matrizes do ano: nome, de onde foi duplicada, quantas etapas × componente e quantos descritores.
- Matriz: ano, origem; por etapa × componente: intervalo mínimo, descritores, revistas ativas afetadas.
- Etapa × componente: intervalo mínimo; descritores (código, descrição); contagem "N de M descritores" na busca.
- Descritor: código, descrição, pré-requisitos (um por linha), práticas, conhecimento, habilidades relacionadas e correspondente, ordem; tarefas (início, fim, texto, ordem) com a faixa da tarefa desenhada na escala da etapa e o tipo do arquivo do item quando houver.
- Impacto: "Afeta N revista(s) ativa(s)"; no arquivo do item e na exclusão, também quantas perdem o "Validado".
- Diferenças: onde, o quê, na origem, nesta matriz.

## Dados gravados (pela mesma regra do admin)

- Matriz: nome (único no ano); cópia nova com origem guardada (Duplicar); etapas × componente, descritores e tarefas recriados pelo arquivo (Reimportar).
- Etapa × componente: intervalo mínimo (vazio = sem linhas vazias).
- Descritor: todos os campos acima; descritor novo (código, descrição, ordem).
- Tarefa: início, fim, texto, ordem; tarefa nova na linha em branco; arquivo do item e texto alternativo (enviar, trocar, remover).
- Exclusão: tarefa ou descritor (com as tarefas dele).

## Ações

| Ação | Onde | Permissão | Resultado |
|---|---|---|---|
| Duplicar | Matriz (modal) | criar matriz | vai para a matriz nova; "Matriz X criada como cópia de Y." |
| Renomear | Matriz (modal) | alterar matriz | "Matriz renomeada para X." |
| Reimportar | página própria | alterar matriz | volta à matriz; "Importado em X: LP 5EF: 12 descritores, …" |
| Diferenças | página própria | ver matriz | tabela ou "Nenhuma diferença para X." |
| Salvar intervalo mínimo | Etapa × CC (HTMX) | editar matriz + bloqueio | "Intervalo mínimo de 5EF LP salvo." |
| Buscar descritor | Etapa × CC (HTMX) | ver | lista filtrada por código ou texto |
| Abrir descritor | Etapa × CC (HTMX, muda a URL) | ver | painel troca sem recarregar |
| Salvar descritor e tarefas | painel (HTMX) | editar matriz + bloqueio | "Descritor D01 salvo." |
| Novo descritor | Etapa × CC (modal) | editar matriz + bloqueio | abre o descritor novo; "Descritor D09 criado." |
| Arquivo do item | painel (modal por tarefa) | editar matriz + bloqueio | "Arquivo do item enviado para a tarefa D01 100-150." / removido / texto alternativo salvo |
| Excluir tarefa / descritor | página de confirmação | excluir tarefa / descritor + bloqueio | volta ao descritor / à etapa × CC; "Tarefa D01 100-150 excluída." |

## Estados

- **Vazio:** ano sem matriz → "Nenhuma matriz em 2027" com o caminho (duplicar de outro ano). Etapa × CC sem descritor → "Nenhum descritor" com "Novo descritor". Busca sem resultado → "Nenhum descritor com esse código ou texto." Sem ano aberto → aviso com link para o admin.
- **Erro de validação:** a página/painel volta com os erros no campo e a mensagem "Nada foi gravado: corrija os erros marcados."
- **Impacto sem confirmação:** "Esta edição afeta N revista(s) ativa(s) (…). Marque a confirmação e salve de novo."
- **Só leitura (perfil):** "Só leitura: seu perfil vê a matriz, mas não altera. Para editar, peça a permissão de matriz a um administrador." Campos desabilitados, sem botões de gravar.
- **Só leitura (bloqueio):** "Somente leitura: Ana está editando (bloqueio até 14:32:10, …). Recarregue para tentar editar." Perdeu o bloqueio no meio: o formulário para de enviar e avisa.
- **Sucesso:** mensagem no topo (lista de mensagens), painel atualizado no lugar.

## Mensagens exatas (novas desta tela; as demais vêm da regra do admin)

- "Só leitura: seu perfil vê a matriz, mas não altera. Para editar, peça a permissão de matriz a um administrador."
- "Nada foi gravado: corrija os erros marcados."
- "Descritor {código} salvo." · "Descritor {código} criado." · "Intervalo mínimo de {etapa} {cc} salvo." · "Matriz renomeada para {nome}."
- "Nada foi excluído: o código não confere. Digite {código} exatamente." (da regra existente)

## Regras de permissão

- Ver: `view_matriz` (matrizes) e `view_matrizetapacc` (etapa × CC).
- Duplicar: `add_matriz`. Renomear e reimportar: `change_matriz`.
- Editar etapa × CC, descritor e tarefas: as permissões de alterar/criar de etapa × CC, descritor e tarefa (o pacote "editar matriz" dos perfis).
- Excluir: `delete_tarefa` / `delete_descritor`.
- Gravar na etapa × CC exige o bloqueio dela (um editor por vez); POST sem permissão é 403.

## Interações com HTMX

- Busca: `input` com atraso de 300 ms troca só a lista.
- Clique num descritor: troca o painel e a URL (`hx-push-url`); a lista volta junto (fora do alvo) para marcar o ativo, mantendo a busca.
- Salvar descritor, salvar intervalo e arquivo do item: `hx-post`; a resposta é o pedaço novo + mensagens.
- Novo descritor e Duplicar/Renomear: modal com `hx-post`; erro volta dentro do modal; sucesso leva à página nova (`HX-Redirect`).
- Reimportar e Excluir: página inteira (formulário comum), porque são irreversíveis e pedem confirmação forte.

## Wireframe

```
Matrizes do ano
┌─────────────────────────────────────────────────────────────────────────┐
│ Matrizes                                                                │
│ Descritores e tarefas que as revistas usam.            [Ver painel]     │
│ [2027][2026][2025]                                                      │
│ ┌──────────────────┬──────────────────┬───────────────┬─────────────┐   │
│ │ Matriz           │ Duplicada de     │ Etapa × CC    │ Descritores │   │
│ │ Comunitária  ›   │ —                │ 8             │ 112         │   │
│ └──────────────────┴──────────────────┴───────────────┴─────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘

Matriz
┌─────────────────────────────────────────────────────────────────────────┐
│ ‹ Matrizes de 2026                                                      │
│ Comunitária                       [Renomear][Duplicar][Reimportar]      │
│ 2026 · cópia de Comunitária (2025)                [Diferenças]          │
│ ┌──────────┬──────┬──────────────────┬────────────┬──────────────────┐  │
│ │ Etapa    │ CC   │ Intervalo mínimo │ Descritores│ Revistas ativas  │  │
│ │ 5EF  ›   │ LP   │ 25               │ 14         │ 23               │  │
│ └──────────┴──────┴──────────────────┴────────────┴──────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘

Etapa × componente (lista + detalhe)
┌─────────────────────────────────────────────────────────────────────────┐
│ ‹ Comunitária                                                           │
│ 5EF LP                                     [Intervalo mínimo [25][Salvar]]│
│ Comunitária 2026 · afeta 23 revistas ativas                             │
│ ┌───────────────────┐ ┌───────────────────────────────────────────────┐ │
│ │ [🔍 Código ou texto]│ │ D01  Localizar informação         [Excluir]  │ │
│ │ [+ Novo descritor] │ │ Identificação: Código [D01] Ordem [1]         │ │
│ │ 14 de 14           │ │ Descrição [....................]              │ │
│ │ ▌D01 Localizar…    │ │ Pré-requisitos (um por linha) [....]          │ │
│ │  D02 Inferir…      │ │ BNCC: Práticas [..] Conhecimento [..] …       │ │
│ │  D03 …             │ │ Tarefas                                       │ │
│ │                    │ │ 0 ├──██───────────┤ 500 [100][150][texto][1]  │ │
│ │                    │ │     PNG [Arquivo do item] [Excluir]           │ │
│ │                    │ │ (linha em branco = tarefa nova)               │ │
│ │                    │ │ [☐ Confirmo: afeta 23 revista(s) ativa(s)]    │ │
│ │                    │ │                          [Salvar descritor]   │ │
│ └───────────────────┘ └───────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
No celular (< 800 px): a lista vira bloco acima do painel (altura limitada).
```

O elemento que marca a tela: a **faixa da tarefa na escala** (barra fina de 0 ao máximo da etapa, com o trecho início–fim preenchido na cor primária), para ver de relance onde cada tarefa cai, como no editor de escala do React.

## Critérios de aceite

1. Com perfil Pedagógica: as páginas abrem (200), com botões de gravar; anônimo vai ao login do admin; sem `view_matriz` → 403.
2. Impresso vê tudo em só leitura (aviso, campos desabilitados, sem "Salvar") e todo POST dá 403.
3. Duplicar cria a cópia com a origem e leva a ela; nome repetido no ano mostra o erro no modal.
4. Reimportar grava pela regra do admin; com etapas × CC existentes, exige digitar o nome da matriz.
5. Diferenças lista o que mudou ou "Nenhuma diferença para X."
6. Intervalo mínimo e descritor gravam só com a confirmação de impacto quando há revistas ativas afetadas; sem ela, a mensagem de impacto aparece e nada grava.
7. Busca filtra por código ou descrição; abrir descritor por HTMX devolve só o painel (com a lista fora do alvo).
8. Arquivo do item envia, troca e remove pela mesma regra do admin (tipo pelos bytes, 5 MB).
9. Excluir tarefa/descritor pede o código digitado; código errado não exclui; certo exclui e volta com a mensagem.
10. Outra pessoa com a etapa × CC aberta: segunda pessoa vê "Somente leitura: … está editando" e não grava.

## Referências técnicas

- Regra: `app/nucleo/admin/matriz.py` (formulários, impacto, exclusão), `app/nucleo/matriz.py` (reimportar e arquivo do item, extraídos do admin), `app/nucleo/servicos/matriz.py`, `app/nucleo/servicos/arquivos.py`.
- Bloqueio: `app/nucleo/ui_bloqueio.py` (`com_bloqueio`, alvo = etapa × CC).
- Visual: `editor/src/projetos/ano/TelaAno.tsx`, `ListaDescritores.tsx`, `TelaDescritor.tsx`.
- Decisões: D-053, D-071, D-076, D-081, D-091, D-101, D-113, D-155, D-180, D-181, D-183, D-185, D-186.
