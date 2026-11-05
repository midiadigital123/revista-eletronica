---
title: "Telas B usam Alpine para estado local somado ao HTMX que já existe, com autosave que pergunta antes de tirar o Validado"
author: Otavio
date: 2026-11-03
branch: feat/telas-b-lacunas
cost: { minutes: 19, tokens: 166883 }
id: l-c3a531df
scope: repo
status: active
src: agent
touches:
  - app/nucleo/static/ui/htmx.min.js
  - app/nucleo/ui_bloqueio.py
---

## Decided
- Interatividade das telas B: Alpine.js (build CSP, componentes registrados com Alpine.data) cuida do estado local (modal de impacto, linha nova, renomear inline, status do salvamento, aviso de saída). O HTMX 2.0.4 continua onde já funciona. Autosave por campo usa fetch com um protocolo JSON único.
- Autosave: campo sem impacto salva ao sair dele; se a gravação tiraria o "Validado" de alguma revista, o servidor não grava e devolve a lista, e a tela abre o modal. O impacto é calculado na hora, porque a mesma variável pode ou não afetar revista validada.
- CDN liberada pelo usuário (03/11): libs novas via jsDelivr com versão exata e SRI.
- A reforma de UX roda antes de S6–S9 do plano de lacunas, para as telas novas já nascerem no padrão.

## Tried and ruled out
- Migrar tudo para Alpine + fetch: reescreveria 6 telas que já usam HTMX, uns 2 a 3 dias sem ganho para o usuário.
- Só JS puro: cada padrão viraria módulo próprio, código demais para manter.
- Autosave de tudo com "desfazer": o impacto no Validado só apareceria depois de gravado.

## Watch out
- Editor de templates mantém "Salvar" explícito: cada gravação cria uma versão assinada.
- Grade de Cortes não tem bloqueio (conflito otimista pelo valor original); o autosave por célula precisa mandar o original e tratar 409.

In the code: plano em plans/revista-express-telas-b-ux.md; HTMX em app/nucleo/static/ui/htmx.min.js; bloqueio em app/nucleo/ui_bloqueio.py (com_bloqueio).
