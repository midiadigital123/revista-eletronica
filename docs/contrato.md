# Contrato — API ↔ Editor ↔ Revista

Fonte da verdade em código: `contrato/schemas.ts`, `contrato/campos-pagina.ts`, `contrato/revista.ts`.
Cópias geradas em `api/src/contrato/` e `editor/src/contrato/` por `node scripts/sync-contrato.mjs`.
O `npm test` de cada projeto falha se as cópias divergirem. **Não edite as cópias.**

Este documento descreve as rotas. Os tipos citados (ex.: `Projeto`, `CriarAnoEntrada`) são os schemas Zod de `contrato/schemas.ts`.

---

## Convenções

- **Base:** `/api`. Corpo e resposta em JSON, exceto upload de imagem (multipart), preview (HTML/CSS/JS/imagem) e zip.
- **Autenticação:** cookie de sessão `revista.sid` (httpOnly, sameSite=lax, `secure` em produção). Toda rota exige login, exceto `POST /auth/login`. A cada requisição, o usuário é reconferido no banco: desativar ou mudar o perfil vale na hora.
- **Validação:** entradas validadas pelos schemas do contrato. Campos desconhecidos → 400.
- **Erros:** sempre no formato `ErroApi`:
  ```json
  { "erro": "mensagem para o usuário", "campo": "cortes.padrao-2", "detalhes": [{ "campo": "...", "erro": "..." }], "bloqueio": { "...": "..." } }
  ```

| Status | Quando |
|---|---|
| 400 | Validação (schema ou regra de domínio). `campo` = primeiro problema; `detalhes` = todos |
| 401 | Sem sessão, ou credenciais inválidas no login |
| 403 | Rota de admin acessada por editor |
| 404 | Projeto, ano, descritor, padrão, usuário ou imagem inexistente |
| 409 | Duplicado: e-mail, slug, ano ou código de descritor |
| 413 | Corpo JSON > 2 MB ou imagem > 5 MB |
| 423 | Escrita sem o bloqueio de edição. `bloqueio` = quem está editando (ou `null`) |

---

## Bloqueio de edição (🔒)

Um projeto é editado por **uma pessoa, numa aba**, por vez.

- **Identidade do editor:** usuário da sessão + header **`X-Sessao-Edicao`**, um UUID por aba guardado em `sessionStorage`. O cliente envia esse header em **toda** requisição.
- **Rotas 🔒:** exigem bloqueio válido do próprio editor. Sem ele → **423**.
- **Duração:** o bloqueio dura **2 min** (`BLOQUEIO_TTL_MS`); o editor renova a cada **30 s**.
- **`POST /projetos/:slug/bloqueio`:** responde 201 `BloqueioPublico`. Adquire se o projeto estiver livre, expirado ou já for deste editor. É atômico (um único `findOneAndUpdate` condicional). Se outra pessoa detém o bloqueio → 423. Sem o header → 400.
- **`PUT /projetos/:slug/bloqueio`:** responde 200 `BloqueioPublico` com `expiraEm` novo. **Só renova, nunca readquire.** Expirado ou de outra pessoa → 423. Depois de um 423, o cliente recarrega o projeto do servidor antes de tentar `POST` de novo.
- **`DELETE /projetos/:slug/bloqueio`:** libera e é idempotente. O editor chama no `pagehide` (`keepalive`) e após 15 min sem interação (`BLOQUEIO_INATIVIDADE_MS`).
- **Leitura é livre** (`GET`, preview, zip, exportar). Quem não tem o bloqueio vê o projeto em modo leitura.
- **Criação:** quem cria um projeto (`POST /projetos`) já sai com o bloqueio.

---

## Auth — `/api/auth`

| Método | Rota | Corpo | Resposta |
|---|---|---|---|
| POST | `/auth/login` | `LoginEntrada` `{email, senha}` | 200 `Usuario` · 401 |
| POST | `/auth/logout` | — | 204 |
| GET | `/auth/me` | — | 200 `Usuario` · 401 |

Usuário inativo não loga (401). O login regenera a sessão.

## Usuários — `/api/usuarios` (só admin)

| Método | Rota | Corpo | Resposta |
|---|---|---|---|
| GET | `/usuarios` | — | 200 `Usuario[]` (ordem por nome) |
| POST | `/usuarios` | `CriarUsuarioEntrada` `{email, nome, senha, perfil}` | 201 `Usuario` · 409 e-mail |
| PATCH | `/usuarios/:id` | `AtualizarUsuarioEntrada` `{nome?, perfil?, ativo?, senha?}` | 200 `Usuario` · 400 · 404 |
| DELETE | `/usuarios/:id` | — | 204 · 400 · 404 |

- **Sempre ≥ 1 admin ativo:** rebaixar, desativar ou excluir o último → 400.
- **Ninguém exclui a própria conta** → 400.
- **Primeiro admin:** criado no boot por `ADMIN_EMAIL`/`ADMIN_SENHA`. É idempotente e não altera a senha de quem já existe.

## Página — `/api/pagina`

| Método | Rota | Resposta |
|---|---|---|
| GET | `/pagina/campos` | 200 `CAMPOS_PAGINA` (chave, rótulo, tipo `texto`/`paragrafos`/`imagem`, max, ajuda) |

---

## Projetos — `/api/projetos`

O identificador na URL é o **`slug`**: minúsculas, números e hífen, até 60 caracteres.

### Projeto

| Método | Rota | Corpo | Resposta |
|---|---|---|---|
| GET | `/projetos` | — | 200 `ProjetoResumo[]` (ordem por nome) |
| POST | `/projetos` | `CriarProjetoEntrada` `{slug, nome, origem}` | 201 `Projeto` (com bloqueio do criador) · 404 origem · 409 slug |
| GET | `/projetos/:slug` | — | 200 `Projeto` |
| PATCH 🔒 | `/projetos/:slug` | `AtualizarProjetoEntrada` `{slug?, nome?}` | 200 `Projeto` · 409 slug |
| DELETE 🔒 | `/projetos/:slug` | — | 204 |
| GET | `/projetos/:slug/revista` | — | 200 `Revista` (Exportar JSON) |

**`origem`:**
- `{tipo: "vazio", anos?: Ano[]}`: anos sem descritores, faixa 0–500 e cortes 125/250/375. Sem `anos`, cria `ANOS_PADRAO` (5ef, 9ef e 3em).
- `{tipo: "importar", revista: Revista}`: aceita o `descritores.json` antigo (sem `cortes`/`pagina`). `Revista.pagina` usa `PaginaTextos`: só textos, sem `null`.
- `{tipo: "copiar", de: slug}`: copia página, anos **e imagens**.

**Exclusão:** é lógica (`excluidoEm`) e libera o slug para reuso. Os dados continuam no banco.

**Renomear o `slug`:** o bloqueio continua valendo; o cliente passa a usar a URL nova.

### Página do projeto

| Método | Rota | Corpo | Resposta |
|---|---|---|---|
| PATCH 🔒 | `/projetos/:slug/pagina` | `PaginaPatch` (chaves de `CAMPOS_PAGINA` dos tipos texto/parágrafos) | 200 `Pagina` |
| GET | `/projetos/:slug/pagina/:chave/imagem` | — | 200 binário (Content-Type da imagem) · 404 |
| PUT 🔒 | `/projetos/:slug/pagina/:chave/imagem` | multipart, campo **`arquivo`** | 200 `Pagina` · 400 tipo · 404 campo · 413 |
| DELETE 🔒 | `/projetos/:slug/pagina/:chave/imagem` | — | 200 `Pagina` (idempotente: sem imagem, devolve a página como está) |

- **`PaginaPatch`:** valor `null`, `""` ou `[]` remove o campo, e a revista volta ao texto padrão do template. Itens vazios em parágrafos são descartados.
- **Imagem:** PNG, JPEG ou WebP, até 5 MB; SVG é recusado. Uma nova substitui a anterior (o arquivo antigo é removido do GridFS). Fica no GridFS; em `Pagina` aparece como `{nome, mime, tamanho}`, onde `nome = nomeArquivoImagem(chave, mime)` (ex.: `heroImagem.png`; JPEG vira `.jpg`). No zip e no preview, o arquivo fica em `arquivos/<nome>`.

### Anos (etapas)

Chave `<n>ef` (1 a 9) ou `<n>em` (1 a 3), ex.: `2ef`, `5ef`, `3em`. Rótulos gerados por `rotuloAno` (`2º EF`, `3ª EM`) e `rotuloAnoLongo` (`2º Ano do Ensino Fundamental`, `3ª Série do Ensino Médio`); ordem por `compararAnos` (EF antes de EM, depois o número). A revista importada/exportada aceita qualquer etapa válida como chave.

| Método | Rota | Corpo | Resposta |
|---|---|---|---|
| POST 🔒 | `/projetos/:slug/anos` | `CriarAnoEntrada` `{ano, scaleRange?, cortes?}` | 201 `AnoProjeto` · 409 |
| PATCH 🔒 | `/projetos/:slug/anos/:ano` | `AtualizarAnoEntrada` `{scaleRange?, cortes?}` | 200 `AnoProjeto` · 400 |
| DELETE 🔒 | `/projetos/:slug/anos/:ano` | — | 204 · 400 se for o último ano |

### Descritores

| Método | Rota | Corpo | Resposta |
|---|---|---|---|
| POST 🔒 | `/projetos/:slug/anos/:ano/descritores` | `CriarDescritorEntrada` (`codigo` + campos opcionais, inclusive `scale`) | 201 `Descritor` · 409 |
| PATCH 🔒 | `…/descritores/:codigo` | `AtualizarDescritorEntrada` `{codigo?, topic?, description?, prerequisites?, bncc?: parcial}` | 200 `Descritor` · 409 código |
| DELETE 🔒 | `…/descritores/:codigo` | — | 204 |
| PUT 🔒 | `…/descritores/:codigo/escala/:padrao` | `LinhaEscala[]` (o padrão inteiro) | 200 `LinhaEscala[]` ordenadas · 404 padrão |

- **Renomear:** `codigo` novo no PATCH renomeia o descritor.
- **Listas:** `prerequisites` e `bncc.skills` são substituídas inteiras; para adicionar ou remover um item, envie a lista nova.
- **Escala:** é salva por padrão inteiro, porque as linhas não têm identidade estável (a ordem vem do nível).

### Regras de domínio (`problemasDoAno` → 400 com `detalhes`)

- **Código:** `D` + 2 dígitos, único no ano.
- **`scaleRange`:** inteiros, `min < max`.
- **Cortes:** inteiros, `min < padrao-1 < padrao-2 < padrao-3 < max`.
- **`level`:** dentro de `scaleRange`; as linhas ficam em ordem decrescente de `level`.
- **Reduzir `scaleRange`** deixando corte ou nível de fora → 400, listando os descritores afetados. Nada é ajustado em silêncio.
- **`content` vazio** vira `"---"` (a revista mostra como "sem item").
- **Nível fora do intervalo do próprio padrão** não é erro (a revista aceita); o editor só mostra um aviso (`padraoDoNivel`).

### Geração da revista

| Método | Rota | Resposta |
|---|---|---|
| GET | `/projetos/:slug/preview/` | 200 `text/html` (index.html renderizado) |
| GET | `/projetos/:slug/preview/styles.css` · `/preview/script.js` · `/preview/assets/:nome` · `/preview/arquivos/:nome` | 200 arquivo |
| GET | `/projetos/:slug/pacote.zip` | 200 `application/zip`, `Content-Disposition: attachment; filename="<slug>.zip"` |

Conteúdo do zip: `index.html`, `styles.css`, `script.js`, `assets/` (setas SVG fixas do template) e `arquivos/<imagens>`. Abre com duplo clique (`file://`), sem servidor.

---

## Template da revista (`revista/`)

- **Arquivos:** `revista/escala.hbs` (cópia de `escala.html` com placeholders Handlebars), `revista/script.js` e `revista/styles.css` (cópias adaptadas). Os arquivos da raiz (`escala.html` etc.) ficam intactos como referência.
- **Contexto do template:**
  - `pagina.<chave>`: textos de `CAMPOS_PAGINA`, escapados pelo Handlebars;
  - `pagina.<chaveImagem>`: caminho relativo `arquivos/<nome>`;
  - `dadosRevista`: string JSON segura (abaixo).
- **Campo ausente:** o template mostra o texto original (`{{#if pagina.heroTitulo}}…{{else}}ANÁLISE DOS RESULTADOS…{{/if}}`).
- **Bloco de dados:** os dados vão num único `<script type="application/json" id="dados-revista">{{{dadosRevista}}}</script>`, no formato `Revista` (`revistaDosAnos`). O `script.js` lê com `JSON.parse(document.getElementById("dados-revista").textContent)`.
- **Serialização de `dadosRevista`:** `JSON.stringify`, depois `<` → `<`, ` ` → `\\u2028` e ` ` → `\\u2029`. Assim nenhum texto fecha o `<script>`.
- **Escape no `script.js`:** todo texto vindo dos dados que vai para `innerHTML` passa por escape de HTML.
- **Imagens:** sempre por caminho relativo (`arquivos/...`), para funcionar por `file://` e no preview.

---

## Como tornar um novo trecho da revista editável

1. Adicione o campo em `contrato/campos-pagina.ts` (chave, rótulo, tipo).
2. Use `{{pagina.<chave>}}` em `revista/escala.hbs`, com o texto atual no `{{else}}`.
3. Rode `node scripts/sync-contrato.mjs`.

A API passa a validar o campo e o editor a mostrá-lo na aba Página, sem outras mudanças.
