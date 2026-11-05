---
title: "Produção atrás do proxy com HTTPS precisa da origem https na lista de confiança do CSRF, senão todo login dá 403"
author: Otavio
date: 2026-11-05
branch: main
cost: { minutes: 54, tokens: 171327 }
id: l-e6523579
scope: repo
status: active
src: agent
touches:
  - state.md
  - README.md
  - docs/docker.md
  - ".env.prod.example"
  - app/requirements.txt
  - app/sistema/settings.py
  - app/sistema/urls.py
  - docker-compose.prod.yml
  - CLAUDE.md
---

## Decided
O app de produção recebe HTTP do proxy reverso, que faz o HTTPS. O navegador manda Origin https://..., o Django compara com http://... e recusa todo POST (login incluído) com 403. A saída escolhida foi listar a origem https na variável de origens confiáveis do CSRF, com cookies Secure ligados por padrão em produção. Os estáticos saem do próprio Django sem DEBUG, para o deploy não depender de a Infra configurar o proxy.

## Tried and ruled out
- Confiar no cabeçalho X-Forwarded-Proto (SECURE_PROXY_SSL_HEADER): depende de cada proxy da Infra mandar o cabeçalho certo; a lista de origens não depende.
- Override do compose de dev para produção: `ports` e `volumes` se somam, então o código montado e a porta do dev continuariam.
- collectstatic no build da imagem: sem DEBUG o settings exige a chave secreta, que não existe no build.

## Watch out
- Testando com curl por HTTP, o cookie csrftoken é Secure e o curl não o reenvia: dá 403 falso. Mande o cookie à mão no cabeçalho Cookie.
- No servidor, o compose de produção tem de ser escolhido explicitamente (Portainer usa o docker-compose.yml por padrão, que é o de dev com DEBUG ligado).
- No .env do dev, POSTGRES_PASSWORD tem de continuar igual à do volume já criado; trocar a senha não muda o banco e o app deixa de conectar.

In the code: docker-compose.prod.yml, .env.prod.example, app/sistema/settings.py (DJANGO_CSRF_TRUSTED_ORIGINS, DJANGO_COOKIE_SECURE, STATIC_ROOT), app/sistema/urls.py (serve de /static/ só sem DEBUG). Teste isolado: docker compose -p revista-prod-teste --env-file <arquivo> -f docker-compose.prod.yml up --build -d.
