---
title: Grade de cortes do admin manda um campo por célula de todos os parceiros e passa do limite de 1000 campos do Django
author: Otavio
date: 2026-11-04
branch: feat/ux-u10d-critica
cost: { minutes: 20 }
id: l-bcae5b8d
scope: repo
status: active
src: agent
touches:
  - app/sistema/settings.py
  - "app/nucleo/cortes.py#grade"
  - app/nucleo/templates/nucleo/cortes.html
---

## Decided
DATA_UPLOAD_MAX_NUMBER_FIELDS = 10_000 em app/sistema/settings.py. O 'Salvar cortes' do admin (/admin/nucleo/corte/) manda c-<parceiro>-<etapa>-<cc> por célula e o-<parceiro> por linha, de TODOS os parceiros cadastrados (Parceiro é global, acumula entre anos). Com 4 etapas × 7 componentes, ~35 parceiros já passam de 1000 campos e o Django recusa o POST inteiro (TooManyFieldsSent: 400, ou 500 na tela de debug).

## Tried and ruled out
- Subir o limite só na view: o Django lê o limite do settings ao montar request.POST, e o CsrfViewMiddleware lê o POST antes da view; não há como subir por rota sem trocar o parser.
- Mandar só as linhas alteradas por JS no submit: resolveria a escala, mas o teste Django não cobre JS e o admin seria a única tela com esse script. Fica como próximo passo se passar de ~340 parceiros com 28 células (o comentário ponytail no settings).

## Watch out
O teste test_70_parceiros_cabem_no_limite_de_campos_do_post usa só 4×2 células e não pega o problema; o test_40_parceiros_com_7_componentes_salvam_a_grade é o que reproduz. O tamanho do corpo continua preso pelo DATA_UPLOAD_MAX_MEMORY_SIZE (2,5 MB).
