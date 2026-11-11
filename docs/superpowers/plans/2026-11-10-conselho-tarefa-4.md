# Conselho sobre a Tarefa 4/7 da fase 2 do F2: plano de execução

> **Para quem executar:** siga a skill `conselho` na thread principal, porque subagente não dispara subagente. Os passos usam `- [ ]`. Ao aprovar, copie este plano para `/home/otavio.peres/dev/revista-express-f2-f2/docs/superpowers/plans/2026-11-10-conselho-tarefa-4.md`.

**Objetivo:** 5 analistas `conselheiro` avaliam as decisões da tarefa 4/7 da fase 2: o resolvido com infográficos, as pendências e o passo "Infográficos". Eles debatem e devolvem um veredito, que é aplicado antes da tarefa 5.

**Arquitetura:**
1. Montar um dossiê curto, só com caminhos, sem opinião.
2. Rodar 5 lentes em paralelo.
3. Montar a mesa de opções.
4. Fazer até 2 rodadas de debate por `SendMessage`.
5. Chamar o presidente novo, se não houver acordo.
6. Repassar o veredito literal ao usuário e registrá-lo no `state.md`.

**Custo:** cerca de 6 agentes (5 analistas e talvez o presidente). Leva de 30 a 45 min de relógio.

## Restrições globais

- Os analistas só leem. Ninguém edita ou commita durante o conselho.
- Worktree `/home/otavio.peres/dev/revista-express-f2-f2`, branch `feat/f2-f2`. Todo prompt cita o caminho absoluto. Comando docker, se algum analista rodar teste: `COMPOSE_PROJECT_NAME=f2-f2 docker compose -p f2-f2 …`.
- O veredito vai ao usuário como veio, sem reargumentar. Se ele pedir mudança, a mudança é aplicada. Se eu tiver um fato que o conselho não viu, mostro o fato e pergunto ao usuário.
- PT-BR em tudo.

## Ponto de atenção para a revisão

1. **A correção ainda roda em segundo plano.** O dossiê só sai depois do commit dela e da suíte verde. Antes disso, o objeto do conselho estaria incompleto.

---

### Passo 1: esperar e conferir a correção (5 min)

- [ ] Esperar o aviso da rodada de correção da T4. Ler a seção "Correção da revisão" no fim de `.superpowers/sdd/2026-11-09-f2-fase-2/task-4-report.md`.
- [ ] Rodar `git -C /home/otavio.peres/dev/revista-express-f2-f2 log --oneline febbe80..HEAD`. Esperado: `bf9cdd7` e o commit `fix: texto de passo desligado não conta variável; PASSOS no modelo (revisão da tarefa 4)`. Anotar o SHA como `4e16fae`.
- [ ] Conferir no relatório: suíte OK com 8 pulados e `makemigrations --check` limpo. Se algo falhou, parar aqui e consertar antes do conselho.
- [ ] Ledger: acrescentar `Task 4: fix round 1/5 (… commits bf9cdd7..4e16fae)` e `Task 4: conselho disparado`.

### Passo 2: dossiê (10 min)

- [ ] Gravar `.superpowers/sdd/2026-11-09-f2-fase-2/conselho-t4-dossie.md`, só com caminhos e citações literais:
  - **Objeto:** `git -C /home/otavio.peres/dev/revista-express-f2-f2 diff febbe80..4e16fae`, commits `bf9cdd7` e `4e16fae`. Arquivos centrais: `servicos/resolver.py`, `servicos/empacotar.py`, `models/revista.py`, `urls/ui_revista.py`, `urls/painel.py`, e os testes `test_resolver`, `test_painel`, `test_cascata`, `test_empacotar`, `test_ui_painel` e `test_ui_validar`.
  - **Requisito:** a mensagem do usuário "segue com a tarefa 4", mais a especificação em `.superpowers/sdd/2026-11-09-f2-fase-2/task-4-brief.md` (com os ajustes de 10/11 no fim) e em `restricoes.md`.
  - **Justificativa declarada:** D-237 no `state.md`, a seção "Decisões fora do brief" de `task-4-report.md`, as linhas `Task 4:` de `progress.md` com as decisões da revisão e as mensagens dos commits `bf9cdd7` e `4e16fae`.
  - **Decisões em julgamento** (uma linha cada, sem opinião):
    1. Formato de `resolvido["f2"]["infograficos"]`: dados crus, com só `textos.*` e `analise` renderizados. Nulos viram `""`.
    2. A pendência `infografico` tem 4 mensagens e só vale para passo ligado. Texto de passo desligado não conta variável nem entra no hash.
    3. Ponte em `empacotar.py:105` com `.get("svg_sha256", revista.svg_sha256)` até a T6.
    4. O hash de toda revista muda uma vez e derruba o "Validado" (D-237).
    5. São 3 consultas a mais com `prefetch_related`: os tetos foram de 13→16 no resolver e de 16→19 por linha no painel.
    6. `PASSOS` mora em `models/revista.py`.
    7. O teste da migração 0022 compara o resolvido sem `infograficos`. O helper `trocar_svg` virou `trocar_imagem`.
    8. Itens adiados: o teste da foto antiga sem `infograficos` vai para T5/T6, e a dica longa do painel vai para a fase 3.

### Passo 3: análise individual (15 min, em paralelo)

- [ ] Disparar 5 `Agent` com `subagent_type: conselheiro` numa mensagem só. Cada prompt leva o caminho do dossiê, a lente e o formato da rodada 1 da skill (`LENTE / JUSTIFICATIVA ENCONTRADA / ACHADOS ≤5 com arquivo:linha / ALTERNATIVAS ≤2 / POSIÇÃO: MANTER | AJUSTAR | TROCAR`).

  | Lente | Pergunta |
  |---|---|
  | Mínimo | O que dá para apagar? Havia um degrau mais simples (código existente, biblioteca padrão, recurso nativo)? |
  | Justificativa | A justificativa se sustenta? Confere com o código e com o requisito? |
  | Alternativas | Dois caminhos diferentes, com custo e ganho concretos de cada. |
  | Falha | Onde quebra: entrada, concorrência, dado existente (revistas validadas, foto arquivada), segurança. |
  | Futuro leitor | Quanto custa entender e mudar isto daqui a 6 meses? O que surpreende? |

### Passo 4: mesa (5 min)

- [ ] Numerar as opções sem julgar. `O1` = manter como está. `O2…On` = cada AJUSTAR ou TROCAR distinto; juntar só os que pedem a mesma mudança. Gravar em `conselho-t4-mesa.md`, ao lado do dossiê.

### Passo 5: debate (10 a 15 min)

- [ ] Carregar `SendMessage` (`ToolSearch select:SendMessage`). Mandar a cada analista as 5 análises e a mesa, pedindo `RÉPLICA (≤3, respondendo a um colega pelo nome da lente) / MUDEI DE POSIÇÃO / VOTO: O<n>`.
- [ ] Com 5 votos iguais, ir ao passo 7. Sem acordo, fazer uma rodada final só com `VOTO FINAL: O<n>` e uma linha de motivo. No máximo 2 rodadas.

### Passo 6: voto de minerva (5 min, só sem acordo)

- [ ] Disparar 1 `conselheiro` novo com o prompt começando por `PRESIDENTE`. Ele recebe o dossiê, as 5 análises, as réplicas, a mesa e o placar, escolhe uma opção e justifica em até 5 linhas.

### Passo 7: repasse e registro (10 min)

- [ ] Mostrar ao usuário exatamente o bloco da skill:
  ```
  CONSELHO — Tarefa 4/7 da fase 2 do F2 (resolvido, pendências, passo Infográficos)
  Veredito: O<n> — <descrição> (unânime | minerva do presidente; placar <x>)
  Mudança a fazer: <exata> | nenhuma
  Vencidos: <lente: argumento, 1 linha cada>
  ```
- [ ] Registrar a **D-243** no `state.md` da f2-f2: veredito, placar e mudança. Atualizar o ledger.
- [ ] Se houver mudança: virar um brief de correção no molde das rodadas da T3 e da T4, com TDD, suíte verde e commit `fix: … (conselho da tarefa 4)`. Depois, uma revisão rápida do diff.
- [ ] Fechar a leva com o learning pendente (`.trail/learnings/2026-11-10-no-f2-gerado-o-tour-leva-otavio.md`) e o commit `docs: atualiza state.md (tarefa 4 e conselho)` por último.

## Verificação

- O bloco do veredito foi mostrado sem comentário meu antes ou depois.
- A D-243 está no `state.md` e commitada como último commit da leva.
- Se o veredito pediu mudança: suíte `COMPOSE_PROJECT_NAME=f2-f2 docker compose -p f2-f2 run --rm app python manage.py test` com 8 pulados e `makemigrations --check` limpo.

## Fora do escopo

A tarefa 5 (páginas) só começa depois do passo 7. Os itens adiados (teste da foto antiga, dica do painel) só entram se o veredito pedir.
