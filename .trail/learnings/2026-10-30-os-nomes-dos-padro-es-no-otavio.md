---
title: "Os nomes dos padrões no F1 vêm das variáveis pd01 a pd05 do projeto, e o nome do parceiro é preenchido pelo sistema"
author: Otavio
date: 2026-10-30
branch: refatoracao-django
cost: { minutes: 62, tokens: 132730 }
id: l-7411a4e0
scope: repo
status: active
src: agent
touches:
  - state.md
  - app/nucleo/admin/revista.py
  - app/nucleo/static/nucleo/template_editor.js
  - app/nucleo/tests/test_admin_revista_textos.py
  - app/nucleo/urls/templates.py
  - app/nucleo/variaveis.py
  - app/nucleo/servicos/resolver.py
---

## Decided
- pd01..pd05 são o nome de cada padrão de desempenho ("pd01 significa padrão 01", nas palavras do usuário). Eles substituem o rótulo fixo "Padrão 01..05" na escala do F1 e também podem ser usados nos textos.
- Um pdNN vazio de um padrão que a revista tem gera pendência e aparece com a faixa vermelha. Um padrão que a revista não tem não cobra valor.
- Como o rótulo é impresso, mudar um pdNN muda o hash e o "o que mudou" de toda revista que tem aquele padrão, LP e MT.
- nome_parceiro é automático e vem do cadastro do parceiro: o usuário disse que o sistema obtém esse valor por outro meio. Não existe coluna manual para ele. A antiga automática "parceiro" foi renomeada.
- A planilha oficial usa <<x>>, mas o sistema continua com {{x}}.

## Tried and ruled out
- Coluna manual nome_parceiro: o valor ficaria duplicado com o cadastro.
- Usar "Padrão 0N" quando pdNN estiver vazio: o rótulo errado iria para o impresso sem ninguém ver.

## Watch out
- Na planilha recebida, os exemplos de singular e plural do adjetivo pátrio estão trocados, e "no_na_ em_nome_parceiro" tem um espaço no nome.
- Branches paralelas que regeram o revista.zip do e2e sempre conflitam nele (é binário). No merge, pegue qualquer lado e regere com REGERAR_FIXTURES=1.

In the code: app/nucleo/variaveis.py (VARIAVEIS), app/nucleo/servicos/resolver.py (rotulo_do_padrao), docs/variaveis.md, migração das variáveis oficiais.
