---
title: "O PDF das atividades do F2 é geral por componente e tipo de infográfico, e o link do template do infográfico vai para uma URL externa ainda pendente"
author: Otavio
date: 2026-11-27
branch: feat/f2-fechamento
id: l-d60639a5
scope: repo
status: active
src: agent
touches:
  - app/e2e/tests/templates-editor.spec.ts
  - app/e2e/tests/templates.ts
  - app/nucleo/servicos/html.py
  - app/nucleo/templates/ui/templates/novo.html
  - app/nucleo/templates_texto.py
  - app/nucleo/tests/test_admin_templates.py
  - app/nucleo/tests/test_preview.py
  - app/nucleo/tests/test_templates_texto.py
  - app/nucleo/tests/test_ui_revista.py
  - app/nucleo/tests/test_ui_templates.py
---

## Decided
Em 27/11 o usuário respondeu que o PDF das atividades (o conteúdo depois de "ATIVIDADES" nos Word de LP, já editorado) é um só para todos os parceiros: um por ano × componente × tipo (Alfa ou Outras Etapas). A revista mostra "Acesse aqui as atividades", que baixa esse PDF. O "Acesse aqui o template do Infográfico" aponta para uma URL externa que ainda não existe. Até chegar, o link sai com o marcador `#pendente` e aparece em vermelho no preview. A Pedagógica troca o endereço pela tela Templates.

## Tried and ruled out
- PDF por revista, na ficha: o usuário disse que o PDF é geral.
- Copiar o PDF do seed para cada revista, como a imagem do item: trocar o PDF exigiria recarregar todas as revistas.
- Inventar um endereço provisório para o template do infográfico: sairia na revista como um link falso.
- Guardar a URL numa variável `{{x}}`: as variáveis são colunas do projeto, e a URL é a mesma para todos.

## Watch out
O PDF fica fora do hash do "Validado": trocá-lo não tira a validação de nenhuma revista. A revista arquivada mostra o PDF atual, não o da época em que foi arquivada.

In the code: modelo `Atividades(ano, componente, tipo, arquivo, arquivo_sha256)`; link no Markdown restrito em `app/nucleo/texto.py` (só https ou `#pendente`); D-307 e D-308 no state.md.
