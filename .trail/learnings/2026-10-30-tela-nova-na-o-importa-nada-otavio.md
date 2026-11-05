---
title: "Tela nova não importa nada do admin, porque o admin já importa as rotas e o import fica circular"
author: Otavio
date: 2026-10-30
branch: feat/telas-b-lacunas
cost: { minutes: 14, tokens: 125825 }
id: l-e38b8309
scope: repo
status: active
src: agent
touches:
  - state.md
  - app/nucleo/templates/ui/_componentes/anos.html
  - app/nucleo/templates/ui/anos/anos.html
  - app/nucleo/templates/ui/cortes.html
  - app/nucleo/templates/ui/matriz/lista.html
  - app/nucleo/templates/ui/revista/lista.html
  - app/nucleo/templates/ui/templates/lista.html
  - app/nucleo/templates/ui/variaveis/pagina.html
  - app/nucleo/tests/test_navegacao.py
  - app/nucleo/tests/test_ui_anos.py
---

## Decided
Na página de anos da tela B, o formulário de um campo do admin foi copiado em vez de importado.

## Tried and ruled out
Importar o form do admin na view da tela B: o admin importa um módulo de rotas (preview), as rotas incluem a view nova, e a view importaria o admin de volta. O Django para no import com "partially initialized module".

## Watch out
O primeiro ano não se abre pela tela: o serviço só abre um ano copiando o anterior. Sem ano nenhum, ele entra pela carga inicial.

In the code:
- cadeia: nucleo/admin/cadastro.py → admin/matriz.py → urls/preview.py → urls/__init__.py → urls/ui_anos.py
- form copiado: AbrirAnoForm em app/nucleo/urls/ui_anos.py
- recusa sem ano anterior: servicos/abrir_ano.py (AnoRecusado "nenhum ano anterior")
