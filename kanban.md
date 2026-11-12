# Kanban — revista-express

## Backlog
- **K-034** Etapa do projeto (`feat/etapa-do-projeto`): 14 commits fora da `main`, tarefa 5 em WIP · pausada
  nota: parada por decisão do usuário em 10/11; worktree `revista-express-etapa` removida em 11/11 (limpa; a branch `feat/etapa-do-projeto` `d0a1954` fica no git e no GitHub: recriar com `git worktree add`); ao retomar, renumerar a `0020_etapa_do_projeto` para depois da 0025
- **K-031** Fase 5 do F2: animação por passo (desejável)
- **K-033** S18 — E2E da temporada

## Doing

## Review

## Done
- **K-041** Proposta de nova UI/UX em demo clicável (`example/ux-proposta/`): 77 páginas, direção "régua de proficiência", dados fictícios, `app/` intacto; aprovada pelo usuário em 12/11, commitada e enviada na `feat/ux-proposta` (sem merge na `main`) · 2026-11-12 · D-267
  nota: 3 achados do revisor ficaram de fora de propósito (abas de Parceiros, barra Gravar na Matriz, legenda de Hoje); a direção ainda não virou plano de implementação no Django
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
