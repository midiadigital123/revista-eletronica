# Kanban — revista-express

## Backlog
- **K-034** Etapa do projeto (`feat/etapa-do-projeto`): 14 commits fora da `main`, tarefa 5 em WIP · pausada
  nota: parada por decisão do usuário em 10/11; branch e worktree `revista-express-etapa` ficam como estão
- **K-029** Fase 4 do F2: remover o SVG enviado, impresso com os infográficos, docs
- **K-030** Merge da `integ/f2-gerado` na `main`, com as fases 1 a 4 juntas (D-249)
- **K-031** Fase 5 do F2: animação por passo (desejável)
- **K-032** S17 — Carga 2026 + desligar o antigo
- **K-033** S18 — E2E da temporada

## Doing
- **K-028** Fase 3 do F2: tela dos infográficos (resolve a pendência `infografico`) · desde 2026-11-10 · D-252 · D-254
  nota: worktree `revista-express-f2-f3`, branch `feat/f2-f3`, stack `-p f2-f3`; os specs E2E `impacto`, `impresso`, `painel` e `revista-textos` voltam ao verde aqui
  - [x] worktree + merge da `main` (`b5fd1e6`)
  - [ ] T0 suíte Django verde depois do merge + plano (`docs/superpowers/plans/2026-11-10-f2-fase-3.md`, D-254)
  - [x] plano da fase 3 aprovado (D-254)
  - [ ] T1 `servicos/pendencias.py` + itens rápidos da auditoria (D-252)
  - [ ] T2 regra de gravação do infográfico + upload da imagem do item
  - [ ] T3 passo "Infográficos" na ficha da revista (sai a UI do SVG)
  - [ ] T4 `criar_demo` com o docx + E2E (`infografico.spec.ts`, 4 specs de volta ao verde)
  - [ ] T5 editor de templates F2, docs, revisão, merge na `integ/f2-gerado`

## Review

## Done
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
