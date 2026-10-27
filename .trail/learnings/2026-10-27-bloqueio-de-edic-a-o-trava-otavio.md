---
title: Bloqueio de edição trava só a escrita e expira em 30 segundos
author: Otavio
date: 2026-10-27
standing: true
id: l-8fb295b1
scope: repo
status: active
src: init-sessions
---

## Decided
- O bloqueio antigo expirava em 2 minutos e valia o projeto inteiro. Na matriz comunitária, travar tudo impediria duas pessoas de trabalhar em partes diferentes. Todos continuam podendo ver.
- In the code: Na matriz, a trava é por matriz x etapa x componente curricular. No projeto, é o projeto inteiro. Expiração de 30 s, e a renovação automática do editor (hoje no ritmo de 2 min) deve rodar a cada ~10 s, senão a trava cai no meio da edição. Trava é só de escrita.

_From past Claude sessions here, Oct 27._
