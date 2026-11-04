# Ficha: Anos e configuração do ano (T03, T05, T06, T07)

Endereços: `/ui/anos/` (rota `ui_anos`: lista e "Abrir ano") e `/ui/anos/<ano>/` (rota `ui_ano`: etapas, componentes e padrões do ano). As duas se abrem pelo seletor de ano do cabeçalho.

## Objetivo

Abrir o ano novo copiando o anterior e manter o que vale para o ano inteiro: as etapas (com a escala), os componentes e os padrões (nome e cor). Matrizes, cortes, projetos e revistas do ano dependem disso.

## Quem usa

| Perfil | O que faz |
|---|---|
| Pedagógica, Mídias Digitais, Admin | Abrem o ano novo; incluem, corrigem e excluem (sem uso) etapas e componentes; corrigem padrões. |
| Admin | Só ele vê "Excluir ano" e apaga o ano inteiro (D-206). |
| Impresso | Vê a lista de anos e a página do ano em texto, sem campos nem botões; não vê "Abrir novo ano". Todo POST recebe 403. |
| Sem login | Vai ao login do admin. |

## Jornada

- **Antes:** a carga inicial cria o primeiro ano. Os seguintes nascem aqui.
- **Aqui:** no cabeçalho, o botão "2026 ▾" abre o seletor. "Abrir novo ano" leva a `/ui/anos/`; "Configurar 2026" leva a `/ui/anos/2026/`.
- **Depois:** com etapas e componentes no lugar, a grade de Cortes ([`cortes.md`](cortes.md)) e as Matrizes passam a ter colunas para o ano.

## Seletor de ano (cabeçalho, todas as telas B)

- Botão "<ano> ▾" com o nome acessível "Ano <ano>: trocar de ano". Abre um popover nativo: Enter ou Espaço abre, Esc fecha e o foco volta ao botão; ao abrir, o foco vai ao ano atual.
- Lista os anos abertos. Cada ano leva à mesma tela no outro ano, mantendo a query (`/painel/2026/?falta=validado` → `/painel/2025/?falta=validado`). Em página de detalhe sem ano na URL, leva ao equivalente do mesmo parceiro no outro ano ou à lista daquele ano. Nunca a um 404.
- Abaixo da linha: "Configurar <ano>" (com `view_ano`) e "Abrir novo ano" (só com `abrir_ano`).
- O ano escolhido fica na sessão: as rotas sem ano (`/ui/matriz/`, `/ui/projeto/`…) abrem nele.
- Nas páginas de Anos, nenhum item do menu fica marcado; o botão do seletor fica destacado (`aria-current`).

## Anos (`/ui/anos/`)

### Dados mostrados

- Tabela com um ano por linha, o mais recente primeiro, e dois links: "Painel de <ano>" e "Etapas e componentes de <ano>".
- Só para o Admin (`delete_ano`, D-206): na última coluna, o botão-ícone (lixeira, `a.btn-icone`) "Excluir ano <ano>", com a dica "Excluir ano". Leva a `/ui/excluir/ano/<ano>/?voltar=/ui/anos/` (rota `ui_excluir`), que lista o que sai junto e pede o ano digitado. Depois: "Ano <ano> apagado, com tudo o que era dele." e a lista sem ele.
- Card "Abrir ano" (só com `abrir_ano`): campo "Ano novo", vazio de propósito, com a dica "Digite o ano. O próximo que pode ser aberto é <maior + 1>."

### Dados gravados

- O ano novo, copiado do maior ano aberto: etapas, componentes, cores e nomes dos padrões, matrizes e templates. Não copia parceiros, cortes nem projetos. Não há desfazer.
- Só abre o ano seguinte ao maior (sem buracos: barra "20277" ou 2028 antes de 2027).

### Estados e mensagens

- **Vazio:** "Nenhum ano aberto" · "O primeiro ano entra pela carga inicial; os seguintes se abrem aqui, copiando o anterior."
- **Sucesso:** "Ano <novo> aberto a partir de <origem>." e a lista recarrega.
- **Recusa (embaixo do campo, nada grava):** "<ano> já está aberto" · "<ano> recusado: o próximo ano que pode ser aberto é <maior + 1>" · "nenhum ano anterior a <ano> para copiar".

## Configurar o ano (`/ui/anos/<ano>/`)

Cabeçalho "Ano <ano>", link "Anos" acima e a frase "Etapas e componentes valem para todas as matrizes, cortes e revistas deste ano." Status do salvamento à direita, para quem grava etapa ou componente. Três cards: Etapas, Componentes e Padrões.

### Etapas

- **Mostra:** código e escala máxima. A ordem é a escolar: todo o fundamental (EF) antes do médio (EM) e, em cada um, pela série (2EF, 5EF, 9EF, 1EM, 3EM). Código fora do padrão vai para o fim. Não há campo de ordem nem arrastar.
- **Grava:** a escala máxima de uma etapa já criada salva sozinha ao sair do campo. O código não muda depois de criado (campo desligado). A escala fica travada quando a etapa já tem corte ou matriz (dica: "Travada: a etapa já tem corte ou matriz.").
- **Linha nova:** "+ Adicionar etapa" abaixo da tabela põe uma linha com o foco no código. "Incluir etapa" (ou Enter) grava; "Descartar" (ou Esc) tira a linha. A etapa nova entra na posição escolar, não no fim.
- **Excluir (D-205):** cada etapa gravada tem, na última coluna, o botão-ícone (lixeira) "Excluir etapa <código>", com a dica "Excluir". É link, não form (a linha está dentro do form da tabela): leva a `/ui/excluir/etapa/<pk>/?voltar=/ui/anos/<ano>/`. Sem uso, sai digitando o código ("Exclusão feita: a etapa <código> de <ano>."); com corte, matriz ou passo de projeto, a página lista o que impede e não apaga.

### Componentes

- **Mostra:** código e nome, na ordem do código.
- **Grava:** o nome de um componente já criado salva sozinho ao sair do campo. O código não muda depois de criado.
- **Linha nova:** "+ Adicionar componente", com "Incluir componente" e "Descartar", como nas etapas.
- **Excluir (D-205):** "Excluir componente <código>", como nas etapas (`/ui/excluir/componente/<pk>/`). Impedem: revista, corte, matriz, passo de projeto e template.

### Padrões (`#padroes`)

- **Mostra:** uma linha por padrão do ano (Padrão 1 a 5): amostra da cor, campo "Nome", seletor de cor com o hexadecimal ao lado e o botão "Salvar" da linha.
- **Grava:** nome e cor do padrão, para todos os projetos do ano que não sobrescrevem no projeto. Aqui **não** há autosave: cada linha grava pelo seu "Salvar", porque mudar nome ou cor pode tirar o "Validado" de muitas revistas. Se tirar, o modal de impacto lista as revistas antes de gravar (Cancelar e Esc voltam o nome e a cor). A mesma cor em outra caixa (`#f72628` × `#F72628`) não conta como mudança.
- **Padrão que falta:** com menos de 5 padrões, "+ Adicionar padrão" abre um formulário com Padrão (só os números livres), Nome e Cor (começa em cinza `#808080`) e o botão "Incluir padrão". Não calcula impacto (o padrão ainda não existia).

### Mensagens exatas

- Etapas/componentes incluídos: "Etapas de <ano> salvas." · "Componentes de <ano> salvos."
- Código repetido: "Já existe a etapa <código> em <ano>." · "Já existe o componente <código> em <ano>." · duas linhas novas iguais: "Código repetido nesta tabela."
- Corrida no banco: "Nada foi salvo: um dos códigos acabou de ser criado por outra pessoa. Confira e salve de novo."
- Padrão salvo: "Padrão <n> de <ano> salvo." Com revistas que perderam o "Validado": "<N> revista(s) perderam o “Validado”: <lista>. Revalide no Painel." (link para `/painel/<ano>/?falta=validado`).
- Padrão novo: "Padrão <n> de <ano> criado." · corrida: "Nada foi salvo: esse padrão acabou de ser criado por outra pessoa."
- Autosave (escala, nome): o status do cabeçalho ("Salvo às HH:MM", "Não salvo: corrija o campo marcado"); com impacto, o modal "Salvar “Escala máxima” de 5EF tira o “Validado” de N revista(s)".

### Estados

- **Ano inexistente:** 404.
- **Só leitura (perfil):** as três tabelas viram texto (código, escala, nome, cor em hexadecimal; padrão sem nome mostra "sem nome"), sem "+ Adicionar", "Salvar" nem "Excluir".
- **Erro na linha nova ou no padrão:** a linha volta com os campos marcados e a lista de erros logo abaixo; nada grava.
- **Bloqueio:** não se aplica. A página não trava nada, como no admin.

## Permissões

- Login obrigatório; anônimo vai ao login do admin.
- `/ui/anos/`: ver exige `view_ano` (403). Abrir exige `abrir_ano`: sem ela o card não aparece e o POST dá 403. "Excluir ano" só com `delete_ano` (só o grupo Admin, D-206).
- `/ui/anos/<ano>/`: ver exige `view_etapa` (403). Etapas: `add_etapa` + `change_etapa`. Componentes: `add_componente` + `change_componente`. Padrões: `change_corpadrao`; padrão novo: `add_corpadrao`. POST de uma tabela sem a permissão dela: 403.
- "Excluir" da linha: etapa com `delete_etapa`, componente com `delete_componente` (Pedagógica, Mídias e Admin; o Impresso não). A página `ui_excluir` confere a mesma permissão (403).
- Autosave (`POST /ui/anos/<ano>/<etapas|componentes>/<pk>/campo/`, rota `ui_ano_campo`): mesma permissão da tabela; tabela fora dessas duas: 404.

## Interações (Alpine e HTMX)

- Etapas e componentes: cada tabela é um `<form x-data="campoAuto">`; a linha gravada leva `data-url` (rota `ui_ano_campo`) e `data-prefixo`. A linha nova leva `data-manual` (fora do autosave) e grava pelo POST da página (`tabela=etapas|componentes`). Componente `linhaNova` com o molde do `empty_form`.
- Padrões: um form comum por linha (`tabela=padroes`, `padrao=<pk>`), com recarga (PRG). O modal é o `_componentes/impacto.html` (U2).
- Abrir ano: form comum (PRG).
- Sem HTMX nestas telas.

## Wireframe (1440 px)

```
┌ Revista Eletrônica  [2026 ▾]  Painel Projetos Matrizes Templates Impresso                  Ana  Admin  Sair ┐
│                     ┌────────────────────┐                                                               │
│                     │ 2026  ←            │                                                               │
│                     │ 2025               │                                                               │
│                     │ ────────────────── │                                                               │
│                     │ Configurar 2026    │                                                               │
│                     │ Abrir novo ano     │                                                               │
│                     └────────────────────┘                                                               │
│ Anos                                                                                                     │
│ Ano 2026                                                              ✓ Salvo às 10:15                   │
│ Etapas e componentes valem para todas as matrizes, cortes e revistas deste ano.                          │
│ ┌ Etapas ─────────────────────────────┐ ┌ Componentes ─────────────────────────┐                         │
│ │ Código   Escala máxima              │ │ Código   Nome                        │                         │
│ │ [5EF]    [500]                  [x] │ │ [LP]     [Língua Portuguesa    ] [x] │                         │
│ │ [9EF]    [500] (travada)        [x] │ │ [MT]     [Matemática           ] [x] │                         │
│ │ [3EM]    [500]                      │ │ [+ Adicionar componente]             │                         │
│ │ [+ Adicionar etapa]                 │ └──────────────────────────────────────┘                         │
│ └─────────────────────────────────────┘                                                                  │
│ ┌ Padrões ───────────────────────────────────────────────────────────────────────────────┐               │
│ │ Padrão      Nome                       Cor                                             │               │
│ │ ■ Padrão 1  [Abaixo do básico     ]    [■] #F72628                         [Salvar]    │               │
│ │ ■ Padrão 2  [Básico               ]    [■] #FFC000                         [Salvar]    │               │
│ │ [+ Adicionar padrão]                                                                    │               │
│ └────────────────────────────────────────────────────────────────────────────────────────┘               │
└──────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

`[x]` é o botão-ícone "Excluir" (lixeira). Em 390 px: os cards empilham; cada tabela rola na horizontal dentro da caixa.

## Critérios de aceite

1. O seletor mostra os anos, "Configurar <ano>" e, só com `abrir_ano`, "Abrir novo ano". Trocar de ano no painel filtrado mantém a tela e o filtro; Esc fecha e devolve o foco.
2. Pedagógica abre o ano seguinte ao maior: "Ano 2027 aberto a partir de 2026."; ano fora de sequência ou já aberto: erro no campo e nada grava.
3. Impresso vê `/ui/anos/` sem o card "Abrir ano"; o POST dá 403.
4. "+ Adicionar etapa" abre a linha com foco; Enter grava; Esc descarta. "1EM" criada depois de "9EF" aparece depois dela; "2EF" aparece antes de "5EF". Não há campo de ordem nem linha vazia no fim.
5. A escala de uma etapa sem corte nem matriz salva sozinha; com corte ou matriz, o campo fica desligado.
6. Código repetido (no banco ou na mesma tabela) mostra o erro e não grava.
7. Padrão: mudar o nome de um padrão usado por revista validada e clicar "Salvar" abre o modal sem gravar; confirmar grava e avisa quem perdeu o "Validado". Salvar sem mudar não mexe na cor.
8. "+ Adicionar padrão" só aparece com menos de 5 padrões e oferece só os números livres.
9. Impresso vê a página do ano só em texto; POST de qualquer tabela dá 403. Ano inexistente: 404.
10. Pedagógica, Mídias e Admin veem "Excluir" em cada etapa e componente gravados (nunca na linha nova); o Impresso não. Componente sem uso sai digitando o código e a página volta ao ano; etapa em uso mostra o que impede.
11. Só o Admin vê "Excluir ano"; Pedagógica, Mídias e Impresso não. O Admin apaga um ano que acabou de abrir digitando o ano.

## Referências técnicas

- Regra: `app/nucleo/servicos/abrir_ano.py` (`abrir_ano`, `AnoRecusado`), `app/nucleo/models/cadastro.py` (`ordem_escolar`, `renumerar_etapas`, `Etapa.save`), `app/nucleo/paleta.py` (`PadraoImpactoForm`, `revistas_afetadas_padrao`), `servicos/impacto.py` (`avisar_perdidos`).
- View: `app/nucleo/urls/ui_anos.py` (`anos`, `ano`, `campo`).
- Seletor: `app/nucleo/contexto.py` (`ano_atual`, `ano_da_sessao`), `templates/ui/_componentes/anos.html`, `static/ui/componentes/seletor-ano.js`.
- Templates: `templates/ui/anos/{anos,ano}.html`, `templates/ui/parciais/ano_linha.html`.
- Excluir: `app/nucleo/urls/ui_excluir.py` (rota `ui_excluir`), `templates/ui/excluir.html`, `servicos/exclusao.py` (`impedimentos`, `excluir`, `resumo_ano`, `apagar_ano`).
- Testes: `app/nucleo/tests/test_ui_anos.py`, `test_ui_base.py`, `test_ui_links.py`, `test_exclusao.py`; `app/e2e/tests/ano.spec.ts`, `anos.spec.ts`, `linhas.spec.ts`, `excluir.spec.ts`.
- Decisões: D-190 (S3, S4, S5), as do plano de UX (D-195 em diante: modal de impacto, linha nova, seletor de ano) e as da exclusão (D-205, D-206; passo E1 de `plans/revista-express-exclusao.md`).
