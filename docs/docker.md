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

Em produção, preencha no `.env`: `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=0`, `DJANGO_ALLOWED_HOSTS` e `POSTGRES_PASSWORD`. Nunca faça commit do `.env`.

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
