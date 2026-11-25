# Edição local do conteúdo da matriz por projeto

Requisito novo de 24/11/2026, chegado depois do plano das etapas 2 a 10. Este documento diz o que mudou,
o que já está decidido, o que é proposta e o que falta decidir. Leia antes de continuar a etapa do projeto
(K-034, branch `feat/etapa-do-projeto`).

## 1. O requisito

A Pedagógica (Luciana) respondeu duas perguntas em 24/11:

1. A edição de descritores e outros elementos da matriz Comunitária vale só para 3 projetos (CE, Joinville,
   ES) ou para qualquer projeto? **Resposta: qualquer projeto.**
2. Quais elementos? **Resposta: todos os elementos, editáveis "localmente" por projeto.**

Tradução: qualquer projeto que use a Comunitária (ou qualquer matriz) precisa poder acrescentar e tirar
descritores, tarefas e demais campos **só para si**, sem alterar a matriz nem os outros projetos.

## 2. O que existe hoje

- O projeto não tem conteúdo próprio. Aponta para uma matriz por `ParceiroAno.matriz` (D-051: "projeto só
  referencia a matriz"; `app/nucleo/models/projeto.py:19`).
- O conteúdo mora em `Matriz` → `MatrizEtapaCC` (etapa × componente, com `passo`) → `Descritor` → `Tarefa`
  (`app/nucleo/models/matriz.py`). Editar a Comunitária muda todas as revistas dela (cerca de 25).
- O que o projeto sobrescreve hoje: só o passo e a cor do padrão. Os cortes já são por projeto.
- Única saída atual para exceção: duplicar a matriz (`Matriz.duplicada_de`, só consulta, D-113) e atribuí-la
  ao parceiro. Criar matriz e atribuir ficou com o superusuário (D-277).

## 3. O que o requisito contraria nas decisões vigentes

| Decisão ou regra | Situação |
|---|---|
| D-051 (projeto só aponta para a matriz) | Já foi substituída em parte pela etapa do projeto (D-229 da branch). O requisito amplia a exceção para todo o conteúdo. |
| D-276 itens 3 e 4 (a base só é uma das 4 canônicas; o botão só aparece para etapa não canônica) | Precisam mudar: canônica também pode ser editada localmente. |
| Regra da branch: "a etapa própria só existe para etapa que a matriz do parceiro não tem" (D-229 da branch) | **Cai.** Agora a cópia do projeto convive de propósito com a etapa da matriz. |
| Pendência de escolha da branch ("manter a do projeto" ou "usar a da matriz", D-231 da branch) | Não faz mais sentido para o caso intencional: a cópia vale sobre a da matriz. Decidir se a pendência some ou muda de texto. |
| Learning permanente "projeto não herda de outro projeto: ele apenas aponta para uma matriz" | Fica em conflito. Quando a decisão sair, salvar learning novo com `trail note --replaces`. |

Não mudam: D-276 item 1 (não canônica nasce apontando para uma canônica), item 2 (clone com vínculo, revisão
em 3 vias), item 5 (quem aponta é a Pedagógica) e D-277 (superusuário cria matriz, template, parceiro e
projeto; usuários editam).

## 4. Escopo: o que é editável

Granularidade da cópia: **uma etapa × componente do projeto** (o equivalente a um `MatrizEtapaCC`).
Dentro dela, tudo é editável, incluindo acrescentar e remover linhas:

- `MatrizEtapaCC`: `passo`.
- `Descritor`: `codigo`, `descricao`, `prerequisitos`, `praticas`, `conhecimento`, `habilidades_relacionadas`,
  `habilidade_correspondente`, `ordem`; acrescentar e remover descritor.
- `Tarefa`: `inicio`, `fim`, `texto`, `arquivo` (item), `texto_alternativo`, `ordem`; acrescentar e remover tarefa.

Fora do escopo: cortes (já são por projeto), cores (já sobrescrevem), variáveis e textos da revista (já são do projeto).

## 5. Mecanismo

### Já decidido (não reabrir)

- A cópia é um **clone com vínculo** à base, com foto da base no momento do clone e **revisão em 3 vias**
  (base de quando clonou, base atual, local). Mudança na base abre pendência obrigatória que bloqueia o
  "Validado". O que o projeto não tocou vem pré-marcado "aplicar"; só grava em "Concluir revisão"; o projeto
  pode recusar item a item; não há fusão dentro de um texto, escolhe-se o campo inteiro (D-115). A foto usa o
  código (Dxx, faixa da tarefa), nunca o id.
- Descartados nas decisões da branch, e que o requisito não reabre: camada de sobrescrita (copy-on-write),
  versões imutáveis da matriz, somar base nova com a local, aplicar a mudança da base sozinha, remontar a
  base antiga pelo `django-simple-history`.

### Proposto, ainda não decidido (confirmar com o usuário antes de implementar)

> **Respondido em 24/11 (D-288).** A cópia não nasce sozinha na primeira edição nem na atribuição da
> matriz: nasce pelo botão "Editar só neste projeto", na aba Matriz do projeto. Os itens 1, 3 e 4 abaixo
> valem como estão; o item 2 vale com o botão no lugar da "primeira edição". A proposta fica como registro.

**O clone nasce na primeira edição, não na atribuição da matriz.**

1. Todo projeto continua apontando para a matriz, como hoje.
2. Na primeira edição de uma etapa × componente, o sistema cria a cópia para aquele projeto.
3. O resolver (`servicos/resolver.py`) lê a cópia quando ela existe e a matriz quando não existe.
4. Só quem tem cópia entra na revisão em 3 vias.

Motivo: clonar tudo na atribuição criaria cópias de todas as etapas de 33 projetos. A cada mudança na
Comunitária, cada cópia pediria revisão e bloquearia o "Validado" de até 66 revistas. Com clone sob demanda,
só entram na revisão as etapas que alguém editou.

Consequência de interface: o botão "Criar etapa do projeto" vira algo como "Editar só neste projeto", para
canônica e não canônica. Para não canônica a base continua obrigatória (D-276 item 1).

## 6. Reaproveitar da branch `feat/etapa-do-projeto`

14 commits fora da `main`; a tarefa 5 está em WIP (`1d005f3`: "matriz_id nulo no resto do sistema").

- `app/nucleo/migrations/0020_etapa_do_projeto.py`: renumerar para `0026` (colide com `0020_infograficos`).
- `app/nucleo/servicos/etapa_projeto.py` e `app/nucleo/tests/test_etapa_projeto.py`: foto canônica, criação em
  branco ou por clone, classificação em 3 vias.
- Pontos de encaixe nomeados nos learnings: `servicos/matriz.py::_afetadas`, `_conteudo` e `diferencas`;
  `servicos/impacto.py::perdem_validado`; `servicos/resolver.py` (`_f1_escalas`, lacunas, `pendencias`);
  `models/matriz.py::MatrizEtapaCC`.
- Armadilha já vista: no modelo da branch a etapa do projeto deixa `matriz_id` nulo, e o resto do sistema
  assumia matriz presente. Com cópia convivendo com a etapa da matriz, confira de novo todo código que
  navega `MatrizEtapaCC → matriz`.
- Os números D-229 a D-231 da branch colidem com os da `main` (lá são os passos do F2 e o merge). Renumere
  ao mesclar (learning de 09/11).

## 7. Regras do repositório que continuam valendo

- Ano em toda tabela, FK composta por `nucleo/db.py::fk_composta`, sempre com `reverse_sql`; o teste de
  `pg_constraint` muda junto.
- Histórico com django-simple-history; a reimportação da matriz apaga e recria descritores e tarefas com ids
  novos, por isso a foto da base usa código.
- Bloqueio de edição por `MatrizEtapaCC` (`servicos/bloqueio.py`, expira em 30 s). A cópia do projeto é outro
  `MatrizEtapaCC`, então duas pessoas editam a Comunitária e a cópia sem se travar.
- "Validado" e "Revista Impressa Atualizada" enviam o hash visto; o servidor recusa se mudou.
- Gravação que tira o "Validado" de alguma revista abre o modal de impacto antes (D-202). Editar a
  Comunitária agora deve também avisar **quais projetos têm cópia** e vão cair em revisão.
- Exclusão só do que nada usa, por `/ui/excluir/<modelo>/<pk>/` (D-205). Excluir descritor ou tarefa da cópia
  segue a confirmação forte (learning de 30/10).
- `Tarefa.arquivo` é caminho de storage compartilhado entre anos; clonar uma tarefa copia o caminho, e só se
  apaga o arquivo quando nenhuma tarefa aponta para ele (`servicos.arquivos.apagar_item_orfao`).
- Permissões em `app/nucleo/permissoes.py`; mudou a tabela, migração de dados nova que sincroniza os grupos.
- Testes E2E nunca editam revista que o próprio teste não criou. O spec cria o parceiro "E2E …" e edita só ele.
- Fluxo git: nada na worktree da `main`; trabalho em `../revista-express-trabalho`, branch `feat/<tema>` a
  partir de `integ/<tema>`; merge na `main` só com o "ok" explícito do usuário.

## 8. Perguntas em aberto

**As 5 perguntas foram respondidas pelo usuário em 24/11 (D-288 no `state.md`).** A resposta vem abaixo de
cada uma.

1. Clone na primeira edição (proposta acima) ou na atribuição da matriz? **Pergunta ao usuário.**
   - **Resposta (D-288, item 1):** nenhum dos dois. A cópia nasce pelo botão "Editar só neste projeto", para
     toda etapa com corte; sem clicar, o projeto lê a matriz e não entra em revisão.
2. A pendência de escolha da branch some quando a cópia é intencional, ou continua para o caso "matriz do
   parceiro passou a ter a etapa"?
   - **Resposta (D-288, item 2):** some. Quando o projeto tem cópia, a cópia sempre vale; voltar à matriz é
     "Desfazer" (D-287).
3. Clone de clone: a branch proíbe na 1ª versão (a base é sempre etapa de matriz). Manter?
   - **Resposta (D-288, item 5):** mantido. A base é sempre etapa de matriz.
4. O que acontece com as cópias quando a matriz do parceiro é trocada (`atribuir_matriz`)? A foto da base
   deixa de bater com a matriz nova.
   - **Resposta (D-288, itens 3 e 4):** as cópias ficam, ligadas à base de onde vieram. E só haverá uma
     matriz, a Comunitária, então o caso quase não ocorre.
5. O `abrir_ano` copia as cópias do projeto para o ano novo? E a cascata, que arquiva o projeto e cria outro,
   passa as cópias adiante (o learning de 06/11 diz que sim)?
   - **Resposta (D-288, item 5):** o `abrir_ano` não leva as cópias; o projeto recriado pela cascata herda
     (D-285).

## 9. O que revisar nas etapas 2 a 10

Plano de 24/11 conhecido: etapas 2 a 6 = etapa do projeto no servidor; 7 a 10 = telas de apontar e de
revisão no layout atual; 11 = redesenho pelo Figma. Este documento não traz o detalhamento de cada etapa.
Para cada uma, confira se ela assume "só não canônica", "só etapa que a matriz não tem" ou "base só
canônica", e ajuste.

**Atualização de 25/11: o que as etapas 7b a 10 entregaram.**

- **7b (D-289):** a cópia local. "Editar só neste projeto" na aba Matriz, para toda etapa que a matriz tem,
  com a própria etapa da matriz como base; a cópia sempre vale; saíram a pendência de escolha e a coluna
  dela (migração `0027`). O desfazer (D-287) serve também para a cópia local.
- **8 (D-292, D-293):** a tela "Revisar mudanças da base" (`/ui/revisao/<pk>/`), com o selo "A base mudou"
  na aba Matriz e o aviso no editor da cópia. No caminho, a revista passou a mostrar descritor com qualquer
  código e a seguir a ordem do editor (D-290, D-291).
- **9 (D-294):** quem edita a etapa da matriz vê os projetos com cópia: aviso fixo no editor e linha no
  modal de impacto.
- **10:** o spec de navegador `app/e2e/tests/etapa-projeto.spec.ts` (cópia local, revisão, modal de impacto
  e impresso: critérios 1, 4 e 5) e os documentos atualizados. "Apontar" fica só nos testes Django.

Falta a etapa 11 (redesenho pelo Figma).

## 10. Critérios de aceite (testáveis)

1. Dois projetos usam a mesma matriz: o projeto A edita um descritor da Comunitária localmente; o projeto B
   continua vendo o texto original.
2. A edição local não altera nenhuma linha de `Matriz`, `MatrizEtapaCC`, `Descritor` ou `Tarefa` da Comunitária.
3. Projeto sem edição local continua resolvendo pela matriz e não ganha pendência.
4. Mudar a Comunitária depois da cópia abre a pendência de revisão só nos projetos com cópia, e o "Validado"
   dessas revistas fica bloqueado até "Concluir revisão".
5. Acrescentar e remover descritor e tarefa na cópia aparece na revista (preview e zip) e no "o que mudou"
   do impresso.
6. Duas pessoas editando, uma na Comunitária e outra na cópia, não se bloqueiam.

## 11. Fontes

`state.md` (D-051, D-113, D-124, D-276, D-277, D-278 e a pergunta em aberto de 24/11); learnings
`2026-11-06-etapa-criada-no-projeto-a-partir-otavio`, `2026-11-06-etapa-do-projeto-passa-para-o-otavio`
(na branch `origin/feat/etapa-do-projeto`), `2026-11-24-etapa-na-o-cano-nica-nasce-otavio` e
`2026-10-27-projeto-na-o-herda-de-outro-otavio`.
