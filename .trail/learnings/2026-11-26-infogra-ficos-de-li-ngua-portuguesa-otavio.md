---
title: Infográficos de Língua Portuguesa são copiados do seed dos Word para cada revista; o modelo único com herança ficou para uma próxima versão
author: Otavio
date: 2026-11-26
branch: feat/redesenho-figma
id: l-b88c5695
scope: repo
status: active
replaces: l-8bdcd965
src: agent
touches:
  - docs/superpowers/plans/2026-11-25-infografico-modelo-lp.md
  - kanban.md
  - state.md
  - app/nucleo/infografico.py
---

## Decided
Em 26/11 o usuário trocou o modelo único (D-297) pela cópia (D-298), por causa do prazo. Os dois Word da Pedagógica viram um seed JSON com as imagens, e um comando copia o conteúdo para cada infográfico ativo de LP. A edição continua na ficha de cada revista. A recarga troca só o campo que ainda é igual ao seed anterior, então corrige em massa sem apagar o que foi editado. A cascata preenche o infográfico de LP criado depois da carga. MT não muda.

## Tried and ruled out
- Modelo único com herança campo a campo (D-297): cerca de 16 h, com 3 tabelas, 2 migrações e uma tela nova, e o risco de confundir NULL (herda) com "" (célula mesclada). A cópia sai em cerca de 6,5 h e não toca no resolver nem no F2. O modelo pode voltar numa próxima versão.
- Cópia sem recarga: cada correção da Pedagógica teria de ser feita em até ~60 infográficos à mão.

## Watch out
- Imagem do item: um arquivo por revista, nunca um caminho compartilhado, porque o apagar_item_orfao apaga o arquivo quando uma revista troca a imagem.
- Desarquivar um infográfico não o preenche de novo: a linha guarda o que tinha.

In the code: plano em docs/superpowers/plans/2026-11-26-infografico-lp-copia.md; gravação por app/nucleo/infografico.py::form_do_campo e servicos/arquivos.py::receber_imagem_item; criação em servicos/cascata.py::_sincronizar_infograficos.
