# Ficha: Projeto (T15 lista, T16 projeto)

## Objetivo

Deixar cada projeto do ano pronto para gerar as revistas: o nome que sai na capa, as 24 variáveis que os textos usam, o passo da escala quando o projeto foge da matriz e as cores dos padrões quando o projeto pinta diferente do ano. Tudo numa página só, que se salva de uma vez.

## Quem usa

| Perfil | O que faz |
|---|---|
| Pedagógica, Mídias Digitais, Admin | Veem e editam tudo: nome, variáveis, passo e cores (incluindo remover uma sobrescrita). |
| Impresso | Vê tudo, não altera. |
| Sem perfil | Não entra (recusado). |

## Jornada

- **Antes:** os cortes do parceiro são lançados (o projeto nasce sozinho) e a matriz do parceiro é escolhida em lote. A paleta e os nomes dos padrões do ano já estão definidos.
- **Aqui:** abrir a lista de projetos do ano, entrar num projeto, preencher o que falta, salvar.
- **Depois:** a planilha de variáveis do ano (mesmos campos, vários projetos lado a lado) e as revistas do projeto, que passam a mostrar os valores gravados.

## Lista de projetos do ano (T15)

- **Mostra:** um projeto por linha, com nome (link para o projeto), parceiro, matriz (ou "sem matriz") e situação (Ativo, ou Arquivado em dd/mm/aaaa). Ativos primeiro, por parceiro.
- **Ações:** trocar o ano; abrir a planilha de variáveis do ano; "Escolher matriz" (só quem pode escolher matriz).
- **Vazio:** "Nenhum projeto neste ano. O projeto do parceiro nasce quando os cortes dele são lançados." com o botão "Lançar cortes".
- Não há incluir nem excluir: projeto nasce e é arquivado pelos cortes.

## Projeto (T16)

### Dados mostrados

- Cabeçalho: nome do projeto, parceiro, ano, matriz; selo "Arquivado" quando for o caso.
- Índice com âncoras: Nome, Variáveis, Passo, Cores.
- **Nome:** campo único.
- **Variáveis:** as 24 variáveis manuais, separadas pelos grupos Coleção, Adjetivo pátrio, Parceiro, Programa, Regional e secretaria, Padrões de desempenho. Cada campo tem o rótulo, a descrição e o marcador que aparece nos textos (`{{issn}}`). As 3 automáticas (nome do parceiro, nome do projeto, ano) não aparecem.
- Nos nomes dos padrões (Padrão 1 a 5) vazios, a dica do campo diz o nome do ano que vale: "padrão do ano: Abaixo do básico".
- **Passo:** a referência do passo da matriz por etapa e componente ("5EF LP: 25"), e a tabela das sobrescritas do projeto (etapa, componente, passo).
- **Cores:** a faixa dos padrões como sai na revista (cor e nome efetivos, com "do projeto" ou "do ano"), e a tabela das sobrescritas (padrão, cor).

### Dados gravados

- Nome do projeto e as 24 variáveis (até 200 caracteres cada).
- Sobrescritas de passo por etapa × componente: a linha existir = sobrescrevi; passo vazio = sem linhas vazias, de propósito; remover a linha = voltar ao passo da matriz.
- Sobrescritas de cor por padrão (até 5, uma por padrão): remover = voltar à cor do ano.
- Tudo junto, numa transação: um erro em qualquer parte, nada grava.

### Ações

| Ação | Quem | Resultado |
|---|---|---|
| Salvar projeto | quem edita, com o bloqueio | grava tudo e volta à página com a mensagem de sucesso |
| Sobrescrever um passo | quem edita | acrescenta uma linha vazia na tabela de passo (sem recarregar) |
| Sobrescrever uma cor | quem edita | acrescenta uma linha com o primeiro padrão sem cor já escolhido e a cor do ano dele; com 5 linhas o botão desliga |
| Remover / Descartar | quem edita | marca a linha para sair ao salvar (Remover = sobrescrita gravada; Descartar = linha nova) |
| Planilha de variáveis do ano / Projetos do ano | todos | navegação |

### Estados

- **Vazio:** sem sobrescrita de passo, a tabela diz "Nenhuma sobrescrita: vale o passo da matriz em todas as etapas e componentes."; sem cor, "Nenhuma sobrescrita: valem as cores do ano." Matriz não escolhida: o cabeçalho diz "matriz ainda não escolhida" e a referência de passo some.
- **Erro de validação:** mensagem no topo, campo com borda vermelha e o erro embaixo; linha de passo/cor com erro destacada, com a lista dos erros logo abaixo. Nada grava.
- **Só leitura (perfil):** aviso no topo, campos desligados, sem botões de ação.
- **Só leitura (outra pessoa editando):** aviso de quem está editando e até quando; campos desligados.
- **Arquivado:** aviso no topo, selo "Arquivado", campos desligados; não trava ninguém.
- **Perdeu o bloqueio durante a edição:** o formulário vira só leitura na hora, com aviso para copiar o que precisar e recarregar.
- **Sucesso:** volta à página com a mensagem e a faixa de cores já com o novo estado.

### Mensagens exatas

- Sucesso: "Projeto {nome} salvo."
- Erro: "Nada foi gravado: corrija os erros marcados."
- Sem permissão: "Só leitura: seu perfil vê o projeto, mas não altera. Para editar, peça a permissão de projeto a um administrador."
- Arquivado: "Só leitura: este projeto foi arquivado e as revistas dele estão congeladas. Para mudar algo, abra o projeto ativo do parceiro."
- Outra pessoa editando: "Somente leitura: {quem} está editando (bloqueio até {hh:mm:ss}, renovado enquanto a página estiver aberta). Recarregue para tentar editar."
- Bloqueio perdido ao salvar: "Não salvo: você perdeu o bloqueio de edição (outra pessoa ou aba abriu esta página). Recarregue e refaça a alteração."
- Bloqueio perdido durante a edição: "Você perdeu o bloqueio de edição: o formulário ficou somente leitura. Copie o que precisar e recarregue a página."
- Texto longo: "Certifique-se de que o valor tenha no máximo 200 caracteres (ele possui N)." (do Django, embaixo do campo)

### Permissões

- Login obrigatório: anônimo vai ao login do admin.
- Ver: permissão de ver projeto. Sem ela, recusado.
- Editar: permissões de projeto, passo e cor (as que o perfil "editar projeto" dá juntas). Sem elas, só leitura e envio recusado.
- Arquivado: ninguém altera, nem com permissão.
- Bloqueio: um editor por projeto; quem abre depois vê só leitura.

### Interações com HTMX

- "Sobrescrever um passo" e "Sobrescrever uma cor" pedem ao servidor uma linha nova do formulário e a acrescentam no fim da tabela; a mesma resposta atualiza o contador de linhas do formulário e, ao chegar a 5 cores, desliga o botão. Sem JavaScript, o resto da página funciona (só não se acrescentam linhas).
- O pedido leva a sessão do bloqueio; sem o bloqueio, é recusado e aparece o aviso de erro padrão.
- Salvar é um envio normal do formulário (recarrega a página).

### Wireframe (1440 px)

```
┌ Revista Eletrônica   Painel Cortes [Variáveis] Matrizes Templates Revistas Impresso     Ana  Admin  Sair ┐
│                                                                                                     │
│ Projeto GO                                         [Planilha de variáveis de 2026] [Projetos de 2026]│
│ GO em 2026, matriz Comunitária.                                                                     │
│ Nome  Variáveis  Passo  Cores                                                                       │
│ ┌ Nome ───────────────────────────────────────────────────────────────────────────────────────────┐ │
│ │ Nome do projeto [Projeto GO                         ]  Aparece na capa e em {{nome_projeto}}.   │ │
│ └─────────────────────────────────────────────────────────────────────────────────────────────────┘ │
│ ┌ Variáveis ──────────────────────────────────────────────────────────────────────────────────────┐ │
│ │ Coleção ─────────────────────────────────────────────────────────────────────────────────────── │ │
│ │ ISSN [            ]                                                                             │ │
│ │ Adjetivo pátrio ─────────────────────────────────────────────────────────────────────────────── │ │
│ │ masc. sing. [mineiro ]   fem. sing. [mineira ]   masc. plural [      ]   fem. plural [      ]   │ │
│ │ … Parceiro, Programa, Regional e secretaria …                                                  │ │
│ │ Padrões de desempenho ───────────────────────────────────────────────────────────────────────── │ │
│ │ Padrão 1 [padrão do ano: Abaixo do básico]  Padrão 2 [ … ]  …                                   │ │
│ └─────────────────────────────────────────────────────────────────────────────────────────────────┘ │
│ ┌ Passo por etapa e componente ───────────────────────────────────────────────────────────────────┐ │
│ │ Na matriz Comunitária: (5EF LP: 25) (5EF MT: 25) (9EF LP: 25) (9EF MT: 25)                      │ │
│ │ Etapa      Componente    Passo                                                                  │ │
│ │ [5EF ▾]    [LP ▾]        [   ]                                  [ ] Remover                     │ │
│ │ [+ Sobrescrever um passo]                                                                       │ │
│ └─────────────────────────────────────────────────────────────────────────────────────────────────┘ │
│ ┌ Cores dos padrões ──────────────────────────────────────────────────────────────────────────────┐ │
│ │ ███████████ ███████████ ███████████ ███████████ ███████████   ← faixa: cor efetiva de cada padrão│ │
│ │ Padrão 1    Padrão 2    Padrão 3    Padrão 4    Padrão 5                                        │ │
│ │ Abaixo…     Básico      Adequado    Avançado    …                                               │ │
│ │ #F72628 do ano  #123456 do projeto …                                                            │ │
│ │ Padrão   Cor                                                                                    │ │
│ │ [2  ]    [■]                                                     [ ] Remover                    │ │
│ │ [+ Sobrescrever uma cor]                                                                        │ │
│ └─────────────────────────────────────────────────────────────────────────────────────────────────┘ │
│ ─────────────────────────────────────────────────────────────────────────────────────────────────── │
│ Salva nome, variáveis, passos e cores juntos.                                     [Salvar projeto]  │ ← fixa no rodapé
└─────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

Em 390 px: uma coluna; campos das variáveis um por linha; a faixa vira lista vertical (amostra à esquerda, padrão, nome e cor à direita); a barra de salvar ocupa a largura.

Escolha visual: o resto da página é quieto (cartões do editor, tipografia Inter); a faixa dos padrões é o único elemento de cor, porque mostra exatamente o que a revista vai pintar.

### Critérios de aceite

1. Quem edita abre o projeto e vê nome, os 6 grupos de variáveis, a referência do passo da matriz, a faixa com as cores do ano e o botão "Salvar projeto"; o projeto fica travado para essa pessoa.
2. Padrão N vazio mostra "padrão do ano: <nome>" como dica; as variáveis automáticas não aparecem.
3. Salvar grava nome, variáveis, passo novo (inclusive com passo vazio) e cor nova de uma vez e volta com "Projeto {nome} salvo."; a faixa passa a mostrar a cor do projeto.
4. Remover uma cor volta à paleta do ano (a linha some do banco).
5. Nome com mais de 200 caracteres ou passo menor que 1: "Nada foi gravado: corrija os erros marcados.", campos marcados, nada grava.
6. Impresso vê tudo desligado, sem botões; enviar é recusado. Sem perfil: recusado ao abrir.
7. Anônimo vai ao login do admin (projeto e lista).
8. Arquivado: aviso, sem salvar, sem travar; envio recusado mesmo com permissão.
9. Outra pessoa editando: aviso de quem edita, sem salvar; envio com sessão de outra aba: "Não salvo: você perdeu o bloqueio…" e nada grava.
10. "Sobrescrever uma cor" traz a linha com o primeiro padrão livre e a cor do ano dele; a 5ª linha desliga o botão; sem o bloqueio o pedido é recusado.
11. Só etapas e componentes do ano do projeto aparecem nas listas da tabela de passo.
12. Lista do ano: projetos com link, "Escolher matriz" só para quem pode; ano vazio mostra o estado vazio; a raiz `/ui/projeto/` abre o ano mais recente.

## Referências técnicas

- Regra: `app/nucleo/projeto.py` (ProjetoForm, PassoForm, PassoFormSet, CorForm, `formsets`), usada também por `app/nucleo/admin/projeto.py`. Limites e dica do `pdNN`: `admin/variaveis.py` (`limitar`, `mostrar_nome_do_ano`, `EDITAVEIS`).
- Cores e nomes efetivos da faixa: `servicos/resolver.py` (`_cores`, `valores_das_variaveis`).
- View: `app/nucleo/urls/ui_projeto.py` (rotas `ui_projeto_inicio`, `ui_projeto_lista`, `ui_projeto`, `ui_projeto_linha`).
- Templates: `templates/ui/projeto/{projeto,lista}.html`, `templates/ui/parciais/projeto_{linha,adicionar}.html`; CSS `static/ui/telas/projeto.css`.
- Testes: `app/nucleo/tests/test_ui_projeto.py`.
- Decisões: D-053, D-060, D-081, D-091, D-093, D-100, D-166, D-167, D-172, D-173, D-175, D-183, D-186.
