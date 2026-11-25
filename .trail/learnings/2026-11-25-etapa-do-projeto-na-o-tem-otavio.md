---
title: "Etapa do projeto não tem matriz: código do editor que usa a matriz da etapa quebra na cópia, e só o caminho de erro mostrou isso"
author: Otavio
date: 2026-11-25
branch: feat/e2e-etapa-projeto
id: l-59a35208
scope: repo
status: active
src: agent
touches:
  - app/nucleo/urls/ui_matriz.py
  - app/nucleo/templates/ui/matriz/form.html
---

## Decided
Em 25/11 o E2E achou erro 500 em "Novo descritor" no editor da cópia do projeto. O caminho feliz funcionava; quebrava só quando o formulário voltava (código repetido, ou revista validada pedindo o modal de impacto), porque essa volta lia o ano pela matriz da etapa, que é vazia na etapa do projeto. A correção manda o ano da própria etapa e o voltar do dono (matriz ou projeto).

## Tried and ruled out
Nada foi descartado: a varredura de 24/11 por usos da matriz da etapa (D-283) olhou filtros e consultas, e não pegou um argumento passado adiante para uma função que o desreferencia.

## Watch out
- No editor da matriz, use o ano e o dono da etapa, nunca os da matriz dela: na etapa do projeto a matriz é vazia.
- Os testes do editor com etapa de projeto cobriam abrir e gravar; os caminhos de erro (form que volta, modal de impacto) precisam de teste próprio com etapa de projeto.
- O caso "revista validada abre o modal" no novo descritor da cópia não foi rodado no navegador depois da correção.

In the code: `app/nucleo/urls/ui_matriz.py` (`novo_descritor`, `_form_em_dialogo`, `_dono`), `app/nucleo/templates/ui/matriz/form.html`, teste `MecDeProjetoTest.test_novo_descritor_com_erro_volta_ao_form_na_etapa_do_projeto`; D-295.
