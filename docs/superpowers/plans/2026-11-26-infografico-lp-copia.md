# Plano — Infográficos de LP preenchidos por cópia do seed dos Word (D-298)

Substitui [`2026-11-25-infografico-modelo-lp.md`](2026-11-25-infografico-modelo-lp.md) (D-297, modelo único).
Vem antes da etapa 11 (redesenho pelo Figma). Estimativa: cerca de 6,5 h.

**Feito em 26/11 (passos 0 a 5).** Mudou no caminho: os textos do infográfico são Markdown, não HTML (anos do ❸ em
negrito); a cascata e a carga ficam atrás da chave `INFOGRAFICOS_DO_SEED` (a suíte Django desliga); a dica do
Referencial ficou de fora (escolha do usuário em 26/11); dois specs E2E passaram a gravar valores diferentes do seed.

## Contexto
A Pedagógica (Bortolucci) enviou dois Word com o conteúdo dos infográficos do F2 de **Língua Portuguesa**:
`AVALIAÇÃO E CURRÍCULO_LP_2026_ALFA_GERAL.docx` (Alfa) e `..._AF_EM_GERAL.docx` (Outras Etapas), iguais para todas
as revistas de LP. Hoje cada `RevistaInfografico` nasce vazio. Em vez de um modelo único com herança (D-297), o
conteúdo é **copiado** para cada infográfico de LP. A edição continua na ficha de cada revista, como hoje.
MT não muda.

## Mapeamento Word → campos (conferido em 25/11)

| No Word                                                             | Campo de `RevistaInfografico*`                                                                                   |
| ------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| "❶Descritor: …"                                                     | `habilidade`                                                                                                     |
| Textos dos cliques ❶ / ❷ / ❸                                        | `texto_descritor` / `texto_progressao` / `texto_habilidades` (❸ inteiro: abertura + bloco por ano com subtítulo) |
| Tabela "Descrição das habilidades" 1EF–3EM                          | 12 etapas: `marca`, `codigo`, `texto`; célula mesclada = código e texto vazios                                   |
| Tabela "Progressão"                                                 | a mesma `marca` (as duas tabelas coincidem nos dois Word)                                                        |
| ❹ "D05 – 2º ano do EF" ×4 + imagem + análise                        | 4 itens: `descritor`, `etapa`, `imagem`, `analise`                                                               |
| "INSERIR DICA: Consulte também o Referencial Curricular da Rede."   | texto do template F2 de LP (seção da tabela)                                                                     |
| "P0020…", "_SUP", legenda, "não vai ter série histórica/percentual" | nada                                                                                                             |

## Passos

0. **Branch (5 min).** `integ/infografico-lp` a partir da `main` e `feat/infografico-lp`, na worktree de trabalho. K-050 em Doing.
1. **Seed a partir do Word (≈ 2 h).** Script de uma vez `scripts/docx_infografico.py` (zip + XML da stdlib; Pillow do host só para empilhar as 2 imagens do 5EF Alfa, D-232). Saída versionada: `app/templates_seed/2026/infograficos/lp-alfa.json`, `lp-outras.json` e as imagens ao lado. Os `.docx` vão para `docs/fontes/2026/`. Textos ricos em Markdown, o formato do editor atual (parágrafos; anos do ❸ em `**negrito**`, porque título `#` é recusado).
2. **Comando `carregar_infograficos` (≈ 1,5 h).** Para cada infográfico ativo de LP do ano: grava habilidade, textos, 12 etapas e 4 itens pelo mesmo caminho do autosave (`nucleo/infografico.py::form_do_campo`, que valida e cria as linhas que faltam) e a imagem por `servicos/arquivos.py::receber_imagem_item` (um arquivo por revista, nunca caminho compartilhado, por causa do `apagar_item_orfao`). Usuário da carga no histórico. Entra no `scripts/povoar-banco-2026.sh`.
3. **Recarga segura (≈ 1,5 h).** `carregar_infograficos --anterior <seed antigo>`: troca só o campo cujo valor atual ainda é igual ao do seed anterior (o seed antigo vem do git). O que a Pedagógica editou na revista fica. Serve para corrigir o texto em todas as revistas de uma vez.
4. **Cascata (≈ 1 h).** `servicos/cascata.py::_sincronizar_infograficos` (linha 110): infográfico de LP criado depois da carga (parceiro que ganha corte no 2EF, revista nova) já nasce preenchido pelo seed. Desarquivar não preenche (a linha guarda o que tinha).
5. **Docs (≈ 0,5 h).** `docs/regras-de-negocio.md`, `README.md` (comando novo), `docs/variaveis.md` se o texto usar `{{x}}`.

## Fora deste plano
Modelo único com herança (D-297): fica para uma próxima versão do sistema, se as correções em massa ficarem frequentes. Modelo de MT.

## Verificação
- Testes Django: seed com 12 etapas e 4 itens por tipo; carga preenche só LP e só infográfico ativo; recarga troca o campo igual ao seed anterior e mantém o editado; cascata cria a Alfa já preenchida.
- `docker compose run --rm app python manage.py test` verde e `makemigrations --check` limpo (não há migração).
- Na 8002, banco refeito pelo script: revista de LP com Alfa e Outras mostra os 4 cliques, as 2 tabelas e os 4 "+" com imagem e análise; editar um campo na ficha continua funcionando.
- O hash das revistas de LP muda uma vez (infográficos estavam vazios): o "Validado" cai, o que é esperado.
