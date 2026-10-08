# Revista Express

Editor web para montar as **revistas eletrônicas de resultados de avaliação** da Fundação CAEd.

A equipe pedagógica digita, descritor por descritor, o que cada faixa da escala de proficiência significa. O sistema transforma esses dados numa revista HTML pronta: você vê o resultado no **preview** e baixa um **pacote `.zip`** que funciona offline.

```
  Equipe pedagógica                 Editor + API                    Entrega
 ┌──────────────────┐       ┌──────────────────────────┐      ┌─────────────────┐
 │ digita descritor,│ ───▶  │ valida, salva no Mongo,  │ ───▶ │ preview no      │
 │ escala, BNCC...  │       │ renderiza a revista      │      │ navegador + .zip│
 └──────────────────┘       └──────────────────────────┘      └─────────────────┘
```

---

## Sumário

1. [Conceitos do domínio](#1-conceitos-do-domínio)
2. [Arquitetura](#2-arquitetura)
3. [Como rodar com Docker](#3-como-rodar-com-docker-recomendado)
4. [Como desenvolver sem Docker](#4-como-desenvolver-sem-docker)
5. [Fluxo de uso](#5-fluxo-de-uso-no-editor)
6. [O contrato compartilhado](#6-o-contrato-compartilhado)
7. [Extração de descritores de PDF](#7-extração-de-descritores-de-pdf)
8. [Testes e qualidade](#8-testes-e-qualidade)
9. [Operação](#9-operação)
10. [Documentos relacionados](#10-documentos-relacionados)

---

## 1. Conceitos do domínio

Antes de mexer no código, vale entender o vocabulário. Ele aparece igual nas telas, na API e nos nomes de arquivos.

```
Projeto (ex.: "SAEGO 2025")
├── Página ............ título, introdução, imagem do topo (compartilhada por todos os cadernos)
└── Cadernos .......... um por disciplina
    ├── lingua-portuguesa
    │   └── Anos ...... 2ef, 5ef, 9ef, 3em...
    │       ├── Faixa da escala (mínimo e máximo, ex.: 0 a 500)
    │       ├── 3 cortes  ──▶ dividem a faixa em 4 padrões
    │       └── Descritores (D01, D02, ...)
    │           ├── tópico, descrição, pré-requisitos
    │           ├── BNCC (práticas, conhecimentos, habilidades)
    │           └── Escala: linhas (nível + texto) em cada padrão
    └── matematica
        └── ...
```

| Termo | O que significa |
|---|---|
| **Projeto** | Uma revista inteira (por exemplo, a de um estado num ano). Tem nome e *slug* (o identificador na URL). |
| **Página** | Os textos e imagens que envolvem a escala: título, introdução, imagem do topo. |
| **Caderno / disciplina** | Uma parte da revista. Ids fixos: `lingua-portuguesa`, `matematica`, `alfabetizacao-lp`, `alfabetizacao-mat`. Ao criar o projeto, você marca disciplinas; **Alfabetização** gera dois cadernos (LP + MT). |
| **Ano (etapa)** | A série avaliada, no formato `<n>ef` ou `<n>em`: `2ef` = 2º ano do Ensino Fundamental, `3em` = 3ª série do Ensino Médio. |
| **Escala de proficiência** | Uma régua numérica (ex.: 0 a 500) onde a nota do aluno é posicionada. |
| **Cortes e padrões** | Três valores de corte dividem a régua em **4 padrões de desempenho** contíguos: o Padrão 01 vai do mínimo até o corte 1, o Padrão 02 começa logo depois, e assim por diante. Cores fixas: 01 `#f72628`, 02 `#ff8d43`, 03 `#b3ccff`, 04 `#0ed3ff`. |
| **Descritor** | Uma habilidade avaliada (D01, D02...). Cada um tem linhas ancoradas em níveis da escala. |
| **BNCC** | Base Nacional Comum Curricular. Cada descritor indica práticas, conhecimentos e códigos de habilidade (ex.: `EF05LP01`). |

**Leitura cumulativa da escala:** uma habilidade ancorada no nível 250 é dominada por todo aluno com nota **maior ou igual** a 250. Por isso a revista mostra a escala como uma régua que se lê de baixo para cima.

---

## 2. Arquitetura

```
 Navegador
    │  http://<host>:8080
    ▼
 ┌─────────────────────────────┐
 │ editor  (nginx)             │  serve o app React e aplica a CSP
 │  /      → SPA React         │
 │  /api/* → proxy para a API  │
 └──────────────┬──────────────┘
                ▼
 ┌─────────────────────────────┐        ┌───────────────────────────────┐
 │ api  (Express, porta 3000)  │ ─────▶ │ mongo  (replica set rs0)      │
 │  • valida com o contrato    │        │  projetos, usuários, sessões, │
 │  • renderiza revista/*.hbs  │        │  imagens (GridFS)             │
 │  • chama o extrator de PDF  │        └───────────────────────────────┘
 └─────────────────────────────┘
```

Os três serviços são definidos em `docker-compose.yml`. Só o editor expõe porta (`8080`); API e Mongo ficam na rede interna.

### Pastas

| Pasta / arquivo | O que tem | Tecnologias |
|---|---|---|
| `editor/` | A interface de edição (SPA). | React 19, Vite, Tailwind 4, shadcn/ui, TanStack Query, react-hook-form + zod, MSW (mocks) |
| `api/` | Rotas REST, regras de domínio, autenticação, geração da revista e do zip. | Express 5, Mongoose, express-session + connect-mongo, Handlebars, archiver, pino |
| `contrato/` | **Fonte da verdade** dos tipos e schemas Zod usados por API e editor. | TypeScript + Zod |
| `revista/` | O template da revista publicada: `escala.hbs`, `script.js`, `styles.css`, `assets/`. | Handlebars, JS puro, CSS |
| `scripts/` | `extrair_descritores.py` (lê o PDF da revista) e `sync-contrato.mjs` (copia o contrato). | Python (só stdlib) + `pdftotext`, Node |
| `docs/` | `contrato.md` (todas as rotas), `docker.md`, `e2e.md`, `fixtures/revista.json`. | — |
| `descritores.json`, `saida/` | Dados reais de exemplo (`saida/` = resultado do extrator). | — |
| `escala.html`, `script.js`, `styles.css` (raiz) | Protótipo original da revista, anterior ao editor. A versão em uso fica em `revista/`. | — |

---

## 3. Como rodar com Docker (recomendado)

Pré-requisito: Docker com o plugin `compose`.

1. Crie o arquivo de ambiente:
   ```bash
   cp .env.example .env
   ```
2. Gere um segredo de sessão e cole em `SESSION_SECRET` no `.env`:
   ```bash
   openssl rand -hex 32
   ```
3. Troque `ADMIN_EMAIL` e `ADMIN_SENHA` no `.env`.
   A API **se recusa a subir** se `SESSION_SECRET` ou `ADMIN_SENHA` ainda começarem com `troque` (valores do exemplo).
4. Suba tudo:
   ```bash
   docker compose up --build
   ```
5. Abra **http://localhost:8080** e entre com o admin do `.env`.
   O admin é criado na primeira subida (seed idempotente: rodar de novo não duplica).

Outras máquinas da mesma rede acessam por `http://<ip-da-máquina>:8080`.

| Quero... | Comando |
|---|---|
| ver os logs | `docker compose logs -f` |
| parar | `docker compose down` |
| parar e **apagar o banco** | `docker compose down -v` |

---

## 4. Como desenvolver sem Docker

Pré-requisito: Node 22.

### Opção A — só o editor, com dados falsos (mais rápido)

Não precisa de API nem de banco. O [MSW](https://mswjs.io/) intercepta as chamadas `/api` no navegador.

```bash
cd editor
npm ci
npm run dev:mock
```

Abra http://localhost:5173.

### Opção B — editor + API reais

1. Tenha um MongoDB **em replica set** (a API usa transações). Um jeito simples:
   ```bash
   docker run -d --name mongo-dev -p 27017:27017 mongo:7 --replSet rs0
   docker exec mongo-dev mongosh --quiet --eval "rs.initiate()"
   ```
2. Configure e suba a API (porta 3000):
   ```bash
   cd api
   cp .env.example .env   # ajuste MONGO_URL para mongodb://localhost:27017/revista?replicaSet=rs0
   npm ci
   npm run dev
   ```
3. Em outro terminal, suba o editor (porta 5173). O Vite repassa `/api` para `localhost:3000`:
   ```bash
   cd editor
   npm ci
   npm run dev
   ```

Para usar **Importar PDF** fora do Docker, instale `python3` e `poppler-utils` (fornece o `pdftotext`).

---

## 5. Fluxo de uso no editor

1. **Entrar.** Login com e-mail e senha. Perfis: `admin` (também cadastra usuários) e `editor`.
2. **Criar projeto.** Em *Projetos > Novo projeto*, informe nome, slug e marque as disciplinas. Escolha a origem:
   - **Vazio** — anos sem descritores, escala de 0 a 500.
   - **Copiar projeto** — duplica página, imagens e as disciplinas marcadas de outro projeto.
   - **Importar PDF** — lê os descritores do PDF da revista e preenche os anos antes de criar.
3. **Editar a Página.** Aba *Página*: título, parágrafos da introdução, imagem do topo.
4. **Editar um caderno.** Cada disciplina tem sua aba. Dentro dela, escolha o ano (ou crie com **+ Ano**) e ajuste:
   - faixa da escala e os 3 cortes;
   - descritores: código, tópico, descrição, pré-requisitos, BNCC;
   - linhas da escala de cada padrão (nível + texto).
5. **Salvar.** Não há botão salvar: cada campo **salva sozinho ao sair dele**. O cabeçalho mostra o estado do salvamento.
6. **Conferir.** **Preview** abre a revista do caderno da aba atual.
7. **Entregar.** **Gerar pacote** baixa o `.zip` (uma pasta por caderno + um índice). **Exportar JSON** baixa os dados brutos.

### Uma pessoa edita por vez

Para ninguém sobrescrever o texto de outra pessoa, o projeto tem **bloqueio de edição**:

- quem abre primeiro fica com o bloqueio (renovado a cada 30 s; expira em 2 min sem renovação);
- quem chega depois vê o projeto em **somente leitura**, com o nome de quem está editando e um botão **Tentar editar**;
- o bloqueio é liberado ao fechar a aba ou após 15 min sem interação.

Detalhes do protocolo em [`docs/contrato.md`](docs/contrato.md#bloqueio-de-edição-).

---

## 6. O contrato compartilhado

API e editor precisam concordar sobre o formato dos dados. Em vez de manter dois conjuntos de tipos, existe **um só**, em `contrato/`:

```
contrato/schemas.ts ─┬─▶ api/src/contrato/schemas.ts     (cópia gerada)
contrato/revista.ts  │
campos-pagina.ts     └─▶ editor/src/contrato/schemas.ts  (cópia gerada)
```

Regra de ouro: **edite só em `contrato/`**, depois rode:

```bash
node scripts/sync-contrato.mjs
```

As cópias levam o cabeçalho `// GERADO por scripts/sync-contrato.mjs`. O `npm test` de `api/` e de `editor/` roda `sync-contrato.mjs --check` antes e **falha se alguma cópia divergir**. O mesmo vale para a fixture `docs/fixtures/revista.json`.

Todas as rotas, corpos, respostas e códigos de erro estão em [`docs/contrato.md`](docs/contrato.md).

---

## 7. Extração de descritores de PDF

`scripts/extrair_descritores.py` lê a seção *"Interpretação pedagógica da escala"* do PDF da revista e gera os dados no formato do editor. Usa só a biblioteca padrão do Python e o `pdftotext`.

```bash
# grava um JSON por disciplina (ex.: saida/lingua-portuguesa.json)
python3 scripts/extrair_descritores.py "<revista.pdf>" saida

# imprime tudo em uma linha, sem gravar arquivos (é assim que a API chama)
python3 scripts/extrair_descritores.py "<revista.pdf>" --stdout
```

**Como funciona:** o script lê cada palavra com suas coordenadas (`pdftotext -bbox`). A posição na página resolve o que texto corrido não resolve: pré-requisitos em duas colunas, rótulos da BNCC centralizados e qual texto pertence a qual faixa da régua.

**Limitação conhecida:** nas páginas do 5º ano o PDF não imprime os números de corte. O script usa a tabela `CORTES_SEM_NUMERO` (valores do Saeb). Se a revista usar outros cortes, atualize essa tabela.

No editor, o mesmo script roda pela rota `POST /api/extracao` (PDF de até 50 MB).

---

## 8. Testes e qualidade

| O que | Comando | Observação |
|---|---|---|
| API | `cd api && npm test` | Vitest + supertest com Mongo em memória (`mongodb-memory-server`). Não precisa de banco. |
| Editor | `cd editor && npm test` | Vitest + Testing Library (jsdom), API simulada pelo MSW. |
| Régua da revista | `node revista/regua.test.mjs` | Testa a montagem das faixas da escala. |
| Extrator de PDF | `python3 scripts/test_extrair_descritores.py` | Usa o PDF real; sem ele, o teste é pulado. Outro PDF: `REVISTA_PDF=<pdf> python3 ...` |
| Tipos | `npm run typecheck` | Em `api/` e em `editor/`. |
| Lint / formatação | `npm run lint` · `npm run format` | ESLint + Prettier, em cada pacote. |

Há também um roteiro **E2E manual** (login, edição, persistência, preview, zip, bloqueio, exclusão) em [`docs/e2e.md`](docs/e2e.md).

---

## 9. Operação

- **Backup e restore do Mongo, troubleshooting:** [`docs/docker.md`](docs/docker.md).
- **Limites de upload:** imagem 5 MB, PDF 50 MB.
- **Segurança:** o nginx do editor aplica Content-Security-Policy; a API usa helmet, limite de tentativas de login e cookie de sessão `httpOnly`. Nunca faça commit do `.env`.

---

## 10. Documentos relacionados

| Arquivo | Para quê |
|---|---|
| [`PRODUCT.md`](PRODUCT.md) | Quem usa, propósito, princípios do produto. |
| [`DESIGN.md`](DESIGN.md) | Sistema visual do editor (cores, tipografia, componentes). |
| [`docs/contrato.md`](docs/contrato.md) | Referência completa da API. |
| [`docs/docker.md`](docs/docker.md) | Docker, backup e troubleshooting. |
| [`docs/e2e.md`](docs/e2e.md) | Roteiro de teste ponta a ponta. |
| [`state.md`](state.md) | Registro das decisões técnicas (D-001, D-002...) e do estado atual. |
