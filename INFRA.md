# Guia de implantação — Revista Eletrônica

Para a equipe de Infra. Tudo o que o servidor precisa para rodar o sistema em produção.
Dúvidas: equipe de Mídias Digitais (dona do repositório).

## Resumo

| Item | Valor |
|---|---|
| Compose de produção | **`docker-compose.prod.yml`** (o `docker-compose.yml` é só de desenvolvimento: **não usar**) |
| Branch | `main` |
| Containers | `app` (Python 3.13 + Django 6.1 + Gunicorn, porta 8000) e `db` (PostgreSQL 17) |
| Imagem | construída a partir de `app/Dockerfile` (não há imagem em registry) |
| Porta publicada | `127.0.0.1:8000` no host (só o proxy acessa) |
| Volumes com dados | `pg-dados` (banco) e `media` (arquivos enviados) |
| Domínio sugerido | `design.revistas.caeddigital.net` |

Máquina: Ubuntu Server 24.04 LTS ou Debian 12, 2 vCPUs, 4 GB de RAM, 40 GB SSD, Docker Engine e Docker Compose V2.
Hoje o sistema usa menos de 300 MB de RAM e cerca de 75 MB de disco.

## 1. Variáveis de ambiente

Modelo comentado: [`.env.prod.example`](.env.prod.example). No Portainer, cadastre as variáveis no stack; fora dele, copie o modelo para `.env` na raiz do repositório.

| Variável | Obrigatória | Valor |
|---|---|---|
| `POSTGRES_PASSWORD` | sim | `openssl rand -hex 24` (só letras e números: ela entra numa URL) |
| `DJANGO_SECRET_KEY` | sim | `openssl rand -hex 32` |
| `DJANGO_ALLOWED_HOSTS` | sim | `design.revistas.caeddigital.net` (sem `https://`; vários separados por vírgula) |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | sim | `https://design.revistas.caeddigital.net` (com `https://`) |
| `APP_PORT` | não | porta no `127.0.0.1` do host; padrão `8000` |
| `DATABASE_URL` | não | só para PostgreSQL gerenciado; aí remova o serviço `db` |
| `DJANGO_COOKIE_SECURE` | não | padrão `1`; `0` só para testar sem HTTPS |

Sem uma obrigatória, o stack não sobe e a mensagem diz qual falta.

Cuidados:

- **`POSTGRES_PASSWORD` só vale na primeira subida.** O PostgreSQL grava a senha ao criar o volume `pg-dados`. Trocar a variável depois não muda a senha do banco, e o app deixa de conectar.
- **`DJANGO_SECRET_KEY` trocada desloga todo mundo.** Não há outro efeito.
- **Sem `DJANGO_CSRF_TRUSTED_ORIGINS` correto, todo login dá 403.** O proxy faz o HTTPS e o Django recebe HTTP; ele só aceita o formulário vindo da origem `https://` listada aqui.
- Nunca versione o `.env` preenchido.

## 2. Stack no Portainer

1. **Stacks → Add stack → Repository.**
2. **Repository URL:** `https://github.com/midiadigital123/revista-eletronica`, **reference** `refs/heads/main`.
3. **Compose path:** `docker-compose.prod.yml`.
4. **Environment variables:** as 4 obrigatórias da seção 1.
5. **Automatic updates:** ligado (polling ou webhook), para cada push na `main` reconstruir o stack. Marque a opção de forçar o redeploy/rebuild: a imagem é construída a partir do repositório.

O ambiente precisa ser **Docker standalone**. Em Swarm, o `build` do compose não funciona; nesse caso, avisem que publicamos a imagem num registry.

Fora do Portainer, o equivalente é:

```bash
git clone https://github.com/midiadigital123/revista-eletronica.git && cd revista-eletronica
cp .env.prod.example .env    # preencher as 4 obrigatórias
docker compose -f docker-compose.prod.yml up --build -d
```

A cada subida, o `app` aplica as migrações do banco e copia os arquivos estáticos antes de iniciar o Gunicorn. Não há passo manual de migração.

## 3. Proxy reverso e HTTPS

Necessário um proxy reverso com HTTPS na frente do app (`127.0.0.1:8000`). Particularidades do sistema:

- Repassar o `Host` original (o Django recusa domínio fora de `DJANGO_ALLOWED_HOSTS`).
- Uploads de até **50 MB** (PDFs e planilhas).
- Requisições de até **120 s** (importar matriz e gerar o zip da revista).
- Se o proxy rodar em container, nos avisem a rede dele para ligarmos o `app` nela.

## 4. Primeiro acesso

Depois do primeiro deploy, crie o primeiro administrador pelo console do container `app` (Portainer → Containers → `<stack>-app-1` → Console) ou pelo terminal:

```bash
docker exec -it <stack>-app-1 python manage.py createsuperuser
```

Com ele, a equipe cadastra os demais usuários pela própria tela do sistema (login próprio, sem SSO e sem envio de e-mail).

Para tornar superusuário alguém que já existe (nenhuma tela faz isso, de propósito):

```bash
docker exec -it <stack>-app-1 python manage.py tornar_superusuario <usuario> [<usuario>...]
```

## 5. Verificar

```bash
curl -sI https://design.revistas.caeddigital.net/conta/entrar/ | head -1   # HTTP/2 200
docker logs --tail 20 <stack>-app-1                                        # "Booting worker" x3 e as requisições
```

Abra o domínio no navegador, entre com o administrador e confira se a página carrega com estilo (CSS). Login que volta com "403 Forbidden": revise `DJANGO_CSRF_TRUSTED_ORIGINS`.

## 6. Backup

Diário, dos dois volumes. O Compose prefixa os volumes com o nome do stack: `<stack>_pg-dados` e `<stack>_media` (`docker volume ls` mostra os nomes).

```bash
# banco (dump consistente, com o sistema no ar)
docker exec <stack>-db-1 pg_dump -U revista -Fc revista > /backup/revista-$(date +%F).dump

# arquivos enviados (capas, itens, F2)
docker run --rm -v <stack>_media:/m:ro -v /backup:/b alpine tar czf /b/media-$(date +%F).tgz -C /m .
```

Prefira o `pg_dump` à cópia crua do volume `pg-dados`: a cópia com o banco rodando pode sair corrompida.

### Restaurar

```bash
docker exec -i <stack>-db-1 pg_restore -U revista -d revista --clean --if-exists < revista-AAAA-MM-DD.dump
docker run --rm -v <stack>_media:/m -v /backup:/b alpine tar xzf /b/media-AAAA-MM-DD.tgz -C /m
docker restart <stack>-app-1
```

## 7. Problemas comuns

| Sintoma | Causa provável |
|---|---|
| Stack não sobe: `required variable ... is missing` | Falta uma variável obrigatória (seção 1) |
| `400 Bad Request` em toda página | Domínio fora de `DJANGO_ALLOWED_HOSTS`, ou o proxy não repassa o `Host` |
| `403 Forbidden` ao entrar | `DJANGO_CSRF_TRUSTED_ORIGINS` sem o `https://` do domínio |
| `502 Bad Gateway` | O `app` ainda está subindo (migrações) ou caiu: `docker logs <stack>-app-1` |
| App em loop de restart, erro de senha no banco | `POSTGRES_PASSWORD` trocada depois de criar o volume `pg-dados` |
| `413 Request Entity Too Large` | Falta o limite de 50 MB no proxy |
| `504 Gateway Timeout` ao importar ou gerar zip | Timeout do proxy abaixo de 120 s |
