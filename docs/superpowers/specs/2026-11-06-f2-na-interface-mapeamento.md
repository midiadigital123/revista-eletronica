# F2 preenchido na interface: mapeamento de viabilidade, tecnologia e tempo

Data: 2026-11-06. Só avaliação; nenhum código foi alterado. Linhas citadas são do commit `f5b65b0`.

Pedido: o F2 passa a ser montado pelo sistema sobre **um template único com passos fixos**; cada
passo é preenchido nas telas B; todo projeto segue a lista, mas pode **desligar passos**, e passo
desligado não aparece (desenho, tour, impresso).

## 1. Como o F2 funciona hoje

1. O design entrega um SVG por revista (parceiro × componente), textos em curvas, ids nomeados à
   mão (D-108). Upload na ficha da revista, passo "Arquivos" (`app/nucleo/templates/ui/parciais/revista_arquivos.html:15-36`,
   `app/nucleo/urls/ui_revista.py:326-349`), até 3 MB (`app/nucleo/servicos/arquivos.py:29`).
2. O SVG passa por lista branca de tags/atributos/CSS e ganha prefixo `f2-` (`arquivos.py:43-50`,
   `sanitizar_svg` em `arquivos.py:261-278`, `receber_svg` em `:280-290`); `foreignObject` e `script` saem com os filhos (`:50`).
3. O template F2 é um `.hbs` com seções `abertura`, `passoN`, `dlg-*` (`app/nucleo/texto.py:34-35`, validação em `:85-96`);
   cada seção exige um id no SVG: `passoN` → `passoN`, `dlg-xx` → `btn-action-xx` (`arquivos.py:370-381`).
   Seed real: `app/templates_seed/2026/f2-lp.hbs` = `abertura`, `passo1`..`passo4`, `dlg-p2`, `dlg-p3`, `dlg-p4-i1`..`i4` ("Conteúdo em breve").
4. A página única injeta o SVG inline em `<div id="revista">` (`app/nucleo/templates/revista/index.html:182`) e os
   `<dialog>` dos modais (`:200-210`); `html.py:46-60` monta o JSON do tour a partir das seções e `:77-81` lê o SVG do storage.
5. `f2-init.js:13-22` configura o svg-tour (cópia fiel, D-103), `:29-48` liga `dlg-xx` ao botão `f2-btn-action-xx`.
6. SVG real (`app/nucleo/tests/fixtures/f2-lp.svg`, 837 KB, viewBox 1190,6 × 793,7): grupos `f2-fundo`, `f2-titulo`, `f2-passo1`..`4`, `f2-linhas`, botões `f2-btn-action-p2`, `p3`, `p4-i1..i4`.
7. O que cada bloco mostra (SAEGO LP 2025): **passo1** cartão amarelo "Descritor" + foto; **passo3** (direita, alto) tabela
   "Descrição das habilidades no referencial curricular do estado" (1EF–3EM × I/A/C/R × código BNCC + texto) + legenda;
   **passo2** (direita, baixo) linha "Progressão da habilidade" 1EF–3EM com I/A/C/R; **passo4** (esquerda, baixo)
   "Tarefas por nível de complexidade" (D05 2EF, D09 5EF, D12 9EF, D12 3EM) + 4 miniaturas "Itens" com botão +.
   O impresso (`docs/fontes/2025/PDFs Matriz Comunitária/SAEGO_2025_RE_LP Web.pdf`, pág. 31) tem ainda "Série histórica" e "Percentual de acerto", que o SVG web não tem.
8. Os textos do tour estão trocados: `passo2` fala em "Itens por ano/série, percentual de acerto" mas enquadra a progressão;
   `passo3` fala em "Progressão" e enquadra a tabela (`state.md:1850`). Confirmado na imagem do SVG.
9. "Validado" exige SVG e todos os ids (`resolver.py:370-375`); hash inclui `svg_sha256` (`resolver.py:283`); o impresso compara só as seções (`resolver.py:299-306`); planilha F2 = uma linha por seção (`planilhas.py:143-158`).
10. Animação aprovada em demo (`example/f2-animado-tour/`): acha as peças pela **ordem dos filhos** do SVG (`animacao.js:186-205`) e desliga sozinha se a contagem mudar.

## 2. O que "preenchido todo na interface" exige

### Passos canônicos propostos (nomes fixos no código, como `Fasciculo`, D-122)

| Passo | Mostra | Dados / de onde vêm | Desligável |
| --- | --- | --- | --- |
| `abertura` | Título "Avaliação e currículo" + componente + texto do painel do tour | Seção `abertura` do template (já existe); `Componente.nome` | não |
| `descritor` | Cartão com código e descrição da habilidade escolhida | **Novo**: escolha do descritor por etapa (ver 5.1); `Descritor.codigo`, `descricao` (`app/nucleo/models/matriz.py:63-72`) | não |
| `habilidades` | Tabela referencial curricular 1EF–3EM × I/A/C/R + código + texto; legenda | **Novo** no banco: `DescritorProgressao` (descritor × ano escolar → marca, código, texto). Não está em `docs/fontes/2025` nem na matriz importada (`importar_matriz.py` só traz `praticas`, `conhecimento`, `habilidades_relacionadas`, `habilidade_correspondente`) | sim |
| `progressao` | Linha 1EF–3EM com I/A/C/R | Derivado de `DescritorProgressao` (só a marca) | sim |
| `tarefas` | Etapa × descritor × item ("Ver item") | `Tarefa.arquivo`, `texto_alternativo`, `inicio`/`fim` (`matriz.py:88-98`) do descritor escolhido em cada etapa; modal "Ver item" já existe no F1 (`index.html:191-198`) | sim |

Modais (`dlg-habilidades`, `dlg-progressao`): texto livre do template, com `{{x}}` (`docs/variaveis.md`), como hoje.
`dlg-p4-i1..i4` somem: o botão do item abre o arquivo da tarefa, não um texto.

Desejável, fora da 1ª versão: `acertos` (percentual de acerto por etapa) e `serie_historica` (2022–2025). Dados não existem no banco nem nas planilhas de `docs/fontes/2025/planilhas importantes/` (só cortes e níveis).

### O que muda de "SVG do design" para "render do sistema"

- O desenho deixa de ser arquivo: vira template Django gerado do resolvido. Sem upload, sem sanitizador, sem ids por convenção, sem gabarito CSV (`arquivos.py:384-396`, `ui_revista.py:382`).
- Textos viram texto real: acessíveis (leitor de tela, zoom do navegador, busca), entram no resolvido → no hash (`resolver.py:293`) e no "o que mudou" (`resolver.py:299-306`) sem código extra.
- A fonte passa a ser a da página. Hoje o F1 declara `"Proxima Nova"` e cai no sistema (`static/revista/f1/styles.css:42-44`; não há `@font-face` nem `.woff2` em `static/revista/`). Proxima Nova é comercial: ou o design fornece webfont licenciada (e a CSP ganha `font-src 'self'`, `index.html:12`), ou o F2 usa a mesma pilha de fallback do F1. Sem decisão, fallback.
- Erro de ordem de camadas da animação acaba: o sistema emite ids estáveis por peça.

## 3. Desligar passos

### Implicações

- **Layout**: o SVG atual tem posições fixas. Com blocos opcionais, o render calcula posições: lista de blocos ligados → grade de 2 colunas (esquerda: descritor, tarefas; direita: habilidades, progressão), cada bloco com altura fixa por tipo e texto longo com `-webkit-line-clamp` (o texto inteiro fica no modal). Conectores desenhados entre cartão e bloco a partir das posições calculadas.
- **Tour**: os passos do JSON (`html.py:46-60`) passam a ser só os ligados; numeração e minimapa seguem (o svg-tour lê `steps` e os `getBBox` dos alvos, `svg-tour.js:1053`).
- **Impresso**: planilha F2 lista só blocos ligados (`planilhas.py:143-158`); a foto guarda a lista (`foto.py:30-33`), então religar um passo aparece no "o que mudou".
- **Validado**: a lista de passos ligados entra no resolvido → mudar derruba o hash; a gravação passa pelo modal de impacto (D-202, `servicos/impacto.py:23`). Pendência nova por passo ligado sem dado (ex.: `habilidades` ligado e `DescritorProgressao` vazio).

### Onde fica a escolha

| Opção | Prós | Contras |
| --- | --- | --- |
| **A. Coluna no Projeto** `f2_passos_desligados` ArrayField (recomendada) | É o que o pedido diz ("o projeto informa"); vale para LP e MT de uma vez; histórico já existe (`models/projeto.py:96`); CHECK `<@ ARRAY[...]` no banco; tela do projeto já tem o padrão de variáveis + modal de impacto (`templates/ui/projeto/projeto.html`); nada a clonar no `abrir_ano` (projeto nasce da cascata, `abrir_ano.py:3-5`) | Não dá para desligar só no MT. Se precisar, vira a opção B depois |
| B. Coluna em `RevistaFasciculo` (linha F2) | Por revista; herança "projeto → revista" seria só o valor inicial | Duas telas para a mesma escolha; herança é código a mais |
| C. Tabela `revista_passo` (revista × passo × ligado) | Permite ordem e dados por passo | Tabela, FK composta com ano, histórico, permissões e migração de grupos para um booleano |

Flag por seção do template (`## passo` com marcador) foi descartada: o template é compartilhado entre projetos (D-104); desligar lá desliga para todos.

## 4. Opções de tecnologia de render (ranqueadas)

Nenhuma precisa de biblioteca nova: Django templates + o `svg-tour.js` já copiado + CSS.

### 1º. SVG gerado pelo servidor, svg-tour mantido (recomendada)

Template Django `revista/f2.svg` emite um `<svg>` com `<g id="f2-<passo>">` por bloco ligado, `<text>` para rótulos curtos e `<foreignObject>` com HTML para textos longos; posições calculadas em Python (`servicos/f2.py`).

- Ganha: zoom, modais, teclado, foco e `svgtour:change`/`svgtour:mode` (`svg-tour.js:1289`, `:1348`) continuam; a animação da demo é portada trocando só `mapear()` (`animacao.js:186-205`) por ids; `prefers-reduced-motion` já tratado (`svg-tour.js:115`, `revista.css:459`).
- Perde/risco: o minimapa serializa o SVG num `<img>` (`svg-tour.js:578-580`): HTML dentro de `foreignObject` só aparece lá se o CSS estiver **dentro** do SVG (`<style>`); senão, `minimap: false` (`svg-tour.js:245`). Texto longo não reflui dentro do SVG: altura fixa por bloco + clamp.
- Sanitizador (D-125): sai. O SVG gerado nunca é input do usuário; o escape do Django cobre os dados. CSP (`index.html:12`) não muda.
- Zip (`file://`): igual a hoje, o SVG já vai inline (`empacotar.py:115`).
- Acessibilidade (D-157): melhor que hoje (texto real; `role="button"` nos `+` continua em `f2-init.js:37-48`).

### 2º. HTML + CSS por blocos, tour leve próprio

Seções `<section id="f2-<passo>">` em grid; "tour" = lista de passos que rola até o bloco e esmaece os outros (~80 linhas de JS); modais `<dialog>` como hoje.

- Ganha: reflow nativo (texto longo, celular), nada de posição calculada, acessibilidade mais simples, menos código que a opção 1.
- Perde: zoom/pan, minimapa, "câmera" do tour e o `svg-tour.js` inteiro; a animação da demo (transform em `<g>`, conector "viajando") precisa ser refeita em CSS por bloco; o E2E `pagina.spec.ts:70` (tour completo) é reescrito.
- É o plano B se o protótipo do 1º mostrar `foreignObject` ruim no zoom ou no minimapa.

### 3º. Híbrido: SVG fixo de fundo + camadas HTML por cima

Fundo (blobs, título) em SVG estático e blocos HTML posicionados por cima.

- Perde: duas coordenadas (viewBox × px) para o zoom do svg-tour manter alinhadas; conectores entre SVG e HTML dependem de JS medindo o DOM. Mais código que as duas acima sem ganho claro. Descartada.

### 4º. Manter o SVG do design e só preencher textos

Descartada: o SVG não tem `<text>` (textos em curvas, D-103); "desligar passo" exigiria um SVG por combinação.

## 5. Mudanças no sistema, por área

Tamanhos: P ≤ 2 h, M ≈ meio dia, G ≈ 1 dia ou mais, com Claude Code.

### 5.1 Modelos e migrações

| Item | Arquivos | Tam. |
| --- | --- | --- |
| `DescritorProgressao` (descritor, ano escolar 1EF..3EM como lista fixa no código, marca I/A/C/R, codigo, texto; FK composta com ano via `nucleo/db.py::fk_composta` + `reverse_sql`; `HistoricalRecords`; teste de `pg_constraint`) | `models/matriz.py`, migração, `tests/test_constraints.py` | M |
| `RevistaF2Descritor` (revista × etapa → descritor; FK composta; CHECK: etapa com corte) | `models/revista.py`, migração | M |
| `Projeto.f2_passos_desligados` ArrayField + CHECK de subconjunto | `models/projeto.py`, migração | P |
| Remover `svg_f2`, `svg_sha256`, `svg_ids` e constraints (`models/revista.py:31-33`, `:52`, `:54`, `:57`) | migração com `reverse_sql` | P |
| `abrir_ano`: clonar `DescritorProgressao` junto com descritores (`abrir_ano.py:96-105` é o padrão) | `servicos/abrir_ano.py` | P |

### 5.2 Validação do template (`texto.py`)

Seções fixas do F2: `abertura`, `passo-<nome>` só dos passos canônicos, `dlg-<nome>`; `ID_F2` (`texto.py:35`) e `validar` (`:85-96`) recusam o resto. O editor deixa de "adicionar passo/diálogo" (`editor-secoes.js:114-149`, `templates_texto.py:152-154`). Seeds `f2-lp.hbs`/`f2-mt.hbs` reescritos com os nomes novos; migração de dados renomeando `RevistaSecao.secao` das cópias existentes. **M**.

### 5.3 Telas B

| Obrigatório | Arquivos | Tam. |
| --- | --- | --- |
| Projeto: checkboxes "Passos do F2" com modal de impacto (`ImpactoForm`, D-202) | `nucleo/projeto.py`, `templates/ui/projeto/projeto.html` | P |
| Revista › Arquivos: tira o SVG, entra "Descritor do F2 por etapa" (select por etapa com corte) | `nucleo/revista.py:26-27`, `:59-65`, `:267-293`, `ui_revista.py:326-349`, `parciais/revista_arquivos.html` | M |
| Matrizes › descritor: grade "Progressão (1EF–3EM)" 12 linhas + importação por planilha xlsx (openpyxl já usado em `planilhas.py`) | `nucleo/matriz.py`, `parciais/matriz_*.html`, comando ou botão de importação | G |
| Templates › editor: sem botões de estrutura; seções do F2 fixas | `editor-secoes.js:114-149`, `templates_texto.py` | P |
| Impacto do template: tirar "ids que faltam no SVG" (`templates_texto.py:83-86`, `templates/ui/templates/impacto.html`) | idem | P |

Desejável: ação em lote "desligar passo em N projetos" (`nucleo/lotes.py` tem o padrão de matriz/template). M.

### 5.4 Permissões

`editar_matriz` ganha `descritorprogressao` (EDITA + delete), `editar_projeto` ganha `revistaf2descritor` (`permissoes.py:51-57`, `:65-75`) + migração de dados que sincroniza os 4 grupos (regra do `CLAUDE.md`). **P**.

### 5.5 Resolver, render e hash

| Item | Arquivos | Tam. |
| --- | --- | --- |
| `resolver`: `f2` = `{secoes, passos: [...ligados], dados: {descritor: {...por etapa}, progressao: [...], tarefas: [...]}}`; sai `svg_sha256`/`svg_ids` (`resolver.py:283`); pendências `svg`/`ids_svg` (`:370-375`) viram `f2_descritor` e `f2_progressao` | `servicos/resolver.py` | M |
| `impresso_de` inclui `f2.dados` e `f2.passos` (`resolver.py:299-306`); fotos antigas continuam legíveis (`.get`) | idem | P |
| Novo `servicos/f2.py`: layout (posições por bloco ligado) + contexto do `revista/f2.svg`; `html.py:77-81` passa a renderizar em vez de ler o storage; `_tour` só com passos ligados (`html.py:46-60`) | `servicos/f2.py`, `servicos/html.py`, `templates/revista/f2.svg`, `index.html:178-183`, `:200-210` | G |
| `f2-init.js`: `BOTOES_MODAL` por `data-modal` emitido pelo servidor em vez de convenção `f2-btn-action-` (`f2-init.js:29-33`); botão de item abre o `itemModal` do F1 | `static/revista/f2/f2-init.js` | P |
| Foto/hash: nada a fazer; tudo entra pelo resolvido (`foto.py:30-33`, `validacao.py:43-46`) | — | — |

### 5.6 Impresso, zip, demo

- Planilha F2: seções + uma aba "Dados" (descritor por etapa, progressão, tarefas) só dos passos ligados (`planilhas.py:143-158`, `:178`). **M**.
- Zip: tirar a checagem de `svg_sha256` e do arquivo no storage (`empacotar.py:105-108`, `:115-117`); o `f2.svg` já sai inline. **P**.
- `criar_demo`: tirar `receber_svg` (`criar_demo.py:40`, `:103`), entrar progressão e descritor de exemplo. **P**.

### 5.7 Testes

- Django: `test_arquivos.py` perde os testes de SVG (28 testes no arquivo, maioria SVG); `test_preview.py` (13), `test_empacotar.py` (15), `test_ui_revista.py` (33), `test_resolver.py`, `test_painel.py`/`test_ui_painel.py` (pendência `svg`) ajustados; novos: layout por passos ligados, pendências novas, `pg_constraint` dos modelos. **G**.
- Régua (`regua.test.mjs`): sem mudança.
- Playwright: `pagina.spec.ts:70` (tour e `dlg-p2`), `:113`, `:130` (screenshots) e `zip.spec.ts` sobre o gabarito regerado (`REGERAR_FIXTURES=1` em `test_preview`/`test_empacotar`, D-156/D-159); spec novo de "desligar passo" cria o próprio parceiro "E2E …" (D-224/D-225) — nunca edita revista real. **M**.

### 5.8 O que sai e o que fica

Sai: upload e sanitizador do SVG (`arquivos.py:29-290`, ~260 linhas, mais o learning de 29/10), gabarito CSV, `ids_esperados`/`ids_faltando`, campo `arquivo_svg` do form, `app/media/f2/` (80 arquivos de dev, cópias do fixture; `media/` está no `app/.gitignore`), fixture `tests/fixtures/f2-lp.svg` (837 KB).

Fica como compatibilidade transitória: só `example/` (demos) e as fotos antigas com `svg_sha256` no JSON. Não vale manter os dois caminhos (SVG enviado × gerado) no código: dobra testes e telas; o corte é por ano (2026 inteiro passa para o gerado).

## 6. Fases e estimativa

Calibração: S07 + S08 + S15 (resolver, página única, zip) saíram numa sessão de ~6 h em 29/10 (`state.md`, D-156 21:30 → D-159 22:20); as ~20 telas B levaram 5 dias úteis (30/10 → 05/11, ~270 commits). Um "passo" do plano = 1 a 3 h; um dia = 3 a 5 passos. Dias abaixo = dias úteis de uma pessoa com Claude Code, incluindo revisão e testes.

| Fase | Entregável verificável | Otimista | Provável |
| --- | --- | --- | --- |
| 0. Protótipo | `f2.svg` com os blocos `descritor` + `habilidades` a partir de dados fixos, dentro do svg-tour: zoom, minimapa e modal funcionando por `file://`. Decide opção 1 × 2 | 1 d | 1 d |
| 1. Dados | `DescritorProgressao` + `RevistaF2Descritor` + grade/importação xlsx + permissões + `abrir_ano` + testes | 2 d | 3 d |
| 2. Render | `servicos/f2.py` + template + `html.py` + `f2-init.js` + seções fixas do template + seeds + resolver/pendências | 2 d | 3 d |
| 3. Passos desligáveis | Coluna no Projeto + tela + impacto + tour/planilha/hash só com ligados + spec E2E próprio | 1 d | 1,5 d |
| 4. Limpeza | Remover SVG (modelo, sanitizador, telas, zip, demo, fixtures), gabaritos regerados, docs (`regras-de-negocio.md`, `modelo-er.md`, `telas-b.md`) | 1 d | 1,5 d |
| 5. Animação por passo (desejável) | Porta de `example/f2-animado-tour/animacao.js` com `mapear()` por ids gerados | 1 d | 2 d |
| **Total** | | **8 d** | **12 d** (sem a fase 5: 7 a 10 d) |

Coerente com a estimativa anterior de 2 a 3 semanas (`state.md:1852`).

Depende de terceiros (fora da conta):
- **Design**: layout de referência por bloco ligado/desligado (ao menos 3 combinações), fonte e licença web, cores dos blocos.
- **Pedagógica**: planilha do referencial por descritor (1EF–3EM, I/A/C/R, código, texto) para LP e MT; textos canônicos de `abertura`, `dlg-habilidades`, `dlg-progressao`; conferir os textos trocados de `passo2`/`passo3` (`state.md:1850`).
- **Otavio**: separar F1 e F2 em páginas (`state.md:1853`) antes ou depois disto? Afeta `index.html` e o zip, não o render do F2.

## 7. Riscos e perguntas em aberto

Riscos (ranqueados):
1. Dado do referencial curricular não existe em formato estruturado: sem a planilha da Pedagógica, a fase 1 vira digitação de ~500 linhas. Mitigação: importação xlsx no mesmo formato da tela.
2. Texto longo em SVG não reflui: bloco `habilidades` com 12 linhas × textos de 400 caracteres estoura a altura fixa. Mitigação: clamp + modal; ou opção 2 (HTML) se o protótipo mostrar que não serve.
3. Minimapa do svg-tour com `foreignObject` (`svg-tour.js:578-580`): pode sair sem estilo. Mitigação: CSS dentro do SVG ou `minimap: false`.
4. Hash de toda revista muda na virada (resolvido novo): todas as revistas validadas de 2026 perdem o "Validado" de uma vez. Mitigação: fazer a virada antes da validação em massa, ou avisar.
5. Fonte: Proxima Nova sem licença web → o F2 gerado fica diferente do impresso. Mitigação: fallback do F1 (já é assim no F1 hoje).

Perguntas:
1. Qual é a lista final de passos e o nome de cada um (proposta na seção 2)? — Pedagógica + Otavio.
2. A escolha de desligar é por projeto (LP e MT juntos) ou por revista? — Otavio.
3. Existe a planilha do referencial por descritor (1EF–3EM) para LP e MT 2026? Em que formato? — Pedagógica.
4. Webfont licenciada do desenho (Proxima Nova ou substituta) ou fallback do sistema? — Design.
5. "Percentual de acerto" e "Série histórica" (só no impresso) entram no F2 web algum dia? Define se o modelo prevê dados por ano. — Pedagógica.

## 8. Recomendação

1. Começar pela **fase 0 (1 dia)**: `f2.svg` gerado com `descritor` + `habilidades` em `foreignObject`, dentro do svg-tour atual, aberto por `file://`; é o que decide entre SVG gerado (opção 1) e HTML por blocos (opção 2).
2. Em paralelo, pedir à Pedagógica a planilha do referencial (risco 1) e ao design a referência de layout com passo desligado.
3. Modelo: coluna `f2_passos_desligados` no Projeto; dados novos em `DescritorProgressao` e `RevistaF2Descritor`, com FK composta e histórico como o resto.
4. Não fazer agora: ação em lote de passos, `acertos`/`serie_historica`, manter upload de SVG em paralelo, animação por passo antes do render estar pronto.
5. Total provável: 8 a 12 dias úteis (7 a 10 sem a animação), mais a espera por design e Pedagógica.
