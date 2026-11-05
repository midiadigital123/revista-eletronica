# Testes de navegador (Playwright)

Os testes ponta a ponta do sistema atual ficam em `app/e2e/` e rodam contra o `app` Django. O roteiro manual do sistema antigo (editor React, API e Mongo) foi aposentado junto com ele (D-187).

## Rodar

```bash
docker compose up -d app
cd app/e2e
npm ci
E2E_ADMIN_USUARIO=<superusuário> E2E_ADMIN_SENHA=<senha> npx playwright test
```

- `baseURL`: `http://localhost:8000` (mude com `E2E_BASE_URL`) (`app/e2e/playwright.config.ts:8`).
- Todo spec roda em dois projetos, `chromium` (1280×720) e `desktop-1440` (1440×900), com `workers: 1`: painel, impresso e revista gravam a mesma revista com o mesmo usuário (D-191).
- Sem `E2E_ADMIN_USUARIO` e `E2E_ADMIN_SENHA`, os specs **pulam em silêncio**. A regra é 0 pulados.
- Os specs gravam no banco apontado. Rode contra o banco de desenvolvimento, nunca contra dados reais.
- Convenções de espera (`alpinePronto`, "Salvo às…") em [`telas/design-system.md`](telas/design-system.md), seção 8.
