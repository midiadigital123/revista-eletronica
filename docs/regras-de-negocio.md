# Regras de negócio vigentes — revista-express

Data: 2026-11-05. Branch de referência: `feat/telas-b-ux` (`2dc2825`).

Este documento lista **só a regra que vale hoje** no sistema Django (`app/nucleo`) que gera as revistas de resultados (fascículos F1 e F2) por parceiro e ano. Não conta a história do projeto. Detalhes de tabelas, variáveis e telas ficam nos documentos linkados.

## Como ler

- Cada regra é uma linha curta, com a fonte entre parênteses.
- `D-xxx` = decisão vigente no `state.md`. Decisão substituída não aparece; aparece a que a substituiu.
- `arquivo:linha` = onde o código garante a regra (caminho a partir da raiz do repositório).
- `learning` = arquivo em `.trail/learnings/` (citado pelo assunto).
- Quando decisão e código divergem, **vale o código**, e a divergência está na seção 10.
- **[não implementado]** marca regra decidida que o código ainda não cumpre.

Documentos que este texto não repete:

| Assunto | Documento |
|---|---|
| Tabelas, FKs compostas, restrições do banco | [`docs/modelo-er.md`](modelo-er.md) |
| Lista e uso das variáveis dos templates | [`docs/variaveis.md`](variaveis.md) |
| Formato da revista impressa (InDesign) | [`docs/design-revista-impressa.md`](design-revista-impressa.md) |
| Telas fora do admin e o que ainda é só admin | [`docs/telas/telas-b.md`](telas/telas-b.md), fichas em [`docs/telas/fichas/`](telas/fichas/) |
| Padrões visuais e protocolo de autosave | [`docs/telas/design-system.md`](telas/design-system.md) |
| Contrato do sistema antigo (Node/Mongo, aposentado) | [`docs/contrato.md`](contrato.md) |

## Índice

1. [Glossário](#1-glossário)
2. [Ciclo do ano](#2-ciclo-do-ano)
3. [Parceiros, projetos e matriz](#3-parceiros-projetos-e-matriz)
4. [Cortes e padrões](#4-cortes-e-padrões)
5. [Templates, textos e variáveis](#5-templates-textos-e-variáveis)
6. [Revista: ciclo de vida, Validado e impresso](#6-revista-ciclo-de-vida-validado-e-impresso)
7. [Edição concorrente](#7-edição-concorrente)
8. [Perfis e permissões](#8-perfis-e-permissões)
9. [Exclusão](#9-exclusão)
10. [Divergências e pontos em aberto](#10-divergências-e-pontos-em-aberto)

---

## 1. Glossário

| Termo | Significado no sistema | Fonte |
|---|---|---|
| **Ano** | Edição anual (ex.: 2026). Quase todo cadastro pertence a um ano; nada de um ano é sobrescrito pelo seguinte. | D-046, `app/nucleo/models/cadastro.py:11` |
| **Parceiro** | Rede avaliada: estado (GO, SE) ou município (JOINVILLE, SALVADOR). Cadastro **global**, sem ano e sem hierarquia UF → cidade. Nome único. | D-047, `app/nucleo/models/cadastro.py:23` |
| **Parceiro_ano** | O parceiro dentro de um ano. Guarda a **matriz** escolhida (nula até alguém escolher). Um por parceiro × ano. | D-088, D-106, `app/nucleo/models/projeto.py:16` |
| **Projeto** | O trabalho de um parceiro_ano: nome e valores das variáveis. Nasce pela cascata dos cortes. No máximo um **ativo** por parceiro_ano. | D-052, D-061, `app/nucleo/models/projeto.py:66` |
| **Matriz** | Conjunto de descritores e tarefas de um ano. Nome único no ano. | D-057, `app/nucleo/models/matriz.py:11` |
| **Matriz comunitária × própria** | Convenção de uso, não um campo: a "Comunitária" (base SAEGO) serve à maioria dos parceiros; uma matriz própria (CE, ES, JOINVILLE…) nasce duplicando outra e não tem relação de herança com ela. | D-048, D-101, D-113 |
| **MEC** | **M**atriz × **E**tapa × **C**omponente (`MatrizEtapaCC`). Unidade de importação, de bloqueio e do intervalo mínimo. Não é o Ministério. | D-091, `app/nucleo/models/matriz.py:42` |
| **Descritor** | Habilidade avaliada (D01, D02…) dentro de uma MEC, com descrição, pré-requisitos e campos BNCC. Código único na MEC. | `app/nucleo/models/matriz.py:63` |
| **Tarefa** | Linha da escala de um descritor: intervalo `[início, fim)` com texto; pode ter arquivo do item (PDF/PNG/JPG) e texto alternativo. Código nas telas: `D01 100-150`. | D-180, D-181, `app/nucleo/models/matriz.py:88` |
| **Etapa** | Série avaliada no ano (2EF, 5EF, 9EF, 3EM), com `escala_max`. A ordem é derivada do código (EF antes de EM, depois a série). | D-086, `app/nucleo/models/cadastro.py:38-54` |
| **Componente** | Componente curricular do ano (LP, MT). Cada componente com corte gera uma revista. | D-086, D-095 |
| **Padrão / cores** | Faixa de desempenho entre dois cortes. n cortes geram n + 1 padrões (2 a 5). Cada padrão tem cor e nome por ano (`CorPadrao`), com sobrescrita por projeto. | D-050, D-064, D-175 |
| **Corte** | Lista de 1 a 4 valores do parceiro_ano × etapa × componente. A existência do corte diz que o parceiro avalia aquela etapa × componente. | D-049, D-055, `app/nucleo/models/projeto.py:33` |
| **Template e versão** | Texto-modelo por ano × componente × fascículo, guardado em versões numeradas só de inserção. A versão atual é a de maior número. | D-098, D-125, `app/nucleo/models/texto.py:22` |
| **Revista** | Projeto × componente (ex.: GO · LP). Unidade do Validado, da foto do impresso e do zip. | D-095, D-097, `app/nucleo/models/revista.py:25` |
| **Fascículo** | Parte da revista: F1 (escalas e textos) e F2 (infográfico em SVG com tour e modais). Lista fixa no código. | D-122, `app/nucleo/models/texto.py:11` |
| **Seção** | Bloco `## id` do template. F1: `introducao` e `fechamento`. F2: as 9 de `texto.SECOES["F2"]` (`abertura`, `passo-*`, `dlg-*`, `tarefas-fechamento`, `fechamento`). A 1ª linha de cada seção é o título. Uma seção editada vira cópia da revista (`RevistaSecao`). | D-111, D-114, D-115, D-139 |
| **Foto** | JSON da revista montada, gravado com o hash. Motivos: `impresso` (clique do Impresso) e `arquivamento`. | D-077, D-151, `app/nucleo/models/revista.py:109` |
| **Validado** | Clique da Pedagógica que grava o hash da revista vista. "Está validada" = hash gravado igual ao hash atual, calculado na hora. | D-074, D-084, `app/nucleo/servicos/validacao.py:20` |
| **Impresso / "Revista Impressa Atualizada"** | Clique do perfil Impresso que grava a foto `impresso` e zera "o que mudou" daquela revista. | D-072, D-077, `app/nucleo/servicos/validacao.py:54` |
| **Intervalo mínimo (passo)** | Distância entre os níveis da régua; gera as linhas vazias. Um campo só, chamado `passo`. | D-091, D-155 |
| **Pendência** | Motivo que bloqueia o Validado (falta matriz, template, SVG, capa, variável…). | D-112, `app/nucleo/servicos/resolver.py:335` |

---

## 2. Ciclo do ano

### 2.1 Abrir ano

| Regra | Fonte |
|---|---|
| Só se abre o ano seguinte ao maior existente (2026 → 2027). Ano repetido, ano com buraco ou sem ano anterior é recusado. | D-148, D-149, `app/nucleo/servicos/abrir_ano.py:60` |
| O primeiro ano não se abre pela tela: entra pela carga inicial (comandos). | learning "Tela nova não importa nada do admin", `app/nucleo/servicos/abrir_ano.py:63` |
| Abrir ano não tem desfazer: a pessoa digita o ano, sem valor sugerido no campo. | D-165, D-190 |
| Tudo numa transação: se falhar no meio, nada fica. A leitura da origem é um retrato só (REPEATABLE READ). | D-125, D-149, `app/nucleo/servicos/abrir_ano.py:51` |
| Quem abre: quem tem `abrir_ano` (Admin, Pedagógica, Mídias Digitais). Tela: `/ui/anos/`. | D-079, D-192, `app/nucleo/urls/ui_anos.py:40` |

### 2.2 O que o ano novo copia do anterior

| Copiado | Não copiado (nasce em branco) |
|---|---|
| Etapas (com `escala_max`) e componentes | Parceiro_ano (a escolha de matriz) |
| Padrões do ano: cor **e** nome | Cortes |
| Matrizes, com MECs (inclusive `passo`), descritores e tarefas | Projetos, nomes de projeto, valores das variáveis |
| Templates, com a **última** versão virando a versão 1 | Template escolhido em cada fascículo, cópias de seção |
| Caminho do arquivo do item (o mesmo arquivo nos dois anos) | Sobrescritas de passo e de cor do projeto, SVG, capa, fotos |

Fontes: D-119, D-106, D-085, D-150, D-175, `app/nucleo/servicos/abrir_ano.py:85-106`.

- Cada matriz copiada aponta `duplicada_de` para a matriz de mesmo nome no ano anterior, só para consulta (D-113, D-148, `app/nucleo/servicos/abrir_ano.py:89`).
- Parceiro é global: não precisa ser recriado no ano novo (`app/nucleo/models/cadastro.py:23`).
- No ano novo, nenhuma revista pode ser validada até alguém escolher matriz e templates; nada é atribuído automaticamente (D-106, learning "No ano novo, matriz e template de texto nascem sem escolha").
- Os cortes do ano novo são digitados de novo na grade, sem sugestão do ano anterior (D-119, D-184).
- Variáveis: o botão "Copiar valores do ano anterior" é manual, por projeto, e só preenche as variáveis **vazias** com as do projeto do mesmo parceiro no ano anterior, mesmo arquivado (D-107, `app/nucleo/planilha_variaveis.py:40-62`).

### 2.3 Histórico: nada se perde entre anos

| Regra | Fonte |
|---|---|
| Dados por ano; abrir um ano nunca altera o anterior. | D-046, learning "O banco guarda o histórico de cada ano" |
| Coerência de ano é garantida pelo banco: FK composta impede corte de 2027 com etapa de 2026. | D-090, D-124, learning "Regras que o banco precisa garantir" |
| Toda tabela de negócio tem histórico por registro (django-simple-history), exceto `TemplateVersao` (só inserção, já é o histórico) e `Bloqueio` (efêmero). | D-082, D-093, `app/nucleo/models/texto.py:49`, `app/nucleo/models/controle.py:15` |
| Versões de template só aceitam INSERT: um trigger no banco recusa sempre o UPDATE e recusa o DELETE, exceto na exclusão de template sem uso e no apagar do ano (seção 9). | D-133, D-207, `app/nucleo/migrations/0006_template_versao_so_insert.py:24`, `app/nucleo/migrations/0017_versao_apagavel.py` |
| Quase todas as FKs são PROTECT: apagar algo em uso é recusado pelo banco, não cascateia. | D-129, D-205 |

---

## 3. Parceiros, projetos e matriz

### 3.1 Parceiro

| Regra | Fonte |
|---|---|
| Cidade com projeto próprio é parceiro separado do estado, com matriz e cortes independentes. | D-047, learning "Cidade com projeto próprio é parceiro separado" |
| Criar parceiro: "Nova linha" na aba Cortes de Projetos (`add_parceiro`). O parceiro nasce sem cortes e sem projeto. | D-189, `app/nucleo/urls/cortes.py:51` |
| Renomear parceiro: na aba Cortes (`change_parceiro`). Muda `{{nome_parceiro}}` e o nome inicial do projeto; se tirar o Validado, abre o modal de impacto. | D-202, `app/nucleo/urls/cortes.py:64` |

### 3.2 Projeto

| Regra | Fonte |
|---|---|
| Projeto não herda de outro projeto: só aponta para uma matriz (pelo parceiro_ano). | D-051, learning "Projeto não herda de outro projeto" |
| Nasce sozinho quando o parceiro_ano recebe o primeiro corte; ninguém cria projeto à mão. | D-061, `app/nucleo/servicos/cascata.py:79-84`, `app/nucleo/admin/projeto.py:64` |
| Nome inicial: `<nome do parceiro> - NOME DO PROJETO`. Enquanto o nome terminar assim, o Validado fica bloqueado. | D-065, D-093, `app/nucleo/servicos/cascata.py:83`, `app/nucleo/servicos/resolver.py:381` |
| Um projeto **ativo** por parceiro_ano (restrição do banco). | D-047, `app/nucleo/models/projeto.py:102-105` |
| O projeto guarda: nome, valores das variáveis, sobrescrita de passo por etapa × componente e sobrescrita de cor por padrão. | D-052, D-053, D-060, D-100, `app/nucleo/models/projeto.py:66` |

### 3.3 Arquivamento de projeto

| Regra | Fonte |
|---|---|
| Revista sem corte do seu componente é arquivada; o projeto é arquivado quando todas as revistas dele estão arquivadas (todos os cortes apagados). | D-065, D-117, `app/nucleo/servicos/cascata.py:86-89` |
| Arquivar é sempre efeito da cascata; não há botão "arquivar projeto". | `app/nucleo/admin/projeto.py:67` |
| Projeto arquivado não volta: se o parceiro recebe cortes de novo no mesmo ano, nasce outro projeto com o nome inicial. | D-068, `app/nucleo/servicos/cascata.py:81` |
| As revistas do projeto novo herdam a última foto `impresso` do mesmo componente nos projetos arquivados do mesmo parceiro_ano (`herdada = true`). | D-094, D-135, `app/nucleo/servicos/cascata.py:135-149` |
| Projeto ou revista arquivados ficam congelados: lotes, planilha de variáveis e "Copiar" pulam; o admin abre só leitura. | D-093, D-167, `app/nucleo/lotes.py:39-56`, `app/nucleo/admin/projeto.py:70` |

### 3.4 Matriz

| Regra | Fonte |
|---|---|
| A matriz é escolha do **parceiro_ano** e vale para todos os componentes dele. | D-088, D-101, `app/nucleo/models/projeto.py:19` |
| Escolher matriz: aba Matriz do projeto ou "Atribuir matriz…" em massa na Lista (`change_parceiroano`). Modal se tirar o Validado. | D-102, D-197, `app/nucleo/servicos/matriz.py:18`, `app/nucleo/lotes.py:135` |
| Projeto não edita conteúdo: todo ajuste de descritor ou tarefa é feito na matriz e vale para todos os parceiros que a usam. | D-048, D-051, D-099 |
| Exceção nova (ex.: parceiro que mudou no ano): duplicar uma matriz, ajustar a cópia e apontar o parceiro para ela. | D-101, `app/nucleo/urls/ui_matriz.py:162` |
| A cópia guarda a origem (`duplicada_de`, de qualquer ano) e mostra a tabela de diferenças; não herda nada. Apagar a origem só zera o vínculo. | D-113, D-124, `app/nucleo/models/matriz.py:17-24`, `app/nucleo/urls/ui_matriz.py:211` |
| Matriz nova nasce vazia pela tela B ("Nova matriz": ano + nome, exige `add_matriz`) e recebe o conteúdo pelo Reimportar (PDF SAEGO ou XLSX); também nasce por duplicação ou pelo comando `importar_matriz`. MEC nova só nasce por importação ou duplicação. | D-141, D-165, D-210, `app/nucleo/urls/ui_matriz.py` (`nova`) |
| Reimportar substitui só as MECs presentes no arquivo: mantém a linha da MEC (id, histórico e trava), apaga e recria descritores e tarefas. Exige digitar o nome exato da matriz. | D-071, D-141, D-146, D-165, `app/nucleo/servicos/importar_matriz.py:41` |
| Reimportar é recusado se alguém está editando uma das MECs, se a escala máxima do arquivo difere de `Etapa.escala_max` ou se o arquivo passa de 20 MB / não é PDF nem XLSX. | D-146, D-168, `app/nucleo/matriz.py:94-111` |
| A importação descarta os cortes impressos no PDF: o padrão de cada tarefa vem dos cortes do parceiro. | D-059 |
| Linhas "---" do PDF não viram tarefa; as linhas vazias vêm do `passo`. | D-141, D-155 |
| Toda edição da matriz mostra quantas revistas ativas ela afeta (e quais perdem o Validado) antes de gravar. | D-076, D-202, `app/nucleo/servicos/matriz.py:131-157` |
| Revista afetada por uma MEC = revista ativa do componente, cujo parceiro_ano usa a matriz e tem corte naquela etapa × componente. | `app/nucleo/servicos/matriz.py:146` |
| Arquivo do item é da matriz (aparece em toda revista que a usa): PDF, PNG ou JPG até 5 MB, tipo conferido pelos bytes; texto alternativo opcional. | D-180, D-185, `app/nucleo/servicos/arquivos.py:29`, `app/nucleo/matriz.py` (`ItemForm`) |
| Descritor novo, edição de campos e reordenação de descritores e tarefas são pela tela da MEC; a ordem entra na revista (impacto). | `app/nucleo/urls/ui_matriz.py:425`, `app/nucleo/urls/ui_matriz.py:505` |

---

## 4. Cortes e padrões

### 4.1 Validação dos cortes

| Regra | Fonte |
|---|---|
| De 1 a 4 cortes por parceiro_ano × etapa × componente (2 a 5 padrões). | D-050, D-055, `app/nucleo/servicos/cascata.py:31`, CHECK `corte_valores_1a4` em `app/nucleo/models/projeto.py:53` |
| Inteiros, estritamente crescentes. | D-055, `app/nucleo/servicos/cascata.py:33-37` |
| Cada corte estritamente dentro da escala: `0 < corte < escala_max` da etapa. Corte igual a 0 ou ao máximo é recusado. | D-153, `app/nucleo/servicos/cascata.py:38` |
| Escala de 2026: 2EF vai a 1000; 5EF, 9EF e 3EM vão a 500 (valor da etapa, editável no ano). | D-055, D-141, `app/nucleo/management/commands/carregar_cadastros.py:6` |
| `escala_max` fica só leitura quando a etapa já tem corte ou MEC. | D-168, D-193 |
| Etapa e componente precisam ser do ano do parceiro_ano; linha repetida é recusada. | D-090, `app/nucleo/servicos/cascata.py:26-30` |
| Todos os erros de uma gravação aparecem juntos; um erro, nada grava. | D-135, `app/nucleo/cortes.py:1-7` |
| Não há "intervalo mínimo entre cortes": a regra é só "crescente". O intervalo mínimo (passo) é da régua, não dos cortes. | D-055, D-091 |

### 4.2 Grade de cortes

| Regra | Fonte |
|---|---|
| Cortes são cadastrados no sistema (fonte da verdade); não há importação da planilha de cortes. A planilha de grupos é só exportada. | D-049, D-184 |
| Grade = parceiros × (etapa × componente) do ano. Digitar cria, mudar edita, esvaziar a célula apaga o corte. | D-188, `app/nucleo/cortes.py` |
| Cada célula grava sozinha (autosave). Sem bloqueio de página: conflito otimista pelo valor original (409 se outra pessoa mudou). | D-196, learning "Telas B usam Alpine…", `app/nucleo/urls/cortes.py:106` |
| Quem edita: Admin, Pedagógica e Mídias Digitais (`add_corte` + `change_corte`). Impresso só vê (POST 403). | D-188 |
| Grupo de corte é calculado: por aba etapa × componente, listas de cortes distintas ordenadas corte a corte e numeradas a partir de 1. | D-049, D-056 |

### 4.3 Cascata (cortes → projeto → revistas)

| Regra | Fonte |
|---|---|
| Gravar cortes substitui **todos** os cortes do parceiro_ano pela lista enviada e roda a cascata numa transação só. | D-135, `app/nucleo/servicos/cascata.py:44` |
| Duas cascatas do mesmo parceiro_ano não rodam ao mesmo tempo (trava na linha do parceiro_ano). | D-125, D-138, `app/nucleo/servicos/cascata.py:54-60` |
| Primeiro corte → projeto novo (se não houver ativo). Componente novo → revista nova com F1 e F2. | D-061, D-095, `app/nucleo/servicos/cascata.py:91-97` |
| Componente que perdeu todos os cortes → revista arquivada, com foto de arquivamento tirada antes de apagar os cortes. | D-117, D-138, `app/nucleo/servicos/cascata.py:61-77` |
| Componente que volta no mesmo ano → a **mesma** revista é reativada (SVG, capa, cópias e fotos mantidos). | D-117, `app/nucleo/servicos/cascata.py:96` |
| Etapa sem corte some da revista; etapa com corte entra. | D-065, `app/nucleo/servicos/resolver.py:130` |

### 4.4 Padrões, cores e régua

| Regra | Fonte |
|---|---|
| Com n padrões, a revista usa as cores 1..n. Cor do ano em `CorPadrao` (5 por ano); `ProjetoCor` sobrescreve. | D-060, D-064, `app/nucleo/servicos/resolver.py:188` |
| Cores de 2026: `#F72628`, `#FF8D43`, `#B3CCFF`, `#0ED3FF` e `#FFFFFF` (5º provisório). | D-064, D-141 |
| Nome do padrão: `CorPadrao.nome` do ano ("Padrão 01" … "Padrão 05"); `pd01`..`pd05` do projeto sobrescrevem quando preenchidos. Pendência só se os dois estiverem vazios. | D-175, `app/nucleo/servicos/resolver.py:122`, `app/nucleo/servicos/resolver.py:229-240` |
| Mudar cor ou nome do padrão do ano muda o hash das revistas que não sobrescrevem aquele padrão; se alguma perder o Validado, abre o modal. | D-177, D-194, D-202, `app/nucleo/paleta.py:19` |
| Mesma cor com outra caixa (`#B3CCFF` × `#b3ccff`) não conta como mudança. | D-194, learning "Seletor de cor do navegador manda a cor em minúsculas" |
| Tarefa vai para o padrão da **âncora maior**: `1 + nº de cortes < fim`. O topo é aberto: 390→446 com corte 400 é P03; 350→400 continua P02. Vale para corte em qualquer valor. | D-044, D-058, `app/nucleo/servicos/resolver.py:78` |
| Linha vazia de um nível igual a um corte pertence ao padrão de cima. | D-151, `app/nucleo/servicos/resolver.py:83` |
| Passo efetivo: o do projeto, se houver sobrescrita (passo nulo nela = "sem linhas vazias", de propósito); senão o da MEC; nulo na MEC = sem linhas vazias. | D-053, D-091, `app/nucleo/servicos/resolver.py:147-164` |
| Todo nível `0 + k·passo < máximo` sem tarefa começando nele vira linha vazia, mesmo dentro de uma tarefa mais larga. | D-155, `app/nucleo/servicos/resolver.py:93` |
| Leitura cumulativa: quem alcança uma habilidade domina todas as de baixo (o destaque da revista vai para as linhas abaixo). | D-035, learning "Ao passar o mouse numa habilidade" |
| Número destacado da régua: preto ou branco pela maior razão de contraste WCAG 2 (com as cores atuais, sempre preto). | D-158 |

---

## 5. Templates, textos e variáveis

### 5.1 Template e versões

| Regra | Fonte |
|---|---|
| Template = um documento por ano × componente × fascículo; nome único nessa combinação. Revista de LP só oferece templates de LP. | D-098, `app/nucleo/models/texto.py:31-35` |
| Formato: Markdown restrito (parágrafo, negrito, itálico, listas) + `{{variavel}}` da lista fixa. HTML, links, crase, citação, título e `{{` fora da lista são recusados ao salvar. Sem lógica (`if`/`each`). | D-105, D-123, D-139, D-144, `app/nucleo/texto.py:1-30` |
| Seções do F1: exatamente `introducao` e `fechamento`. F2: exatamente as 9 de `texto.SECOES["F2"]`, todas obrigatórias (D-238). Seção repetida ou texto antes da 1ª seção é recusado. | D-111, D-114, D-139, `app/nucleo/texto.py:34-35` |
| A 1ª linha de cada seção é o título (texto puro, não editável na revista). | D-115, D-139 |
| Teto de 100 000 caracteres por template. | D-163, `app/nucleo/texto.py:32` |
| Editar o texto cria a versão N+1; nunca há UPDATE de texto. Texto igual ao atual salva só o nome, sem versão nova. | D-115, D-162, `app/nucleo/templates_texto.py:90` |
| Antes de gravar, a tela de impacto lista as revistas que usam o template (e quantas têm cópia) e os SVGs que ficariam sem algum id exigido. | D-099, D-162, D-166, `app/nucleo/templates_texto.py:69` |
| O "Confirmar" só grava se o texto e a versão-base forem os da tela de impacto (assinatura válida por 30 min). Duplo clique não duplica versão. | D-163, `app/nucleo/templates_texto.py:31` |
| O editor de templates mantém o botão "Salvar" (não tem autosave). | D-196 |
| Editar exige `change_template` + `add_templateversao`; template novo nasce com a versão 1, na mesma transação (tela B "Novo template", exige `add_template` + `add_templateversao`; texto inicial com as seções fixas do fascículo). | D-162, `docs/telas/telas-b.md` (seção 2) |
| Seed: `carregar_templates` cria o template "Padrão" a partir dos `.hbs` do repositório e nunca sobrescreve; depois disso a fonte é o banco. | D-098, D-139, D-176 |

### 5.2 Template na revista: ao vivo e cópia por seção

| Regra | Fonte |
|---|---|
| Cada fascículo da revista escolhe um template (nulo até escolher). Escolha pela revista ou "Atribuir template…" em massa (`change_revistafasciculo`). | D-102, D-106, `app/nucleo/lotes.py:211` |
| A revista lê o template **ao vivo**: editar o template muda todas as revistas que o usam e derruba o Validado delas. | D-099, D-104 |
| Só a seção editada vira cópia (`RevistaSecao`), guardando a versão do template de onde saiu; as outras seções continuam ao vivo. | D-115, D-170, `app/nucleo/models/revista.py:86` |
| Cópia nasce só quando o texto muda; texto igual ao template não cria cópia. Cópia que a pessoa deixa igual ao template continua cópia: só o descarte explícito apaga. | D-170 |
| Template mudou numa seção com cópia: o texto da revista não muda; aparece aviso com diff "Seu texto | Template novo", com "Manter meu texto" ou "Descartar cópia". Não bloqueia o Validado. | D-087, D-115, D-170, `app/nucleo/servicos/resolver.py:386` |
| Não há fusão automática de textos. | D-115 |
| Trocar o template de um fascículo com cópias exige digitar "descartar N cópia(s)"; as cópias saem na mesma transação. | D-104, D-170, D-171, `app/nucleo/revista.py:128` |
| O lote de template pula revistas com cópia naquele fascículo e lista as puladas. | D-164, `app/nucleo/lotes.py:190-208` |
| Editar textos exige `change_revista` + `add/change_revistasecao`. Revista arquivada mostra os textos da foto e recusa gravação. | D-170, D-171, `app/nucleo/revista.py:228` |

### 5.3 Variáveis

| Regra | Fonte |
|---|---|
| Lista fixa no código: 3 automáticas (`nome_parceiro`, `nome_projeto`, `ano`) + 24 manuais, uma coluna por variável em `Projeto`, até 200 caracteres. | D-100, D-172, D-173, `app/nucleo/variaveis.py:19` |
| Lista completa, descrição e exemplos: [`docs/variaveis.md`](variaveis.md). | D-172 |
| Valores só no projeto; renascem vazios a cada ano. | D-100, D-119 |
| Variável usada sem valor: destaque vermelho no preview e pendência que bloqueia o Validado. Variável não usada não cobra. Valor só com espaços conta como vazio. | D-100, D-144, D-151, `app/nucleo/servicos/resolver.py:285-289` |
| `pd01`..`pd05` são o nome dos padrões (regra 4.4) e também podem ser usados nos textos. | D-173, D-175 |
| Mudar uma variável derruba o Validado só da revista cujo texto efetivo a usa (o hash cobre o texto renderizado, não o valor cru). | D-125, D-151 |
| Edição: na ficha do projeto ou na planilha projetos × variáveis, com autosave por célula. | D-107, D-204, `app/nucleo/urls/ui_projeto.py:371` |

---

## 6. Revista: ciclo de vida, Validado e impresso

### 6.1 Ciclo de vida

| Estado | Como entra | Como sai | Fonte |
|---|---|---|---|
| Ativa | Cascata cria (componente com corte) ou reativa (corte voltou no mesmo ano) | Perde todos os cortes do componente | D-117, `app/nucleo/servicos/cascata.py:91-97` |
| Arquivada | Cascata: foto de arquivamento + `arquivada_em` | Cortes do componente voltam no mesmo ano (mesma linha) | D-117, `app/nucleo/servicos/cascata.py:61-77` |

- Revista nunca é apagada e não nasce à mão (D-117, `app/nucleo/admin/revista.py:215-224`).
- Uma revista por projeto × componente (`app/nucleo/models/revista.py:49`).
- Revista arquivada mostra o conteúdo da foto de arquivamento, não os dados vivos (D-117, `app/nucleo/servicos/resolver.py:248-256`).
- Revista arquivada não pode ser validada nem marcada impressa (`app/nucleo/servicos/validacao.py:35`, `app/nucleo/servicos/validacao.py:66`).
- Preview abre sempre; fascículo sem template aparece como faixa vermelha (D-116, `app/nucleo/servicos/resolver.py:58`).

### 6.2 Arquivos da revista: SVG do F2 e capa

| Regra | Fonte |
|---|---|
| SVG: um por revista (parceiro × componente), entregue pelo design já nomeado pela convenção, até 3 MB. | D-108, `app/nucleo/servicos/arquivos.py:27` |
| Ids exigidos: `passoN` → `passoN`; `dlg-xx` → `btn-action-xx`. SVG com id faltando é gravado com aviso e gabarito CSV, mas vira pendência. | D-111, D-164, `app/nucleo/servicos/arquivos.py:368-388` |
| SVG passa por lista branca de tags, atributos e CSS; `<!DOCTYPE>`, at-rules e URL externa recusam o arquivo inteiro. | D-137, D-145, learning "O SVG enviado pelo design passa por lista branca" |
| Capa: PNG, JPG ou WebP até 5 MB, tipo pela assinatura dos bytes. É campo da revista, fora do template. | D-109, D-137, `app/nucleo/servicos/arquivos.py:28` |
| Trocar SVG ou capa muda o hash (derruba o Validado); reenviar o mesmo arquivo não muda. | D-118, D-151 |
| Arquivo antigo é apagado do disco só depois do commit e só se o caminho mudou. | D-137 |

### 6.3 Validado

| Regra | Fonte |
|---|---|
| O estado "validada" não é guardado: é `hash_validado == hash atual`, calculado na hora. | D-084, D-125, `app/nucleo/servicos/validacao.py:20` |
| Hash = sha256 do JSON canônico da revista montada (escalas, cores, textos renderizados de F1 e F2, infográficos com o `imagem_sha256` dos itens, `capa_sha256`). Passo desligado não entra (D-243). | D-118, D-125, D-151, D-237, `app/nucleo/servicos/resolver.py:293` |
| O clique envia o hash da versão vista; se a revista mudou, o servidor recusa. | D-089, `app/nucleo/servicos/validacao.py:39` |
| Revalidar a mesma versão não troca quem validou nem quando. | D-174, `app/nucleo/servicos/validacao.py:41` |
| Validação em lote: a tela mostra cada revista e envia pares (revista, hash visto); o servidor recusa as que mudaram. | D-120, `app/nucleo/urls/painel.py:165` |
| Quem valida: `validar_revista` (Admin, Pedagógica, Mídias Digitais). | D-074, `app/nucleo/permissoes.py:76` |

**Pendências que bloqueiam o Validado** (`app/nucleo/servicos/resolver.py:335-383`):

| Código | Condição | Fonte |
|---|---|---|
| `matriz` | parceiro_ano sem matriz | D-088, D-106 |
| `corte_sem_matriz` | etapa com corte que a matriz escolhida não tem | D-093 |
| `corte_invalido` | cortes fora de ordem ou da escala (defensivo) | D-154 |
| `template_f1`, `template_f2` | fascículo sem template | D-112 |
| `infografico` | habilidade vazia; passo ligado sem dado (Habilidades: código ou texto; Progressão: 2 marcas; Tarefas: 4 imagens); passo desligado não gera pendência | D-237, D-243 |
| `capa` | falta capa | D-112 |
| `variaveis` | variável usada nos textos efetivos sem valor | D-100 |
| `nome_projeto` | nome ainda termina em " - NOME DO PROJETO" | D-093 |

**O que tira o Validado**: qualquer mudança que altere a revista montada, venha de onde vier.

| Origem da mudança | Afeta | Fonte |
|---|---|---|
| Descritor, tarefa, ordem, arquivo do item ou passo da MEC | Todas as revistas ativas que usam a MEC | D-076, D-078 |
| Texto do template | Todas as revistas que usam o template, na seção sem cópia | D-099 |
| Cópia de seção, troca de template | Só a revista | D-115 |
| Variável do projeto | Só as revistas cujo texto usa a variável | D-125 |
| Nome do projeto ou do parceiro | Revistas que usam a variável correspondente | D-125, D-202 |
| Corte (inclui mudar o padrão de uma tarefa) | Revista do componente | D-077 |
| Cor ou nome do padrão do ano; sobrescrita de cor/`pdNN` | Revistas com aquele padrão que não sobrescrevem | D-153, D-175 |
| Troca de matriz do parceiro_ano | Revistas do parceiro | D-101 |
| SVG ou capa | Só a revista | D-118 |

- Desfazer a mudança faz o Validado voltar sozinho (o hash volta) (D-094, `app/nucleo/servicos/validacao.py:3-4`).
- Seção desatualizada (template mudou sob uma cópia) só avisa; não bloqueia (D-087).

**Modal de impacto (D-202)**: nas telas B, a gravação que tira o Validado de alguma revista **não grava**; o servidor devolve a lista e a tela abre o modal. Gravação que só afeta revistas não validadas grava direto, sem modal. O cálculo simula a gravação num savepoint desfeito e compara o hash (`app/nucleo/servicos/impacto.py:23`, D-196, D-202). O admin mantém o checkbox "Confirmo: afeta N revista(s)" (`app/nucleo/matriz.py:130-155`).

### 6.4 Foto e impresso

| Regra | Fonte |
|---|---|
| "Revista Impressa Atualizada" só é aceito se a revista está validada exatamente no hash que a tela mostrou. | D-074, D-089, `app/nucleo/servicos/validacao.py:54-76` |
| O clique grava uma foto `impresso` com o resolvido inteiro; se o hash da foto diferir do visto, desfaz. Roda com o bloqueio do projeto. | D-151, D-178, `app/nucleo/urls/impresso.py:202-211` |
| "O que mudou" = diferença entre a última foto `impresso` e a revista atual, nunca contra a última validação. Primeira vez: sem foto anterior. | D-077, learning "O que mudou para o impresso vem de um botão" |
| O impresso compara escalas (com fim e item), cores e textos do F1 e textos do F2; SVG e capa ficam fora do diff. | D-112, D-118, D-153, D-178, `app/nucleo/servicos/resolver.py:299` |
| Mudança de formatação (negrito, itálico, listas) aparece no diff. | D-178 |
| O impresso não baixa de novo para saber o que mudou; as planilhas (por revista) podem ser baixadas a qualquer momento. | D-072, D-078, D-177 |
| Planilhas do impresso: células sempre texto (sem fórmula) e caracteres de controle removidos. | D-168, D-178 |
| Quem marca: só o perfil Impresso. Admin **não** marca. | D-177, `app/nucleo/permissoes.py:19` |

### 6.5 Entrega (zip)

| Regra | Fonte |
|---|---|
| Um zip por revista: site estático com sumário (`index.html`), F1 e uma página F2 por infográfico ativo, aberto por duplo clique. | D-103, D-109, D-159, D-233 |
| Revista com pendência não gera zip (lista as pendências). | D-159, `app/nucleo/servicos/empacotar.py:31` |
| Leva só os itens que o HTML usa; zip reprodutível (mesmo conteúdo, mesmos bytes). | D-160 |
| "Baixar zip" fica na lista de revistas (não no Painel). | D-179 |

---

## 7. Edição concorrente

### 7.1 Bloqueio de escrita

| Regra | Fonte |
|---|---|
| Quem abre primeiro edita; os outros veem em "Somente leitura". Bloqueio é só de escrita: todos continuam vendo. | D-080, D-081, learning "Bloqueio de edição trava só a escrita" |
| Alvos e granularidade: **MEC** (matriz × etapa × componente), **projeto inteiro** e **template inteiro**. Exatamente um alvo por trava. | D-081, D-109, `app/nucleo/models/controle.py:30-37` |
| A revista trava o projeto dela. | D-140 |
| Expira em 30 s sem renovação; a página renova a cada 10 s (também ao voltar à aba). | D-081, D-143, `app/nucleo/servicos/bloqueio.py:21`, `app/nucleo/static/nucleo/bloqueio.js:69` |
| Relógio é sempre o `now()` do banco. | D-140, `app/nucleo/servicos/bloqueio.py:1-12` |
| A mesma pessoa em outra aba ou recarga assume o bloqueio; a aba antiga perde a escrita e mostra "Você perdeu o bloqueio". Outra pessoa continua barrada. | D-191, `app/nucleo/servicos/bloqueio.py:44-60` |
| Renovar nunca readquire: bloqueio perdido = formulário possivelmente velho; o texto digitado continua copiável. | D-140, D-143 |
| Toda escrita confere o bloqueio dentro da transação (`FOR SHARE`); excluir também é negado com bloqueio de outra pessoa. | D-143, `app/nucleo/servicos/bloqueio.py:83`, `app/nucleo/admin/bloqueio.py:65-70` |
| Lotes (matriz, template, planilha de variáveis, impresso) adquirem o bloqueio de cada projeto só durante a escrita; projeto aberto por outra pessoa é pulado e listado. | D-121, D-164, `app/nucleo/lotes.py:39` |
| Reimportar matriz é recusado se uma MEC substituída está em edição. | D-146 |

### 7.2 Autosave e conflito otimista

| Regra | Fonte |
|---|---|
| Campo salva ao sair dele (telas B); o editor de templates mantém "Salvar". | D-196 |
| Protocolo único: 200 gravou; 200 com `impacto` = não gravou, abrir modal; 422 erro de validação; 409 conflito; 403 sem permissão. | `app/nucleo/ui_autosave.py:1-14` |
| 409 por conflito: o cliente manda o valor `original`; se o banco tem outro valor, nada grava e a resposta traz o `atual`. O próximo envio grava por cima, de propósito. | D-168, D-204, `app/nucleo/urls/ui_projeto.py:383-399` |
| Grade de Cortes e planilha de Variáveis não têm bloqueio de página: usam esse conflito otimista por célula. | D-165, D-204, learning "Telas B usam Alpine…" |
| Planilha de Variáveis: um 409 de bloqueio (projeto aberto por outra pessoa) trava só a linha daquele projeto, não a planilha inteira. | D-204, `app/nucleo/templates/ui/parciais/variaveis_linha.html:7`, `app/nucleo/static/ui/componentes/autosave.js:181` |
| Na revista e na ficha do projeto, um 409 trava a página inteira. | D-204 |
| Grade de cortes do admin aceita até 10 000 campos por POST (~340 parceiros com 28 células). | D-203, `app/sistema/settings.py:101` |

---

## 8. Perfis e permissões

Fonte única: `app/nucleo/permissoes.py`. Grupos fixos criados por migração; mudar a tabela exige migração de dados nova (o teste `GruposNoBancoTest` falha sem ela) (D-136, learning "No admin só se exclui a sobrescrita do projeto").

- **Admin** = Pedagógica + gerenciar usuários + apagar o ano + marcar impressa (D-083, D-220, `app/nucleo/permissoes.py`, `ADMIN_MARCA_IMPRESSA = True`).
- **Mídias Digitais** = exatamente a Pedagógica (D-073, `app/nucleo/permissoes.py:95`).
- **Impresso** = ver tudo + marcar impressa (D-074, `app/nucleo/permissoes.py:96`).
- Todos os perfis veem tudo (`ver_tudo`) (`app/nucleo/permissoes.py:44`).

### 8.1 Matriz perfil × ação

| Ação | Admin | Pedagógica | Mídias | Impresso | Fonte |
|---|:-:|:-:|:-:|:-:|---|
| Ver tudo (telas, preview, planilhas, zip) | ✓ | ✓ | ✓ | ✓ | `permissoes.py:44` |
| Abrir ano | ✓ | ✓ | ✓ | — | D-079, `permissoes.py:45` |
| Criar/editar parceiro, etapa, componente, parceiro_ano (matriz do parceiro) | ✓ | ✓ | ✓ | — | `permissoes.py:49` |
| Editar paleta do ano (cor e nome dos padrões) | ✓ | ✓ | ✓ | — | D-079, `permissoes.py:60` |
| Criar/duplicar/reimportar/editar matriz, MEC, descritor, tarefa, item | ✓ | ✓ | ✓ | — | D-079, `permissoes.py:50-57` |
| **Excluir** descritor e tarefa (confirmação forte) | ✓ | ✓ | ✓ | — | D-181, `permissoes.py:50-57` |
| Preencher cortes (criar, editar, esvaziar) | ✓ | ✓ | ✓ | — | D-188, `permissoes.py:58` |
| **Excluir** parceiro, etapa, componente, matriz ou template, só se nada os usa; desativar parceiro | ✓ | ✓ | ✓ | — | D-205, D-207, D-208, `permissoes.py:47` |
| **Apagar o ano inteiro** | ✓ | — | — | — | D-206, `permissoes.py:48` |
| Criar/editar template (nova versão) | ✓ | ✓ | ✓ | — | D-102, `permissoes.py:59` |
| Editar projeto (nome, variáveis), revista (SVG, capa, template, textos) | ✓ | ✓ | ✓ | — | `permissoes.py:65-75` |
| **Excluir** sobrescrita de passo e de cor do projeto ("voltar ao do ano/matriz") | ✓ | ✓ | ✓ | — | D-166, `permissoes.py:68-69` |
| Validar revista | ✓ | ✓ | ✓ | — | D-074, `permissoes.py:76` |
| Marcar "Revista Impressa Atualizada" | — | — | — | ✓ | D-177, `permissoes.py:19` |
| Criar/editar usuário (sem excluir) | ✓ | — | — | — | D-142, `permissoes.py:83` |
| Pôr alguém nos grupos Impresso ou Admin | só superusuário | — | — | — | D-168 |

### 8.2 Regras de usuários

| Regra | Fonte |
|---|---|
| Usuário sai desativado (`is_active`). Excluir só pela tela Usuários e só quem não tem rastro: nenhuma edição no histórico (`history_user`), versão de template, validação, foto de revista nem ação no admin. Com rastro, a página lista o que impede e manda desativar. Mesma regra de quem pode desativar; o admin do Django não exclui (sem `auth.delete_user`). | D-142, D-205, D-218, `app/nucleo/usuarios.py::rastros` |
| O formulário de usuário não tem `is_superuser`, `is_staff` nem permissões avulsas; usuário novo nasce `is_staff`. | D-142, `app/nucleo/admin/usuarios.py:34-75` |
| Superusuário só por comando, com acesso ao servidor: `createsuperuser` (novo) ou `tornar_superusuario <usuario>...` (quem já existe; nome inexistente não muda nada). Ele tem tudo; o que o Admin não tem é pôr alguém no grupo Admin e alterar outro Admin. | D-142, D-219, D-220, `app/nucleo/management/commands/tornar_superusuario.py` |
| O Admin (não superusuário) atribui Pedagógica, Mídias Digitais e Impresso; não vê superusuários; não muda os próprios grupos nem se desativa; não altera (dados, senha, grupo, ativo) outro Admin, só vê. O Impresso ele gerencia por inteiro e ele mesmo marca impressa (D-220, substitui a parte da D-211 que deixava o Impresso só com o superusuário). | D-168, D-220, `app/nucleo/usuarios.py` (módulo comum do admin e da tela B) |
| Gerenciar usuários também pela tela B (`/ui/usuarios/`): listar, criar (nasce `is_staff`), trocar o grupo (um por usuário na B), ativar/desativar, redefinir a senha. Exige `auth.change_user` (criar: também `add_user`). O superusuário não tem restrição. | D-190, D-210, `app/nucleo/urls/ui_usuarios.py` |
| "Link de acesso" (tela Usuários, só POST): link para a pessoa definir a própria senha, o mesmo do `criar_usuarios`, com mensagem pronta para enviar. Mesma regra de "Redefinir senha" (`pode_editar`) e só para ativo. Vale `PASSWORD_RESET_TIMEOUT` (3 dias) e cai quando a senha muda ou a pessoa entra. O endereço vem do `Origin` do POST (https atrás do proxy). A página aberta pelo link é tela B, não o admin (D-212). | D-216, `app/nucleo/usuarios.py::caminho_definir_senha`, `app/nucleo/urls/conta.py` |

### 8.3 Regras de tela

| Regra | Fonte |
|---|---|
| Toda função que o perfil pode usar precisa de controle na tela B; link para o admin não conta. O que o perfil não pode usar não aparece. | D-189, D-190, learning "Toda função do back precisa de botão na tela nova" |
| Cada controle confere a permissão no template e a view repete a conferência (403). | learning "Toda função do back precisa de botão na tela nova" |
| `hash_validado`, `validado_*` e `arquivada_em` só são escritos pelos serviços, nunca por formulário. | D-142 |

---

## 9. Exclusão

Regra geral (D-205): uma entidade pode ser excluída quando nada depende dela. Quando algo depende, a página `/ui/excluir/<modelo>/<pk>/` mostra o que impede, com contagem e links, e não apaga nada. O PROTECT continua no banco. A confirmação é sempre digitar o código ou o nome. O Impresso nunca exclui. Serviço: `app/nucleo/servicos/exclusao.py`; rota: `app/nucleo/urls/ui_excluir.py`; página: `templates/ui/excluir.html`.

| Entidade | Em uso quando | Em uso → | Quem exclui | Onde | Fonte |
|---|---|---|---|---|---|
| Ano | — | O Admin apaga o **ano inteiro**, com tudo o que há nele; a página mostra as contagens e pede que ele digite o ano | Só Admin (`delete_ano`) | Lista de anos (lixeira) | D-206 |
| Parceiro | Tem Corte ou Projeto em algum ano (ParceiroAno vazio sai junto) | Oferece **Desativar** (`desativado_em`): some dos anos em que não tem dados; Reativar desfaz | Pedagógica, Mídias, Admin | Grade de Cortes (lixeira no nome) | D-205, D-208 |
| Etapa | Tem Corte, MEC ou passo do projeto | Explica | Pedagógica, Mídias, Admin | Página do ano (por linha) | D-205 |
| Componente | Tem revista, MEC, corte, passo do projeto ou template | Explica | Pedagógica, Mídias, Admin | Página do ano (por linha) | D-205 |
| Matriz | Algum parceiro usa (`ParceiroAno.matriz`) ou outra pessoa edita uma MEC dela (MEC, descritor e tarefa saem junto) | Explica, com link para Lotes | Pedagógica, Mídias, Admin | Fim da página da matriz | D-205 |
| Template | Alguma revista usa o template ou uma versão dele, ou outra pessoa o edita | Explica, com links para as revistas. Sem uso, sai **com as versões** | Pedagógica, Mídias, Admin | Lista (lixeira) e fim do editor | D-207 |
| Corte | Nunca | Esvaziar a célula apaga e arquiva a revista | Quem preenche cortes | Grade | D-188, `servicos/cascata.py:121-122` |
| Descritor, Tarefa | Regra própria, com impacto no Validado | — | Pedagógica, Mídias, Admin | Tela da MEC | D-181 |
| Sobrescrita, cópia de seção, arquivo do item | Nunca | Voltar ao valor herdado / descartar cópia / remover arquivo | Editores | Ficha do projeto, revista, MEC | D-166, D-170, D-150 |
| Projeto, Revista | Sempre (a revista existe enquanto houver corte) | Arquivam pela cascata ao limpar os cortes | — | — | D-065, D-117 |
| Usuário | Sempre que tem autoria | Desativar | Admin | Admin do Django | D-142, D-205 |
| Foto | — | Nunca se apaga: é o histórico (exceto ao apagar o ano inteiro) | — | — | D-206 |

Travas que continuam:
- **Versões de template:** o trigger recusa sempre o UPDATE. O DELETE só passa quando a transação liga `SET LOCAL revista.apagar_versoes = 'on'`, e só fazem isso a exclusão de template sem uso e o apagar do ano (migração `0017_versao_apagavel`, D-206/D-207).
- **Admin do Django:** o "Excluir" leva à mesma página da tela B, e não existe exclusão em massa (`ExclusaoAdminMixin`, `admin/cadastro.py`).
- **Teste-trava:** `tests/test_exclusao.py` lista toda FK que não é PROTECT contra uma lista permitida, para nenhuma cascata nova apagar histórico.

---

## 10. Divergências e pontos em aberto

### 10.1 Decisão ou documento × código

Situação em 05/11. **Resolvida** = o documento já diz o que o código faz. **Aberta** = precisa de mudança de código ou de resposta do usuário; nenhuma mudança de código foi feita aqui.

| # | Decisão / documento | Código (vale este) | Situação |
|---|---|---|---|
| 1 | ~~D-205: excluir o que não está em uso.~~ | Ver seção 9. | **Resolvida** em 04/11 (E0–E5, D-206 a D-208). |
| 2 | ~~`docs/modelo-er.md`: aquisição do bloqueio aceitava `sessao_edicao = EXCLUDED.sessao_edicao`.~~ | Aceita o **mesmo usuário**, em qualquer sessão (D-191, `app/nucleo/servicos/bloqueio.py:56`). | **Resolvida** em 05/11: o ER descreve o `ON CONFLICT` atual, o TTL de 30 s e a perda de renovação da sessão antiga. |
| 3 | ~~`docs/modelo-er.md`: "a foto do impresso guarda só os textos (D-112)" e "foto em REPEATABLE READ".~~ | A foto guarda o resolvido inteiro; o diff do impresso cobre escalas, cores e textos (`app/nucleo/servicos/resolver.py:299`, D-151, D-153). A foto roda em READ COMMITTED, na transação do chamador, com savepoint no clique do impresso (D-178, `app/nucleo/servicos/foto.py:7-31`, `app/nucleo/servicos/validacao.py:72`). | **Resolvida** em 05/11: o ER foi corrigido. |
| 4 | D-055: faixa 0–1000 no 2EF e 0–500 nas demais, limites aceitos. | O limite vem de `Etapa.escala_max`, campo editável da etapa (`app/nucleo/models/cadastro.py:60`, `app/nucleo/urls/ui_anos.py:90-98`), e o corte fica **estritamente** dentro de `(0, escala_max)` (D-153, `app/nucleo/servicos/cascata.py:38`). Os números 1000 e 500 só existem na carga inicial (`app/nucleo/management/commands/carregar_cadastros.py:6`). | **Aberta.** A D-153 já trocou "aceitos" por "estritamente"; falta decidir o resto. **Pergunta ao usuário:** o limite correto é o `escala_max` de cada etapa (como o código faz) ou os números fixos 1000 e 500? Se for o `escala_max`, a D-055 deve ser reescrita assim no `state.md`, e etapa nova pode ter outra escala sem mudar código. |
| 5 | D-076, D-099, D-180: avisar "afeta N revistas" antes de salvar. | As telas B só abrem o modal quando alguma revista **perde o Validado** (D-202, `app/nucleo/servicos/impacto.py:23`). O admin continua pedindo o checkbox "Confirmo: afeta N revista(s)" sempre que há revista afetada (`app/nucleo/matriz.py:146-147`; o `ImpactoForm(modal=True)` das telas B desliga isso, `app/nucleo/matriz.py:130`). | **Aberta.** A D-202 manteve o admin como está de propósito, mas o `state.md` ainda lista a pergunta. **Pergunta ao usuário:** igualar o admin ao modal das telas B (avisar só quando perde o Validado) ou manter os dois comportamentos? |
| 6 | D-047: parceiro tem no máximo **um** projeto. | A restrição é um projeto **ativo** por parceiro_ano; os arquivados se acumulam (D-068, `app/nucleo/models/projeto.py:102-105`). | **Resolvida nos documentos** (seção 3.2 aqui e o ER já dizem "ativo"). Falta só uma nota "ativo, ver D-068" na D-047 do `state.md`, que não foi tocado. |
| 7 | D-107: "Copiar valores do ano anterior". | Copia só para variáveis **vazias**; não sobrescreve o que já foi digitado (`app/nucleo/planilha_variaveis.py:51-62`). | **Resolvida nos documentos** (seção 2.2 aqui). Falta só registrar a regra mais estreita na D-107 do `state.md`. |
| 8 | `app/nucleo/permissoes.py:17`: "Pergunta em aberto: admin pode clicar Revista Impressa Atualizada?" | Fechada pela D-177 (não pode); `ADMIN_MARCA_IMPRESSA = False` (`app/nucleo/permissoes.py:19`). | **Aberta (só comentário no código).** **Pergunta ao usuário:** posso trocar o comentário por "Fechada: não (D-177)", numa mudança sem efeito no comportamento? |
| 9 | `app/nucleo/permissoes.py:14`: usuário não se apaga porque "histórico usa SET_NULL". | `Revista.validado_por`, `FotoRevista.criada_por` e `TemplateVersao.criada_por` são PROTECT (`app/nucleo/models/revista.py:37`, `:116`; `app/nucleo/models/texto.py:57`). | **Aberta (só comentário no código).** A regra (desativar) continua valendo; o motivo no comentário está incompleto. Mesma pergunta da linha 8. |
| 10 | `app/nucleo/models/controle.py:18`: "apagar o alvo apaga a trava (CASCADE)". | O CASCADE existe só no ORM; no banco a FK é NO ACTION, então um DELETE direto no banco é recusado se há trava (D-133). | **Aberta no comentário; resolvida no ER**, que agora diz isso na seção ON DELETE. Mesma pergunta da linha 8. |
| 11 | Regra "toda função do back na tela B" (D-189, D-190). | Ainda só no admin: usuários, criar template, criar matriz (a primeira só por comando), planilha de grupos de corte, gabarito de ids, baixar item (`docs/telas/telas-b.md`, seção 2). | **Resolvida** por S6–S9 (D-210): sobram no admin só login, índice e histórico por registro. |
| 12 | Este documento (seção 5.3) dizia "25 manuais". | `VARIAVEIS` tem 27 itens: 3 automáticas e **24** manuais (`app/nucleo/variaveis.py:21-50`, `docs/variaveis.md`). | **Resolvida** em 05/11: seção 5.3 corrigida. |

### 10.2 Perguntas em aberto do `state.md` que afetam regra de negócio

Só as não marcadas `[x]`.

| Pergunta | Depende de | Observação |
|---|---|---|
| Seeds 2026 (D-139): `f2-mt.hbs` é cópia do LP; modais `dlg-p4-i1..i4` com "Conteúdo em breve."; fechamento do F1 = "Utilização dos resultados"?; nome do template "Padrão". | Pedagógica | A abertura do F1 de MT já foi trocada (D-176). |
| Bloqueio (D-140): portar a saída por inatividade do editor antigo? POST recusado deve reexibir o digitado em vez de descartar? | usuário | Hoje o bloqueio só cai por falta de renovação (30 s). |
| SVG com `<!DOCTYPE>` é recusado (D-137): o design exporta sem DOCTYPE? | usuário / design | Se exportar com DOCTYPE, todo upload falha. |
| Autor da foto herdada (D-135): usuário da cascata (atual) ou autor da foto original? | usuário | Hoje: usuário da cascata. |
| Intervalo mínimo e cor sobrescritos não têm `versao_base`: mudança no valor da matriz/ano não avisa o projeto que sobrescreveu. Precisa? | usuário | — |
| `skills[]` → "relacionadas" × "correspondente" na planilha: a heurística pelo "(" serve ao impresso? | equipe de impressão | Mesma heurística no importador (D-141). |
| Alternativa de exibição da escala (régua proporcional ou lista por padrão). | Pedagógica | Recomendação vigente: manter a régua. |
| O template "Padrão (F1)" do dev está na versão 8, com texto de teste E2E. Gravar versão nova com o texto da v1 muda o hash das revistas que o usam. | usuário | Dado do ambiente de dev, não regra; afeta o Validado dessas revistas. |

Perguntas ainda abertas no `state.md` que **já têm resposta** em decisão posterior (fechar no `state.md`):

| Pergunta aberta | Respondida por |
|---|---|
| "Admin pode clicar Revista Impressa Atualizada?" | D-177 (não) |
| "Lista real de perfis e matriz papel × ação" | D-073, D-136, D-142, D-166, D-181 (seção 8) |
| "Onde guardar o status 'aplicado no impresso'…" | D-077 (foto `impresso`) |
| "Migrar `api/` para Django mantendo o React?" | D-121, D-183 (Django, telas B próprias) |
| "Levar a opção 1 (D-032) para `revista/`?" | D-033, D-038 (portada; demo apagada) |
| "`docs/modelo-er.md` está desatualizado em dois pontos (bloqueio e foto). Corrigir?" | Corrigido em 05/11 (seção 10.1, linhas 2 e 3) |
