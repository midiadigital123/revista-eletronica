# Docker — Revista Eletrônica

## Quick Start

### 1. Configurar variáveis de ambiente

Copiar `.env.example` para `.env` na raiz do repositório:

```bash
cp .env.example .env
```

Gerar um `SESSION_SECRET` seguro:

```bash
openssl rand -hex 32
```

Abrir `.env` e preencher:
- `SESSION_SECRET`: valor gerado acima
- `ADMIN_EMAIL`: email do admin (ex: `admin@exemplo.org`)
- `ADMIN_SENHA`: senha do admin (alterar na produção)
- `LOG_LEVEL`: `info` ou `debug` (opcional)

### 2. Build e start dos containers

```bash
docker compose up --build
```

O editor fica acessível em `http://localhost:8080`.

Logs:

```bash
docker compose logs -f
```

### 3. Parar os containers

```bash
docker compose down
```

Para remover volumes também:

```bash
docker compose down -v
```

## MongoDB: Backup e Restore

### Backup

Fazer dump do banco de dados:

```bash
docker compose exec mongo mongodump --out /tmp/backup
docker cp revista-mongo:/tmp/backup ./backup
```

### Restore

Restaurar de um backup anterior:

```bash
docker cp ./backup revista-mongo:/tmp/backup
docker compose exec mongo mongorestore /tmp/backup
```

## Troubleshooting

- **Porta 8080 já em uso:** `docker compose up --build -p <nome-customizado>`
- **MongoDB não conecta:** verificar se o container `mongo` está saudável com `docker compose ps`
- **API não inicia:** conferir logs com `docker compose logs api` e garantir que `.env` tem `MONGO_URL` e `SESSION_SECRET`
