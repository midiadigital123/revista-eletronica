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
- **Mostra:** um grupo por projeto (ativos primeiro, por parceiro), com o nome do projeto (link), o parceiro em cinza e a matriz (pílula azul, ou "sem matriz" em âmbar). Selos: "Arquivado em dd/mm/aaaa", "Em edição por <nome>: será pulado" (o bloqueio do próprio usuário não conta: o lote o toma, D-191/D-221), "Sem projeto ativo". Abaixo, uma linha por revista: o componente (LP/MT), o balão de pendências ("N pendências" ou ✓), o link para a revista, a Situação ("Em preparo", "Pronta para validar", "Validada", "Impressa" ou "Arquivada") e os botões-ícone "Abrir preview" (nova aba) e "Baixar zip". Parceiro do ano sem projeto aparece com "sem projeto".
- **Ações em massa** (só quem pode): caixa de marcar por parceiro e "Marcar todos os parceiros" no cabeçalho. A barra fixa embaixo mostra "N selecionado(s)", "Atribuir matriz…" e "Atribuir template…"; sem nada marcado, os dois ficam desligados ("Marque ao menos um parceiro").
  - **Atribuir matriz…** abre um modal com o select "Matriz" (só as do ano).
  - **Atribuir template…** abre um modal com "Componente" e "Template F1" / "Template F2" ("Não mudar" deixa como está). Fascículo com texto próprio na revista é pulado e listado.
  - Projeto em edição por outra pessoa é pulado e listado ("Pulados: …"). Se alguma revista validada mudar, o modal de impacto lista as revistas antes de gravar. Ao gravar, volta à Lista com "Matriz <nome> escolhida para N parceiro(s)." / "Template escolhido em N revista(s)."
- **Vazio:** "Nenhum projeto neste ano" · "O projeto do parceiro nasce quando os cortes dele são lançados." · botão "Lançar cortes". Sem ano aberto: "Nenhum ano aberto" com "Abrir anos" (só com `abrir_ano`).
- Não há incluir nem excluir: o projeto nasce e é arquivado pelos cortes.

## Projeto (T16)

### Dados mostrados

- Trilha "Projetos de <ano>" acima do título.
- Cabeçalho: nome do projeto e a lista Parceiro, Ano, Matriz ("ainda não escolhida"), Revistas (LP, MT), Situação (Ativo ou o selo "Arquivado"). O status do salvamento fica à direita, para quem grava.
- Abas (a aba é a URL, `?aba=`; aba desconhecida vira Dados):
  - **Dados:** "Nome do projeto" (aparece na capa e em `{{nome_projeto}}`) e as 24 variáveis manuais, nos grupos Coleção, Adjetivo pátrio, Parceiro, Programa, Regional e secretaria, Padrões de desempenho. Cada campo tem o rótulo, a descrição e o marcador (`{{issn}}`). As 3 automáticas (nome do parceiro, nome do projeto, ano) não aparecem. Link "Ver a planilha de variáveis de <ano>".
  - **Matriz:** select "Matriz de <parceiro> em <ano>" com as matrizes do ano, a dica para usar "Atribuir matriz…" na Lista e o passo de cada etapa × componente na matriz ("5EF LP: 25"). Abaixo, o cartão "Etapas do projeto" (seção própria, mais abaixo): uma linha por corte do parceiro, dizendo se a etapa usa a matriz ou é cópia do projeto (com a base).
  - **Cortes:** a linha deste parceiro da grade de Cortes, um bloco por etapa ("5EF até 500") com os componentes lado a lado, e o link "Ver a grade de cortes de <ano>".
  - **Passos e cores:** as amostras dos padrões (cor e nome efetivos, selo "do ano" ou "sobrescrita") e, por etapa, uma célula por componente com o passo ("Matriz: 25", "fora da matriz" ou "sem linhas vazias") e o selo "da matriz" ou "sobrescrito". Link "Editar as cores do ano" (com `change_corpadrao`). O nome do padrão se troca nas variáveis pd01 a pd05, na aba Dados.
  - **Revistas:** um cartão por componente com Template F1 e F2 (ou "sem template") e Capa (✓ ou falta), o selo "Validada", "Sem “Validado”" ou "Arquivada", e os botões "Abrir revista" e "Preview".

### Cartão "Etapas do projeto" (aba Matriz; D-276, D-286 a D-289, D-292)

Uma linha por etapa × componente com corte do parceiro, nos componentes das revistas ativas. O cartão não aparece sem cortes. Descrição do cartão: "Cada etapa usa a matriz até alguém escolher “Editar só neste projeto”: aí o projeto ganha uma cópia, e o que for editado nela não muda a matriz nem os outros projetos. Se a matriz mudar depois, o projeto revisa as mudanças. Etapa fora de 2EF, 5EF, 9EF e 3EM parte de uma etapa canônica de qualquer matriz."

| Estado da linha | O que mostra | Ações (com o bloqueio da ficha e permissão de gravar) |
|---|---|---|
| A matriz tem a etapa e o projeto não tem cópia | "· usa a matriz <nome>" | botão "Editar só neste projeto": cria a cópia e abre o editor nela |
| O projeto tem cópia | "· cópia do projeto · base: <etapa> <componente> da <matriz (ano)>", ou "sem base (a base foi apagada)" | "Editar" ("Ver" para quem não grava): abre o editor da cópia (`ui_matriz_mec`); "Desfazer a cópia" (a matriz tem a etapa) ou "Desfazer apontamento" (etapa não canônica) |
| Cópia cuja base mudou sem revisão | o mesmo, mais o selo "A base mudou" | "Revisar mudanças da base" (`/ui/revisao/<pk>/`), para todo perfil; some depois de "Concluir revisão" |
| Etapa não canônica sem cópia | select "Escolha a etapa canônica" (etapas 2EF, 5EF, 9EF e 3EM do mesmo componente, agrupadas por matriz, de qualquer ano) | botão "Apontar": cria a cópia a partir da base escolhida. Sem bloqueio ou permissão: "· sem base". Sem nenhuma base possível: "· sem base: nenhuma matriz tem etapa canônica de <componente>" |
| Etapa canônica que a matriz não tem | "· a matriz não tem esta etapa" | nenhuma: corrige-se na matriz (pendência `corte_sem_matriz`) |

- "Editar só neste projeto" e "Apontar" usam a mesma rota (`ui_projeto_etapa_apontar`, POST, form nativo por linha, sem JS); a regra fica em `servicos/etapa_projeto.py::criar`. Se a gravação tira o "Validado" de alguma revista, nada grava e a aba reabre com o modal de impacto daquela linha; confirmar reenvia e grava.
- Quando o projeto tem a cópia, a revista usa a cópia; sem ela, a etapa da matriz. Não há escolha entre as duas: voltar à matriz é desfazer a cópia (D-288).
- **Desfazer** (`ui_projeto_etapa_desfazer`, página própria, D-287): confirmação forte, digitando a etapa e o componente ("5EF LP"). A página diz quantos descritores e tarefas saem e lista as revistas ativas do componente, marcando as que perdem o "Validado". Título e botão: "Desfazer a cópia" quando a matriz tem a etapa (a revista volta a usar a etapa da matriz); "Desfazer o apontamento" na etapa não canônica (a etapa volta a ficar sem base, pronta para ser apontada de novo). Vale mesmo com a cópia já editada. É recusado se outra pessoa está com a etapa aberta no editor.

### Dados gravados (um campo por vez)

- Nome do projeto e as 24 variáveis (até 200 caracteres cada).
- Matriz do parceiro no ano: pelo mesmo serviço da ação em massa (`servicos.matriz.atribuir_matriz`).
- Cortes: pela rota da grade (`cortes_celula`), com o mesmo conflito otimista.
- Passo por etapa × componente: um número sobrescreve; vazio (ou "Voltar ao passo da matriz") volta ao da matriz; "Sem linhas vazias" grava a linha com passo nulo, de propósito.
- Cor por padrão: a cor escolhida sobrescreve a do ano; escolher a própria cor do ano (ou "Voltar à cor do ano") apaga a sobrescrita. Só a caixa diferente (`#f72628` × `#F72628`) não é mudança.
- Etapa do projeto: a cópia (etapa × componente, descritores e tarefas, com a base e a foto dela) nasce em "Editar só neste projeto" ou "Apontar" e é apagada inteira em "Desfazer"; o conteúdo dela se edita no editor da matriz (ficha [`matriz.md`](matriz.md)).
- Qualquer gravação que mude o texto de uma revista validada abre o modal de impacto antes de gravar.

### Ações

| Ação | Quem | Resultado |
|---|---|---|
| Sair de um campo alterado (Dados, Cortes, passo) | quem edita, com o bloqueio | grava só o campo; o status mostra "Salvo às HH:MM" |
| Escolher a matriz / uma cor | quem edita, com o bloqueio | grava ao escolher |
| "Voltar ao passo da matriz" / "Voltar à cor do ano" | quem edita | apaga a sobrescrita daquela célula ou padrão |
| "Sem linhas vazias" | quem edita | marca a célula como sem linhas vazias (desliga o número) |
| "Editar só neste projeto" (aba Matriz, etapa que a matriz tem) | quem edita, com o bloqueio | cria a cópia e abre o editor nela, com "<etapa> <componente>: cópia criada. O que for editado aqui vale só para <projeto>." |
| Escolher a base e "Apontar" (aba Matriz, etapa não canônica) | quem edita, com o bloqueio | cria a cópia e volta à aba Matriz com "<etapa> <componente> apontada para <etapa da base> de <matriz>." |
| "Editar" / "Ver" (linha da cópia) | todos | abre a cópia no editor da matriz; o voltar do editor traz de volta à aba Matriz |
| "Desfazer a cópia" / "Desfazer apontamento" (linha da cópia) | quem edita, com o bloqueio | página de confirmação forte; ao confirmar, apaga a cópia e volta à aba Matriz com "Cópia de <etapa> <componente> desfeita." ou "Apontamento de <etapa> <componente> desfeito." |
| "Revisar mudanças da base" (aba Matriz, só com a base mudada) | todos abrem; conclui quem edita matriz, com o bloqueio da etapa | abre `/ui/revisao/<pk>/`; "Concluir revisão" grava as escolhas e volta à aba Matriz com "Revisão de <etapa> concluída: …" |
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
- **Sem conexão:** "Não salvo: sem conexão · Tentar de novo"; só aí (ou com envio pendente) o navegador avisa ao fechar, recarregar ou voltar. Clicar num link ou botão que sai da página com campo alterado em foco, falha ou envio pendente abre o diálogo "Alterações não salvas" (Salvar e sair, Descartar e sair, Continuar editando; D-223, [`design-system.md`](../design-system.md) §5).

### Mensagens exatas

- Sem permissão: "Só leitura: seu perfil vê o projeto, mas não altera. Para editar, peça a permissão de projeto a um administrador."
- Arquivado: "Só leitura: este projeto foi arquivado e as revistas dele estão congeladas. Para mudar algo, abra o projeto ativo do parceiro."
- Outra pessoa editando: "Somente leitura: {quem} está editando (bloqueio até {hh:mm:ss}, renovado enquanto a página estiver aberta). Recarregue para tentar editar."
- Bloqueio perdido ao salvar: "Não salvo: você perdeu o bloqueio de edição (outra pessoa ou aba abriu esta página). Recarregue e refaça a alteração."
- Bloqueio perdido durante a edição: "Você perdeu o bloqueio de edição: o formulário ficou somente leitura. Copie o que precisar e recarregue a página."
- Matriz de outro ano: "Escolha uma matriz de <ano>."
- Apontar sem base válida: "Não apontado: escolha a base."
- Desfazer com a etapa aberta por outra pessoa: "Não desfeito: {quem} está editando esta etapa. Tente de novo quando a pessoa fechar o editor." Na página de desfazer: "Confira acima o que sai: desfazer não se desfaz pela tela."
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
11. A aba Matriz mostra "A base mudou" e "Revisar mudanças da base" só na cópia cuja base mudou; depois de concluir a revisão, os dois somem.
12. Revisão (regras em [`regras-de-negocio.md`](../../regras-de-negocio.md), "Revisão da base da etapa do projeto"): decisões abertas e sem marca, o resto recolhido com "Usar o da base"; concluir grava e volta à aba Matriz; base mudada com a tela aberta dá 409 e nada grava; Impresso e projeto arquivado veem só leitura (POST 403); etapa da matriz e cópia solta dão 404.
13. "Editar só neste projeto" cria a cópia e abre o editor nela; editar a cópia não muda a matriz nem a revista de outro projeto. Com revista validada que muda, o modal de impacto abre antes de gravar.
14. Etapa não canônica: sem base escolhida, nada é apontado; com a base, a linha passa a "cópia do projeto · base: …". Etapa canônica que a matriz não tem não ganha botão.
15. Desfazer pede a etapa e o componente digitados; texto errado não desfaz; certo apaga a cópia e a linha volta a "usa a matriz" (cópia local) ou ao select de base (não canônica). O Impresso não vê o link e o POST dele dá 403.

## Referências técnicas

- Regra: `app/nucleo/projeto.py` (`ProjetoForm`, `MAX_CORES`), usada também por `app/nucleo/admin/projeto.py`; `EDITAVEIS` em `nucleo/variaveis.py`; `servicos/matriz.py` (`atribuir_matriz`); `nucleo/lotes.py` (forms e gravação das ações em massa).
- Cores e nomes efetivos: `servicos/resolver.py` (`valores_das_variaveis`).
- View: `app/nucleo/urls/ui_projeto.py` (rotas `ui_projeto_inicio`, `ui_projeto_lista`, `ui_projeto_massa`, `ui_projeto`, `ui_projeto_campo`, `ui_projeto_matriz`, `ui_projeto_etapa_apontar`, `ui_projeto_etapa_desfazer`; também monta as rotas `cortes` e `ui_variaveis`). Etapa do projeto: `servicos/etapa_projeto.py` (`criar`, `desfazer`, `pendente`, `vigente`), `templates/ui/projeto/desfazer_etapa.html`. Revisão: `app/nucleo/urls/ui_revisao.py` (rotas `ui_revisao`, `ui_revisao_arquivo`), `templates/ui/projeto/revisar_etapa.html` e `parciais/revisao_{cartao,lado}.html`, CSS `static/ui/telas/revisao.css`, testes em `test_ui_revisao.py`.
- Templates: `templates/ui/projeto/{lista,projeto}.html`, `_componentes/projetos_abas.html`, `_componentes/selo_sobrescrita.html`; JS `static/ui/componentes/sobrescrita.js`, `static/ui/telas/lotes.js`; CSS `static/ui/telas/projeto.css`.
- Testes: `app/nucleo/tests/test_ui_projeto.py`, `test_ui_projeto_abas.py`, `test_ui_projetos.py`; `test_etapa_projeto.py`; `app/e2e/tests/projeto.spec.ts`, `etapa-projeto.spec.ts`.
- Decisões: D-053, D-060, D-081, D-091, D-093, D-100, D-102, D-121, D-166, D-167, D-172, D-173, D-175, D-183, D-186, as do plano de UX (D-195 em diante), D-221 e as da etapa do projeto (D-276, D-279 a D-289, D-292).
