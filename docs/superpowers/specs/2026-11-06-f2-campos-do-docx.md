# Campos que o docx "Avaliação e Currículo" preenche (LP 2026 AF_EM)

Fonte: docx que a Pedagógica manda ao impresso (`Cópia de AVALIAÇÃO E CURRÍCULO_LP_2026_AF_EM.docx`, 765 KB),
convertido com `npx -y @firecrawl/anydoc` em `docs/fontes/2026/avaliacao-e-curriculo-lp-2026-af-em.md`
(`md:NN` abaixo = linha desse arquivo). O docx em si não está no repositório.

## 1. Estrutura do documento

| Bloco | Conteúdo | Linhas |
| --- | --- | --- |
| Cabeçalho | "AVALIAÇÃO E CURRÍCULO" + componente | md:1-3 |
| Abertura | 4 parágrafos (BNCC, referenciais, matriz como recorte, objetivo da seção) | md:5-11 |
| ❶ Descritor | texto da habilidade destacada; **TEXTO DO CLIQUE ❶** com 4 parágrafos (3 genéricos + 1 que cita a habilidade) | md:13, md:17-23 |
| ❷ Progressão | tabela 12 etapas (1EF–3EM) × marca I/A/C/R; **clique ❷** com 3 parágrafos específicos da habilidade | md:27-29, md:33-37 |
| ❸ Descrição das habilidades | tabela 12 linhas: etapa, marca, "(código BNCC) texto", com células mescladas; legenda fixa I/A/C/R; **clique ❸** = 1 parágrafo de abertura + 6 blocos com subtítulo em negrito (1º e 2º; 3º e 4º; 5º; 6º e 7º; 8º e 9º; EM) + 2 parágrafos de fechamento | md:41-54, md:56-64, md:68-96 |
| ❹ Tarefas | 4 itens "(4,N) Dxx – etapa" (D05 2EF, D09 5EF, D12 9EF, D12 3EM); **clique ❹** = título + 1 parágrafo de abertura + por item: subtítulo da etapa, id do item (`P00208914`), id do suporte (`P00208914_SUP`), 2 parágrafos (descrição e gabarito/análise) + 2 parágrafos de fechamento comparando os 4 | md:100-106, md:110-158 |
| Agora é com você | 2 parágrafos + link "Acesse aqui" para o template do infográfico | md:160-164 |

Não vem no documento: percentual de acerto e série histórica (o impresso tira de dados; confirmado fora do F2 web, como no mapeamento).

## 2. Campos, um a um

| # | Campo | Granularidade | Hoje no sistema | O que falta |
| --- | --- | --- | --- | --- |
| 1 | Título "Avaliação e Currículo" | fixo | seed `abertura` (`f2-lp.hbs:1-2`) | nada |
| 2 | Componente | revista | `Componente.nome` | nada |
| 3 | Abertura (4 parágrafos) | componente × ano (LP e MT terão o seu) | seção `abertura` guarda só título + 1 frase do painel do tour | decidir onde o texto corrido aparece na web (antes do infográfico?) e se vira seção nova (`introducao`) ou a `abertura` cresce |
| 4 | Habilidade destacada (texto do ❶) | revista | `Descritor.descricao` por matriz × etapa; mas o código muda por etapa (D05/D09/D12/D12) e a redação do 2EF é outra ("Inferir informações em textos que articulam linguagem verbal e não verbal") | campo de texto na revista (redação canônica) + descritor escolhido por etapa (`RevistaF2Descritor` do mapeamento) |
| 5 | Clique ❶ (4 parágrafos) | 3 genéricos por componente × ano; o 4º cita a habilidade | não existe: o SVG atual e o protótipo não têm botão no cartão do descritor | seção `dlg-descritor` nova + botão `+` no cartão; o 4º parágrafo pede variável (`{{habilidade_destacada}}`) ou fica como texto da revista |
| 6 | Marca por etapa (❷, 12 valores) | revista | não existe | tabela nova por revista × etapa (`marca`); legenda I/A/C/R fixa no código |
| 7 | Clique ❷ (3 parágrafos) | revista (cita os anos desta habilidade) | seção `dlg-p2` do seed | renomear para `dlg-progressao`; conteúdo é por revista, não por template (ver §4) |
| 8 | Tabela ❸ (código BNCC + texto por faixa de etapas) | revista | não existe (`importar_matriz` traz só `praticas`, `conhecimento`, `habilidades_relacionadas`, `habilidade_correspondente`) | na mesma tabela do item 6: `codigo_bncc` e `texto` opcionais; linha vazia = "igual à de cima" (mescla); 5EF tem marca C e nenhum código (consolidação de EF15LP18 + EF15LP04) |
| 9 | Clique ❸ (abertura + 6 blocos + fechamento) | revista | seção `dlg-p3` do seed, formato com negrito e parágrafos já permitido (D-131) | renomear para `dlg-habilidades`; conteúdo por revista |
| 10 | Itens ❹: código do descritor + etapa (4) | revista | `Descritor` e `Tarefa` existem (`matriz.py:63-115`: `arquivo`, `texto`, `texto_alternativo`, `inicio`/`fim`) | escolha por revista de qual tarefa de qual descritor em cada etapa de terminalidade (2EF, 5EF, 9EF, 3EM) |
| 11 | Arquivos do item: `Pxxxx` e `Pxxxx_SUP` | tarefa | `Tarefa.arquivo` (um arquivo só) | o suporte (`_SUP`) é um segundo arquivo: campo novo na tarefa ou imagem única montada pelo design |
| 12 | Clique ❹: 1 abertura + 2 parágrafos por item + 2 de fechamento | revista | 4 seções `dlg-p4-i1..i4` com "Conteúdo em breve" | texto analítico por item (campo na escolha do item 10 ou seção `dlg-tarefa-N`); abertura e fechamento comuns aos 4 precisam de lugar (modal único? repetir?) |
| 13 | "Agora é com você" (2 parágrafos + link) | componente × ano | não existe | seção `fechamento` nova + campo para o arquivo/URL do template do infográfico |

## 3. O que muda em relação ao mapeamento (seção 2 de `2026-11-06-f2-na-interface-mapeamento.md`)

1. O passo `descritor` **tem modal** (clique ❶): entra `dlg-descritor` e um botão `+` no cartão.
2. A abertura é texto corrido de 4 parágrafos, não só a introdução do painel do tour.
3. A marca I/A/C/R vem da tabela ❷; a tabela ❸ só agrupa etapas em faixas (rowspan) com código e texto. Uma tabela por revista × etapa com `marca`, `codigo_bncc?`, `texto?` cobre as duas.
4. A habilidade destacada não é um `Descritor` do banco: é uma redação canônica com um descritor diferente por etapa. `DescritorProgressao` (pendurado no descritor) não serve; a tabela pendura na revista.
5. Tarefas: cada item tem 2 parágrafos de análise e 2 arquivos (item + suporte); há abertura e fechamento comuns aos 4.
6. Há um fechamento ("Agora é com você") com link para um template do infográfico.

## 4. Ponto estrutural para a fase 1

Os cliques ❶ (4º parágrafo), ❷, ❸ e ❹ e a habilidade destacada são **conteúdo da revista** (dependem da habilidade escolhida), não do template. No modelo atual o template é a regra e a sobrescrita por revista (D-104) é a exceção; no F2 vira o contrário. Proposta: o template F2 guarda só o genérico (abertura, clique ❶ sem o 4º parágrafo, legenda, abertura/fechamento do ❹, "Agora é com você"); o específico vive em campos da revista (tabela por etapa, escolha de item por etapa com análise, textos dos cliques ❷ e ❸). Entra no resolvido como hoje → hash, foto e planilha do impresso seguem sozinhos.

## 5. Perguntas (de quem depende)

1. ~~"AF_EM" no nome do arquivo~~ Respondida em 06/11 (D-230): ver §6. Restam: a estrutura do Alfa é a mesma (progressão 1EF–3EM, itens só do 2EF?); o docx recebido traz um item do 2EF, é o "Outras Etapas"? — Pedagógica
2. Os 4 parágrafos da abertura aparecem na web antes do infográfico (texto corrido) ou só no impresso? — Otavio
3. Clique ❹: um modal por item (e a abertura/fechamento comuns vão onde?) ou um modal único com os 4 itens? — Otavio + Pedagógica
4. Suporte do item (`_SUP`): segundo arquivo da tarefa ou uma imagem única montada pelo design? — design
5. "Acesse aqui o template do infográfico": que arquivo é, quem fornece e vale por ano ou por componente? — Pedagógica

## 6. Infográficos por revista (D-230, 06/11)

Cada revista (projeto × componente) tem até **2 infográficos** no F2, derivados dos cortes pela cascata
(`app/nucleo/servicos/cascata.py`, `gravar_cortes`), nunca escolhidos à mão:

| Infográfico | Existe quando | Etapas que cobre |
| --- | --- | --- |
| Avaliação e Currículo – Alfa | o parceiro tem cortes para o **2EF** naquele componente | 2EF |
| Avaliação e Currículo – Outras Etapas | há cortes para **alguma etapa ≠ 2EF** | todas as outras, aglutinadas num só |

Até 4 por projeto (2 LP + 2 MT). Consequências para a fase 1: todos os campos da §2 marcados "revista" passam a ser
**por infográfico** (revista × tipo), inclusive os passos desligados (D-229 refinada); o template F2 provavelmente
vira um por tipo × componente; a navegação do F2 (página e zip), a planilha do impresso e o "Validado" precisam
contar com 0, 1 ou 2 infográficos por revista.
