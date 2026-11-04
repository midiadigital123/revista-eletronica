# Plano: exclusão só do que não está em uso (D-205)

Data: 2026-11-04. Base: `feat/telas-b-ux` (`20630c3`). Execução no padrão D-201: um subagente e um worktree por passo, compose isolado, TDD com teste Django antes, Playwright onde houver tela.

**Regra (D-205):** toda entidade pode ser excluída quando nada depende dela. Em uso, a tela diz o que impede, com contagem e links, e oferece arquivar ou desativar quando isso existir. O `PROTECT` continua no banco. `TemplateVersao` continua só de inserção (D-125). Usuário é desativado, nunca excluído. Nenhuma cascata apaga histórico.

Correção do levantamento: hoje a tela B **não** exclui Matriz. `templates/ui/matriz/excluir.html` serve só para tarefa e descritor (`urls/ui_matriz.py:521-552`, D-181).

## 1. Regra por entidade

FKs são `PROTECT`, salvo quando a tabela diz o contrário. "Partes" saem junto com a entidade e não contam como uso. "Ped/Míd/Admin" quer dizer Pedagógica, Mídias Digitais e Admin. O Impresso nunca exclui.

| Entidade | "Em uso" quer dizer | Quando está em uso | Quem exclui | Botão | Existe hoje? |
|---|---|---|---|---|---|
| Ano | Vazio: sai direto. Com dados: o Admin pode **apagar o ano inteiro** (D-206) | A página lista tudo o que sai junto, com contagens (projetos, revistas, fotos, matrizes, templates e versões, cortes); o Admin digita o ano para confirmar | **Só Admin** (D-206) | Tela B `ui/anos/anos.html:21`; o admin do Django leva à mesma página | Não |
| Parceiro | Tem Corte ou Projeto em algum ano (ParceiroAno vazio é parte) | Explica e oferece **Desativar** (D-208): some dos anos em que não tem dados; Reativar desfaz | Ped/Míd/Admin | `ui/parciais/cortes_grade.html:21` (no `<th>`); admin `ParceiroAdmin` (`admin/cadastro.py:75`) | Não |
| Etapa | Tem Corte, MatrizEtapaCC ou ProjetoPasso | Explica | Ped/Míd/Admin | `ui/parciais/ano_linha.html:10`; admin `EtapaAdmin` (`:93`) | Não |
| Componente | Tem Revista, RevistaFasciculo, MEC, Corte, ProjetoPasso ou Template | Explica | Ped/Míd/Admin | `ano_linha.html:10`; admin `ComponenteAdmin` (`:106`) | Não |
| Matriz | Algum `ParceiroAno.matriz` aponta para ela; MEC com bloqueio de outra pessoa (MEC, descritor e tarefa são partes) | Explica, com link para a aba Matriz ou Lotes | Ped/Míd/Admin | `ui/matriz/matriz.html:18`; admin `MatrizAdmin` (`admin/matriz.py:78`) | Não |
| Template | Alguma revista usa (RevistaFasciculo.template, RevistaSecao.template ou uma versão dele). As versões são partes | Livre: **exclui de fato, com as versões** (exceção à D-125, D-207). Em uso: explica, com links para as revistas | Ped/Míd/Admin, nunca o Impresso (D-207) | Tela B `ui/templates/editar.html` e `lista.html` | Não |
| Corte | Nunca está em uso | Célula vazia apaga e arquiva a revista (`servicos/cascata.py:120-122`) | Quem preenche cortes | Grade | **Sim** |
| Projeto, Revista | Sempre: a revista existe enquanto houver corte, e a cascata recriaria a que fosse apagada (`cascata.py:82-98`) | Já arquivam pela cascata | — | Admin segue negando | Sim (arquivar) |
| Descritor, Tarefa | Regra própria (D-181, com impacto) | Mantém | Ped/Míd/Admin | `urls/ui_matriz.py:533-552` | **Sim** |
| ProjetoPasso, ProjetoCor, RevistaSecao | Nunca estão em uso | Já se excluem (`ui_projeto.py:444/:467`; "voltar ao template") | Editores | — | **Sim** |
| Usuário | Tem TemplateVersao, FotoRevista ou `Revista.validado_por` | Desativar (`is_active`) | Admin | Admin (`admin/usuarios.py:37`) | **Sim** |
| CorPadrao, ParceiroAno, MatrizEtapaCC, RevistaFasciculo, FotoRevista, TemplateVersao, Bloqueio | Partes, histórico ou dados fixos | Sem botão próprio | — | — | — |

## 2. Mecanismo comum (passo E0)

- **`servicos/exclusao.py`**:
  - `impedimentos(obj)` devolve uma lista com (rótulo plural, contagem, até 5 links). A coleta com `Collector` e `ProtectedError` é feita separada por objeto e por parte, porque o PROTECT não desconta o que já está sendo coletado. Para Matriz, também conta a MEC com bloqueio de outra pessoa.
  - `excluir(obj, usuario)` roda em `atomic` com `select_for_update` e confere de novo antes de apagar. Grava `_history_user` e apaga as partes antes do objeto. Um `IntegrityError` numa corrida vira `EmUso`.
  - `PARTES = {Parceiro: ["parceiroano_set"], Matriz: ["matrizetapacc_set"], Template: ["templateversao_set"]}`.
  - `apagar_ano(ano, usuario)` (D-206): em `atomic`, apaga tudo do ano na ordem das dependências (fotos → seções → revistas → projetos/passos/cores → cortes → ParceiroAno → tarefas/descritores/MEC → matrizes → versões → templates → cores do padrão → componentes → etapas → ano). `resumo_ano(ano)` devolve as contagens para a página de confirmação. Só o Admin pode.
  - **Exceção ao trigger da `TemplateVersao`** (D-206, D-207): uma migração troca a função `template_versao_so_insert` para deixar o DELETE passar só quando a transação ligou `SET LOCAL revista.apagar_versoes = 'on'`. Só `excluir(template)` e `apagar_ano` ligam essa chave. UPDATE continua proibido sempre.
- **`urls/ui_excluir.py`**: rota `/ui/excluir/<modelo>/<pk>/` (`ui_excluir`). `REGISTRO` lista ano, parceiro, etapa, componente e matriz. A rota exige `nucleo.delete_<modelo>` e devolve 403 sem ela. Reaproveita o `ExcluirForm` (`nucleo/matriz.py:211`): digitar o código ou o nome. O `?voltar=` é validado com `url_has_allowed_host_and_scheme`.
- **`templates/ui/excluir.html`**: segue a estrutura de `ui/matriz/excluir.html`. Em uso, lista os impedimentos com links e diz o que fazer. Livre, usa `_componentes/confirmar.html` e o `btn-destrutivo`.
- **Permissões**: ação `excluir_sem_uso` em `permissoes.py:41` (`delete_` de parceiro, etapa, componente, matriz e template), dada à Pedagógica (`:81`), e com isso à Mídias e ao Admin. `delete_ano` só no grupo Admin (D-206). Migração de dados `0016_excluir_sem_uso` com a lista congelada, como na 0014.
- **`Etapa.delete()`** renumera as etapas com `renumerar_etapas`, como o `save` já faz (`models/cadastro.py:72`).
- **Campo novo, um só:** `Parceiro.desativado_em` (D-208), migração `0018_parceiro_desativado_em`. Serviço `desativar_parceiro`/`reativar_parceiro` e `parceiros_do_ano(ano)` (ativos + desativados com Corte ou Projeto ativo no ano). O `Template.arquivado_em` saiu com a D-207. A migração `0017_versao_apagavel` só troca a função do trigger.
- **Trava de regressão:** um teste lista toda FK de `nucleo` que não é PROTECT contra uma lista permitida: `Bloqueio.*`, `Descritor.matriz_etapa_cc`, `Tarefa.descritor`, `RevistaFasciculo.revista`, `RevistaSecao.revista_fasciculo`, `Matriz.duplicada_de`.

Fica de fora:
- modal de impacto: sem uso, nenhuma revista perde o Validado;
- lixeira e restaurar: descartados em 30/10;
- exclusão em massa;
- contagem prévia nas listas: evita um `Collector` por linha;
- botões para Projeto, Revista, MEC, ParceiroAno e CorPadrao.

## 3. Passos

| Passo | Branch | Arquivos donos | Testes | Horas |
|---|---|---|---|---|
| **E0 base** (sozinho, primeiro) | `feat/excl-base` | `servicos/exclusao.py`, `urls/ui_excluir.py`, `urls/__init__.py`, `templates/ui/excluir.html`, `permissoes.py`, `migrations/0016_*` e `0017_*`, `models/cadastro.py` (`Etapa.delete`) | `test_exclusao.py` (impedimentos por entidade, partes, bloqueio da MEC, corrida, lista de FKs, template livre com versões, trigger ainda barra fora da chave, `apagar_ano` com tudo, só Admin, view 403/GET/POST, código errado), `test_permissoes.py`, `e2e/tests/excluir.spec.ts` | 6 |
| E1 anos | `feat/excl-anos` | `ui/anos/anos.html`, `ui/parciais/ano_linha.html`, `urls/ui_anos.py` | `test_ui_anos.py`, `ano.spec.ts`, `anos.spec.ts` | 2,5 |
| E2 parceiro | `feat/excl-parceiro` | `ui/parciais/cortes_grade.html`, `urls/cortes.py` (a grade usa `parceiros_do_ano`; o parceiro desativado aparece marcado "desativado") | `test_ui_cortes.py`, `cortes.spec.ts` | 2 |
| E3 matriz | `feat/excl-matriz` | `ui/matriz/matriz.html` | `test_ui_matriz.py`, `mec.spec.ts` | 1,5 |
| E4 template | `feat/excl-template` | `ui/templates/editar.html`, `ui/templates/lista.html` (link "Excluir" para `ui_excluir`, escondido do Impresso; template com bloqueio de outra pessoa conta como impedimento) | `test_ui_templates.py`, `templates-editor.spec.ts` (o spec passa a apagar o template "E2E…" que cria) | 1,5 |
| E5 admin | `feat/excl-admin` | `admin/cadastro.py` (`ExclusaoAdminMixin`: `delete_view` leva ao `ui_excluir`, sem `delete_selected`; sai o `SoLeitura` do `AnoAdmin`), `admin/matriz.py`, `admin/templates.py` (filtro "arquivado"), comentários D-205 em `admin/revista.py`, `admin/projeto.py` e `admin/usuarios.py` | `test_admin_cadastro.py` | 1,5 |

**Integração:**
- E0 é mergeado em `feat/telas-b-ux`. Depois, E1–E5 rodam em paralelo a partir do topo do E0.
- O merge vai na ordem E5 → E2 → E3 → E1 → E4.
- No fim: suíte Django, `makemigrations --check` e Playwright nas duas larguras. Antes do Playwright, recriar a demo de 2026 e o ano 2025 vazio.
- Total: cerca de 15 h de agente, ou cerca de 9 h de relógio.

**Cuidados:**
- Só o E0 cria migração.
- O spec que exclui ano cria o próprio ano (ex.: 2019) e nunca usa o 2025.
- Nas linhas de formset e na grade, o "Excluir" é um link para a página, porque form dentro de form é HTML inválido.
- Com a exclusão pronta, os specs passam a apagar os parceiros "E2E …" e os templates "E2E …" que criam.
- O spec do E1 que apaga ano usa um ano próprio criado pelo `abrir_ano` (ex.: 2019, com matriz e templates copiados), nunca o 2025 nem o 2026.
- Depois da integração, atualizar a seção 9 de `docs/regras-de-negocio.md`.

## 4. Respostas do usuário (04/11)

1. Ano: abre a exceção para apagar o ano inteiro, só o Admin, direto pela tela B (D-206).
2. Template: todos os perfis menos o Impresso excluem pela tela; o template sem uso sai com as versões (D-207).
3. "Desativar parceiro": sim (D-208).
4. Só o Admin exclui Ano (D-206).
