# E2E manual: editor, API real e Mongo

Pré-requisito: `.env` na raiz (SESSION_SECRET, ADMIN_EMAIL, ADMIN_SENHA) e `docker compose up --build -d`. Editor em http://localhost:8080.
O seed não cria projeto: o primeiro vem de "Novo projeto" > Importar arquivo > `docs/fixtures/revista.json`.

## Roteiro (executado com Playwright; todos os passos passaram)

1. **Login e usuários.** Entre como admin, abra Usuários, "Novo usuário" (perfil Editor), clique em Sair e entre como o editor. Esperado: lista de projetos com o nome do editor no topo.
2. **Projeto.** Projetos > Novo projeto > nome "Projeto E2E", slug `e2e`, Importar arquivo (`docs/fixtures/revista.json`). Esperado: abre `/projetos/e2e` com "Editando".
3. **Edições.**
   - Aba Página: título do topo "Titulo Novo E2E"; dois parágrafos; remover o 2º; enviar um PNG (aparece `heroImagem.png`).
   - 5º EF: "Corte 02 → 03" = 260; D02 renomeado para D41 (a URL muda para `/D41`); em D01, +linha no Padrão 03 com nível 280 e remover a linha 2 do Padrão 01.
4. **Persistência.** F5 na tela. Esperado: tudo continua (cortes 0/125/260/375/500, D41, linha 280, 1 linha no Padrão 01, página com título, 1 parágrafo e imagem).
5. **Preview** (`/api/projetos/e2e/preview/`). Esperado: título novo, imagem 40x40, D41, 260 e a linha nova. Único erro de console: imagens `localhost:3845` bloqueadas pela CSP (esperado).
6. **Pacote .zip.** `curl -b cookies http://localhost:8080/api/projetos/e2e/pacote.zip -o p.zip`, `python3 -I -m zipfile -t p.zip`, extrair e `google-chrome --headless=new --dump-dom file://.../index.html`. Esperado: zip íntegro (index.html, styles.css, script.js, arquivos/heroImagem.png) e DOM com título, D41, linha nova e `arquivos/heroImagem.png`.
7. **Bloqueio.** Com o projeto aberto no editor, `POST /api/projetos/e2e/bloqueio` com a sessão do admin e `X-Sessao-Edicao: qualquer` retorna 423 "Projeto em edição por <nome>". A lista mostra "Em edição por <nome>". Ao fechar a aba do editor, o `bloqueio` da lista vira `null` e o admin recebe 201. Com o admin segurando o bloqueio, o editor abre o projeto em "Somente leitura" (campos desabilitados, botão "Tentar editar"); após o admin liberar (DELETE, 204), "Tentar editar" passa para "Editando".
8. **Intervalo mínimo e linhas vazias.** Em um projeto vazio (LP, 5º EF, escala 0–500), aba da etapa: intervalo mínimo 25 > "Gerar linhas vazias". Esperado: 20 linhas vazias por descritor (níveis 0, 25, … 475); no preview a régua marca de 25 em 25. Uma etapa sem intervalo (ex.: 2º EF) continua com níveis manuais.
9. **Cores dos padrões.** "Cores dos padrões" > preencher verdes (`#14532d`, `#228b22`, `#90ee90`, `#0b6b3a`) > Salvar. Esperado: barra e rótulos da escala verdes no preview e no `pacote.zip`. Copiar o projeto (Novo projeto > Copiar) herda as cores; "Restaurar padrão" volta a `#f72628`, `#ff8d43`, `#b3ccff`, `#0ed3ff`.
10. **Exportar planilhas.** "Exportar planilhas" no cabeçalho (ou `curl -b cookies http://localhost:8080/api/projetos/e2e/planilhas.zip -o pl.zip`), `python3 -I -m zipfile -l pl.zip`. Esperado: um `.xlsx` por caderno e etapa em `<caderno>/`, com abas `Níveis` e escala; a cor dos padrões bate com a do projeto. O `pacote.zip` traz os mesmos arquivos em `<caderno>/planilhas/`.
11. **Exclusão.** Excluir > confirmar. Esperado: volta à lista, que fica vazia.

Limpeza usada no teste: usuários de teste removidos pela API (DELETE /api/usuarios/:id).
