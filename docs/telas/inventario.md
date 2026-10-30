# Inventário das telas (UI) — revista-express em Django admin

Fonte: branch `refatoracao-django` em 2026-10-30 (D-046 a D-175; S01–S12 e S16 feitos; S13, S17, S18 não iniciados). Trabalho só leitura.
Caminhos relativos a `/home/otavio.peres/dev/revista-express/`.

**Ponto de partida:** as telas de S11a, S11b1, S11b2, S11c e S12 **já existem e funcionam** (cadastros, matriz, grade de cortes, templates, textos por seção, projeto, aba Variáveis, uploads, lotes, painel, Validado). Este inventário parte delas. Nenhuma deve ser refeita; o que falta é listado em "Lacunas" como ajuste pontual ou tela nova. A seção 6, "Estilo existente", é referência obrigatória para as telas novas.

Perfis (`app/nucleo/permissoes.py:73-84`): **Admin** = Pedagógica + usuários; **Pedagógica** e **Mídias Digitais** = tudo menos usuários e "marcar impressa"; **Impresso** = só leitura + `marcar_impressa`. Admin **não** marca impressa (`permissoes.py:16`).

---

## 1. Jornada da temporada

```
[Abrir ano] ──> [Conferir cadastros do ano] ──> [Matrizes] ──> [Parceiros] ──> [Cortes]
   T03              T05 T06 T07                 T09–T11         T04          T08 (+T08b planilha de grupos)
   Ped/Mid/Adm      Ped/Mid/Adm                 Ped/Mid/Adm     Ped/Mid/Adm  Ped/Mid/Adm
                                                                               │ cascata (S06): projeto + revistas
                                                                               ▼
[Escolher matriz] ──> [Escolher templates] ──> [Editar templates] ──> [Projeto: nome + variáveis]
   T18 (lote)           T19 (lote)               T12 T13 T14           T16 / T17 (+ copiar do ano anterior)
   Ped/Mid/Adm          Ped/Mid/Adm              Ped/Mid/Adm           Ped/Mid/Adm
                                                                               │
                                                                               ▼
[Revista: SVG + capa + textos por seção] ──> [Preview] ──> [Painel] ──> [Validado]
   T21 (gabarito de ids T21b)                   T22          T23         T21 (1 a 1) / T24 (lote)
   Ped/Mid/Adm (design entrega o SVG)           todos        todos       Ped/Mid/Adm
                                                                               │
                                    ┌──────────────────────────────────────────┴───────────────┐
                                    ▼                                                          ▼
                     [Impresso: "o que mudou" + Revista Impressa Atualizada]        [Baixar zip da revista]
                        T26 (FALTA, S13) + T27 planilhas (FALTA, S13)                  T20 (action)
                        Impresso                                                        Mídias Digitais
```

Fora da jornada: **T25 Usuários** (Admin, antes de tudo) e **T02 Índice do admin** (porta de entrada).
Primeiro ano (2026): `carregar_cadastros`, `importar_matriz`, `carregar_templates` são comandos (S17), sem tela.

---

## 2. Tabela de telas

Status: **ok** = existe e atende; **desatualizada** = existe, mas a mudança recente (24 variáveis D-172/D-173; nome dos padrões por ano D-175; placeholder de `pdNN`) a quebrou ou não está coberta; **falta** = não existe. Ajustes que não vêm da mudança recente ficam na seção 4, não mudam o status.

| id | Nome | URL / admin | Perfis | Lê → Grava (ER) | Decisões | Status | Antes → Depois |
|---|---|---|---|---|---|---|---|
| T01 | Login | `/admin/login/` (Django) | todos | `auth_user` | — | ok | — → T02 |
| T02 | Índice do admin | `/admin/` (Django padrão; `app/nucleo/templates/admin/` só tem `nucleo/`) | todos | — | D-120 | ok (atalho para o Painel: lacuna 4b) | T01 → qualquer |
| T03 | Anos + Abrir ano | `/admin/nucleo/ano/`, `/admin/nucleo/ano/abrir/` (`app/nucleo/admin/cadastro.py:37-69`) | Ped/Mid/Adm (`nucleo.abrir_ano`); Impresso vê | lê `ano`; grava `ano` + cópia de `etapa`, `componente`, `cor_padrao` (cor **e nome**), `matriz`→`matriz_etapa_cc`→`descritor`→`tarefa`, `template`+última `template_versao` (`servicos/abrir_ano.py`) | D-079, D-106, D-119, D-124, D-148, D-175 | ok | — → T05/T07 |
| T04 | Parceiros | `/admin/nucleo/parceiro/` (`cadastro.py:72-75`) | Ped/Mid/Adm | `parceiro.nome` | D-047 | ok | T03 → T08 |
| T05 | Etapas | `/admin/nucleo/etapa/` (`cadastro.py:90-100`) | Ped/Mid/Adm | `etapa.codigo`, `escala_max`, `ordem` | D-055, D-086 | ok | T03 → T08 |
| T06 | Componentes | `/admin/nucleo/componente/` (`cadastro.py:103-106`) | Ped/Mid/Adm | `componente` | D-086, D-095 | ok | T03 → T08 |
| T07 | Padrões do ano (cor e nome) | `/admin/nucleo/corpadrao/` (`cadastro.py:109-114`; `verbose_name_plural` em `models/cadastro.py:87`) | Ped/Mid/Adm (`editar_paleta`) | `cor_padrao.padrao`, `cor`, **`nome`** (`list_display` `cadastro.py:112`; campo `models/cadastro.py:81`) | D-060, D-064, D-086, **D-175** | **ok** (D-175 coberta: `nome` existe, é editável e aparece na lista) | T03 → T16 |
| T08 | Grade de cortes | `/admin/nucleo/corte/?ano=AAAA` (`admin/cortes.py:73-179`, `templates/nucleo/cortes.html`) | Ped/Mid/Adm (`add_corte`+`change_corte`); Impresso vê readonly (`cortes.html:30`) | lê `parceiro`, `etapa`, `componente`, `corte`; grava `corte.valores` via `gravar_cortes` → `parceiro_ano`, `projeto`, `revista`, `revista_fasciculo`, arquivamento (`foto_revista`) | D-049, D-050, D-055, D-061, D-065, D-068, D-093, D-117, D-135, D-153, D-165, D-168 | ok | T04/T05 → T18 |
| T08b | Planilha de grupos de corte | `/admin/nucleo/corte/exportar/?ano=` (`cortes.py:43-104`) | todos (`view_corte`) | lê `corte`, `parceiro`, `etapa`, `componente` | D-049, D-056 | ok | T08 → impresso |
| T09 | Matrizes (lista, edição, Duplicar, Reimportar, Diferenças) | `/admin/nucleo/matriz/`, `/<pk>/change/`, `/<pk>/duplicar/`, `/<pk>/reimportar/`, `/<pk>/diferencas/` (`admin/matriz.py:101-208`; `templates/admin/nucleo/matriz/change_form.html`) | Ped/Mid/Adm (`editar_matriz`); Impresso vê | lê `matriz`, `matriz_etapa_cc`; grava `matriz.nome`, `duplicada_de`; reimportar recria `matriz_etapa_cc`, `descritor`, `tarefa` | D-048, D-053, D-057, D-071, D-101, D-113, D-124, D-141, D-146, D-165, D-168 | ok | T03 → T10 / T18 |
| T10 | Etapa × CC da matriz (MEC) + descritores inline | `/admin/nucleo/matrizetapacc/<pk>/change/` (`matriz.py:292-313`) | Ped/Mid/Adm | `matriz_etapa_cc.passo`; `descritor` (codigo, descricao, ordem) | D-053, D-076, D-081, D-091, D-155, D-165 | ok | T09 → T11 |
| T11 | Descritor + tarefas inline | `/admin/nucleo/descritor/<pk>/change/` (`matriz.py:338-368`) | Ped/Mid/Adm | `descritor.*`; `tarefa.inicio`, `fim`, `texto`, `ordem` (`:318`) | D-058, D-076, D-081, D-165, D-166 | ok (`tarefa.arquivo` sem campo: lacuna 4a, não vem da mudança recente) | T10 → T23 |
| T12 | Templates (lista com abas) | `/admin/nucleo/template/` (`admin/templates.py:117-160`, `templates/nucleo/template_change_list.html`) | Ped/Mid/Adm; Impresso vê | lê `template`, nº da última `template_versao`, contagem de `revista_fasciculo` ativos e com `revista_secao` | D-098, D-102, D-162 | ok (2 links a corrigir: lacuna 4b) | T03 → T13 |
| T13 | Editar template (Markdown + Inserir variável + preview ao vivo) | `/admin/nucleo/template/<pk>/change/`, `/add/`; `POST /templates/preview` (`templates.py:42-95`; `urls/templates.py`) | Ped/Mid/Adm (`change_template`+`add_templateversao`) | lê última `template_versao`; grava `template.nome` + nova `template_versao` | D-105, D-109, D-111, D-114, D-123, D-125, D-162, D-163 | ok (menu "Inserir variável" lê `VARIAVEIS`, já com as 24 e `pd01..05`: `templates.py:54-56`) | T12 → T14 |
| T14 | Impacto da mudança do template | mesmo URL de T13 no POST (`templates.py:211-274`; `templates/nucleo/template_impacto.html`) | idem T13 | lê `revista_fasciculo` ativos, `revista_secao`, `foto_revista` impresso, `revista.svg_ids` | D-099, D-118, D-162, D-163, D-166 | ok | T13 → T13 |
| T15 | Projetos (lista) | `/admin/nucleo/projeto/` (`admin/projeto.py:76-127`) | Ped/Mid/Adm; Impresso vê | `projeto`; links para T17, T18, T19 (`:121-127`) | D-061, D-065 | ok | T08 → T16 |
| T16 | Projeto (nome, 24 variáveis por grupo, passo e cor por projeto) | `/admin/nucleo/projeto/<pk>/change/` (`projeto.py:19-110`; placeholders `admin/variaveis.py:77-82`) | Ped/Mid/Adm | grava `projeto.nome` + 24 colunas de variáveis, `projeto_passo`, `projeto_cor` | D-053, D-060, D-064, D-091, D-093, D-100, D-164, D-166, D-167, **D-172, D-173, D-175** | **ok** (fieldsets gerados de `VARIAVEIS` por grupo, `projeto.py:88-92`; `pdNN` vazio mostra "padrão do ano: …") | T08 → T17/T21 |
| T17 | Aba Variáveis (planilha projetos × variáveis) | `/admin/nucleo/projeto/variaveis/?ano=` (`variaveis.py:137-186`; `templates/nucleo/variaveis.html`) | Ped/Mid/Adm (`change_projeto`); Impresso vê desabilitado | lê `projeto` ativos, última `template_versao` (onde cada variável aparece), `cor_padrao.nome`; grava só colunas alteradas de `projeto`; "Copiar do ano anterior" grava só vazias | D-100, D-107, D-119, D-121, D-164, D-167, **D-172, D-173, D-175** | **ok** (colunas de `VARIAVEIS`, `variaveis.py:183`; legenda "escala do F1" para `pdNN`, `:178-179`; placeholder `:95`) | T16 → T21 |
| T18 | Lote "Escolher matriz" | `/admin/nucleo/projeto/escolher-matriz/?ano=` (`admin/lote.py:144-170`) | Ped/Mid/Adm (`change_parceiroano`) | lê `parceiro_ano`, `matriz`; grava `parceiro_ano.matriz_id` | D-057, D-088, D-101, D-102, D-106, D-121, D-164, D-167 | ok (única tela que grava `parceiro_ano.matriz_id`; não há admin de ParceiroAno) | T08/T09 → T19 |
| T19 | Lote "Escolher template F1/F2" | `/admin/nucleo/revista/escolher-template/?ano=&componente=` (`lote.py:203-249`) | Ped/Mid/Adm (`change_revistafasciculo`) | lê `revista` ativas, `template`; grava `revista_fasciculo.template_id` | D-098, D-102, D-104, D-106, D-121, D-164, D-167 | ok | T18 → T21 |
| T20 | Revistas (lista) + action "Baixar zip" | `/admin/nucleo/revista/` (`admin/revista.py:349-368`, `:548-571`) | todos; zip exige `view_revista` | lê `revista`; zip lê o resolvido | D-103, D-112, D-159, D-160 | ok | T23 → entrega |
| T21 | Revista (SVG, capa, template por fascículo, textos por seção, Validado) | `/admin/nucleo/revista/<pk>/change/`; `POST /<pk>/validar/` (`revista.py:349-530`; `templates/nucleo/revista_change_form.html`) | Ped/Mid/Adm; Impresso só leitura | grava `revista.svg_f2/svg_sha256/svg_ids`, `capa/capa_sha256`, `revista_fasciculo.template_id`, `revista_secao`, `revista.hash_validado/validado_em/validado_por` | D-074, D-087, D-089, D-093, D-104, D-108, D-112, D-115, D-116, D-117, D-118, D-140, D-164, D-170, D-171, D-174 | ok (link para o preview e seção do impresso: lacunas 4b/4c) | T19 → T22/T23 |
| T21b | Gabarito de ids do SVG (CSV) | `/admin/nucleo/revista/<pk>/gabarito-ids/` (`revista.py:532-546`) | todos (`view_revista`) | lê seções efetivas do F2 | D-108, D-111, D-164 | ok | T21 → design |
| T22 | Preview da revista (F1 + F2) | `/preview/<id>/`, `/preview/<id>/capa` (`urls/preview.py:33-58`) | todos (`view_revista`) | lê o resolvido (`corte`, `matriz_etapa_cc`, `descritor`, `tarefa`, `cor_padrao`/`projeto_cor`, `template_versao`/`revista_secao`, `revista.svg_f2`, `capa`); arquivada lê `foto_revista` | D-116, D-117, D-145, D-156, D-157, D-173, D-175 | ok (rótulo `pdNN` efetivo: `servicos/resolver.py:119-124`, `:226-236`) | T21 → T23 |
| T23 | Painel da temporada | `/painel/<ano>/?falta=&parceiro=` (`urls/painel.py:102-131`; `templates/nucleo/painel.html`) | todos (`view_revista`); lote só com `validar_revista` | lê o resolvido de cada revista ativa + `foto_revista` impresso | D-078, D-112, D-120, D-174 | ok (link da coluna Impresso espera o S13: `painel.py:50`) | T21 → T24/T26 |
| T24 | Validar em lote | `/painel/<ano>/validar/?revista=…` (`painel.py:147-173`; `templates/nucleo/painel_validar.html`) | Ped/Mid/Adm (`validar_revista`) | lê resolvido, pendências, seções desatualizadas, diff contra última `foto_revista` impresso; grava `revista.hash_validado/validado_*` por par (revista, hash) | D-078, D-087, D-089, D-120, D-121, D-174 | ok | T23 → T26 |
| T25 | Usuários | `/admin/auth/user/` (`admin/usuarios.py:30-78`) | Admin (grupos Pedagógica/Mídias); superusuário (todos) | `auth_user`, `auth_user_groups` | D-073, D-083, D-142, D-168 | ok | T01 → — |
| T26 | Tela do impresso: "o que mudou" + "Revista Impressa Atualizada" | prevista em S13 (`plans/revista-express-django.md:447-454`); só `resolver.conteudo_impresso` e `foto.fotografar` existem (`servicos/resolver.py:296-310`, `servicos/foto.py:26-28`) | Impresso (`marcar_impressa`); demais veem | lê `conteudo_impresso(revista)` + última `foto_revista` impresso ou herdada; grava `foto_revista(motivo='impresso', hash, criada_por)` | D-066, D-072, D-074, D-077, D-089, D-094, D-097, D-103, D-109, D-112, D-118, D-153 | **falta** | T23 → T27 |
| T27 | Planilhas do impresso (F1 por etapa × CC + F2 seções) + "Baixar planilhas" | prevista em S13 (`plans:455-458`); nada em `servicos/` | Impresso; todos podem baixar (D-078) | lê o resolvido | D-049, D-078, D-109 | **falta** | T26 → InDesign |
| T28 | Histórico por registro (django-simple-history) | nenhum admin usa `SimpleHistoryAdmin` (grep em `admin/*.py` sem ocorrência); só a "História" padrão (LogEntry) | todos | `historical_*` | D-082 | **falta** (desejável) | — |

Componentes sem tela própria: bloqueio (`POST /bloqueio/renovar`, `/liberar` em `urls/bloqueio.py`; `static/nucleo/bloqueio.js`; mixin `admin/bloqueio.py`) em T10, T11, T13, T14, T16, T21; filtros de ano (`lote.py:90-103`, `templates/nucleo/_filtros.html`) em T08, T17, T18, T19, T23.

**Contagem:** existe ok **25** (T01–T25, incluindo T08b e T21b) · existe desatualizada **0** (a mudança D-172/D-173/D-175 está coberta em T07, T13, T16, T17, T22) · falta **3** (T26, T27, T28).

---

## 3. Requisitos por tela (verificáveis)

### T03 Anos + Abrir ano
- Sem incluir/alterar/excluir Ano pelo CRUD (`cadastro.py:21-29`); só "Abrir ano" com `nucleo.abrir_ano` (`cadastro.py:50-51`, D-079).
- Copia etapas, componentes, cores **e nomes** dos padrões, matrizes e templates; não copia parceiros, cortes, projetos nem escolhas (D-106, D-119, D-175; aviso `cadastro.py:66-67`).
- Ano repetido recusado (`cadastro.py:58-59`); sem desfazer (`:33`).

### T04–T06 Parceiros, Etapas, Componentes
- Etapa/Componente: `ano` e `codigo` readonly na edição (`cadastro.py:86-87`); `escala_max` readonly com corte ou MEC (`cadastro.py:95-100`, D-055).
- Parceiro: nome único (`models/cadastro.py:22`).

### T07 Padrões do ano (cor e nome)
- Padrão 1..5, cor `#RRGGBB` (`models/cadastro.py:76-96`).
- `nome` começa "Padrão 0N" (migração 0011) e vale como rótulo do F1 e `{{pdNN}}` quando o projeto não sobrescreve (D-175; `resolver.py:226-236`).
- Não decidido/não feito: aviso "afeta N revistas" ao mudar nome/cor (lacuna 4b, pergunta Q2).

### T08 Grade de cortes
- Célula "350, 400, 500": 1 a 4 inteiros, crescentes, dentro de (0, escala_max) exclusivo (D-055, D-153).
- Só linhas alteradas gravam, cada parceiro inteiro, tudo numa transação; célula vazia = corte apagado (`cortes.py:1-6`).
- Conflito com outra sessão: mantém o digitado, mostra o valor atual, 2º salvar sobrescreve (`cortes.py:147-171`, D-168).
- Gravar exige `add_corte` + `change_corte`; sem permissão a grade é readonly (`cortes.py:85-86`, `cortes.html:30`).
- Salvar dispara a cascata (D-061, D-117, D-135).
- Planilha de grupos: uma aba por etapa × CC, grupo por lista de cortes distinta (D-056); células forçadas a texto (`cortes.py:64-67`).

### T09 Matrizes
- Nome único por ano (`matriz.py:90-98`); `ano`/`duplicada_de` readonly na edição (`:113-114`).
- Duplicar: `add_matriz`, de qualquer ano, guarda `duplicada_de` (D-101, D-113, D-124; `matriz.py:137-151`).
- Reimportar: PDF/xlsx até 20 MB com assinatura (`matriz.py:56-75`); etapa × CC existentes exigem digitar o nome da matriz e mostram "afeta N revistas" (`matriz.py:182-191`, D-071, D-076); `passo` vazio mantém (`:192`).
- Diferenças da origem: só consulta (D-113). MEC não é criada à mão nem excluída (`matriz.py:30-46`, `:264-265`).

### T10 / T11 MEC e Descritor
- Bloqueio por MEC, 30 s renovados a cada 10 s; POST sem bloqueio recusado (D-080, D-081, D-140; `admin/bloqueio.py:90-104`).
- Com N revistas ativas afetadas: caixa "Confirmo: afeta N revista(s)" obrigatória (D-076; `matriz.py:214-235`).
- `passo` = "Intervalo mínimo", vazio = sem linhas vazias (D-091, D-155; `matriz.py:307-313`).
- Descritor: código único na MEC (`matriz.py:327-335`); pré-requisitos um por linha (`:268-278`).
- Sem `delete_tarefa/descritor` nos perfis (D-166); sem `actions`/`list_editable` (`admin/bloqueio.py:18-20`).

### T12 Templates (lista)
- Abas Textos F1, Textos F2, Matrizes, Variáveis (D-102; `templates.py:153-160`).
- "usado por N (M com cópia)" com link para o painel filtrado (D-102).
- Impresso só vê (`templates.py:164-170`).

### T13 / T14 Editar template + impacto
- Textarea Markdown restrito, "Inserir variável" com `VARIAVEIS`, preview ao vivo com variáveis coloridas (D-123; `templates.py:42-57`; `urls/templates.py`).
- Ao salvar: `texto.validar` recusa seção obrigatória ausente, `#` no corpo, links, imagens, HTML, `{{x}}` fora da lista (D-105, D-125; `templates.py:85-91`).
- Texto mudado → tela de impacto → "Confirmar e criar versão" cria `template_versao` N+1; "Voltar e editar" não grava (D-099, D-162; `templates.py:202-274`).
- Assinatura da tela (hash + versão-base, 30 min) tem de bater (D-163; `templates.py:98-108`, `:219-227`).
- Texto igual à versão atual: salva só o nome (`templates.py:188-200`). `ano`, `componente`, `fasciculo` readonly (`:172-174`).
- Bloqueio por template (D-109); duplo "Confirmar" não duplica versão (`:194`).

### T15 / T16 Projeto
- Sem incluir nem excluir (`projeto.py:101-105`); arquivado só leitura, inclusive inlines (`projeto.py:107-110`; `admin/bloqueio.py:59-69`; D-093, D-167).
- Nome e cada variável até 200 caracteres com mensagem no form (`variaveis.py:68-74`).
- 24 variáveis manuais em fieldsets por grupo (`projeto.py:88-92`); automáticas não aparecem (D-172, D-173).
- `pd01..pd05` vazios: placeholder "padrão do ano: <nome>" (`variaveis.py:77-82`, D-175).
- Passo por etapa × CC do ano do projeto (`projeto.py:28-36`); excluir a linha = voltar ao da matriz (D-166). Cor: até 5, `type=color`, excluir = voltar à paleta (`projeto.py:61-66`).
- Bloqueio do projeto (D-081); links de lote conforme permissão (`projeto.py:121-127`).

### T17 Aba Variáveis
- Linha por projeto ativo do ano, coluna por variável manual; legenda com descrição e "onde aparece" (D-107, D-173; `variaveis.py:27-40`, `:177-183`).
- Grava só células alteradas, projeto a projeto sob o bloqueio; travado/arquivado pulado e listado (D-121, D-164, D-167; `variaveis.py:102-111`, `:157-169`).
- "Copiar valores do ano anterior" por projeto: só colunas vazias, projeto do mesmo parceiro em ano−1 (D-107, D-119; `variaveis.py:43-65`, `:114-134`).
- Sem `change_projeto`: campos desabilitados, POST 403 (`variaveis.py:140`, `:151-152`, `:172-175`).

### T18 / T19 Lotes
- Seleção múltipla + "Aplicar aos selecionados"; travados/arquivados pulados e listados (D-102, D-121; `lote.py:36-75`).
- Matriz: só do ano; `change_parceiroano` (`lote.py:129-146`).
- Template: componente obrigatório; só templates do mesmo ano/CC/fascículo; fascículo com cópias pulado (D-098, D-104; `lote.py:176-247`).

### T20 Revistas + zip
- Sem incluir/excluir (`revista.py:447-456`, D-117).
- Zip: uma revista por vez; recusa com pendências (D-112; `revista.py:556-571`); nome `<parceiro>-<cc>-<ano>.zip` (`servicos/empacotar.py:40-44`).

### T21 Revista
- Bloqueio = projeto da revista (`revista.py:370-371`); arquivada = só leitura com textos da foto (`revista.py:417-428`, `:450-453`; D-117, D-171).
- SVG até 3 MB, sanitizado; ids faltando **gravam com aviso** + esperados + "Baixar gabarito de ids" (D-108, D-164; `revista.py:86-92`, `:435-445`, `:458-466`). Capa PNG/JPG/WebP até 5 MB (`:94-101`).
- Template por fascículo só do mesmo ano/CC/fascículo (`:109-115`); com cópias exige digitar "descartar N cópia(s)" e apaga na mesma transação (D-104, D-170, D-171; `:123-152`).
- Textos: campo por seção, rótulo `id · título` não editável; cópia nasce ao mudar o texto; igual ao template não cria; desatualizada mostra diff + "Manter meu texto" / "Descartar cópia"; editar e descartar juntos é erro (D-104, D-115, D-170; `:66-84`, `:254-323`).
- "Validado": form separado com `hash_visto` + sessão; recusa se mudou, pendência, bloqueio perdido ou arquivada; revalidar com o mesmo hash não regrava quem/quando (D-074, D-089, D-174; `:510-530`; `servicos/validacao.py`). Botão desabilitado com pendências (`revista_change_form.html:21`).
- Seções desatualizadas só avisam (D-087). `hash_validado`, `validado_*`, `arquivada_em` readonly (D-142; `:357-360`).

### T22 Preview
- GET, login + `view_revista`, senão 403 (`preview.py:28-31`).
- Abre sempre; faixa vermelha para template ausente, SVG ausente, variável vazia (D-116; `templates/revista/index.html:61`, `:179-180`).
- Arquivada mostra a foto (D-117); capa com `nosniff`, `no-store`, CSP sandbox (D-145).
- Rótulo do padrão = `pdNN` do projeto, senão nome do ano; vazio aparece como `{{pdNN}}` destacado (D-173, D-175; `resolver.py:119-124`).

### T23 Painel
- Linha por revista ativa; colunas Matriz, Template F1, Template F2, Variáveis, SVG, Capa, Validado, Impresso; ✓ ou "falta" com link (D-120; `painel.py:31-77`).
- Filtros por pendência e parceiro (`:106-121`); "Validar selecionadas" só com `validar_revista` (`painel.html:10-23`).
- "Validado" calculado na hora (D-094); "Impresso" = última foto igual ao `impresso_de` atual (D-118; `painel.py:72-74`).

### T24 Validar em lote
- Por revista: pendências (será recusada), seções desatualizadas (aviso), diff contra a última foto impressa; pares `pk:hash`; cada par gravado ou recusado sob o bloqueio; "Pulados: …" e "Validadas N" só com N > 0 (D-078, D-120, D-121, D-174; `painel.py:147-173`; `painel_validar.html:11-15`).
- Pré-marca só as sem pendência e não validadas (`painel_validar.html:11`).

### T25 Usuários
- Sem `is_superuser`, `is_staff`, `user_permissions`; novo nasce `is_staff`; ninguém exclui (`usuarios.py:34-41`, `:72-78`; D-142).
- Admin não superusuário: não vê superusuários, só atribui Pedagógica/Mídias, não muda os próprios grupos, não edita outro Admin (`usuarios.py:43-70`; D-168).

### T26 Tela do impresso (falta)
- Diff entre `conteudo_impresso(revista)` e a última `foto_revista` impresso ou herdada; primeira vez mostra tudo como novo (D-072, D-077, D-094; `resolver.py:296-310`).
- Conteúdo: escalas do F1 por etapa (cortes, descritores/tarefas por padrão, rótulos `pdNN`), cores (D-153), textos F1/F2; **sem** SVG e capa (D-112, D-118, D-126).
- Organização: fascículo → etapa ou seção, ordem das páginas, antes → depois, "copiar texto novo" (`plans:449-453`).
- "Revista Impressa Atualizada": só com "Validado" nesta versão; envia o hash visto; recusa se mudou; grava `foto_revista(motivo='impresso')` em REPEATABLE READ (D-074, D-089, D-097, D-125).
- `marcar_impressa` só no Impresso (D-074, D-142); os demais veem o diff.
- Entrada pela coluna Impresso do Painel (`painel.py:50`) e por T21.

### T27 Planilhas (falta)
- F1: `openpyxl`, `LAYOUTS` de `api/src/modules/planilhas/layout.ts`, N padrões (`plans:455-457`); F2: seção, título, texto (D-109).
- "Baixar planilhas": zip com F1 e F2; a qualquer momento (D-078).
- Rótulos dos padrões = `pdNN` efetivo (D-173, D-175).
- Gabarito: comparar célula a célula com o `service.ts` antigo sobre `revista-3cortes.json` (`plans:467`).

---

## 4. Lacunas

### 4a. Dados do ER que nenhuma tela preenche

| Dado | Situação | Classificação |
|---|---|---|
| `foto_revista(motivo='impresso')`, `hash`, `criada_por` | só `foto.fotografar` existe; nenhuma tela chama com motivo impresso (T26) | **obrigatória 2026** |
| `tarefa.arquivo` (imagem/PDF do item, D-041, D-150) | `TarefaInline.fields` sem o campo (`matriz.py:318`); importador não preenche | desejável |
| `template.origem` | preenchido pelo seed; não aparece no admin (`templates.py:176-179`) | desejável |
| `template_versao` antigas (texto, `criada_por`, `criada_em`) | só a última é mostrada; sem lista de versões | desejável |
| `historical_*` (D-082) | sem `SimpleHistoryAdmin` (T28) | desejável |
| `ano` inicial (2026) | só por `carregar_cadastros` (S17) | aceito pelo plano |

### 4b. Ajustes pontuais em telas existentes (não refazer)

| Tela | Ajuste | Classificação |
|---|---|---|
| T21 Revista | link "Abrir preview" para `/preview/<pk>/` (nenhum template do admin linka: grep em `templates/nucleo/*.html` sem ocorrência; D-116 pressupõe o preview) | **obrigatória 2026** (1 link) |
| T23 Painel | link da coluna Impresso (`painel.py:50` devolve `None`) → T26 | **obrigatória 2026** (com T26) |
| T07 Padrões do ano | aviso "afeta N revistas ativas do ano; derruba o Validado" ao mudar `nome`/`cor` (`docs/variaveis.md:66-67` descreve o efeito; nenhuma D decide o aviso) | desejável (Q2) |
| T12 Templates | aba "Variáveis" → planilha T17 (`admin:nucleo_projeto_variaveis`) em vez da lista de Projetos (`templates.py:158`); "usado por" usa `?template=` que o painel ignora (`templates.py:147-151`; `painel.py:106-110`) | desejável |
| T23 Painel | pendência `variaveis` de `pdNN` com nome do ano vazio linka para o projeto; poderia linkar também para T07 | desejável |
| T02 Índice | atalho para o Painel do ano e para os Cortes (D-120 "tela principal"); hoje o Painel só aparece na lista de Revistas (`revista.py:550-551`) | desejável (Q5) |

### 4c. Telas previstas e não feitas

| Tela | Passo | Classificação |
|---|---|---|
| T26 Impresso: "o que mudou" + "Revista Impressa Atualizada" | S13 | **obrigatória 2026** (sem ela o perfil Impresso não tem ação e D-072/D-074 não fecham) |
| T27 Planilhas F1/F2 + "Baixar planilhas" | S13 | **obrigatória 2026** (entrega ao InDesign, D-049/D-109) |
| T28 Histórico por registro | nenhum passo | desejável |
| Zip em lote (todas as revistas do ano) | citado em `revista.py:558`, não feito | desejável |

### As 5 lacunas mais graves
1. T26 tela do impresso + "Revista Impressa Atualizada" (S13).
2. T27 planilhas F1/F2 (S13).
3. Link da coluna Impresso no Painel (`painel.py:50`), junto com 1.
4. Link para o Preview em T21 (D-116 sem porta de entrada no admin).
5. Aviso de impacto em T07 ao mudar nome/cor do padrão do ano (mudança silenciosa derruba o "Validado" de todas as revistas do ano, D-175).

---

## 5. Perguntas ao usuário

1. **Admin pode clicar "Revista Impressa Atualizada"?** (`permissoes.py:14-16`; plano, pergunta 2). Recomendação: **não**; T25 já impede o Admin de entrar no grupo Impresso (D-168).
2. **Mudar nome/cor do padrão do ano (T07) pede "Confirmo: afeta N revistas ativas", como a MEC (D-076)?** Recomendação: **sim**, reaproveitando `ImpactoForm` (`matriz.py:214-235`), N = revistas ativas do ano que não sobrescrevem aquele `pdNN`/cor.
3. **T26 é página própria (`/impresso/<revista>/`) ou seção dentro de T21?** Recomendação: **página própria só leitura** (estilo de T24), ligada do Painel e de T21: o Impresso não tem `change_revista`, e T21 carrega o bloqueio do projeto sem necessidade.
4. **Planilhas (T27): por revista, por ano ou os dois?** Recomendação: **por revista em T26** agora; lote por ano no Painel depois.
5. **O Painel vira a página inicial depois do login?** Recomendação: **sim**: `admin/index.html` próprio com o link e redirect de `/` para `/painel/<maior ano>/`; atende a D-120 com custo baixo.

---

## 6. Estilo existente (referência obrigatória para as telas novas)

As telas novas (T26, T27 e os ajustes de 4b) seguem o que já está em uso. Nada de CSS framework nem tema novo.

| Elemento | Como é feito hoje | Onde |
|---|---|---|
| Base | Tema padrão do Django admin; páginas próprias estendem `admin/base_site.html` com `{% block content %}<div id="content-main">` e `breadcrumbs` "Início › …" | `templates/nucleo/painel.html:1-6`, `painel_validar.html:1-3`, `lote.html:1`, `variaveis.html:1`, `cortes.html:1`, `admin_form.html:1-13`, `template_impacto.html:1-20` |
| Change forms com bloqueio | estendem `nucleo/bloqueio_change_form.html` (hidden `_bloqueio_sessao` + `bloqueio.js` com `defer`); JS renova a cada 10 s e, com 409/403, põe o form em `readOnly`/`disabled` | `templates/nucleo/bloqueio_change_form.html:5-13`; `static/nucleo/bloqueio.js:42-67`; `templates/nucleo/revista_change_form.html:1` |
| Change lists com atalhos | estendem `admin/change_list.html` e injetam links em `object-tools-items` (`lotes` = [(texto, url)]) | `templates/nucleo/change_list_lotes.html:3-5`; `templates/admin/nucleo/ano/change_list.html:3-7`; `templates/admin/nucleo/matriz/change_form.html:3-7` |
| Abas | `<nav class="abas-templates">` com `aria-current="page"` na ativa | `templates/nucleo/template_change_list.html:5-7`; `static/nucleo/template_editor.css:5-7` |
| Filtros (ano, parceiro, pendência) | `<p class="filtro">Rótulo: <strong>ativo</strong> · <a>outro</a>` via `lote.filtro()` + `_filtros.html` | `admin/lote.py:98-103`; `templates/nucleo/_filtros.html:1-5`; `cortes.html:16` |
| Formulário simples (Duplicar, Reimportar, Abrir ano) | `admin_form.html`: `<p>{{ aviso }}</p>`, `errornote`, `<fieldset class="module aligned">`, `submit-row` com `{{ botao }}` | `templates/nucleo/admin_form.html:13-27`; `admin/cadastro.py:63-69`; `admin/matriz.py:148-164` |
| Tabelas de dados | `<div class="module"><table>` do admin; cabeçalho com `<th>`; rolagem horizontal inline quando há muitas colunas | `templates/nucleo/variaveis.html:7-10`, `:27-32`; `painel.html:8-11`; `matriz_diferencas.html:9` |
| Grade editável (cortes) | `<table id="cortes">` com `<input type="text">` por célula, linha com erro em `tr.com-erro` + `tr.erros` (`var(--message-error-bg)`, `var(--error-fg)`), CSS inline no `extrastyle` | `templates/nucleo/cortes.html:4-13`, `:21-39` |
| Botões | `submit-row` + `<input type="submit" class="default">` para a ação principal; `class="button"` para secundários ("Copiar valores do ano anterior", "Inserir variável", "Baixar gabarito de ids"); botão desabilitado no envio (`onsubmit`) | `painel.html:23`; `variaveis.html:41`, `:47`; `widgets/editor_texto.html:9`; `admin/revista.py:343-346`; `revista_change_form.html:17-21`; `template_impacto.html:50-52` |
| Confirmação forte | digitar uma frase exata num `CharField` "Confirmação" ("descartar N cópia(s)"; nome da matriz) ou marcar "Confirmo: afeta N revista(s) ativa(s)" | `admin/revista.py:117-147`, `:155-156`; `admin/matriz.py:62-65`, `:182-191`, `:214-235` |
| Tela intermediária de impacto | POST reenviado em hidden + assinatura; tabela de revistas afetadas; "Confirmar e criar versão" / "Voltar e editar" | `templates/nucleo/template_impacto.html:20-52`; `admin/templates.py:211-247` |
| Avisos e erros | `messages.success/warning/error` do admin ("Pulados: …", "Não validada: …"); `<p class="errornote">` para erro de form; `<strong class="impacto-alerta">` (`var(--error-fg)`) para aviso em linha; `<p class="impacto-alerta">` para "seções desatualizadas" | `admin/lote.py:85-87`; `admin/revista.py:526-529`; `painel_validar.html:12-13`; `revista_change_form.html:13`; `static/nucleo/template_editor.css:24` |
| Faixa vermelha (lacuna) | `<div class="faixa-vermelha" role="alert">` (`#b00020`, texto branco, negrito) no preview e no change form | `servicos/resolver.py:57`; `templates/revista/index.html:33`, `:61`, `:179-180`; `admin/revista.py:219-222` |
| Variável vazia / marcador | `<span class="variavel-vazia">{{nome}}</span>` amarelo (`#fde68a` / `#713f12`), monoespaçado | `static/nucleo/template_editor.css:18-21`; `urls/templates.py:9-11` |
| Diff "antes | depois" | `difflib.HtmlDiff(wrapcolumn=70).make_table(..., context=True)` com `table.diff` (verde `diff_add`, amarelo `diff_chg`, vermelho `diff_sub`; `diff_next` oculto) | `admin/revista.py:248-251`; `urls/painel.py:134-144`; `static/nucleo/template_editor.css:28-34` |
| Texto Markdown mostrado | `<pre class="texto-template">` (pre-wrap, 13px) para leitura; `EditorTexto`/`EditorSecao` (textarea monoespaçada + preview ao vivo em 2 colunas, debounce 400 ms) para edição | `static/nucleo/template_editor.css:9-16`, `:25`; `static/nucleo/template_editor.js:28-39`; `admin/templates.py:42-57`; `admin/revista.py:229-237` |
| Células de status | `✓` ou `<a>falta</a>` com `title` explicando, por coluna `td.coluna-<nome>` | `templates/nucleo/painel.html:17-19`; `urls/painel.py:60-77` |
| Lote | checkbox por item + `fieldset.module` por revista com `<h2><label><input type="checkbox">` | `templates/nucleo/painel_validar.html:10-19`; `lote.html:7-18`; `admin/lote.py:118-127` |
| Downloads | `HttpResponse` com `Content-Disposition: attachment` (xlsx, csv, zip); CSV à prova de fórmula; xlsx com `data_type = "s"` | `admin/cortes.py:96-104`, `:64-67`; `admin/revista.py:326-328`, `:544-546`, `:569-571` |
| Mensagens padrão | PT-BR, sem "Opa"; causa + correção ("Não salvo: você perdeu o bloqueio de edição."; "Zip recusado. Pendências: …") | `admin/bloqueio.py:94`, `:115-129`; `admin/revista.py:567` |

Regras que as telas novas herdam: nenhuma `action` de escrita nem `list_editable` em admin com o mixin (`admin/bloqueio.py:18-20`); toda escrita de estado leva o hash visto (D-089) e o bloqueio da sessão (`revista.py:510-530`); arquivado é só leitura (D-093); texto renderizado passa por `texto.renderizar`/`format_html` (escape no servidor).
