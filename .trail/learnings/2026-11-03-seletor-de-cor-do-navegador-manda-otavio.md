---
title: "Seletor de cor do navegador manda a cor em minúsculas, e a mesma cor em outra caixa não pode contar como mudança"
author: Otavio
date: 2026-11-03
branch: feat/telas-b-lacunas
cost: { minutes: 15, tokens: 81493 }
id: l-d4af7399
scope: repo
status: active
src: agent
touches:
  - app/nucleo/admin/cadastro.py
  - app/nucleo/paleta.py
  - state.md
  - app/e2e/tests/anos.spec.ts
  - app/nucleo/templates/ui/anos/ano.html
  - app/nucleo/templates/ui/anos/anos.html
  - app/nucleo/tests/test_ui_anos.py
  - app/nucleo/urls/ui_anos.py
---

## Decided
Na edição da paleta do ano pela tela B, cor igual com outra caixa (#B3CCFF × #b3ccff) não é mudança: não pede confirmação e o valor gravado fica como estava. A carga inicial gravou as cores em maiúsculas, e o seletor de cor do navegador sempre devolve minúsculas.

## Tried and ruled out
Usar o campo de cor padrão do formulário: salvar só o nome contava a cor como alterada, pedia a confirmação de impacto à toa e, ao gravar, trocava a caixa da cor, o que muda o hash da revista e pode tirar o "Validado" de revistas sem mudança real.

## Watch out
Qualquer tela nova com seletor de cor sobre dado gravado em maiúsculas tem o mesmo problema (hoje a cor do projeto não tem: as cores do projeto já nascem minúsculas pelo próprio seletor).
Depois de "Não salvo", a instância do form já tem os valores enviados (o Django monta a instância mesmo com erro): a amostra de cor tem que ler o valor inicial do form, não a instância.

In the code:
- app/nucleo/urls/ui_anos.py: CorField.has_changed (compara em minúsculas) e PadraoForm.clean_cor (devolve a cor gravada quando só a caixa difere)
- app/nucleo/templates/ui/anos/ano.html: amostra usa f.initial.cor
