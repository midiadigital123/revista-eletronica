# Docker — Revista Express

O `docker-compose.yml` da raiz sobe dois serviços: `db` (PostgreSQL 17) e `app` (Django, porta 8000 só em `127.0.0.1`). Mongo, API e editor React saíram do compose (D-187). Variáveis: `app/.env.example`; o compose lê o `.env` da **raiz**, e todas têm default de desenvolvimento.

## Subir

```bash
docker compose up -d --wait db
docker compose run --rm app python manage.py migrate
docker compose run --rm app python manage.py createsuperuser
docker compose up -d app
```

O `app` abre em `http://localhost:8000/` (leva ao Painel do ano mais novo; sem ano, a `/ui/anos/`). O `CMD` da imagem já roda `migrate` antes do servidor (`app/Dockerfile`).

Produção usa outro compose: ver [Produção](#produção). Nunca faça commit do `.env`.

## Produção

`docker-compose.prod.yml` (D-214): Gunicorn (3 workers, timeout 120 s) no lugar do `runserver`, `DEBUG` desligado, código dentro da imagem, mídia no volume `media`, `restart: unless-stopped`. Ao subir, roda `migrate` e `collectstatic`.

```bash
cp .env.prod.example .env      # preencher: POSTGRES_PASSWORD, DJANGO_SECRET_KEY, DJANGO_ALLOWED_HOSTS, DJANGO_CSRF_TRUSTED_ORIGINS
docker compose -f docker-compose.prod.yml up --build -d
docker compose -f docker-compose.prod.yml exec app python manage.py createsuperuser
```

- O app escuta só em `127.0.0.1:${APP_PORT:-8000}`; o proxy reverso do servidor (Nginx/Traefik) faz o HTTPS e repassa para lá, com limite de upload de 50 MB.
- Os estáticos saem do próprio Django (`sistema/urls.py`, só sem DEBUG); a mídia sai pelas views com permissão, nunca direto do proxy.
- Backup: volume `pg-dados` (use o `pg_dump` abaixo, com `-f docker-compose.prod.yml`) e volume `media`.
- Testar no próprio PC sem mexer no dev: `docker compose -p revista-prod-teste --env-file <arquivo> -f docker-compose.prod.yml up --build -d` com `APP_PORT` livre; `down -v` no fim.

## Dia a dia

| Quero… | Comando |
|---|---|
| ver os logs | `docker compose logs -f app` |
| rodar os testes | `docker compose run --rm app python manage.py test` |
| abrir um shell Django | `docker compose run --rm app python manage.py shell` |
| parar | `docker compose down` |
| parar e **apagar o banco** | `docker compose down -v` |

Cada worktree usa o próprio banco com `docker compose -p <nome> …` (o compose não fixa `container_name` nem expõe a porta do Postgres).

## PostgreSQL: backup e restore

```bash
# backup
docker compose exec db pg_dump -U revista revista > backup-$(date +%F).sql

# restore (num banco vazio)
docker compose exec -T db psql -U revista revista < backup-AAAA-MM-DD.sql
```

## Troubleshooting

- **Porta 8000 já em uso:** `APP_PORT=8001 docker compose up -d app`, ou outro nome de projeto com `-p`.
- **`app` não sobe:** `docker compose logs app`. Sem `DJANGO_DEBUG=1`, a `DJANGO_SECRET_KEY` é obrigatória.
- **Tela quebrada depois de trocar de branch:** falta aplicar migração. `docker compose run --rm app python manage.py migrate`.
- **Banco não conecta:** `docker compose ps` deve mostrar `db` como `healthy`.
