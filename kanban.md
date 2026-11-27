# Kanban — revista-express

## Backlog
- **K-048** Etapa 11 — Redesenho das telas pelo Figma (menu Projetos · Modelos · Impresso) e retirada dos botões de criar matriz, template e parceiro · D-277 · mapa de páginas em `docs/telas/mapa-de-paginas.md` (25/11)
- **K-031** Fase 5 do F2: animação por passo (desejável)
- **K-033** S18 — E2E da temporada

## Doing

## Review
- **K-055** F2 de MT: bloco "Tarefas por nível de complexidade" com barrinhas 1→4 e texto da habilidade, no mesmo `f2.svg` (`feat/f2-mt`); ficha do item de MT com campo Habilidade · D-305 · suíte 1099 OK; E2E não rodado
## Done
- **K-054** Design system do Figma (Telas – v1 e Componentes) extraído para HTML em `docs/design-system-figma/` (`feat/design-system-figma`): tokens, componentes, 23 telas, sem mexer em `app/`; conferido no navegador; na `main` com push · insumo da K-048 · 2026-11-27 · D-304
- **K-053** Mescla explícita de marca e habilidade no referencial do F2 (`feat/f2-mescla`): toggles "Junta com a de cima" por coluna, vazio sem juntar fica vazio, marca juntada = uma letra centrada; UI com elo entre etapas e célula única (D-303) · suíte 1093 OK; na `main` com push · 2026-11-27 · D-301 a D-303
- **K-052** Linhas da tabela "Descrição das habilidades" do F2 crescem com o texto (`feat/f2-linhas-crescem`): alturas estimadas no servidor, Progressão e viewBox descem; `test_f2` e `test_empacotar` OK; na `main` (sem push) · 2026-11-27 · D-300
- **K-051** Títulos dos blocos Descrição e Progressão do F2 citam a BNCC (`feat/f2-titulos`): `f2.svg` e zip gabarito regenerado; `test_empacotar` e `test_f2` 32 OK; na `main` com push · 2026-11-26 · D-299
- **K-050** Infográficos de LP preenchidos por cópia do seed dos dois Word (`feat/infografico-lp`): seed (`scripts/docx_infografico.py`), `carregar_infograficos` (só o vazio; recarga `--anterior`) e cascata para o infográfico novo; Django 1086 OK, E2E 176 passaram sem pulos; na `main` com push · 2026-11-26 · D-298
- **K-049** F1 sem a seção "Fechamento" (`feat/f1-sem-fechamento`): regra, página, seeds, migração 0028 (versão nova dos templates F1 e cópias apagadas) e testes Django e E2E; na `main` com push (Django verde, E2E dos 4 specs não rodado) · 2026-11-25 · D-296
- **K-034** Etapa do projeto (`feat/etapa-do-projeto`): etapas 2 a 10 do plano de 24/11 (D-276) · etapa 2 de 11 feita em 24/11: `main` mesclada na branch, migration `0026`, decisões D-279 a D-281, suíte 968 OK · etapa 3 de 11 feita em 24/11: `criar()` só aponta para canônica e pendência `etapa_sem_base` (D-282), suíte 971 OK · etapa 4 de 11 feita em 24/11: tarefa 5 (`matriz_id` nulo) revisada e fechada (D-283), suíte 974 OK; para a etapa 7: editor da matriz e link do impedimento de exclusão com etapa de projeto, rótulo "Matriz:" na aba Passos · etapa 5 de 11 feita em 24/11: `concluir()` e `escolher()` da revisão em 3 vias (D-284), suíte 992 OK; para a etapa 8: a tela chama `concluir` sob o bloqueio e relê a etapa antes de cada `revisao()` · etapa 6 de 11 feita em 24/11: a cascata transfere a etapa do projeto para o projeto recriado (D-285), suíte 994 OK · etapa 7 de 11 feita em 24/11: apontar a etapa não canônica na aba Matriz do projeto, com o modal de impacto, e editor da matriz abrindo etapa de projeto (D-286), e desfazer o apontamento com confirmação forte (D-287); plano revisto pela edição local por projeto (D-288): etapa 7b feita em 24/11: "Editar só neste projeto" para toda etapa da matriz, a cópia sempre vale, sai a pendência de escolha e a coluna `preferida` (D-289, migration 0027); correção em 24/11: descritor com código fora de "D" + 2 dígitos sumia da revista (D-290) e a revista passa a seguir a ordem dos descritores do editor (D-291); etapa 8 de 11 feita em 24/11: tela "Revisar mudanças da base" em `/ui/revisao/<pk>/`, com entradas na aba Matriz e no editor da cópia, e 2 defeitos do `concluir` corrigidos (D-292), suíte 1061 OK; correção do diff da última palavra (D-293); etapa 9 de 11 feita em 25/11: aviso fixo no editor da matriz e linha "Abre revisão em" no modal de impacto (D-294), suíte 1065 OK; etapa 10 de 11 feita em 25/11: spec E2E da etapa do projeto (3 testes, E2E inteiro 176 passaram), "Desfazer a cópia" na cópia local, erro 500 do "Novo descritor" na cópia corrigido e documentos conferidos contra o código (D-295), suíte 1067 OK; mesclada na `main` com o "ok" do usuário · 2026-11-25 · D-276 a D-295
- **K-047** Etapa 1 de 11 — Carga com etapas não canônicas: `importar_cortes` cria as 7 etapas que a Somativas pede, grava "100, 200, 300" onde falta corte e atribui a Comunitária; banco da 8002 refeito (33 parceiros, 232 cortes, 84 arbitrários, 66 revistas); mesclada na `main` (suíte 922 OK) · 2026-11-24 · D-278
  nota: o banco do dev (8000) ainda tem a carga antiga
- **K-046** `ano.spec` cria o próprio parceiro e o helper do painel espera o HTMX ligar; E2E inteiro 170 passaram, 0 falhas; mesclado na `main` · 2026-11-18 · D-275
- **K-045** Controles `<c-input>`, `<c-select>`, `<c-textarea>` (45 convertidos, 3 crus) e `classe_css` nos widgets; mesclados na `main` (suíte 918 OK, E2E 169 passaram, 1 falha conhecida do `ano.spec`) · 2026-11-18 · D-274
- **K-044** Componentes `<c-icone>` (68 svgs, 26 desenhos), `<c-modal>` (7), `<c-botao-icone>` (11) e `<c-voltar>` (13) nas telas B; mesclados na `main` (suíte 916 OK, E2E 147 passaram) · 2026-11-18 · D-272 · D-273
- **K-043** Migração dos componentes das telas B para django-cotton: cabeçalho, campo, selo, aviso, card e botão (219 usos convertidos, 29 crus com motivo na catraca); mesclada na `main` (suíte 910 OK, E2E 149 passaram) · 2026-11-18 · D-271
- **K-042** Demo: página Projeto (detalhe) refeita com django-cotton (7 componentes, suíte 901 OK, E2E 2/2, capturas), aprovada pelo usuário · 2026-11-18 · D-270
- **K-040** Botão "Copiar de <ano>" some sem ano anterior e script `scripts/povoar-banco-2026.sh` (banco do zero com a carga 2026, provado idêntico ao dev), com seção no README; mergeado na `main` · 2026-11-12 · D-265 · D-266
- **K-039** Bancos Docker das worktrees apagados: stacks `carga2026` e `revista-express-carga-2026` (volumes) e 30 imagens antigas; dev da 8000 intacto · 2026-11-12 · D-262
  nota: 95 volumes anônimos sem dono ficaram (pergunta em aberto)
- **K-032** S17 — Carga 2026: comando `importar_cortes` (33 parceiros, 148 cortes pela cascata), conferido pelo usuário nas telas B e mergeado direto na `main` (suíte 900 OK) · 2026-11-12 · D-261
  nota: 40 cortes sem dado na planilha (RS, Angra, Rio (município), SP, AL, RJ, TO…); a planilha de cortes é a de 2025: a Pedagógica valida os valores
- **K-030** `integ/f2-gerado` na `main` pelo PR #12 (fases 1 a 4 do F2 + K-038); bancos locais apagados e dev do zero · 2026-11-11 · D-249 · D-260
  nota: no deploy, toda revista impressa com infográfico fica "pendente" no impresso uma vez (D-256); apagar à mão os `media/f2/*.svg` órfãos; backup antes (a 0024 apaga as colunas do SVG)
- **K-038** Ajustes do F2 depois da Demonstração: cartão do tour só com título, fechamento das tarefas na página, modal ❶ sem texto em dobro, ❷/❸ certos, referencial junto do ❷, caixas de 4 linhas, "Do template" no cartão; mergeado na `integ/f2-gerado` (Django 898 OK, Playwright 170/170) · 2026-11-11 · D-258 · D-259
- **K-029** Fase 4 do F2: sai o SVG enviado, impresso com os textos dos infográficos, `tarefas-fechamento` sem o parágrafo do D05; mergeada na `integ/f2-gerado` por fast-forward (Django 894 OK, Playwright 169/170) · 2026-11-11 · D-256 · D-257
- **K-028** Fase 3 do F2: tela dos infográficos, mergeada na `integ/f2-gerado` por fast-forward (Django 910 OK, Playwright 169/170) · 2026-11-11 · D-252 · D-254 · D-255
- **K-037** Redesign do `kanban.html` com JS puro (busca, recolher colunas e checklist), `eefa697` na `main` de `~/.claude/skills/kanban` · 2026-11-10
- **K-027** Skill `kanban`: quadro substitui o "Plano" do `state.md` · 2026-11-10 · D-253
- **K-036** `integ/docs-atualizacao` na `main` (PR #9, conflito do `state.md` resolvido) · 2026-11-10
- **K-025** Abrir ano na `main` (PR #8) · 2026-11-10 · D-246
- **K-035** Apagar as 78 worktrees mergeadas e limpas (o checkout da `main` ficou) · 2026-11-10
- **K-026** Auditoria do código: itens rápidos e `pendencias_f1/f2` entram na T1 da fase 3 · 2026-11-10 · D-252
  nota: D-252 ainda sem commit na worktree `revista-express-f2-f2`
- **K-024** Conselho da fase 2 do F2 + T0 da fase 3 · 2026-11-10 · D-249 a D-251
- **K-023** Fase 2 do F2: render, template de 9 seções, páginas separadas · 2026-11-10 · D-242 a D-248
- **K-022** Fase 1 do F2: tabelas dos infográficos e cascata Alfa/Outras Etapas · 2026-11-06 · D-233 a D-235
- **K-021** Fase 0 do F2: protótipo do SVG gerado · 2026-11-06 · D-228
- **K-020** S16 — Abrir ano
- **K-019** S13 — Impresso + planilhas
- **K-018** S12 — Painel + Validado
- **K-017** S11c — Admin: projeto, variáveis, arquivos, lote
- **K-016** S11b2 — Admin: cópia por seção
- **K-015** S11b1 — Admin: templates
- **K-014** S11a — Admin: cadastros, cortes, matriz
- **K-013** S15 — Zip por revista
- **K-012** S08 — Página única F1 + F2
- **K-011** S07 — Resolver, foto, hash, pendências
- **K-010** S14 — Perfis e permissões
- **K-009** S10 — Bloqueio
- **K-008** S09 — Serviço de SVG e capa
- **K-007** S06 — Cascata dos cortes
- **K-006** S05 — Templates: formato, validação, seed
- **K-005** S04 — Cadastros iniciais + importador de matriz
- **K-004** S03b — Revista JS/CSS para 2 a 5 padrões
- **K-003** S03 — Parceiro_ano, corte, projeto, revista, texto, controle
- **K-002** S02 — Modelos de cadastro e matriz + FK composta
- **K-001** S01 — Esqueleto Django + PostgreSQL + Playwright
