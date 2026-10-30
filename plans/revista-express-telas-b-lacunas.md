# Blueprint — Telas B cobrem tudo o que o back faz (21 itens)

> Depois da aprovação, este arquivo é copiado para `plans/revista-express-telas-b-lacunas.md` (versionado) e cada passo vira uma linha no `state.md`.

## Contexto
A auditoria de 30/10 (D-189) achou 18 lacunas nas telas B (UI Django fora do admin). Em cada uma, o back permite a ação a um perfil, mas a tela não a oferece, manda para o admin ou mostra o que o perfil não pode usar. O usuário achou mais três:
- **19.** Não dá para atribuir uma matriz pela ficha do projeto. No banco local, 0 de 2 `ParceiroAno` têm matriz, então nenhuma revista carrega matriz.
- **20.** A ficha da revista mostra o nome do projeto sem caminho para editá-lo.
- **21.** O preview com matriz nula mostra o F1 vazio (select, pré-requisitos e BNCC em branco) **sem faixa vermelha**. Só o template ausente tem faixa (`servicos/resolver.py:58`).

Regra do usuário (learning `l-9d315257`): toda função do back precisa de um controle na tela B, link para o admin não conta, e nada que o perfil não possa usar deve aparecer.
Resultado esperado: os 4 perfis trabalham só pelas telas B. O admin fica como ferramenta do perfil Admin.

## Modo de execução
- **Git direto:** branch `feat/telas-b-lacunas`, criada a partir de `refatoracao-django`. Um commit por passo, merge no fim.
- **Antes de tudo:** o S0 faz o commit do que está pendente (D-189 e o learning).
- **Subagente:** cada passo pode rodar num subagente com o brief do próprio passo.
- **Modelo:** o padrão (Sonnet), menos S2 e S9, que pedem o mais forte por causa do bloqueio de edição e de segurança.

## Invariantes (conferir ao fim de cada passo)
1. `docker compose exec -T app python manage.py test nucleo` passa.
2. `docker compose exec -T app python manage.py makemigrations --check --dry-run` não acusa migração. Nenhum passo cria migração: todas as permissões já estão nos papéis certos.
3. `cd app/e2e && npx playwright test` passa **em todo passo** que troca link ou tela.
4. Todo controle novo é checado duas vezes: `perms.`/flag no template e a mesma permissão na view (403).
5. O teste do passo cobre as duas pontas: o perfil com permissão grava, e o Impresso não vê o controle e recebe 403 no POST.
6. `grep -rn "admin:" app/nucleo/templates/ui` só pode diminuir.

## Padrões a reaproveitar (não reinventar)
- **Cadastro simples:** `modelform_factory` + `messages` + `redirect` (POST/redirect/GET), como em `novo_parceiro` (`app/nucleo/urls/cortes.py`).
- **Bloqueio de edição:** `com_bloqueio(_alvo, …)` (`app/nucleo/ui_bloqueio.py:82-84`). O POST precisa usar a **mesma sessão** de bloqueio do GET (`servicos/bloqueio.py:53-55`). Nunca chamar `lotes.aplicar`/`escrever_travado` a partir de uma página que já trava, porque eles abrem uma `nova_sessao()` (`lotes.py:47-49`) e a gravação é recusada.
- **Confirmação de impacto no "Validado":** `revistas_afetadas_padrao` + `PadraoImpactoForm` (`admin/cadastro.py:117-185`).
- **Regras de usuário:** `UsuarioAdmin` (`admin/usuarios.py:23-78`).
- **Testes:** `Base` (`nucleo/tests/test_admin_cadastro.py:87`) e `usuario(nome, papel)` (`nucleo/tests/test_resolver.py:64`). Visual: `docs/telas/design-system.md` e `ui/_componentes/`.

## Grafo de dependências
```
S0 → S1 → S2 → S3 → S4 → S5
          ├──→ S6 → S8
          ├──→ S7            (S7 em paralelo com S6)
          └──→ S9            (independente depois de S1)
Fechamento: depois de todos
```
S6 e S8 mexem no mesmo arquivo, `urls/ui_matriz.py`, por isso rodam em série.

## Mapa item → passo
| Item | Passo |
|---|---|
| 10 a 13, 16, 18 (links, mensagens, menu) | S1 |
| **19** matriz no projeto, **20** nome do projeto, **21** faixa sem matriz, 6 renomear parceiro | S2 |
| 1 abrir ano | S3 |
| 5 etapas e componentes | S4 |
| 4 paleta | S5 |
| 2 nova matriz | S6 |
| 3 novo template | S7 |
| 8, 9, 14, 15 downloads | S8 |
| 7 usuários | S9 |
| 17 botão Admin | Fechamento |

---

## S0 — Commit do pendente (~5 min)
- **Tarefas:** commit de `urls/cortes.py`, `ui/cortes.html`, `test_ui_cortes.py` e `.trail/learnings/2026-10-30-toda-func-a-o-do-back-otavio.md`; depois `state.md` num commit próprio; depois criar a branch `feat/telas-b-lacunas`.
- **Saída:** `git status` limpo.

## S1 — Links e mensagens sem admin nem 403 (~2 h)
- **Brief:** `link()` (`app/nucleo/urls/painel.py:40-52`) aponta as pendências do painel para o admin. Em "matriz", isso dá 403 ao Impresso (`admin/lote.py:59`).
- **Tarefas:**
  1. Mudar os destinos em `link()`:
     - `matriz` e `corte_sem_matriz` → `ui_projeto`;
     - `corte_invalido` → `cortes`;
     - `variaveis` e `nome_projeto` → `ui_projeto`;
     - `impresso` → `reverse("ui_impresso", args=[ano]) + "?revista=<pk>"`;
     - template, SVG, capa e Validado → `reverse("ui_revista_editar", args=[ano, pk])`.
  2. "Abra um ano no admin" (`ui/cortes.html:25`, `variaveis/pagina.html:22`, `matriz/lista.html:19`, `templates/lista.html:25`, `revista/lista.html:16`): o link só aparece com `perms.nucleo.abrir_ano`. Sem a permissão, o texto vira "Peça a um administrador para abrir o ano". "Cadastre os componentes" (`lotes/template.html:11`) segue a mesma regra, com `add_componente`.
  3. Trocar os `rota_b` com fallback para o admin (`base.html:28-37`, `painel_tarefa.html:24-26`, `projeto/lista.html:14-16`, `projeto/projeto.html:16`, `parciais/variaveis_linha.html:10`, `templates/lista.html:33-34`). Esses fallbacks **não estão mortos**: sem `ano` no contexto, `rota_b` devolve "" (`templatetags/ui.py:15-20`). Usar `{% if ano %}<rota> ano.ano{% else %}<rota>_inicio{% endif %}` e criar `ui_lotes_inicio`, que redireciona para o ano mais recente, como faz `cortes_inicio`.
  4. Na ficha da revista (`ui/revista/revista.html:24`), "Tela do impresso" passa a apontar para `ui_impresso` + `?revista=`.
  5. Na ficha do projeto (`projeto.html:12`), ao lado de "ainda não escolhida": um link "Escolher matriz" para `ui_lotes_matriz` (só com `change_parceiroano`). Fica até o seletor do S2. A tela de lotes funciona (`test_ui_lotes.py:38,50`); o problema é que quase não se chega a ela.
  6. Menu (`base.html`): incluir "Projetos" (`ui_projeto_inicio`/`ui_projeto_lista`) e "Lotes" (`ui_lotes_inicio`/`ui_lotes_matriz`).
  7. Atualizar o Playwright:
     - `painel.spec.ts:56-63` esperava o admin depois do "falta" de Variáveis; agora espera a ficha do projeto.
     - `impresso.spec.ts:66-71` esperava o h1 "Impresso:"; o da tela B é "Impresso".
- **Verificação:** um teste novo, `test_ui_links.py`, confere que, para Impresso e Pedagógica, todo link do painel renderizado devolve 200 e nenhum contém `/admin/`. E o Playwright passa.

## S2 — Matriz, nome e faixas da ficha (~3 h, modelo mais forte)
- **Brief:** a matriz fica em `ParceiroAno.matriz` (`models/projeto.py:19`, nula até ser escolhida). Hoje só a tela de lotes (`ui_lotes_matriz`) a grava, pela regra `lotes.MatrizLoteForm` + `gravar_matriz` (`lotes.py:107-140`). A ficha do projeto (`ui/projeto/projeto.html:12`) só mostra "ainda não escolhida". A ficha inteira já é um único `<form>`, com `bloqueio.html` dentro (`projeto.html:29-30`).
- **Tarefas:**
  1. **Matriz (19):**
     - Form **separado** no cabeçalho da ficha (`projeto.html:10-17`), fora do form principal, com o campo hidden da sessão de bloqueio (`request.bloqueio.campo`).
     - Rota `ui_projeto_matriz`, sob `@com_bloqueio(_alvo, …)`.
     - Validar com `MatrizLoteForm(ano=…, data={"alvos": [pa.pk], "matriz": …})` e gravar `pa.matriz` direto, **sem** `lotes.aplicar`.
     - Visível com `change_parceiroano`; sem a permissão, mostra só o nome da matriz.
  2. **Faixa sem matriz (21), FORA do resolvido.**
     - **Causa:** sem matriz, `resolver.py:138` não busca descritores; `dados` só traz `scaleRange`, `cortes` e `padroes` (`:160-169`). O JS monta as abas e nunca chama `updateContent` (`static/revista/f1/script.js:667-711`). Nenhuma faixa trata matriz (`templates/revista/index.html:61,179-180`, flags em `servicos/html.py:83-85`).
     - **Não copiar `FAIXA_SEM_TEMPLATE`:** ela mora dentro do resolvido (`resolver.py:266`). Uma chave nova ali muda o hash de todas as revistas, e todas perdem o "Validado".
     - **Preview:** em `contexto_pagina` (`servicos/html.py`), a flag `sem_matriz` = há etapas e nenhuma tem descritor (calculada de `dados`, então também cobre `corte_sem_matriz` e a foto arquivada), e uma faixa "Falta escolher a matriz" em `index.html` perto da linha 61, só no preview (D-116).
     - **Ficha da revista:** `ui/_componentes/faixa.html` quando `parceiro_ano.matriz_id` é nulo, como a faixa de template (`ui/revista/revista.html:48`), levando ao seletor da ficha do projeto.
     - **Teste:** o hash de uma revista sem matriz não muda com a mudança.
  3. **Nome do projeto (20): editar na própria revista.** Um link para a ficha não serve: a revista trava o projeto (`ui_revista.py:61-66`), e a ficha abriria só leitura com "em edição por" a própria pessoa (`bloqueio.js:86-87`).
     - No `<h1>` da revista (`ui/revista/revista.html:15`), um botão "Editar nome" que abre um campo em linha.
     - O POST usa `acao == "nome"` dentro de `revista()` (`ui_revista.py:144-150`), que já roda sob `_salvar` com a sessão da revista, com `modelform_factory(Projeto, fields=["nome"])` e limite de 200.
     - A guarda é uma flag de contexto com a mesma checagem da view (`request.pode_gravar and not arquivada`), nas duas pontas.
     - A lista de revistas (`ui/revista/lista.html:29`) já leva à revista, então não muda.
  4. **Renomear parceiro (6):**
     - Botão "Renomear" por linha da grade de cortes, visível com `change_parceiro`.
     - Rota `cortes_renomear_parceiro`, com `modelform_factory(Parceiro, fields=["nome"])(instance=…)`.
     - O nome entra no hash (`resolver.py:236, 293-296`) e vale para todos os anos. Por isso: confirmação que lista as revistas validadas que perdem o "Validado", no padrão de `revistas_afetadas_padrao`.
- **Verificação:**
  - O teste faz o GET da ficha (pega o bloqueio) e depois o POST da matriz; a ficha mostra o nome da matriz.
  - Outra sessão com o projeto aberto recebe "em edição por".
  - O preview sem matriz mostra a faixa vermelha, e o hash não muda.
  - Renomear lista o impacto e grava só depois da confirmação.
  - O Impresso recebe 403 em tudo.

## S3 — Abrir ano na tela B (~45 min)
- **Brief:** o serviço `servicos/abrir_ano.py:43` faz tudo e recusa ano fora de sequência (`:64-65`). O admin (`admin/cadastro.py:36-71`) **obriga a digitar o ano**, porque não há desfazer.
- **Tarefas:** `ui/anos/` com a lista de anos e um formulário "Abrir ano" em que se **digita** o ano (o próximo aparece como dica) e um texto de confirmação igual ao do admin. Rota `ui_anos`, ligada a `_componentes/anos.html` e às mensagens do S1, que trocam "Peça…" pelo link desta tela.
- **Verificação:** a Pedagógica abre 2027; um ano fora de sequência dá erro e nada é gravado; o Impresso recebe 403.

## S4 — Etapas e componentes (~2 h 30)
- **Brief:** só o admin edita (`admin/cadastro.py:94-110`). Na edição, o ano e o código ficam somente leitura (senão a checagem de unicidade vira erro 500). `escala_max` fica somente leitura **quando há corte ou matriz gravados** (`:98-102`). O componente tem `codigo` **e `nome`** (`:105-108`).
- **Tarefas:** na página do ano (S3), duas tabelas, Etapas (código, escala máxima, ordem) e Componentes (código, nome), com "Adicionar" e edição em linha (HTMX, padrão de `ui_projeto_linha`), repetindo as regras de somente leitura.
- **Verificação:** criar e editar funcionam; código duplicado dá mensagem e não erro 500; escala com corte aparece como somente leitura; o Impresso só lê.

## S5 — Paleta do ano (~1 h 30)
- **Brief:** `CorPadrao` só existe no admin (`admin/cadastro.py:190-211`). A confirmação de impacto é reutilizável: `revistas_afetadas_padrao` + `PadraoImpactoForm` (`:117-185`).
- **Tarefas:** seção "Padrões" na página do ano, com `modelform_factory(CorPadrao, form=PadraoImpactoForm, fields=["nome", "cor"])` e o `impacto` na classe, como em `:197-201`.
- **Verificação:** trocar uma cor lista as revistas afetadas, e depois de confirmar elas perdem o "Validado". O contraste da régua segue o WCAG.

## S6 — Nova matriz (~2 h)
- **Brief:** a B duplica, renomeia e reimporta (`ui_matriz_duplicar`, `_renomear`, `_reimportar`), mas não cria. O estado vazio manda rodar `importar_matriz` (`ui/matriz/lista.html:46`). Exige `add_matriz`.
- **Tarefas:** um botão "Nova matriz" (nome + ano) que leva ao reimportar, já existente, para subir o arquivo. Trocar o texto do estado vazio.
- **Verificação:** criar, importar o arquivo de exemplo e ver os descritores.

## S7 — Novo template (~2 h, em paralelo com S6)
- **Brief:** "Novo template" vai a `admin:nucleo_template_add` (`ui/templates/lista.html:14,59`; regra em `admin/templates.py:132`). Exige `add_template` + `add_templateversao` (D-115).
- **Tarefas:** rota `ui_templates_novo` com o mesmo form e a mesma validação do admin, redirecionando para `ui_templates_editar`.
- **Verificação:** criar e ver a 1ª versão; o Impresso recebe 403.

## S8 — Downloads pela tela B (~1 h, depois de S6)
- **Tarefas:**
  1. Planilhas F1/F2: usar a rota que já existe fora do admin, `impresso_planilhas` (`urls/impresso.py:163-176`), e colocar o botão na ficha e na lista da revista.
  2. Gabarito de ids (`admin/revista.py:279`): rota B com a mesma função. O botão aparece quando **há template F2**, mesmo sem SVG, porque o gabarito serve para montar o SVG.
  3. Planilha de grupos (`admin/cortes.py:32`): rota B.
  4. Arquivo do item: um GET de download em `ui_matriz_item`, que já envia e remove arquivos.
- **Verificação:** cada download devolve 200 com o tipo certo; nenhum `admin:` sobra nesses templates.

## S9 — Usuários na tela B (~4 h, modelo mais forte)
- **Brief:** só o perfil Admin tem `gerenciar_usuarios`. Copiar as regras de `UsuarioAdmin` (`admin/usuarios.py:23-78`) para um módulo comum, usado pelo admin e pela B:
  - quem não é superusuário só atribui **Pedagógica e Mídias Digitais** (`:23-27`);
  - superusuários ficam fora da lista (`:43-45`);
  - ninguém muda os próprios grupos nem se desativa (`:50-51`);
  - não mexe em quem tem grupo fora dos permitidos (`:52-53`);
  - não edita outro Admin (`:56-64`);
  - usuário novo nasce com `is_staff=True` (`:71-74`);
  - nunca apagar, só desativar (D-142).
- **Tarefas:** listar, criar (`UserCreationForm`), mudar o grupo, ativar ou desativar, e redefinir a senha.
- **Verificação:** um teste para cada regra acima; um não-Admin recebe 403.

## Fechamento (~30 min)
1. Botão "Admin" do cabeçalho (`base.html:41`, item 17): aparece só com `perms.auth.change_user`. Fica para o fim porque, até o S7, a Pedagógica ainda precisa do admin.
2. Rodar a suíte, `makemigrations --check` e o Playwright; `grep -rn "admin:" app/nucleo/templates/ui` só pode mostrar login, logout e o botão Admin.
3. `trail check`, merge em `refatoracao-django`, `state.md` num commit próprio por último.

**Total:** ~20 h de execução (~17 h com S6 e S7 em paralelo).
**Plano de volta:** um commit por passo, e `git revert <sha>` desfaz cada um isoladamente.
