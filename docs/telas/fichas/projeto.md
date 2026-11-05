# Ficha: Projetos (T15 lista, T18/T19 ações em massa) e Projeto (T16)

Endereços: `/ui/projeto/ano/<ano>/` (rota `ui_projeto_lista`, hub Projetos, aba Lista) e `/ui/projeto/<pk>/?aba=…` (rota `ui_projeto`). As outras abas do hub, Cortes e Variáveis, têm fichas próprias: [`cortes.md`](cortes.md) e [`variaveis.md`](variaveis.md).

## Objetivo

Deixar cada projeto do ano pronto para gerar as revistas: o nome que sai na capa, as 24 variáveis que os textos usam, a matriz, os cortes do parceiro, o passo da escala quando o projeto foge da matriz e as cores dos padrões quando o projeto pinta diferente do ano. A Lista mostra todos os projetos com as revistas e faz as atribuições em massa (matriz, template). Na página do projeto, cada campo salva sozinho.

## Quem usa

| Perfil | O que faz |
|---|---|
| Pedagógica, Mídias Digitais, Admin | Veem e editam tudo: nome, variáveis, matriz, cortes, passo e cores (incluindo voltar ao herdado). Atribuem matriz e template em massa na Lista. |
| Impresso | Vê tudo, não altera: sem caixas de marcar, sem barra de ações, campos desligados. POST: 403. |
| Sem perfil | Não entra (403). |

## Jornada

- **Antes:** os cortes do parceiro são lançados na aba Cortes (o projeto nasce sozinho). A paleta e os nomes dos padrões do ano já estão definidos ("Configurar <ano>", ficha [`anos.md`](anos.md)).
- **Aqui:** na Lista, marcar parceiros e "Atribuir matriz…" / "Atribuir template…"; abrir um projeto e preencher o que falta, aba por aba.
- **Depois:** a página da revista (templates, arquivos, textos, "Validar revista") e o Painel.

## Hub Projetos, aba Lista (T15; substitui a lista de Revistas e os Lotes)

- **Cabeçalho:** "Projetos" e as abas Lista · Cortes · Variáveis (a aba é a URL; o seletor de ano mantém a aba).
- **Mostra:** um grupo por projeto (ativos primeiro, por parceiro), com o nome do projeto (link), o parceiro em cinza e a matriz (pílula azul, ou "sem matriz" em âmbar). Selos: "Arquivado em dd/mm/aaaa", "Em edição por <nome>: será pulado", "Sem projeto ativo". Abaixo, uma linha por revista: o componente (LP/MT), o balão de pendências ("N pendências" ou ✓), o link para a revista, a Situação ("Em preparo", "Pronta para validar", "Validada", "Impressa" ou "Arquivada") e os botões-ícone "Abrir preview" (nova aba) e "Baixar zip". Parceiro do ano sem projeto aparece com "sem projeto".
- **Ações em massa** (só quem pode): caixa de marcar por parceiro e "Marcar todos os parceiros" no cabeçalho. A barra fixa embaixo mostra "N selecionado(s)", "Atribuir matriz…" e "Atribuir template…"; sem nada marcado, os dois ficam desligados ("Marque ao menos um parceiro").
  - **Atribuir matriz…** abre um modal com o select "Matriz" (só as do ano).
  - **Atribuir template…** abre um modal com "Componente" e "Template F1" / "Template F2" ("Não mudar" deixa como está). Fascículo com texto próprio na revista é pulado e listado.
  - Projeto em edição por outra sessão é pulado e listado ("Pulados: …"). Se alguma revista validada mudar, o modal de impacto lista as revistas antes de gravar. Ao gravar, volta à Lista com "Matriz <nome> escolhida para N parceiro(s)." / "Template escolhido em N revista(s)."
- **Vazio:** "Nenhum projeto neste ano" · "O projeto do parceiro nasce quando os cortes dele são lançados." · botão "Lançar cortes". Sem ano aberto: "Nenhum ano aberto" com "Abrir anos" (só com `abrir_ano`).
- Não há incluir nem excluir: o projeto nasce e é arquivado pelos cortes.

## Projeto (T16)

### Dados mostrados

- Trilha "Projetos de <ano>" acima do título.
- Cabeçalho: nome do projeto e a lista Parceiro, Ano, Matriz ("ainda não escolhida"), Revistas (LP, MT), Situação (Ativo ou o selo "Arquivado"). O status do salvamento fica à direita, para quem grava.
- Abas (a aba é a URL, `?aba=`; aba desconhecida vira Dados):
  - **Dados:** "Nome do projeto" (aparece na capa e em `{{nome_projeto}}`) e as 24 variáveis manuais, nos grupos Coleção, Adjetivo pátrio, Parceiro, Programa, Regional e secretaria, Padrões de desempenho. Cada campo tem o rótulo, a descrição e o marcador (`{{issn}}`). As 3 automáticas (nome do parceiro, nome do projeto, ano) não aparecem. Link "Ver a planilha de variáveis de <ano>".
  - **Matriz:** select "Matriz de <parceiro> em <ano>" com as matrizes do ano, a dica para usar "Atribuir matriz…" na Lista e o passo de cada etapa × componente na matriz ("5EF LP: 25").
  - **Cortes:** a linha deste parceiro da grade de Cortes, um bloco por etapa ("5EF até 500") com os componentes lado a lado, e o link "Ver a grade de cortes de <ano>".
  - **Passos e cores:** as amostras dos padrões (cor e nome efetivos, selo "do ano" ou "sobrescrita") e, por etapa, uma célula por componente com o passo ("Matriz: 25", "fora da matriz" ou "sem linhas vazias") e o selo "da matriz" ou "sobrescrito". Link "Editar as cores do ano" (com `change_corpadrao`). O nome do padrão se troca nas variáveis pd01 a pd05, na aba Dados.
  - **Revistas:** um cartão por componente com Template F1 e F2 (ou "sem template"), SVG do F2 e Capa (✓ ou falta), o selo "Validada", "Sem “Validado”" ou "Arquivada", e os botões "Abrir revista" e "Preview".

### Dados gravados (um campo por vez)

- Nome do projeto e as 24 variáveis (até 200 caracteres cada).
- Matriz do parceiro no ano: pelo mesmo serviço da ação em massa (`servicos.matriz.atribuir_matriz`).
- Cortes: pela rota da grade (`cortes_celula`), com o mesmo conflito otimista.
- Passo por etapa × componente: um número sobrescreve; vazio (ou "Voltar ao passo da matriz") volta ao da matriz; "Sem linhas vazias" grava a linha com passo nulo, de propósito.
- Cor por padrão: a cor escolhida sobrescreve a do ano; escolher a própria cor do ano (ou "Voltar à cor do ano") apaga a sobrescrita. Só a caixa diferente (`#f72628` × `#F72628`) não é mudança.
- Qualquer gravação que mude o texto de uma revista validada abre o modal de impacto antes de gravar.

### Ações

| Ação | Quem | Resultado |
|---|---|---|
| Sair de um campo alterado (Dados, Cortes, passo) | quem edita, com o bloqueio | grava só o campo; o status mostra "Salvo às HH:MM" |
| Escolher a matriz / uma cor | quem edita, com o bloqueio | grava ao escolher |
| "Voltar ao passo da matriz" / "Voltar à cor do ano" | quem edita | apaga a sobrescrita daquela célula ou padrão |
| "Sem linhas vazias" | quem edita | marca a célula como sem linhas vazias (desliga o número) |
| Abrir revista / Preview | todos | página da revista / preview em nova aba |
| Projetos de <ano> / planilha de variáveis / grade de cortes | todos | navegação |

### Estados

- **Vazio:** sem etapas no ano, a aba Passos e cores mostra "Nenhuma etapa neste ano" e a aba Cortes "Sem etapas ou componentes". Sem revistas: "Nenhuma revista neste projeto" · "As revistas nascem dos cortes do parceiro, uma por componente." Matriz não escolhida: o cabeçalho diz "ainda não escolhida".
- **Erro (422):** o erro aparece embaixo do campo e o status diz "Não salvo: corrija o campo marcado". Nada grava.
- **Impacto:** o modal "Salvar “<campo>” tira o “Validado” de N revista(s)" (ou "Trocar a matriz…", "Salvar o passo…", "Salvar a cor…") lista as revistas. Cancelar ou Esc volta o valor gravado e o foco.
- **Só leitura (perfil):** aviso no topo, campos desligados, sem botões de ação.
- **Só leitura (outra pessoa editando):** aviso de quem está editando e até quando; campos desligados.
- **Arquivado:** aviso no topo, selo "Arquivado", campos desligados; não trava ninguém. POST: 403.
- **Perdeu o bloqueio durante a edição (409):** o formulário vira só leitura na hora, com aviso para copiar o que precisar e recarregar.
- **Sem conexão:** "Não salvo: sem conexão · Tentar de novo"; só aí (ou com envio pendente) o navegador avisa ao sair.

### Mensagens exatas

- Sem permissão: "Só leitura: seu perfil vê o projeto, mas não altera. Para editar, peça a permissão de projeto a um administrador."
- Arquivado: "Só leitura: este projeto foi arquivado e as revistas dele estão congeladas. Para mudar algo, abra o projeto ativo do parceiro."
- Outra pessoa editando: "Somente leitura: {quem} está editando (bloqueio até {hh:mm:ss}, renovado enquanto a página estiver aberta). Recarregue para tentar editar."
- Bloqueio perdido ao salvar: "Não salvo: você perdeu o bloqueio de edição (outra pessoa ou aba abriu esta página). Recarregue e refaça a alteração."
- Bloqueio perdido durante a edição: "Você perdeu o bloqueio de edição: o formulário ficou somente leitura. Copie o que precisar e recarregue a página."
- Matriz de outro ano: "Escolha uma matriz de <ano>."
- Cor inválida: "Use uma cor no formato #RRGGBB."
- Texto longo: "Certifique-se de que o valor tenha no máximo 200 caracteres (ele possui N)." (do Django)
- Lista, ações em massa: "Marque ao menos um parceiro." · "Escolha a matriz." · "Escolha o template do F1, do F2 ou dos dois." · "Nada foi gravado: Escolha o componente." · "Pulados: <projeto> (projeto em edição por <nome>)."

### Permissões

- Login obrigatório: anônimo vai ao login das telas B (`/conta/entrar/`).
- Ver: `view_projeto` ou `change_projeto`. Sem elas, 403.
- Editar a ficha: `change_projeto` e as permissões de passo e cor (`add/change/delete` de `projetopasso` e `projetocor`, que o perfil "editar projeto" dá juntas). Sem elas, só leitura e envio 403.
- Aba Matriz: `change_parceiroano`. Aba Cortes: as permissões de cortes (ficha [`cortes.md`](cortes.md)).
- Ações em massa: matriz com `change_parceiroano`, template com `change_revistafasciculo`. Sem elas, a barra não aparece e o POST dá 403.
- Arquivado: ninguém altera, nem com permissão.
- Bloqueio: um editor por projeto; quem abre depois vê só leitura. A Lista não trava nada; a ação em massa trava cada projeto só durante a escrita.

### Interações (Alpine e HTMX)

- A ficha é um `<form x-data="campoAuto" data-url="…/campo/">` (rota `ui_projeto_campo`, `POST /ui/projeto/<pk>/campo/`) com a sessão de bloqueio. É a mesma rota da planilha de Variáveis (um só ponto de escrita). Passo vai como `passo-<etapa>-<componente>` ou `sem-<etapa>-<componente>`; cor como `cor-<padrão>`. Protocolo em [`design-system.md`](../design-system.md) §5.
- Matriz: form próprio (`campoAuto`, rota `ui_projeto_matriz`) com a mesma sessão de bloqueio.
- Cortes: form próprio (`campoAuto`, rota `cortes_celula`).
- Passo e cor: componente `sobrescrita` (`static/ui/componentes/sobrescrita.js`) liga o selo e o "Voltar ao…".
- Lista: os modais ficam dentro do form `massa`; o botão de cada um envia para a sua ação (`formaction`, `POST /ui/projeto/ano/<ano>/massa/<matriz|template>/`). `lotes.js` cuida de marcar todos, do contador e de ligar os botões.

### Wireframe (1440 px)

```
┌ Revista Eletrônica  [2026 ▾]  Painel [Projetos] Matrizes Templates Impresso             Ana         Sair ┐
│ Projetos de 2026                                                                                      │
│ Projeto GO                                                                       ✓ Salvo às 10:15     │
│ Parceiro GO   Ano 2026   Matriz Comunitária   Revistas LP, MT   Situação Ativo                        │
│  Dados   Matriz   Cortes   Passos e cores   Revistas                                                  │
│  ━━━━━                                                                                                │
│ ┌ Nome ────────────────────────────────────────────────────────────────────────────────────────────┐ │
│ │ Nome do projeto [Projeto GO                         ]  Aparece na capa e em {{nome_projeto}}.    │ │
│ └──────────────────────────────────────────────────────────────────────────────────────────────────┘ │
│ ┌ Variáveis ──────────────────────────────────────── Ver a planilha de variáveis de 2026 ──────────┐ │
│ │ Coleção ──────────────────────────────────────────────────────────────────────────────────────── │ │
│ │ ISSN [            ]                                                                              │ │
│ │ Adjetivo pátrio ──────────────────────────────────────────────────────────────────────────────── │ │
│ │ masc. sing. [goiano  ]   fem. sing. [goiana  ]   …                                              │ │
│ │ … Parceiro, Programa, Regional e secretaria, Padrões de desempenho …                            │ │
│ └──────────────────────────────────────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────────────────────────────────┘

Lista:
│  Lista   Cortes   Variáveis                                                                          │
│ [■] Projeto / revista                                  Situação               Ações                  │
│ [✓] Projeto GO  GO  [Comunitária]                      Em edição por Ana: será pulado                │
│      LP (2) Língua Portuguesa                          Em preparo             ↗  ⤓                   │
│      MT ✓  Matemática                                  Pronta para validar    ↗  ⤓                   │
│ ── barra fixa ─────────────────────────────────────────────────────────────────────────────────────── │
│ 1 selecionado(s)                                         [Atribuir matriz…] [Atribuir template…]     │
```

Em 390 px: uma coluna; abas quebram em linha; a tabela da Lista rola dentro da caixa, com a primeira coluna fixa.

### Critérios de aceite

1. A Lista mostra um grupo por projeto, com as revistas, a Situação, preview e zip; o Impresso não vê caixas nem barra, e o POST em massa dá 403.
2. "Atribuir matriz…" com dois parceiros marcados grava os dois e volta com "Matriz <nome> escolhida para 2 parceiro(s)."; projeto em edição é pulado e listado; com revista validada que muda, o modal abre antes.
3. `/ui/lotes/2026/matriz/`, `/ui/revista/2026/`, `/ui/variaveis/2026/` e `/cortes/2026/` redirecionam (302) para a aba equivalente.
4. O projeto abre na aba Dados; as cinco abas existem; `?aba=xyz` vira Dados.
5. Sair de uma variável alterada grava só ela ("Salvo às"); mais de 200 caracteres dá 422 e nada grava.
6. A aba Matriz grava ao escolher, pelo mesmo serviço da ação em massa; matriz de outro ano dá 422.
7. Passo: número sobrescreve, vazio volta ao da matriz, "Sem linhas vazias" grava passo nulo. Cor: a cor do ano apaga a sobrescrita.
8. Impresso vê tudo desligado; enviar é recusado (403). Sem perfil: 403 ao abrir. Anônimo: login das telas B (`/conta/entrar/`).
9. Arquivado: aviso, sem gravar, sem travar; envio recusado mesmo com permissão.
10. Outra pessoa editando: aviso de quem edita; envio com a sessão de outra aba dá 409 e o form vira só leitura.

## Referências técnicas

- Regra: `app/nucleo/projeto.py` (`ProjetoForm`, `MAX_CORES`), usada também por `app/nucleo/admin/projeto.py`; `EDITAVEIS` em `nucleo/variaveis.py`; `servicos/matriz.py` (`atribuir_matriz`); `nucleo/lotes.py` (forms e gravação das ações em massa).
- Cores e nomes efetivos: `servicos/resolver.py` (`valores_das_variaveis`).
- View: `app/nucleo/urls/ui_projeto.py` (rotas `ui_projeto_inicio`, `ui_projeto_lista`, `ui_projeto_massa`, `ui_projeto`, `ui_projeto_campo`, `ui_projeto_matriz`; também monta as rotas `cortes` e `ui_variaveis`).
- Templates: `templates/ui/projeto/{lista,projeto}.html`, `_componentes/projetos_abas.html`, `_componentes/selo_sobrescrita.html`; JS `static/ui/componentes/sobrescrita.js`, `static/ui/telas/lotes.js`; CSS `static/ui/telas/projeto.css`.
- Testes: `app/nucleo/tests/test_ui_projeto.py`, `test_ui_projeto_abas.py`, `test_ui_projetos.py`; `app/e2e/tests/projeto.spec.ts`.
- Decisões: D-053, D-060, D-081, D-091, D-093, D-100, D-102, D-121, D-166, D-167, D-172, D-173, D-175, D-183, D-186 e as do plano de UX (D-195 em diante).
