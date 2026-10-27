---
title: "Mudou a revista e a prévia não muda: falta reconstruir a imagem da API"
author: Otavio
date: 2026-10-27
standing: true
id: l-ec6aca49
scope: repo
status: active
src: init-sessions
touches:
  - revista/styles.css
  - revista/script.js
  - revista/escala.hbs
---

## Watch out
- A API copia a pasta da revista para dentro da imagem Docker no build, então editar os arquivos não altera o preview nem a revista gerada. Isso pegou a equipe várias vezes ao ajustar a escala.
- In the code: Depois de editar revista/styles.css, revista/script.js ou revista/escala.hbs, rode `docker compose up -d --build api` e dê Ctrl+Shift+R no editor (localhost:8080). O Dockerfile faz `COPY revista ./revista`.

_From past Claude sessions here, Oct 21._
