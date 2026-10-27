---
title: "Ao passar o mouse numa habilidade, destacar as de baixo, não as de cima"
author: Otavio
date: 2026-10-27
standing: true
id: l-9f9ea61f
scope: repo
status: active
src: init-sessions
touches:
  - revista/styles.css
  - revista/escala.hbs
---

## Watch out
- A leitura pedagógica é cumulativa: quem alcança uma habilidade já domina todas as inferiores. A primeira implementação inverteu o sentido e a legenda também estava errada.
- In the code: Em revista/styles.css o realce leve deve usar o seletor das linhas seguintes (`~ .linha`). A legenda em revista/escala.hbs diz: "Quem alcança uma habilidade já domina todas as que estão abaixo dela."

_From past Claude sessions here, Oct 21._
