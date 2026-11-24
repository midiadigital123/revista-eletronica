---
title: "Componente de template fica com as tags do Django numa linha só, e formatador automático não pode tocar neles"
author: Otavio
date: 2026-11-18
branch: main
cost: { minutes: 34, tokens: 254639 }
id: l-742c2530
scope: repo
status: active
src: agent
touches:
  - state.md
---

## Decided
- Os componentes de template das telas B (django-cotton) são escritos com cada tag `{% … %}` inteira numa linha. O HTML que cada um gera é travado por teste, para que qualquer quebra apareça na suíte e não na tela.
- A migração das telas para os componentes segue em levas (cabeçalho, campo, selo, aviso, card, botão), sempre com saída HTML idêntica e sem editar teste existente. Um teste-catraca falha se alguém voltar a escrever à mão um componente já migrado.

## Tried and ruled out
- Confiar só nos testes de página e no E2E para pegar componente quebrado: dois componentes (aba e botão) foram reformatados por um formatador depois de a suíte e o E2E passarem, e entraram quebrados num commit. Tag `{%` partida em várias linhas não é lida pelo Django: sai como texto cru ou dá erro de sintaxe só quando o componente é usado.
- Variável da página dentro de atributo do componente não é escapada duas vezes: conferido com `&` e `<`, sai escapada uma vez só. Não precisa de `|safe` nem de cuidado extra.

## Watch out
- Não se sabe qual formatador foi (o VS Code do repositório já desliga o format-on-save para templates; o suspeito é um hook de formatação da sessão do agente). Depois de editar um componente, confira que ele continua numa linha por tag antes de commitar.
- Nome de componente dentro de comentário do próprio arquivo, com `<` e `>`, é lido como tag pelo formatador e pelo compilador: escreva sem os sinais.
- Template criado a partir de texto (`Template("…")`) não passa pelo compilador do cotton; em teste, compile antes.

In the code:
- `app/nucleo/templates/cotton/*.html`; `.prettierignore` com `app/nucleo/templates/`
- `app/nucleo/tests/test_componentes_cotton.py`: `MIGRADOS`, `EXCECOES`, `renderizar()` = `Template(CottonCompiler().process(fonte))`
- state.md D-270 e D-271
