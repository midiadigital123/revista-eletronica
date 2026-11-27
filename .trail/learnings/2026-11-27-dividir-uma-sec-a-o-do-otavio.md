---
title: Dividir uma seção do template F2 por tipo exige trocar também os textos F2 de exemplo dos testes e do E2E
author: Otavio
date: 2026-11-27
branch: integ/f2-fechamento
id: l-abb2f610
scope: repo
status: active
src: agent
touches:
  - app/nucleo/tests/test_preview.py
  - app/e2e/tests/templates.ts
  - scripts/docx_infografico.py
---

## Decided
Quando uma seção do F2 vira duas (tarefas-fechamento na D-306, fechamento na D-312), o caminho é sempre o mesmo: lista de seções, rótulos, página do tipo, migração que cria versão nova do template e divide as cópias das revistas, e os seeds .hbs passados pela mesma função da migração (assim seed e banco saem idênticos).

## Tried and ruled out
Rodar só os testes dos módulos tocados antes da suíte inteira: passaram, mas a suíte inteira deu 25 falhas e 2 erros. Os textos F2 de exemplo ficam espalhados em vários arquivos de teste e, com a seção antiga, o template é recusado na validação; o sintoma aparece longe da causa ("o modal de impacto não abriu", "Agora é com você não encontrado").

## Watch out
O Word de Matemática tem formato próprio, diferente do de Português: um "TEXTO DO CLIQUE:" por passo, progressão antes da descrição, descrição que para no 7º ano e itens identificados pelo nível, não pela etapa. Por isso o conversor tem dois ramos.

In the code:
- textos F2 de exemplo: `F2` em app/nucleo/tests/test_preview.py, `F2_9` em test_admin_templates.py, `F2_NOVO` em test_texto.py, `TEXTO_F2` em app/e2e/tests/templates.ts; mensagem "Seções obrigatórias faltando" em test_admin_templates.py
- migrações 0031 e 0034 (`por_tipo`, `frente`); seeds aplicados com `importlib.import_module("nucleo.migrations.0034_fechamento_por_tipo").por_tipo` dentro do container
- conversor: `scripts/docx_infografico.py <docx> mt alfa <pasta>` (`converter_mt`)
