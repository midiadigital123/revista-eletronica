# Rascunho de UI: telas e ajustes que faltam (revista-express, Django admin)

Base: `inventario-telas.md` (mesma pasta) + código em `app/nucleo/` (branch `refatoracao-django`, 2026-10-30). Só planejamento: nada foi editado no repositório.

**Estilo:** tudo segue a seção 6 do inventário (tema padrão do Django admin; `breadcrumbs` "Início › …"; `module`; `submit-row`; `object-tools-items`; `messages`; `errornote`; `impacto-alerta`). Nenhum tema, fonte, CSS ou framework novo. Onde precisar de CSS, ele vai no `template_editor.css` que já existe.

**Fora deste rascunho:** T26 (tela do impresso) e T27 (planilhas) estão com outro agente. Aqui só aparece **onde elas entram na navegação**: link da coluna Impresso do Painel, atalho do perfil Impresso e "Abrir tela do impresso" em T21.

**Crítica de UX (skill `impeccable`, modo Operate):** foi aplicada como lente de hierarquia, fluxo, carga cognitiva, estados vazios e mensagens. O fluxo completo do `critique` não rodou. Ele pede dois subagentes, o detector e o navegador. Este trabalho não sobe servidor e não edita o repositório, então a crítica foi feita só no contexto deste agente. As conclusões estão em cada item, na linha "Crítica". Achado à parte: o `PRODUCT.md` e o `DESIGN.md` que a skill carregou descrevem o editor React antigo (shadcn, autosave). Eles não descrevem o Django admin atual. Não foram usados como referência visual.

---

## Fazer agora (obrigatório para 2026)

| # | Item | Estimativa |
|---|---|---|
| 1 | Links para o Preview (T21, Painel, T20) | **1 h** |
| 2 | Aviso "afeta N revistas" em T07, com a lista de quem perde o "Validado" | **4 h** |
| 3 | Painel como entrada: atalho no índice, link "Painel AAAA" no topo, `/` → Painel, próxima tarefa por perfil | **3 h** |
| 4 | T12: aba Variáveis → T17, e "usado por" com filtro `template` funcionando no Painel | **1,5 h** |

**Total: 9,5 h**, já com os testes de cada item. Ordem: 1 é o menor e destrava a conferência do design. 2 evita a perda silenciosa do "Validado". 3 junta as entradas, inclusive as de T26. 4 é correção de links.

---

### 1. Links para o Preview `/preview/<pk>/`

- **Na jornada:** T21 Revista (antes) → **T22 Preview** → T23 Painel / "Validado" (depois). Hoje nenhum template do admin aponta para `reverse("preview", args=[pk])`. Quem quer conferir digita a URL.
- **Quem usa:** todos com `view_revista`, inclusive o Impresso, que só lê.
- **Lê:** `revista.pk`, `revista.arquivada_em`. **Grava:** nada.
- **Falta no ER/telas:** nada no ER. Nas telas: o link em T21, no Painel e na lista T20.
- **Onde:**
  - T21: `<li>` em `object-tools-items`. O bloco já existe no `admin/change_form.html`, que `nucleo/revista_change_form.html` herda. Fica ao lado de "Histórico".
  - Painel: link "preview" na célula "Revista".
  - T20: coluna `list_display` "Preview".
  - Todos abrem com `target="_blank" rel="noopener"`.

```
Início › Núcleo › Revistas › Parceiro X · LP 2026
┌───────────────────────────────────────── [Abrir preview ↗] [Histórico] ┐
│ module: SVG e capa ...                                                 │
│ module: Template por fascículo ...                                     │
│ module: Textos por seção ...                                           │
│ module: Validado ...                                                   │
└────────────────────────────────────────────────────────────────────────┘

Painel:  Revista                         Matriz  Template F1 ...  Validado
         Parceiro X · LP  (preview ↗)    ✓       falta            falta
```

- **Estados:**
  - Vazio (sem SVG ou template): o link aparece igual. O preview abre e mostra a faixa vermelha (D-116). `title` do link: "Abre mesmo com pendências; o que falta aparece em faixa vermelha."
  - Erro (SVG ausente no storage → 404 em `preview.py:42`): mensagem da página 404: "SVG do F2 não encontrado no storage. Envie o SVG de novo na revista." Hoje o texto diz só a causa. Acrescentar a correção.
  - Só leitura (arquivada): o texto do link muda para "Abrir preview (versão arquivada) ↗", porque o preview mostra a foto (D-117).
  - Sucesso: nova aba com F1 + F2.
- **Crítica:** a ação mais frequente da conferência não tinha entrada no admin. Isso obriga a lembrar a URL (heurística 6, reconhecer em vez de lembrar). Em T21 o link fica no topo, em `object-tools`, e não dentro do módulo Validado. Assim, quem confere vê o link antes de rolar a página.
- **Aceite:**
  1. Em `/admin/nucleo/revista/<pk>/change/` há `a[href="/preview/<pk>/"][target=_blank]`.
  2. Em `/painel/2026/`, cada linha tem o mesmo link.
  3. A lista `/admin/nucleo/revista/` tem a coluna "Preview".
  4. Revista arquivada: o texto contém "versão arquivada".
  5. Teste com usuário Impresso: o link aparece e o GET retorna 200.

---

### 2. T07 Padrões do ano: aviso "afeta N revistas" e quem perde o "Validado"

- **Na jornada:** T03 Abrir ano → **T07** → T16/T17 Projeto. O risco aparece **depois** do "Validado". Mudar `nome` ou `cor` de um padrão muda o hash de toda revista ativa do ano que não sobrescreve aquele padrão (`resolver.py:24-27`, D-175, D-153). O "Validado" cai sem aviso, e a coluna Impresso volta para "falta".
- **Quem usa:** Pedagógica, Mídias e Admin (`change_corpadrao`). O Impresso vê o form do admin em modo só leitura, sem o aviso.
- **Lê:**
  - `cor_padrao`;
  - revistas ativas do ano (`arquivada_em IS NULL`);
  - `projeto.pdNN` (para o nome) e `projeto_cor` do padrão N (para a cor);
  - o resolvido de cada candidata: `dados[etapa]["padroes"]`, para saber se a revista tem o padrão N, e `hash_validado` + `validacao.validada()`.
- **Grava:** `cor_padrao.nome` / `cor`, como hoje. Nada novo.
- **Falta no ER/telas:** nada no ER. Na tela: `CorPadraoAdmin.form = ImpactoForm` (reaproveitado de `admin/matriz.py:214-235`), mais a função `revistas_afetadas_padrao(cor_padrao)` em `servicos/`.
- **Regra de "afetada":** revista ativa do mesmo ano que tem o padrão N em alguma etapa e em que vale ao menos uma das condições:
  - (`projeto.pdNN == ""`) para o nome;
  - (sem `ProjetoCor` do padrão N) para a cor.
  - "Perde o Validado" = afetada **e** `validada(revista, hash atual)`.
- **Quando pede confirmação:** só quando `{"nome", "cor"} ∩ form.changed_data` não é vazio e N > 0. Salvar sem mudança não pede nada.
  - Isso difere do `ImpactoForm` da MEC, que pede sempre. Fica num `clean()` sobrescrito, com 3 linhas.
- **Lista no form:** `help_text` do checkbox com até 20 nomes, depois "e mais N". Escapar com `format_html_join`.

```
Início › Núcleo › Padrões do ano (cor e nome) › Padrão 3 #b3ccff (2026)
┌ errornote (só no POST sem confirmar) ──────────────────────────────────┐
│ Corrija o erro abaixo.                                                 │
└────────────────────────────────────────────────────────────────────────┘
┌ module aligned ────────────────────────────────────────────────────────┐
│ Ano:     2026 (readonly)        Padrão: 3 (readonly)                   │
│ Cor:     [#b3ccff ]                                                    │
│ Nome:    [Padrão 03 — Adequado          ]                              │
│ ─────────────────────────────────────────────────────────────────────  │
│ [ ] Confirmo: afeta 12 revista(s) ativa(s); 5 perdem o “Validado”      │
│     Perdem o “Validado”: Parceiro A · LP, Parceiro A · MT, Parceiro B… │
│     As demais afetadas ainda não estavam validadas.                    │
└────────────────────────────────────────────────────────────────────────┘
submit-row: [Salvar] [Salvar e continuar editando]
```

- **Estados:**
  - Vazio (N = 0: ano sem revistas ativas, ou todos os projetos sobrescrevem): o checkbox fica oculto (`HiddenInput`, como o `ImpactoForm` já faz) e o salvar é normal.
  - Erro (mudou nome/cor e não marcou): `errornote` + erro no form (texto abaixo). O digitado é mantido.
  - Só leitura: ano antigo com revistas arquivadas dá N = 0, porque a arquivada lê a foto. O Impresso vê o form do admin sem `submit-row` e sem checkbox.
  - Sucesso: `messages.success` e, se alguém perdeu o "Validado", também `messages.warning` com link para o Painel filtrado.
- **Mensagens exatas:**
  - Rótulo: `Confirmo: afeta {n} revista(s) ativa(s); {v} perdem o “Validado”` (com v = 0: `Confirmo: afeta {n} revista(s) ativa(s)`).
  - Erro (`clean`): `Não salvo: mudar o nome ou a cor do Padrão {p} de {ano} afeta {n} revista(s) ativa(s) (as que não sobrescrevem pd0{p} ou a cor no projeto). Confira a lista, marque a confirmação e salve de novo.`
  - Sucesso: `Padrão {p} de {ano} salvo.`
  - Aviso pós-salvar: `{v} revista(s) perderam o “Validado”: {nomes}. Revalide no Painel.` O link "Painel" vai para `/painel/{ano}/?falta=validado`.
- **Junto (desejável do 4b, +0 h):** no Painel, a pendência `variaveis` de `pdNN` vazio no projeto e nome do ano vazio ganha um segundo link, "ou preencher o nome do ano", para `admin:nucleo_corpadrao_change`.
- **Crítica:**
  - É o ponto de maior risco emocional da jornada (heurística 5, prevenção de erro). Uma edição de 1 campo derruba o trabalho de validação de várias pessoas.
  - A contagem sozinha não basta. Quem decide precisa ver **nomes**: "5 perdem o Validado" vira "vou ter que pedir revalidação ao parceiro A". Por isso a lista vem no form.
  - O aviso pós-salvar fecha o ciclo com a próxima ação (revalidar).
- **Aceite (testes Django):**
  1. Com 2 revistas ativas sem `pd03` e 1 com `pd03` preenchido, mudar o nome do padrão 3 sem confirmar retorna o form com o erro, e N = 2.
  2. Mudar só a cor, com 1 dos projetos tendo `ProjetoCor(padrao=3)`: N conta só as revistas sem `ProjetoCor`.
  3. Revista cujas etapas têm só 2 padrões não entra em N para o padrão 3.
  4. Com confirmação: salva, e a mensagem de aviso lista exatamente as revistas que tinham `validada()` True antes e False depois. O teste compara com `validacao.validada` recalculado após o save.
  5. Salvar sem mudar nome/cor não pede confirmação.
  6. Ano com todas as revistas arquivadas: checkbox oculto.
- **Estimativa: 4 h.** São 1 h para o serviço, 1 h para o form e o admin, e 2 h para os testes. O resolvido de cada candidata custa o mesmo que uma carga do Painel.
  - `ponytail:` resolve cada candidata no GET e no POST. Se ficar lento com muitas revistas, guardar a lista na sessão entre GET e POST.

---

### 3. Painel como entrada e navegação da temporada

- **Na jornada:** T01 Login → **T02 Índice** → próxima tarefa do perfil. Hoje o Painel (D-120, "tela principal") só é achado pelos `object-tools` da lista de Revistas (`revista.py:548-551`).
- **Quem usa:** todos.
- **Lê:**
  - `Ano` (maior ano = "ano da temporada");
  - permissões do usuário (`has_perm`, nunca nome de grupo, como em `permissoes.py`);
  - para os contadores: a mesma `painel.linha()` do Painel.
  - Recomendação: **sem contadores no índice**. Eles exigem resolver todas as revistas a cada visita ao índice. Os links levam ao Painel já filtrado, e o Painel mostra a contagem.
- **Grava:** nada.
- **Falta no ER/telas:** nada no ER. Faltam 3 coisas pequenas:
  1. `templates/admin/index.html`, que estende o do Django e acrescenta um `module` "Temporada AAAA" no topo de `content-main`;
  2. `templates/admin/base_site.html`, com o link "Painel AAAA" em `{% block userlinks %}` antes de `block.super`, visível em todas as páginas;
  3. em `sistema/urls.py`, o `path("", …)` redireciona para `/painel/<maior ano>/`, ou para `/admin/` quando não há ano.
  - O "ano da temporada" vem de um `simple_tag` `ano_temporada` (1 query) em `templatetags/`.

**Próxima tarefa por perfil (links do módulo "Temporada"):**

| Perfil (por permissão) | Links, em ordem | Destino |
|---|---|---|
| Impresso (`marcar_impressa`) | **Revistas para atualizar no impresso** | `/painel/AAAA/?falta=impresso`; a célula leva a T26 (outro agente) |
| Pedagógica / Admin (`validar_revista`) | **Painel: o que falta**, Cortes, Variáveis, Escolher matriz, Escolher template F1/F2, Validar no Painel | `/painel/AAAA/`, `corte/?ano=`, `projeto/variaveis/?ano=`, os lotes; cada um aparece só com a permissão |
| Mídias Digitais (mesmas permissões da Pedagógica; ver obs.) | **Revistas validadas para baixar o zip** | `/admin/nucleo/revista/`; o zip continua sendo a action T20 (ver Pergunta 3) |
| Admin (`auth.change_user`) | + Usuários | `/admin/auth/user/` |
| Início de ano (`abrir_ano`, mês sem ano novo) | Abrir ano AAAA+1 | `/admin/nucleo/ano/abrir/` |

Obs.: o inventário diz que Mídias tem "tudo menos usuários e marcar impressa". Então Mídias tem `validar_revista` e vê o mesmo bloco da Pedagógica. O link "Revistas validadas para baixar o zip" entra para quem tem `view_revista` e não tem `marcar_impressa`. Se Mídias e Pedagógica tiverem as mesmas permissões, o bloco é um só, com os dois links.

```
Início                                                    [Painel 2026] [Ver o site] [Alterar senha] [Sair]
┌ module: Temporada 2026 ────────────────────────────────────────────────┐
│ Próxima tarefa                                                         │
│   ▸ Painel: o que falta nas revistas de 2026                           │
│   ▸ Validar no Painel                                                  │
│ Montagem                                                               │
│   Cortes · Variáveis · Escolher matriz · Escolher template F1/F2       │
└────────────────────────────────────────────────────────────────────────┘
┌ module: Núcleo (lista padrão do admin) ...                             ┐
┌ module: Autenticação e autorização ...                                 ┐
```

**Breadcrumbs:** sem nova hierarquia. As páginas próprias da jornada passam a ter "Painel AAAA" no meio, como `painel_validar.html` já faz:
- Painel: `Início › Painel da temporada 2026` (como hoje);
- Validar em lote: `Início › Painel › Validar…` (como hoje);
- T26 (outro agente): `Início › Painel 2026 › Impresso: <revista>`;
- Cortes, Variáveis, Escolher matriz e Escolher template **ficam como estão**. Elas são do ano, não do Painel. O link "Painel AAAA" em `userlinks` dá a volta em 1 clique de qualquer página.

**Onde T26/T27 entram (só navegação):**
- Painel: `painel.link("impresso", …)` (`painel.py:50`) deixa de retornar `None` e retorna a URL de T26.
- T21: `<li>Abrir tela do impresso</a>` em `object-tools`, ao lado de "Abrir preview".
- Índice: o link do perfil Impresso.
- "Baixar planilhas" (T27) fica dentro de T26.

- **Estados:**
  - Vazio (nenhum `Ano`): o módulo mostra `Nenhum ano aberto. Abra o primeiro ano em Anos › Abrir ano.` com o link quando há `abrir_ano`. Sem a permissão: `Nenhum ano aberto. Peça a um Admin para abrir o ano.` `/` vai para `/admin/`, e `userlinks` não mostra "Painel".
  - Erro: `/painel/<ano inexistente>/` → 404 do Django, como hoje. Nenhum link gera ano inexistente, porque todos vêm do `simple_tag`.
  - Só leitura (Impresso): só o link do Impresso e o do Painel; nenhum link de lote.
  - Sucesso: 1 clique do índice até a lista filtrada da própria tarefa.
- **Crítica:**
  - Hoje a primeira tela depois do login é a lista alfabética de modelos: 15+ itens, todos com o mesmo peso. São mais de 4 opções na decisão mais importante, "o que eu faço agora", o que sobrecarrega a carga cognitiva.
  - O módulo "Temporada" põe 1 a 2 ações em destaque por perfil e deixa o resto na lista padrão, abaixo.
  - Não troca o índice por um redirect. O Admin precisa do índice para Usuários e cadastros.
- **Aceite:**
  1. Login como Impresso: o índice mostra "Revistas para atualizar no impresso" com `href="/painel/2026/?falta=impresso"` e nenhum link de lote.
  2. Login como Pedagógica: mostra Painel, Cortes, Variáveis e os 2 lotes.
  3. Usuário sem `change_parceiroano` não vê "Escolher matriz".
  4. Toda página do admin tem "Painel 2026" no `#user-tools`.
  5. `GET /` com login → 302 para `/painel/2026/`. Sem `Ano` → 302 para `/admin/`.
  6. Banco sem `Ano`: o índice mostra a frase de vazio, sem erro 500.
- **Estimativa: 3 h.** São 1 h para os templates, 0,5 h para a tag e o redirect, e 1,5 h para os testes por perfil.

---

### 4. T12 Templates: dois links quebrados

- **Na jornada:** T12 → T17 (aba Variáveis) e T12 → T23 (usado por).
- **Quem usa:** Pedagógica, Mídias e Admin. O Impresso vê.
- **Lê:** `template.pk`, `ano`; no Painel, `revista_fasciculo.template_id`. **Grava:** nada.
- **Falta no ER/telas:**
  - (a) `templates.py:158` aponta para `admin:nucleo_projeto_changelist`. O certo é `reverse("admin:nucleo_projeto_variaveis") + "?ano=…"`, com o ano do filtro da lista quando houver.
  - (b) `templates.py:146-151` monta `/painel/{ano}/?template={pk}` à mão, e o painel ignora o `template`. Correção: `reverse("painel", …)` no link, e no Painel (`painel.py:106-121`) o filtro `template` (`revistas.filter(fasciculos__template_id=pk)`, conferir o `related_name`).
  - Quando ativo, o filtro aparece como `<p class="filtro">Template: <strong>LP F2 2026</strong> · <a>limpar</a></p>`, no padrão de `_filtros.html`.
  - Os outros filtros (falta/parceiro) preservam o `template` na URL.

```
Início › Painel da temporada 2026
Falta: Tudo · Matriz · ...      Parceiro: Todos · A · B
Template: LP F2 2026 · limpar
┌ #painel ───────────────────────────────────────────────┐
│ Revista            Matriz  Template F1 ... Validado    │
└────────────────────────────────────────────────────────┘
```

- **Estados:**
  - Vazio: "Nenhuma revista ativa com esse filtro." (texto que já existe).
  - Erro (`template` inexistente ou de outro ano): o filtro é ignorado, sem erro, como já acontece com `parceiro` inválido.
  - Só leitura: igual ao Painel atual.
  - Sucesso: "usado por 7" leva a uma lista com 7 linhas.
- **Crítica:** um contador clicável que leva a uma lista que não bate com o número quebra a confiança na tela (heurística 1). A aba "Variáveis" que abre "Projetos" contradiz o próprio rótulo (heurística 4).
- **Aceite:**
  1. Aba Variáveis: `href` resolve para `/admin/nucleo/projeto/variaveis/`.
  2. Template usado por N revistas ativas: o link leva ao Painel com exatamente N linhas (teste com 2 templates e 3 revistas).
  3. Trocar o filtro Parceiro mantém `template=` na URL.
- **Estimativa: 1,5 h.**

---

## Depois

### D1. T28 Histórico por registro: **decisão: o `simple_history` no admin basta**

- **Recomendação:** trocar `admin.ModelAdmin` por `SimpleHistoryAdmin` em Projeto, Revista, CorPadrao, Template, Matriz, MatrizEtapaCC e Descritor. Todos os modelos já têm `HistoricalRecords()` (`models/*.py`). O botão "Histórico" do admin passa a listar as versões, com quem, quando e motivo (`_change_reason` já é gravado em `servicos/matriz.py:48`, `abrir_ano.py:71`, `cascata.py:102`).
- **Obrigatório junto:** `SIMPLE_HISTORY_REVERT_DISABLED = True` em `sistema/settings.py`. O "reverter" do `simple_history` grava sem passar pelo bloqueio (`BloqueioAdminMixin`), sem hash visto e sem a cascata. Isso quebraria D-081, D-089 e D-093.
- **Por que não uma tela "o que mudou nesta revista":** a revista resolvida junta cerca de 10 tabelas (corte, MEC, descritor, tarefa, cor, projeto, versão de template, seção). O diff que importa para o trabalho já existe:
  - T24 / T26 comparam o resolvido com a última `foto_revista` impressa;
  - T14 mostra o impacto do template;
  - T09 mostra as diferenças da matriz.
  - Uma tela nova duplicaria esse diff com outra regra. Adiar até alguém pedir "quem mudou o corte da revista X", o que o histórico do Corte (Projeto › Histórico) já responde.
- **Lê:** `historical_*`. **Grava:** nada (revert desligado).
- **Estado só leitura:** o histórico de um registro arquivado mostra as versões normalmente.
- **Aceite:**
  1. "Histórico" em Projeto lista as versões do `historical_projeto` com o usuário.
  2. Não existe botão "Reverter": a URL de revert retorna 403 ou 404.
  3. O usuário Impresso vê o histórico e não altera nada.
- **Estimativa: 1,5 h.**

### D2. `tarefa.arquivo` no inline T11 (depende da Pergunta 1)

- **Na jornada:** T10 → **T11** → T22 / zip (`empacotar._itens` já empacota `arquivos/itens/<id>.<tipo>`; `resolver.py:19-20`).
- **Quem usa:** Pedagógica, Mídias e Admin.
- **Grava:** `tarefa.arquivo` (caminho no storage) via `arquivos._gravar`. Falta um `receber_item()` no padrão de `receber_capa`: tipo pelo conteúdo, PNG/JPG/WebP/PDF, até 5 MB.
- **Cuidado:** o caminho é compartilhado entre anos pelo `abrir_ano` (`models/matriz.py:93-94`). Trocar o arquivo só apaga o antigo se nenhuma outra `Tarefa` usar o mesmo caminho.
- **Inline:** coluna "Arquivo do item" = `FileField` não ligado ao modelo + texto "atual: <nome> (baixar)" + checkbox "Remover". É o mesmo padrão de `arquivo_svg` / `arquivo_capa` em `admin/revista.py:53-56`.
- **Mensagens:**
  - `Arquivo do item acima de 5 MB. Reduza a imagem ou exporte o PDF com menos resolução.`
  - `Tipo não aceito: use PNG, JPG, WebP ou PDF.`
- **Bloqueio:** o inline já está sob o bloqueio da MEC. Com N revistas afetadas, vale o mesmo "Confirmo: afeta N".
- **Aceite:**
  1. Enviar PNG na tarefa grava `arquivo`, e o preview mostra o item.
  2. Trocar um arquivo compartilhado com o ano anterior não apaga o do ano anterior.
  3. O zip contém `arquivos/itens/<id>.png`.
- **Estimativa: 4 h.**

### D3. Outros desejáveis (sem rascunho agora)

1. Botão "Baixar zip" por linha no Painel, quando validada: uma view GET que reaproveita `zip_revista`. Hoje o zip é uma action da lista, com 3 cliques (Pergunta 3). **2 h.**
2. Lista de versões do template (`template_versao` antigas) em T13: o D1 já cobre isso via Histórico do `TemplateVersao`. **0 h** se D1 incluir `TemplateVersaoAdmin` só leitura.
3. `template.origem` readonly no form de T13. **0,25 h.**
4. Zip em lote do ano (`revista.py:558`). **3 h.**
5. Mensagem do 404 do preview com a correção. Já entra no item 1 se couber.

---

## Perguntas ao usuário

1. **As matrizes de 2026 têm imagem ou PDF por item (`tarefa.arquivo`)?** Recomendação: **se tiverem, D2 sobe para "Fazer agora"** (+4 h). Sem tela, o importador não preenche e o item some do preview e do zip. Se não tiverem, fica para 2027.
2. **`/` redireciona para o Painel do maior ano, mantendo o índice do admin com o módulo "Temporada" no topo?** Recomendação: **sim**. Trocar o índice pelo Painel tiraria do Admin o acesso a Usuários e cadastros, e o módulo dá a cada perfil a próxima tarefa em 1 clique.
3. **Mídias Digitais baixa o zip pelo Painel (botão por linha validada) já em 2026?** Recomendação: **não agora**. O link do índice para a lista de Revistas + action "Baixar zip" funciona. O botão no Painel (D3.1, 2 h) entra quando o volume de revistas tornar os 3 cliques um gargalo.
