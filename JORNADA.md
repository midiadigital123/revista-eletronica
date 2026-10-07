# JORNADA — Revista Eletrônica em Django

## Estado atual
<!-- sobrescrever -->
- Marco: M1 — Projeto rodando
- Último passo concluído: M1 Passo 2 (app `revista` em INSTALLED_APPS; `check` ok)
- Funcionando agora: venv + Django 5.2.18; `.gitignore` protege .venv, pycache e db.sqlite3

## Próxima ação
<!-- sobrescrever -->
M1 Passo 3: view `ola` em `revista/views.py` + `revista/urls.py` + `include` em `config/urls.py`.

## Escopo
- Propósito: a equipe cria e edita projetos de revista (descritores D01–D40 por ano, BNCC, escala de proficiência) e vê a revista renderizada a partir do banco, no lugar do `descritores.json` fixo.
- MVP: login (User do Django) + Projeto 1─N Ano (5ef/9ef/3em) 1─N Descritor (tópico, descrição, pré-requisitos, BNCC, escala). Fluxo: login → projetos → ano → descritor → editar → ver a revista.
- Depois do MVP: bloqueio de edição entre usuários, upload de imagens, zip offline, importar `descritores.json`, perfis admin/editor, PostgreSQL + Docker.

## Mapa de marcos
| Marco | Aplicação neste sistema | Status |
|---|---|---|
| M0 Ambiente | `django/` com venv, Django 5.2 LTS, `.gitignore` | ✅ |
| M1 Projeto rodando | projeto `config` + app `revista` com página "olá" | 🔄 |
| M2 Modelos e admin | models Projeto, Ano, Descritor; cadastro pelo `/admin/` | ⬜ |
| M3 Ler dados | lista de projetos → anos → descritores; `escala.html` vira template Django | ⬜ |
| M4 Formulários e CRUD | criar/editar/excluir projeto e descritor fora do admin | ⬜ |
| M5 Autenticação | login, páginas restritas, quem criou cada projeto | ⬜ |
| M6 Relacionamentos e consultas | filtro por ano, busca de descritor, `prefetch_related` na revista | ⬜ |
| M7 Testes | permissões, render da revista, validação do descritor | ⬜ |
| M8 API (opcional) | JSON dos descritores (o `script.js` poderia consumir) | ⬜ |
| M9 Produção | Docker + PostgreSQL, `check --deploy` | ⬜ |

## Diagnóstico inicial
| Área | sei / acho que sei / não sei |
|---|---|
| Python | não sei |
| HTTP | não sei |
| SQL / modelagem | não sei |
| Git | sei |
| Docker | sei |

## Conceitos
- Dominados: venv, requirements.txt, projeto vs app, manage.py, leitura da linha de log HTTP (método, caminho, status)
- Frágeis (revisar): por que o banco não vai para o Git (pergunta de fixação sem resposta)

## Registro de erros
<!-- acrescentar: erro → causa → o que aprendeu -->
- `ModuleNotFoundError: No module named 'django.revista'` → string de INSTALLED_APPS é caminho de import Python, não de pasta → ler traceback de baixo para cima; `a.b` = módulo b dentro do pacote a.

## Decisões
<!-- só acrescentar -->
- D-001: Django 5.2 LTS (segurança até abr/2028) — a versão mais nova é 6.1, mas a LTS dá estabilidade para aprender sem trocar de versão no meio.
- D-002: projeto em `django/` neste repositório — reaproveita `escala.html`, `styles.css` e `descritores.json` direto.
- D-003: MVP enxuto (Projeto → Ano → Descritor) — primeira vitória mais cedo; bloqueio, imagens e zip depois.
- D-004: SQLite até o M9 — zero configuração; PostgreSQL entra junto com Docker.
- D-005: branch `django` para a trilha; commits com `git add` explícito — a `main` tem trabalho Express não commitado.

## Entregue pronto pelo Claude
<!-- partes feitas fora do modo mentor, para revisar depois -->
