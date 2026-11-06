# Etapa do projeto — plano de implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** o projeto cria uma etapa só dele (em branco ou clone de uma etapa de matriz), e cada mudança na base vira uma revisão em 3 vias que bloqueia o Validado até alguém concluir.

**Architecture:** a etapa do projeto é uma `MatrizEtapaCC` comum com `projeto_id` no lugar de `matriz_id`, mais `base_id` e `base_foto` (jsonb canônico da base, chaveado por código). A pendência é detectada por comparação `foto(base atual) ≠ base_foto`, entra nas `lacunas` do resolver e, por isso, no hash do Validado. O motor de 3 vias é uma função pura sobre três fotos; só a conclusão da revisão grava.

**Tech Stack:** Django 6 + PostgreSQL (jsonb, CHECK, trigger, FK composta via `nucleo/db.py::fk_composta`), django-simple-history, telas B (HTMX + Alpine, `ui_autosave.responder_campo`, `ui_bloqueio.com_bloqueio`), testes `manage.py test`, Playwright em `app/e2e`.

**Spec:** `docs/superpowers/specs/2026-11-06-etapa-do-projeto-design.md` (D-226, D-227, D-228 em `state.md`).

## Global Constraints

- Textos, nomes e mensagens em PT-BR. Mensagens de pendência seguem o padrão de `resolver.py::pendencias` (frase com ponto final).
- Ano em toda tabela: FK composta por `fk_composta(...)` com `reverse_sql`; `tests/test_constraints.py` (`FKS_COMPOSTAS`, `FKS_MANUAIS`, `CHECKS`, `ANULAVEIS`) muda na mesma migração.
- Regra que o banco garante fica em SQL: CHECK, unique parcial e trigger (padrão da migração 0006 para trigger, 0003 para FK com `ON DELETE SET NULL`).
- Escrita concorrente passa por `servicos/bloqueio.py`; a MEC já é alvo do bloqueio (`ui_bloqueio.com_bloqueio`). Teste de concorrência usa `TransactionTestCase`.
- Toda função tem controle na tela B (D-189, D-210); confirmação que afeta vários lugares é modal de impacto, não checkbox.
- Sem fusão dentro de um texto (D-115): a unidade da escolha é o campo inteiro ou a tarefa inteira.
- E2E cria o próprio parceiro "E2E …" e edita só ele (D-225); `limpar_e2e` apaga tudo no fim.
- Atalho com teto conhecido leva comentário `ponytail:`.
- `state.md`: ao fim do Task 12, decisão nova que substitui em parte a D-051 ("projeto não edita conteúdo"); `docs/regras-de-negocio.md` e `docs/modelo-er.md` atualizados.
- Comando de teste: `docker compose run --rm app python manage.py test <módulo> -v 2` (em worktree, `docker compose -p <nome>`).

## Review Focus

1. Reimportação da base só com espaços/quebras diferentes não pode abrir pendência → teste em Task 2 (`test_foto_normaliza_espacos`).
2. Base apagada (apagar ano, exclusão forçada) → `base_id` vira NULL, pendência some, etapa vira cópia solta → teste em Task 1 (`test_base_apagada_vira_nulo`) e Task 4 (`test_sem_base_nao_ha_lacuna`).
3. Base mudou entre abrir a revisão e clicar em Concluir → gravação recusada com "recarregue", nada aplicado → teste em Task 6 (`test_concluir_recusa_se_base_mudou`).
4. Clone de etapa com `escala_max` menor (9EF 500 → 7EF 400) → tarefas fora da escala caem em `corte_invalido`, nada quebra → teste em Task 2 (`test_clone_fora_da_escala_vira_corte_invalido`).
5. Projeto arquivado → editor da etapa do projeto é só leitura, como o resto da ficha (D-093) → teste em Task 7 (`test_arquivado_e_so_leitura`).

---

## Mapa de arquivos

| Arquivo | Responsabilidade |
|---|---|
| `app/nucleo/migrations/0020_etapa_do_projeto.py` | colunas, CHECKs, unique parcial, FK composta, FK SET NULL, trigger |
| `app/nucleo/models/matriz.py` | campos novos em `MatrizEtapaCC` |
| `app/nucleo/servicos/etapa_projeto.py` (novo) | `foto`, `hash_foto`, `criar`, `classificar`, `derivadas`, `mec_vigente`, `concluir`, `escolher` |
| `app/nucleo/servicos/resolver.py` | MEC do projeto em `_f1_escalas`; lacuna `base`; pendências `base` e `etapa_em_dobro` |
| `app/nucleo/servicos/matriz.py` | `_afetadas` inclui derivadas |
| `app/nucleo/servicos/{abrir_ano,exclusao,cascata}.py`, `management/commands/limpar_e2e.py` | convivem com `matriz_id` nulo; herança na cascata; impedimento de exclusão |
| `app/nucleo/urls/ui_projeto.py`, `templates/ui/projeto/projeto.html` | criar etapa (aba Matriz), pendência de escolha |
| `app/nucleo/urls/ui_matriz.py` | editor da MEC aceita MEC de projeto |
| `app/nucleo/urls/ui_revisao.py` (novo), `templates/ui/projeto/revisar_etapa.html` (novo) | tela de revisão em 3 vias |
| `app/nucleo/templates/ui/_componentes/impacto.html`, `app/nucleo/ui_autosave.py` | lista "Abre revisão em" |
| `app/nucleo/tests/test_etapa_projeto.py` (novo), `test_ui_revisao.py` (novo) + testes existentes | |
| `app/e2e/tests/etapa-do-projeto.spec.ts` (novo) | ponta a ponta |

---

### Task 1: Migração e modelo

**Files:**
- Modify: `app/nucleo/models/matriz.py:42-60`
- Create: `app/nucleo/migrations/0020_etapa_do_projeto.py`
- Test: `app/nucleo/tests/test_constraints.py`

**Interfaces:**
- Produces, em `MatrizEtapaCC`: `matriz` (null=True), `projeto = FK(Projeto, PROTECT, null=True)`, `base = FK("self", SET_NULL, db_constraint=False, null=True, related_name="derivadas")`, `base_foto = JSONField(null=True)`, `preferida = TextField(null=True)` com valores `"projeto"` | `"matriz"` (nulo = ainda não escolheu; só faz sentido quando a matriz do parceiro também tem a etapa, D-228).
- Nomes no banco (o teste de catálogo confere): `fk_matriz_etapa_cc_projeto_ano` (`(projeto_id, ano_id) → projeto(id, ano_id)`), `fk_matriz_etapa_cc_base` (`base_id → matriz_etapa_cc(id) ON DELETE SET NULL`), CHECKs `matriz_etapa_cc_um_dono` (`num_nonnulls(matriz_id, projeto_id) = 1`), `matriz_etapa_cc_base_outra` (`base_id <> id`), `matriz_etapa_cc_base_tem_foto` (`base_id IS NULL OR base_foto IS NOT NULL`), `matriz_etapa_cc_preferida` (`preferida IN ('projeto','matriz')`), unique parcial `matriz_etapa_cc_projeto_uniq` em `(projeto_id, etapa_id, componente_id) WHERE projeto_id IS NOT NULL`, trigger `matriz_etapa_cc_base_de_matriz` (recusa `base_id` apontando para MEC com `matriz_id IS NULL`; recusa UPDATE de `base_id` para valor não nulo diferente do atual).

- [ ] **Step 1: Escrever os testes que falham** em `test_constraints.py`: acrescentar as entradas acima em `FKS_COMPOSTAS`/`FKS_MANUAIS`/`CHECKS`, `("matriz_etapa_cc", "matriz_id")` e `("matriz_etapa_cc", "projeto_id")` em `ANULAVEIS`, e três testes na classe que já testa recusas do banco:

```python
def test_mec_sem_dono_ou_com_dois_donos_e_recusada(self):  # IntegrityError nos dois casos
def test_base_so_pode_ser_mec_de_matriz(self):  # base = MEC de projeto → IntegrityError (trigger)
def test_base_apagada_vira_nulo(self):  # apagar a base por SQL → derivada.base_id is None, base_foto mantida
```

- [ ] **Step 2: Rodar e ver falhar**: `… test nucleo.tests.test_constraints -v 2` → FAIL (constraints ausentes).
- [ ] **Step 3: Modelo e migração.** Campos no modelo; migração com `AlterField` (matriz null), `AddField` ×4, `AddConstraint` para os CHECKs e o unique parcial, `fk_composta("matriz_etapa_cc", "projeto")`, `RunSQL` da FK SET NULL (copiar a 0003) e do trigger (copiar a forma da 0006). `makemigrations --check` tem que ficar limpo.
- [ ] **Step 4: Rodar e ver passar**: `test_constraints` e `makemigrations --check`.
- [ ] **Step 5: Commit** `feat(matriz): etapa do projeto no modelo e no banco (D-227)`.

---

### Task 2: Foto canônica e criação da etapa

**Files:**
- Create: `app/nucleo/servicos/etapa_projeto.py`
- Test: `app/nucleo/tests/test_etapa_projeto.py` (classe `Base` monta `Mundo` de `test_resolver.py` e cria `cls.e4 = Etapa(codigo="4EF", escala_max=500, ordem=…)` e um corte GO LP 4EF)

**Interfaces:**
- `foto(mec: MatrizEtapaCC) -> dict`: `{"passo": int|None, "descritores": {codigo: {"ordem": int, <CAMPOS_DESCRITOR>…, "tarefas": {f"{inicio}-{fim}#{n}": {"texto", "arquivo", "texto_alternativo", "ordem"}}}}}`. Texto normalizado: `" ".join(s.split())` em todo campo de texto (`ponytail:` — a identidade da tarefa por faixa faz "corrigir a faixa" parecer remover + criar; parear por `(inicio, fim)` se incomodar).
- `hash_foto(f: dict) -> str` = `resolver.sha256(f)`.
- `criar(projeto, etapa, componente, usuario, base: MatrizEtapaCC | None = None) -> MatrizEtapaCC`. Levanta `CriacaoRecusada(ValueError)` quando: projeto arquivado; a matriz do parceiro já tem etapa × componente (regra 5); já existe etapa do projeto igual; `base` não é de matriz; `base.componente.codigo != componente.codigo` (regra 8). Com base: `select_for_update(no_key=True)` na matriz da base, `clonar` de `abrir_ano.py:22` para descritores e tarefas (motivo `"clone de <base>"`), `base_foto = foto(base)`. Sem base: MEC vazia, `base=None`.

- [ ] **Step 1: Testes que falham**

```python
def test_foto_e_por_codigo_e_nao_por_id(self):      # recriar D01 com outro pk → mesma foto
def test_foto_normaliza_espacos(self):               # "Lê,  interpreta.\n" == "Lê, interpreta."
def test_criar_em_branco(self):                      # mec.projeto == projeto, matriz None, base None, 0 descritores
def test_criar_clone_copia_e_guarda_foto(self):      # 2 descritores, 3 tarefas, base_foto == foto(base), histórico "+"
def test_recusa_se_matriz_ja_tem_a_etapa(self):      # 5EF LP em GO → CriacaoRecusada
def test_recusa_base_de_projeto_e_componente_diferente(self):
def test_clone_fora_da_escala_vira_corte_invalido(self):  # e7 escala 400, clone do 9EF com tarefa 450-480 na base → "corte_invalido" em pendencias(); exige Task 4 — marcar @skip até lá
```

- [ ] **Step 2: Rodar e ver falhar** (`ImportError`).
- [ ] **Step 3: Implementar** `foto`, `hash_foto`, `criar` conforme as assinaturas.
- [ ] **Step 4: Rodar e ver passar** `test_etapa_projeto`.
- [ ] **Step 5: Commit** `feat(etapa-projeto): foto canônica e criação em branco ou por clone`.

---

### Task 3: Motor de 3 vias (função pura)

**Files:**
- Modify: `app/nucleo/servicos/etapa_projeto.py`
- Test: `app/nucleo/tests/test_etapa_projeto.py`

**Interfaces:**
- `Item = NamedTuple(chave: str, campo: str, antes, base, local, situacao: str)`; `chave` é `"passo"`, `"D01"` ou `"D01/100-150#1"`; `campo` é o nome do campo (`"descricao"`, `"texto"`, `"arquivo"`, `"ordem"`, `"passo"`…) ou `"existe"` para item inteiro criado/apagado; `situacao ∈ {"entra", "conflito"}`.
- `classificar(antes: dict, base: dict, local: dict) -> list[Item]`: por célula (A, B, L): `B == A` → nada; `L == B` → nada; `L == A` → `"entra"`; senão `"conflito"`. Item ausente conta como `None` (apagar de um lado e editar do outro é conflito). Ordem de saída: passo, depois descritores por `ordem` da base, tarefas dentro do descritor.

- [ ] **Step 1: Testes que falham** (dicts montados à mão, sem banco):

```python
def test_so_base_mudou_entra(self)               # descricao: A="x", B="y", L="x" → Item("D01","descricao","x","y","x","entra")
def test_so_local_mudou_nao_aparece(self)
def test_os_dois_iguais_nao_aparece(self)
def test_os_dois_diferentes_e_conflito(self)
def test_base_apagou_e_local_editou_e_conflito(self)   # B sem D02, L com D02 editado → ("D02","existe",…,"conflito")
def test_base_acrescentou_descritor_entra(self)
def test_arquivo_da_tarefa_entra_na_comparacao(self)
```

- [ ] **Step 2: Rodar e ver falhar.** **Step 3: Implementar `classificar`.** **Step 4: Ver passar.**
- [ ] **Step 5: Commit** `feat(etapa-projeto): classificação em 3 vias`.

---

### Task 4: Resolver, pendências e impacto

**Files:**
- Modify: `app/nucleo/servicos/resolver.py:130-185` (`_f1_escalas`), `:243-290` (`resolver`), `:335-383` (`pendencias`)
- Modify: `app/nucleo/servicos/matriz.py:146-157` (`_afetadas`)
- Modify: `app/nucleo/servicos/etapa_projeto.py` (`derivadas`, `mec_vigente`)
- Test: `app/nucleo/tests/test_resolver.py`, `test_etapa_projeto.py`

**Interfaces:**
- `mec_vigente(projeto, etapa_id, componente_id) -> MatrizEtapaCC | None`: a MEC que a revista usa para a célula: se só a matriz tem, a da matriz; se só o projeto tem, a do projeto; se as duas têm, `preferida == "matriz"` → a da matriz, senão a do projeto (D-228: até escolher, vale a do projeto).
- `derivadas(*mecs) -> QuerySet[MatrizEtapaCC]`: MECs de projeto ativo com `base__in=mecs`.
- Resolver: `_f1_escalas` monta `mecs` por `mec_vigente`; `resolver()` acrescenta à `lacunas` `{"tipo": "base", "etapa": "4ef"}` para cada MEC de projeto usada cujo `base_id` não é nulo e `hash_foto(foto(base)) != hash_foto(base_foto)`, e `{"tipo": "etapa_em_dobro", "etapa": "4ef"}` quando as duas existem e `preferida is None`.
- `pendencias()`: `Pendencia("base", "A etapa 4EF tem mudanças da base para revisar.")` e `Pendencia("etapa_em_dobro", "A matriz agora tem 4EF: escolha qual usar.")`; `corte_sem_matriz` passa a considerar a MEC do projeto como "tem".
- `_afetadas(mecs)`: além do filtro atual, `| Q(projeto__matrizetapacc__in=derivadas(*mecs), componente_id=…)` (revistas ativas dos projetos derivados do mesmo componente).

- [ ] **Step 1: Testes que falham** (em `test_etapa_projeto.py`, com GO LP 4EF clonado do 5EF LP):

```python
def test_revista_usa_a_etapa_do_projeto(self)                 # resolver(go["LP"])["f1"]["etapas"] contém "4ef" e D01
def test_corte_sem_matriz_some_com_a_etapa_do_projeto(self)
def test_editar_a_base_abre_lacuna_e_tira_o_validado(self)    # validar; editar D01 da base; hash muda; "base" em pendencias
def test_sem_base_nao_ha_lacuna(self)                         # base_id=None → nenhuma lacuna "base"
def test_matriz_ganha_a_etapa_vira_pendencia_de_escolha(self) # criar 4EF LP na Comunitária → "etapa_em_dobro"; preferida="matriz" → revista usa a da matriz
def test_afetadas_inclui_a_revista_derivada(self)             # impacto(base) lista go["LP"]
```

   Tirar o `@skip` de `test_clone_fora_da_escala_vira_corte_invalido`.
- [ ] **Step 2: Ver falhar.** **Step 3: Implementar.** **Step 4: Ver passar** `test_etapa_projeto`, `test_resolver`, `test_painel`, `test_ui_validar`.
- [ ] **Step 5: Commit** `feat(resolver): etapa do projeto na revista, lacuna da base e pendência de escolha`.

---

### Task 5: `matriz_id` nulo no resto do sistema

**Files:**
- Modify: `app/nucleo/servicos/abrir_ano.py:78-95`, `servicos/exclusao.py:137-145` e `:208-240`, `management/commands/limpar_e2e.py:28-35`, `urls/ui_matriz.py:240-244` (`_mec`: `select_related("ano", …)` em vez de `"matriz__ano"`), `servicos/importar_matriz.py` (só se assumir matriz; conferir com `trail grep "matriz_etapa_cc__matriz"` e `trail grep "\.matriz\b"` nos ~35 pontos citados na spec §7)
- Test: `test_abrir_ano.py`, `test_exclusao.py`, `test_limpar_e2e.py`

**Interfaces:**
- `abrir_ano`: copia só `MatrizEtapaCC.objects.filter(ano=origem, matriz__isnull=False)` (a etapa do projeto não passa de ano, spec §2).
- `apagar_ano`: a ordem de `ORDEM_ANO` apaga MECs de projeto antes dos projetos.
- `limpar_e2e.dependentes`: `(MatrizEtapaCC, {"projeto__parceiro_ano__in": pas})` antes de `Projeto`.
- `exclusao.impedimentos(mec_base)`: devolve impedimento `"projetos com etapa derivada"` listando `derivadas(mec)` com link para a ficha do projeto (regra 6).

- [ ] **Step 1: Testes que falham**

```python
# test_abrir_ano.py
def test_etapa_do_projeto_nao_passa_de_ano(self)
# test_exclusao.py
def test_base_com_derivada_nao_e_excluida(self)        # impedimentos lista "Projeto GO"
def test_apagar_ano_com_etapa_do_projeto(self)
# test_limpar_e2e.py
def test_apaga_etapa_do_projeto_do_parceiro_e2e(self)
```

- [ ] **Step 2: Ver falhar.** **Step 3: Implementar** e rodar a suíte inteira para achar os `.matriz` que quebram com nulo. **Step 4: Suíte inteira verde** (`… test -v 1`).
- [ ] **Step 5: Commit** `fix: MEC sem matriz no abrir ano, apagar ano, exclusão e limpar_e2e`.

---

### Task 6: Concluir a revisão (serviço)

**Files:**
- Modify: `app/nucleo/servicos/etapa_projeto.py`
- Test: `app/nucleo/tests/test_etapa_projeto.py` (+ uma classe `TransactionTestCase`)

**Interfaces:**
- `Escolha = Literal["base", "local"]`; `escolhas: dict[tuple[chave, campo], Escolha | str]` — `str` = texto editado à mão (botão "Editar…", só para campos de texto).
- `concluir(mec, escolhas, hash_base_visto: str, usuario) -> int` (nº de células aplicadas). Em `transaction.atomic()` com `select_for_update` na MEC do projeto e `no_key=True` na matriz da base: recalcula `itens = classificar(mec.base_foto, foto(base), foto(mec))`; se `hash_foto(foto(base)) != hash_base_visto` → `raise Conflito(MUDOU, …)` (mesma classe de `ui_autosave`); se algum conflito sem escolha → `RevisaoIncompleta(ValueError)`; aplica: `"entra"` sem escolha ou escolha `"base"` → grava o valor da base no local (criar/apagar descritor ou tarefa, trocar campo; `arquivo` passa por `servicos.arquivos` para o órfão); `"local"` → nada; texto → grava o texto. Por fim `mec.base_foto = foto(base)`; `save()` com `_change_reason = f"revisão da base: aplicou {n}, manteve {m}"`.
- `escolher(mec, preferida: Escolha, usuario)` grava `preferida` (D-228, botões "Manter a do projeto" / "Usar a da matriz").

- [ ] **Step 1: Testes que falham**

```python
def test_concluir_aplica_o_que_entra_e_avanca_a_foto(self)       # D01.descricao vira a da base; base_foto == foto(base); hash volta a bater (D-094)
def test_manter_o_meu_nao_grava_e_nao_volta_a_perguntar(self)    # 2ª chamada de classificar → []
def test_texto_editado_a_mao(self)
def test_conflito_sem_escolha_e_recusado(self)                   # RevisaoIncompleta, nada gravado
def test_concluir_recusa_se_base_mudou(self)                     # hash velho → Conflito, nada gravado
def test_usar_o_da_base_troca_o_arquivo_e_apaga_o_orfao(self)    # usa MediaTemporaria de test_item
# TransactionTestCase
def test_duas_conclusoes_simultaneas_a_segunda_recusa(self)
```

- [ ] **Step 2: Ver falhar.** **Step 3: Implementar.** **Step 4: Ver passar.**
- [ ] **Step 5: Commit** `feat(etapa-projeto): concluir revisão e escolher etapa preferida`.

---

### Task 7: Tela — criar a etapa e editar pelo editor da matriz

**Files:**
- Modify: `app/nucleo/urls/ui_projeto.py` (rotas `ui_projeto_etapa_nova` POST `/ui/projeto/<pk>/etapa/nova/`, `ui_projeto_etapa_preferida` POST `/ui/projeto/<pk>/etapa/<mec>/preferida/`), `templates/ui/projeto/projeto.html:143-165` (aba Matriz)
- Modify: `app/nucleo/urls/ui_matriz.py:240-244, 339-380` (`_mec`, `_pagina_mec`: permissão e breadcrumb para MEC de projeto)
- Test: `test_ui_projeto_abas.py`, `test_ui_matriz.py`

**Interfaces:**
- Na aba Matriz, abaixo do select: uma linha por pendência `corte_sem_matriz` da revista ("A matriz não tem 4EF LP") com o botão **Criar etapa do projeto**, que abre um `<dialog>` (padrão de `_form_em_dialogo`) com: rádio "Em branco" / "A partir de", `<select name="base">` com as MECs de matriz do mesmo componente, de qualquer ano, agrupadas por matriz (`<optgroup label="Comunitária (2026)">`). POST chama `criar(...)`; `CriacaoRecusada` → mensagem de erro no diálogo. Passa pelo bloqueio da ficha (`com_bloqueio`) e por `responder_campo` com o impacto (criar a etapa muda a revista).
- Lista das etapas do projeto na aba: "4EF LP · base: 5EF LP da Comunitária" com link para `ui_matriz_mec` e, quando houver, badge "mudanças da base para revisar" (link da Task 8) ou "a matriz agora tem 4EF" com os dois botões de `escolher`.
- `ui_matriz._mec`: MEC de projeto exige `nucleo.change_projeto` (ação `editar_projeto`) para editar e `view_projeto` para ver; breadcrumb "Projetos › Projeto GO › 4EF LP"; projeto arquivado → só leitura (`so_leitura.html`).

- [ ] **Step 1: Testes que falham**

```python
# test_ui_projeto_abas.py
def test_aba_matriz_mostra_botao_criar_etapa_na_pendencia(self)
def test_criar_etapa_clone_pela_tela(self)               # POST → MEC criada, redirect para a aba, pendência some
def test_criar_recusa_sem_bloqueio_e_sem_permissao(self)
def test_escolher_preferida_pela_tela(self)
# test_ui_matriz.py
def test_editor_abre_mec_de_projeto_com_breadcrumb_do_projeto(self)
def test_impresso_nao_edita_mec_de_projeto(self)
def test_arquivado_e_so_leitura(self)
```

- [ ] **Step 2: Ver falhar.** **Step 3: Implementar.** **Step 4: Ver passar** + `test_ui_links` (links novos).
- [ ] **Step 5: Commit** `feat(ui): criar etapa do projeto na aba Matriz e editá-la no editor`.

---

### Task 8: Tela de revisão em 3 vias

**Files:**
- Create: `app/nucleo/urls/ui_revisao.py` (incluir em `urls/__init__.py` como `path("ui/revisao/", …)`), `templates/ui/projeto/revisar_etapa.html`, estilos em `static/ui/` seguindo `docs/telas/design-system.md`
- Test: `app/nucleo/tests/test_ui_revisao.py`

**Interfaces:**
- GET `/ui/revisao/<mec>/` (`ui_revisao`): contexto `{"mec", "base", "itens": classificar(...), "hash_base": hash_foto(foto(base)), "mudou_em", "mudou_por"}` (`mudou_em/por` do último `history` da base e de seus descritores/tarefas). Cabeçalho: "5EF LP da Comunitária mudou em 06/11 (por Fulana). Faltam N decisões." Grupo "Precisa da sua decisão" (aberto): cartão por conflito, colunas "No seu projeto" / "Na base", diff do texto da base com `<del>`/`<ins>` (usar `difflib.SequenceMatcher` por palavra, no servidor), rádios **Manter o meu** · **Usar o da base** · **Editar…** (textarea com o local). Grupo "Vem da base, confira" (`<details>` fechado): itens "entra", rádio já em "Usar o da base", pode virar "Manter o meu". Para `arquivo`: `<img>` antes × depois. Rodapé: **Concluir revisão** desabilitado até todo conflito ter rádio (Alpine).
- POST `/ui/revisao/<mec>/` (`ui_revisao_concluir`): campos `escolha[<chave>|<campo>]` = `base|local|texto:<…>` e `hash_base`; sob `com_bloqueio` da MEC; `responder_campo` com `gravar=lambda d: concluir(...)` (o modal de impacto já lista quem perde o Validado); `Conflito` → 409 "recarregue"; `RevisaoIncompleta` → erro de form.
- Permissão: `editar_projeto`; Impresso vê a página sem botões.

- [ ] **Step 1: Testes que falham**

```python
def test_pagina_lista_conflitos_e_entradas(self)        # 1 conflito aberto, 1 "entra" no details
def test_diff_marca_del_e_ins(self)
def test_concluir_grava_e_volta_para_a_aba_matriz(self)
def test_concluir_com_hash_velho_da_409(self)
def test_impresso_so_le(self)
```

- [ ] **Step 2: Ver falhar.** **Step 3: Implementar** (template segue `docs/telas/design-system.md`; `<del>`/`<ins>` com texto auxiliar `sr-only` "saiu"/"entrou"). **Step 4: Ver passar.**
- [ ] **Step 5: Commit** `feat(ui): tela de revisão da etapa do projeto em 3 vias`.

---

### Task 9: Modal de impacto de quem edita a base

**Files:**
- Modify: `app/nucleo/ui_autosave.py:78-111` (`responder_campo`: `impacto["revisoes"]`), `templates/ui/_componentes/impacto.html`, `urls/ui_matriz.py:295-302` (`_perdem`/`_avisar` para o editor clássico), `urls/ui_matriz.py:210-227` (`reimportar_view`: contagem)
- Test: `test_ui_autosave.py`, `test_ui_matriz.py`

**Interfaces:**
- `impacto.html` recebe `revisoes: list[str]` ("Projeto GO LP · 4EF") e mostra o bloco "Abre revisão em:" quando não vazio. `responder_campo` ganha `revisoes: Callable[[], Iterable[str]] | None = None`; as views do editor de matriz passam `lambda: [str(d) for d in derivadas(mec)]`. O modal passa a ser obrigatório também quando `revisoes` não é vazio (mesmo mecanismo de `modal`).
- Reimportar: a confirmação diz "abre revisão em N projeto(s)".

- [ ] **Step 1: Testes que falham**

```python
def test_modal_lista_abre_revisao_em(self)               # editar D01 da base sem confirmar → impacto.revisoes == ["Projeto GO LP · 4EF"]
def test_reimportar_avisa_projetos_derivados(self)
```

- [ ] **Step 2: Ver falhar.** **Step 3: Implementar.** **Step 4: Ver passar.**
- [ ] **Step 5: Commit** `feat(impacto): aviso de revisão nos projetos derivados`.

---

### Task 10: Cascata — projeto recriado herda a etapa (D-228)

**Files:**
- Modify: `app/nucleo/servicos/cascata.py:44-98`
- Test: `test_cascata.py`

**Interfaces:**
- Em `gravar_cortes`, quando nasce o projeto novo (`projeto is None` → cria): para cada MEC com `projeto__parceiro_ano=pa` e `projeto__arquivado_em__isnull=False`: `m.projeto = novo; m._change_reason = "projeto recriado pela cascata"; m.save()` (não usar `update()`: perde o histórico). Transfere, não copia (`base_id` e `base_foto` vêm junto).

- [ ] **Step 1: Teste que falha** `test_projeto_recriado_herda_a_etapa_do_projeto(self)` (arquiva tirando todos os cortes; volta cortes; a MEC aponta para o projeto novo; revista nova usa "4ef").
- [ ] **Step 2: Ver falhar.** **Step 3: Implementar.** **Step 4: Ver passar** `test_cascata`.
- [ ] **Step 5: Commit** `feat(cascata): projeto recriado herda as etapas do projeto (D-228)`.

---

### Task 11: E2E

**Files:**
- Create: `app/e2e/tests/etapa-do-projeto.spec.ts`

**Interfaces:** o spec cria o parceiro "E2E Etapa <sufixo>" com cortes 4EF LP (a cascata gera projeto e revista) e a matriz "E2E Base <sufixo>" (cópia da Demonstração, `matrizPropria` de D-225). Fluxo: criar etapa 4EF LP a partir do 5EF LP da matriz própria → editar D01 na matriz própria (confirmar o modal, que lista "Abre revisão em") → Validar mostra a pendência → abrir a revisão, "Usar o da base", Concluir → pendência some.

- [ ] **Step 1: Escrever o spec** e **Step 2: rodar** `cd app/e2e && npx playwright test etapa-do-projeto` com o app de pé → verde; `limpar_e2e --simular` não lista sobra depois do teardown.
- [ ] **Step 3: Commit** `test(e2e): etapa do projeto de ponta a ponta`.

---

### Task 12: Documentação e decisão

**Files:**
- Modify: `docs/regras-de-negocio.md` (seção 3.4: etapa do projeto, as 10 regras da spec §5 + D-228), `docs/modelo-er.md` (colunas novas de `matriz_etapa_cc`), `docs/telas/telas-b.md` (aba Matriz, tela de revisão), `CLAUDE.md` (lista de `servicos/`: `etapa_projeto`), `state.md`

- [ ] **Step 1: Atualizar os docs** e registrar em `state.md` a decisão "D-2xx — Etapa do projeto implementada; substitui em parte a D-051" (contexto, decisão, motivo, descartadas, arquivos).
- [ ] **Step 2: `trail check`** limpo (ou justificar no commit).
- [ ] **Step 3: Commits** `docs: etapa do projeto nas regras, no ER e nas telas` e, por último, `docs: atualiza state.md`.

---

## Autorrevisão (feita ao escrever)

- **Cobertura da spec:** §4.1 criar → T2, T7; §4.2 editar → T7; §4.3 detectar, lacuna, modal, reimportar → T4, T9; §4.4 revisar → T3, T6, T8; §5 regras 1–7 → T4, T5, T6, T7; regra 8 (componente) → T2; regra 9 (Validado volta) → T6; regra 10 (campos, arquivo) → T3, T6, T8; §7 modelo → T1; `abrir_ano`/`apagar_ano`/`limpar_e2e` → T5; §10 herança na cascata → T10; §10 matriz ganha a etapa → T1 (`preferida`), T4, T6, T7; E2E → T11; docs e D-051 → T12.
- **Nomes consistentes entre tarefas:** `foto`, `hash_foto`, `criar`, `classificar`, `Item`, `derivadas`, `mec_vigente`, `concluir`, `escolher`, `preferida`, `CriacaoRecusada`, `RevisaoIncompleta`, lacunas `base` e `etapa_em_dobro`.
- **Review Focus:** os 5 itens têm teste nomeado em T1, T2, T4, T6, T7.
