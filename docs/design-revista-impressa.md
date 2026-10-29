---
name: Revista da Escola SAEGO 2025 (impressa)
description: Revista editorial em preto sobre branco, com um único amarelo de marca-texto e cor reservada aos dados (padrões, progressão, acerto).
source: "revista/modelo/PDFs Matriz Comunitária/SAEGO_2025_RE_{Alfa_2EF_5EF,LP,MT} Web.pdf (InDesign 21.2, 210 × 280 mm)"
colors:
  ink: "#000000"
  paper: "#ffffff"
  marca-texto: "#ffed00"
  marca-texto-escuro: "#ffeb00"
  cinza-painel: "#f6f6f6"
  cinza-faixa: "#f5f5f5"
  cinza-fio: "#c6c6c6"
  cinza-fio-claro: "#dadada"
  cinza-legenda: "#878787"
  cinza-texto: "#575756"
  verde-linha-do-tempo: "#00863c"
  azul-anotacao: "#2362ad"
  padrao-1-abaixo-do-basico: "#b8ffd8"
  padrao-2-basico: "#2bff8a"
  padrao-3-proficiente: "#00c257"
  padrao-4-avancado: "#00662e"
  progressao-introduzir: "#e6f6fb"
  progressao-aprofundar: "#a9ffff"
  progressao-consolidar: "#08b4d7"
  progressao-retomar: "#006991"
  acerto-ate-40: "#f25656"
  acerto-41-60: "#f9bc45"
  acerto-61-80: "#c0f3ff"
  acerto-acima-80: "#72caf0"
  etapa-5ef: "#ffb8d1"
  etapa-9ef: "#d45ea7"
  etapa-3em: "#73264d"
typography:
  display:
    fontFamily: "Gotham, 'Montserrat', sans-serif"
    fontSize: "24.5pt"
    fontWeight: 700
    lineHeight: 1.1
    letterSpacing: "0.02em"
  headline:
    fontFamily: "Gotham, 'Montserrat', sans-serif"
    fontSize: "15pt"
    fontWeight: 700
    lineHeight: 1.2
  title:
    fontFamily: "Gotham, 'Montserrat', sans-serif"
    fontSize: "13pt"
    fontWeight: 400
    lineHeight: 1.3
  kicker:
    fontFamily: "Gotham, 'Montserrat', sans-serif"
    fontSize: "10pt"
    fontWeight: 300
    letterSpacing: "0.12em"
  body:
    fontFamily: "'Proxima Nova', 'Figtree', sans-serif"
    fontSize: "10pt"
    fontWeight: 400
    lineHeight: "15pt"
  body-strong:
    fontFamily: "'Proxima Nova', 'Figtree', sans-serif"
    fontSize: "10pt"
    fontWeight: 700
    lineHeight: "15pt"
  dado:
    fontFamily: "'Proxima Nova Condensed', 'Barlow Semi Condensed', sans-serif"
    fontSize: "9pt"
    fontWeight: 300
    lineHeight: 1.35
  dado-verbo:
    fontFamily: "'Proxima Nova Condensed', 'Barlow Semi Condensed', sans-serif"
    fontSize: "9pt"
    fontWeight: 600
  label:
    fontFamily: "'Proxima Nova', 'Figtree', sans-serif"
    fontSize: "8pt"
    fontWeight: 400
  folio:
    fontFamily: "Gotham, 'Montserrat', sans-serif"
    fontSize: "14pt"
    fontWeight: 700
  running-head:
    fontFamily: "Gotham, 'Montserrat', sans-serif"
    fontSize: "5pt"
    fontWeight: 300
    letterSpacing: "0.3em"
rounded:
  none: "0"
  pill: "9999px"
spacing:
  fio: "0.5pt"
  marcador: "6pt"
  gutter: "18pt"
  margem-externa: "75pt"
  margem-topo: "32pt"
components:
  descritor-chip:
    backgroundColor: "{colors.marca-texto}"
    textColor: "{colors.ink}"
    typography: "{typography.headline}"
    rounded: "{rounded.none}"
    padding: "6pt 10pt"
  numero-etapa:
    backgroundColor: "{colors.marca-texto}"
    textColor: "{colors.ink}"
    typography: "{typography.display}"
    rounded: "{rounded.none}"
    padding: "0 6pt"
  faixa-ano:
    backgroundColor: "{colors.cinza-faixa}"
    textColor: "{colors.ink}"
    rounded: "{rounded.none}"
    padding: "6pt 0"
  quadro-pre-requisitos:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.ink}"
    rounded: "{rounded.none}"
    padding: "14pt 16pt"
  painel-cinza:
    backgroundColor: "{colors.cinza-painel}"
    textColor: "{colors.ink}"
    rounded: "{rounded.none}"
    padding: "24pt 30pt"
  etiqueta-exemplo:
    backgroundColor: "{colors.marca-texto}"
    textColor: "{colors.ink}"
    rounded: "{rounded.none}"
    padding: "3pt 6pt"
  celula-padrao-1:
    backgroundColor: "{colors.padrao-1-abaixo-do-basico}"
    textColor: "{colors.ink}"
  celula-padrao-4:
    backgroundColor: "{colors.padrao-4-avancado}"
    textColor: "{colors.paper}"
---

# Design System: Revista da Escola SAEGO 2025 (impressa)

Extraído de três PDFs (Alfabetização 2º/5º EF com 173 páginas, Língua Portuguesa com 100 e Matemática com 136). Os três usam **o mesmo sistema**: mesma paleta, fontes, grid e componentes. Só muda o conteúdo e a ilustração. Os valores de cor vêm dos vetores do PDF e foram conferidos por amostragem de pixel. As medidas estão em pontos (pt) do impresso.

## Overview

**North Star (proposta): "O Caderno Marcado".** É uma página de relatório técnico em preto sobre branco, em que alguém passou um marca-texto amarelo só no que importa. Fora do amarelo, a cor só aparece quando é **dado**: verde para padrões de desempenho, ciano para a progressão no currículo, semáforo para percentual de acerto e magenta para etapas.

O tom é institucional e arejado. Títulos em Gotham Bold caixa-alta, texto corrido em Proxima Nova 10/15 justificado com hifenização, margens largas e muito branco. A ilustração (plantas e flores em verde-limão, cortadas em retângulos sobrepostos) aparece só em capas, aberturas e cantos. Ela é decoração editorial e não carrega informação.

O vocabulário gráfico é ortogonal: retângulos de canto vivo, fios finos de 0,5pt, quadradinhos de 6pt como marcadores e linhas de chamada em ângulo reto ligando caixas. Não há sombra nem cantos arredondados, exceto em bolinhas de legenda e fotos circulares.

**Key Characteristics:**
- Um amarelo só (`#ffed00`, o amarelo de processo CMYK), usado como marca-texto, nunca como fundo de página.
- Cor semântica separada por tipo de dado; cada escala é monocromática e ordenada do claro ao escuro.
- Gotham (geométrica) para títulos, Proxima Nova para texto e Proxima Nova Condensed para dado denso.
- Fios finos, quadrados pretos de 3pt e linhas de chamada em L no lugar de caixas pesadas.
- Painéis cinza-claro (`#f6f6f6`) dão profundidade no lugar de sombra.

## Colors

Monocromático com um acento de marca e quatro famílias de cor de dados que nunca se misturam.

### Primary
- **Marca-texto** (`#ffed00`): o único acento da marca. Aparece no fio do cabeçalho de página, no sublinhado de título, no chip do descritor (D01), nos números de etapa (03, 04…), nas etiquetas "Exemplo 1", no bloco "Descritor: D14…", no "Isto é:" e nos marcadores quadrados de seção. `#ffeb00` é a mesma cor com outra conversão de perfil e deve ser tratada como sinônimo.

### Neutral
- **Tinta** (`#000000`): todo o texto (mais de 99% dos caracteres), folios e fios de destaque.
- **Papel** (`#ffffff`): fundo de todas as páginas internas.
- **Cinza-painel** (`#f6f6f6`, com variante `#f5f5f5`): painéis de destaque, faixa do ano, rodapé BNCC e retângulos decorativos.
- **Cinza-fio** (`#c6c6c6`, mais claro `#dadada`): fios de tabela, divisórias e borda de quadro.
- **Cinza-legenda** (`#878787`): "PÁGINA 5" no sumário e unidades ("100 pontos").
- **Cinza-texto** (`#575756`): ficha catalográfica e textos de crédito.

### Cores de dados (o coração do sistema)
**Padrões de desempenho, rampa verde** (escala vertical e tabela de cortes):
- Padrão 01 · Abaixo do básico `#b8ffd8`
- Padrão 02 · Básico `#2bff8a`
- Padrão 03 · Proficiente `#00c257`
- Padrão 04 · Avançado `#00662e` (único com texto branco)

**Progressão no Referencial Curricular, rampa ciano** (I/A/C/R):
- Introduzir `#e6f6fb` · Aprofundar `#a9ffff` · Consolidar `#08b4d7` · Retomar `#006991`

**Percentual de acerto, semáforo:**
- Até 40% `#f25656` · 41–60% `#f9bc45` · 61–80% `#c0f3ff` · Acima de 80% `#72caf0`

**Etapas (5º EF / 9º EF / 3ª EM), rampa magenta:**
- `#ffb8d1` · `#d45ea7` · `#73264d`

**Apoio:** verde `#00863c` nos rótulos da linha do tempo e azul `#2362ad` nas linhas de chamada do guia "Orientação para leitura".

### Named Rules
**A Regra do Marca-Texto Único.** O amarelo marca e nunca preenche. Ele aparece em peças pequenas (chip, sublinhado, marcador, número) e em no máximo um bloco grande por página. A página nunca tem fundo amarelo.

**A Regra da Cor É Dado.** Fora do amarelo, cor só existe para codificar um dado. Cada tipo de dado tem sua família de cor, e as famílias não se emprestam. Verde é padrão e ciano é currículo, sempre.

**A Regra da Rampa Ordenada.** Toda escala de dado vai do mais claro (menos) ao mais escuro (mais). O texto fica preto até a cor de fundo ficar escura demais; só então passa a branco.

## Typography

**Display:** Gotham (Bold, Medium, Book, Light)
**Texto:** Proxima Nova (Regular, Semibold, Bold, Light, Italic)
**Dado:** Proxima Nova Condensed (Light, Regular, Semibold, Bold)

**Caráter:** a Gotham é geométrica e institucional e fala em caixa-alta. A Proxima Nova é humanista e confortável para ler muito texto. A versão condensada faz caber o texto pedagógico longo das linhas da escala e das tabelas BNCC sem reduzir o corpo.

As duas famílias são comerciais (Hoefler e Mark Simonson). Para web auto-hospedada sem licença, os substitutos mais próximos são **Montserrat** (Gotham), **Figtree** (Proxima Nova) e **Barlow Semi Condensed** (Proxima Nova Condensed). Antes de usar as originais, confirme se a Fundação tem licença web.

### Hierarchy
- **Display** (Gotham Bold, 24,5pt, caixa-alta): título de capítulo ("SUMÁRIO", "INTERPRETAÇÃO PEDAGÓGICA DA ESCALA"), sempre com sublinhado amarelo de 3pt.
- **Número de capítulo** (Gotham Light, cerca de 60pt): o "1", "2", "3", "4" isolados na página de abertura e no sumário.
- **Headline** (Gotham Bold, 13,6–15pt, caixa-alta): título de seção ("SÉRIE HISTÓRICA DA HABILIDADE", "TAREFAS POR NÍVEL DE COMPLEXIDADE"), precedido de quadrado amarelo de 6pt.
- **Title** (Gotham Book/Medium, 11–13pt): subtítulo de etapa ("Elaboração dos itens", "RESULTADOS DE PARTICIPAÇÃO").
- **Kicker** (Gotham Light/Book, 8–10pt, caixa-alta, espaçamento largo): "RESULTADOS GERADOS PELA TEORIA…", "PÁGINA 7", "LÍNGUA PORTUGUESA".
- **Body** (Proxima Nova Regular 10/15pt, justificado): texto corrido em 1 ou 2 colunas. Abre com capitular de 3 linhas na primeira página do capítulo.
- **Dado** (Proxima Nova Condensed Light 9pt, com verbo em Semibold): linhas da escala, descrição das habilidades e tabelas BNCC. O verbo da habilidade ("**Distinguir** fatos de opiniões…") vai em Semibold.
- **Label** (Proxima Nova 8pt): números do eixo da escala, legendas e notas (nota em Light Italic 8pt).
- **Running head** (Gotham Light 5pt, espaçamento de cerca de 0,3em): "SAEGO . 2025" e "REVISTA DA ESCOLA . LÍNGUA PORTUGUESA".

### Named Rules
**A Regra das Três Vozes.** Gotham fala (títulos), Proxima lê (texto) e a Condensed mostra (dado). Não troque os papéis.

**A Regra do Verbo em Negrito.** Em qualquer descrição de habilidade, o verbo de comando vai em Semibold e o resto em Light.

## Layout

- **Página:** 210 × 280 mm (595 × 794pt), em spreads.
- **Margens:** cerca de 75pt (26 mm) na lateral do texto corrido, com coluna de texto entre 77pt e 521pt. Páginas de dado (escala, BNCC) abrem para cerca de 42pt.
- **Colunas:** 1 coluna larga para texto introdutório e 2 colunas com gutter de cerca de 18pt para texto corrido. As páginas de infográfico em spread usam composição livre, ligada por linhas de chamada.
- **Cabeçalho de página:** fio cinza de 0,5pt em y≈34pt de ponta a ponta. Na borda externa fica um **tab amarelo** de 37 × 6pt com um quadrado preto de 3pt na ponta, seguido do folio em Gotham Bold 14pt. Na outra ponta, o running head em 5pt.
- **Ritmo vertical:** linha de base de 15pt no texto. Seções são separadas por grandes respiros (40–60pt), não por fios.
- **Abertura de capítulo:** página quase vazia com o número em Gotham Light gigante e ilustração ou foto cinza esmaecida ao fundo.
- **Densidade:** baixa no texto e alta nas páginas de dado. A página de descritor concentra quatro blocos (cabeçalho, pré-requisitos, escala, BNCC) e mesmo assim deixa branco à direita do eixo.

## Elevation & Depth

Plano. Não há sombra projetada em nenhum elemento. A profundidade vem de **camadas tonais**: retângulos cinza-claro (`#f6f6f6`) deslocados atrás de caixas brancas com borda, painéis cinza que "vazam" da margem e círculos cinza muito claros e enormes no fundo das páginas de abertura e sumário. Fotos aparecem em cinza esmaecido (cerca de 20% de opacidade) quando são fundo.

**A Regra do Deslocamento.** Para destacar uma caixa, desloque um retângulo cinza ou um contorno amarelo alguns pontos atrás dela. Nunca use sombra.

## Shapes

- **Canto vivo em tudo:** caixas, chips, painéis, células de tabela e fotos recortadas.
- **Exceções circulares:** bolinhas de legenda (cerca de 8pt), marcadores de etapa e fotos circulares de 40pt usadas como vinheta.
- **Fios:** 0,5pt cinza (`#c6c6c6`) para tabela e divisória, 0,5pt preto para separar padrões na escala e 3pt amarelo como sublinhado de título.
- **Marcadores:** quadrado amarelo de 6pt antes de headline e quadrado preto de 3pt como "nó" nas pontas de fio e linha de chamada.
- **Linhas de chamada:** fio preto de 0,5pt em ângulo reto (forma de L) ligando caixas e terminando em quadradinho preto. É a assinatura dos infográficos (linha do tempo, "Avaliação e currículo").
- **Contorno amarelo vazio:** retângulo de 1,5pt amarelo sem preenchimento, usado como acento deslocado.

## Components

### Chip do descritor
Retângulo amarelo de canto vivo com "D01" em Proxima Nova Bold de cerca de 13pt preto, seguido da descrição em Regular 10pt na mesma linha. É a âncora de cada página de descritor.

### Faixa do ano
Barra cinza (`#f5f5f5`) de largura total com "9º ANO DO ENSINO FUNDAMENTAL" centralizado em Gotham Medium de cerca de 10pt. Na seção "Itens", vira barra com número em círculo amarelo e cor de etapa (rosa, magenta ou vinho).

### Quadro de pré-requisitos
Caixa branca com borda cinza de 0,5pt. Título em Proxima Semibold 9pt ("Pré-requisitos necessários…") e lista em **2 colunas** com marcador quadrado preto pequeno (Wingdings).

### Escala de proficiência (componente-assinatura)
- Eixo vertical de 0 a 500, com ticks a cada 25 pontos (Proxima Light 8pt, traço curto à direita do número).
- **Barra vertical estreita** (cerca de 6pt) pintada em segmentos com a rampa verde dos 4 padrões: Padrão 01 embaixo e mais claro, Padrão 04 em cima e mais escuro.
- Rótulos dos padrões à esquerda ("Abaixo do básico", "Básico", "Proficiente", "Avançado") em Proxima Semibold 9pt, cada um entre **fios pretos** que marcam os cortes. O valor do corte vai em **negrito** (200, 250, 300).
- À direita, uma linha por nível (fio cinza fino entre níveis). O texto da tarefa fica em Condensed Light 9pt e nível sem tarefa recebe "–". Os fios pretos dos cortes atravessam a largura toda.

### Rodapé BNCC
Faixa cinza no pé da página com o título "BNCC" precedido de quadrado amarelo. Abaixo, uma tabela de 2 colunas: rótulos em células brancas (Proxima Semibold 9pt) e valores em Condensed Light sobre o cinza, com fios brancos entre as linhas.

### Tabela de padrões (cortes)
Cabeçalho em Proxima Semibold sem fundo. Cada célula de faixa ("Até 200", "201 a 250"…) é pintada com a cor do padrão e o texto vai em Semibold centralizado (branco no Avançado). Antes da tabela vem a etiqueta amarela "Língua Portuguesa" seguida de fio amarelo.

### Número de etapa
"03", "04"… em Gotham Bold de cerca de 20pt sobre um retângulo amarelo justo, com quadradinho preto no canto inferior direito. Logo abaixo, o título em Gotham Book sobre retângulo branco, ligado a outros passos por linhas de chamada em L.

### Painel e nota
- **Painel cinza:** fundo `#f6f6f6` com padding generoso, para texto de apoio ("Proficiência — É um valor estimado…").
- **Nota com marcador:** caixa com borda cinza e quadrado amarelo de 6pt "pendurado" na borda esquerda.
- **"Isto é:" / "Note que":** bloco amarelo sólido com o rótulo em negrito, fio curto e painel cinza com a explicação.

### Tabelas de dados
Sem bordas verticais. Cabeçalho em Proxima Semibold caixa-alta 8pt e linhas separadas por fio cinza claro. A coluna de valor (ACERTO) é pintada com a cor do semáforo. Ícones ✓ e ✗ em quadrado verde e vermelho aparecem no exemplo da TRI.

## Do's and Don'ts

### Do:
- **Do** use `#ffed00` como marca-texto em peças pequenas (chip D01, sublinhado de 3pt, marcador de 6pt) e no máximo um bloco amarelo grande por tela.
- **Do** pinte os Padrões 01–04 com a rampa verde do claro ao escuro e separe os padrões na escala com fio preto e o valor do corte em negrito.
- **Do** use a condensada light com o verbo em semibold para todo texto pedagógico denso (linhas da escala, BNCC, habilidades).
- **Do** crie profundidade com retângulos cinza `#f6f6f6` deslocados, sem sombra.
- **Do** ligue elementos relacionados com linhas de chamada em ângulo reto terminadas em quadradinho preto.

### Don't:
- **Don't** arredonde cantos de caixas, chips ou tabelas. Círculo só em legenda e vinheta.
- **Don't** use cor fora do amarelo que não codifique dado, e não reaproveite a rampa de uma família de dado em outra.
- **Don't** pinte fundo de página ou de seção inteira de amarelo.
- **Don't** use a ilustração verde-limão como fundo atrás de texto ou dado. Ela fica em capas, aberturas e margens.
- **Don't** troque Gotham por Proxima em título nem o inverso no texto corrido.

## Notas para o sistema web

1. **Conflito com o editor:** `DESIGN.md` (editor) e `PRODUCT.md` usam por padrão as cores de padrão `#f72628`, `#ff8d43`, `#b3ccff` e `#0ed3ff` (vermelho→azul). A revista impressa SAEGO 2025 usa a **rampa verde** acima. Como as cores já são dado do projeto, a rampa verde pode entrar como predefinição "SAEGO 2025" sem mudar o modelo.
2. **Peças com melhor custo de reuso na revista web (`escala.html`):** chip do descritor, escala vertical com barra segmentada, quadro de pré-requisitos em 2 colunas, rodapé BNCC e cabeçalho com tab amarelo.
3. **Fontes:** Gotham e Proxima Nova exigem licença web. Sem ela, use Montserrat, Figtree e Barlow Semi Condensed auto-hospedadas (CSP sem CDN).
