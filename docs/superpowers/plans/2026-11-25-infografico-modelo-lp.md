> **Substituído pela D-298 em 26/11:** ver [`2026-11-26-infografico-lp-copia.md`](2026-11-26-infografico-lp-copia.md). Fica como histórico do modelo único, que pode voltar numa próxima versão.

# Plano — Modelo de infográfico de LP pré-preenchido pelos dois Word (antes da etapa 11)

## Contexto
A Pedagógica (Bortolucci) enviou dois Word com todo o conteúdo dos infográficos do F2 de **Língua Portuguesa**:
`AVALIAÇÃO E CURRÍCULO_LP_2026_ALFA_GERAL.docx` (Alfa) e `..._AF_EM_GERAL.docx` (Outras Etapas). O conteúdo vale
para todas as revistas de LP. Hoje cada `RevistaInfografico` (`app/nucleo/models/revista.py:131`) nasce vazio e é
preenchido revista a revista no passo "Infográficos" da ficha.

Decidido pelo usuário em 25/11:
1. **Modelo único** por ano × componente × tipo (Alfa, Outras), editado num lugar só.
2. **A revista pode sobrescrever qualquer campo** (como a cópia de seção do template, D-115); o que ela não mexeu vem do modelo.
3. **Imagem dupla do 5EF Alfa** (suporte + enunciado) vira uma imagem só na carga.
MT não muda: sem modelo, a revista continua preenchendo tudo, como hoje.

## Mapeamento Word → campos (conferido nos dois arquivos)

| No Word | Campo |
|---|---|
| "❶Descritor: …" | `habilidade` |
| Textos dos cliques ❶ / ❷ / ❸ | `texto_descritor` / `texto_progressao` / `texto_habilidades` (❸ inteiro: abertura + bloco por ano com subtítulo) |
| Tabela "Descrição das habilidades" 1EF–3EM | 12 etapas: `marca`, `codigo`, `texto`; célula mesclada = código e texto vazios |
| Tabela "Progressão" | a mesma `marca` (as duas tabelas coincidem nos dois Word) |
| ❹ "D05 – 2º ano do EF" ×4 + imagem + análise | 4 itens: `descritor`, `etapa`, `imagem`, `analise` |
| "INSERIR DICA: Consulte também o Referencial Curricular da Rede." | texto do template F2 de LP (seção da tabela), não do modelo |
| "P0020…", "_SUP", legenda, "não vai ter série histórica/percentual" | nada (rótulo do design ou já resolvido) |

## Passos (≈ 2 dias de trabalho; cada passo fecha com testes verdes)

0. **Branch.** O mapa de páginas está sem commit na `feat/redesenho-figma` (worktree de trabalho): pedir o ok para commitá-lo antes. Depois: `integ/infografico-modelo` a partir da `main` e `feat/infografico-modelo`. Card K-050 em Doing, decisão D-297 no `state.md`.
1. **Seed a partir do Word (≈ 2 h).** Script de uma vez `scripts/docx_infografico.py` (zip + XML da stdlib; Pillow do host só para juntar as 2 imagens do 5EF Alfa, empilhadas). Saída versionada, como os `.hbs`: `app/templates_seed/2026/infograficos/lp-alfa.json`, `lp-outras.json` e as imagens ao lado. Os `.docx` vão para `docs/fontes/2026/`. A análise e os textos ❸ viram HTML com `<p>` e `<h4>` para os títulos dos anos (o mesmo formato do editor rico atual).
2. **Modelo de dados (≈ 3 h).** Tabelas novas `modelo_infografico` (ano, componente, tipo, habilidade, 3 textos; único por ano × componente × tipo), `modelo_infografico_etapa` e `modelo_infografico_item`, espelhando as da revista, com FK composta de ano (`nucleo/db.py::fk_composta`) e histórico. Nas tabelas da revista, os campos de conteúdo passam a aceitar NULL: **NULL = herda do modelo**, `""` = vazio de propósito. A migração troca `""` por NULL (nenhuma revista de LP tem conteúdo hoje; a de MT continua igual, porque sem modelo NULL e `""` dão o mesmo). O teste de `pg_constraint` muda junto. Comando `carregar_infograficos` (lê o seed, como `carregar_templates`) entra no `scripts/povoar-banco-2026.sh` e no `abrir_ano` (copiar o modelo do ano anterior).
3. **Resolver e pendências (≈ 2 h).** `servicos/resolver.py::_infograficos` junta campo a campo: valor da revista se não for NULL, senão o do modelo, senão `""`. Mesmo formato de saída: preview, zip, F2 gerado (`servicos/f2.py`) e impresso não mudam. `servicos/pendencias.py` passa a olhar o valor resolvido. O hash das revistas de LP muda uma vez (elas estavam vazias).
4. **Tela do modelo (≈ 4 h).** `/ui/infograficos/<ano>/` (lista: LP Alfa, LP Outras) e `/ui/infograficos/m/<pk>/` (editor), reaproveitando o parcial `parciais/revista_infograficos.html` e o `nucleo/infografico.py::form_do_campo` (prefixo do campo aponta para o modelo). A gravação passa pelo modal de impacto (D-202) com as revistas de LP que **não** sobrescreveram aquele campo. Entrada: link "Infográficos" na página de Templates (na etapa 11 vira parte de "Modelos"). Permissão nova em `nucleo/permissoes.py` (Pedagógica edita) + migração de dados que sincroniza os grupos.
5. **Ficha da revista (≈ 3 h).** O passo "Infográficos" mostra o valor do modelo com o selo "do modelo" (`_componentes/selo_sobrescrita.html`); editar grava a sobrescrita ("desta revista"); "Voltar ao modelo" grava NULL. Imagem do item: trocar sobrescreve; voltar ao modelo apaga a da revista.
6. **Documentos e E2E (≈ 2 h).** `docs/regras-de-negocio.md`, `docs/modelo-er.md`, `docs/telas/telas-b.md`, `docs/telas/mapa-de-paginas.md`, ficha nova. E2E só sobrescreve campos da revista do próprio parceiro "E2E …"; **não edita o modelo de LP** (ele alimenta revistas reais): o editor do modelo é testado no Django.

Fora deste plano (fica anotado): aviso "o modelo mudou depois da sua sobrescrita" (como as cópias desatualizadas do D-115); modelo de MT.

## Arquivos principais
`app/nucleo/models/revista.py` (+ modelo novo), `app/nucleo/migrations/0029_*`, `app/nucleo/infografico.py`, `app/nucleo/servicos/resolver.py`, `app/nucleo/servicos/pendencias.py`, `app/nucleo/urls/ui_infograficos.py` (novo), `app/nucleo/urls/ui_revista.py`, `app/nucleo/templates/ui/parciais/revista_infograficos.html`, `app/nucleo/permissoes.py`, `app/nucleo/management/commands/carregar_infograficos.py`, `scripts/povoar-banco-2026.sh`.

## Verificação
- `docker compose run --rm app python manage.py test` verde e `makemigrations --check` limpo.
- Testes novos: seed com 12 etapas e 4 itens por tipo; resolver (NULL herda, `""` vale, MT sem modelo igual a hoje); editor do modelo com modal de impacto; sobrescrita e "Voltar ao modelo"; permissão.
- Na 8002, banco refeito pelo script: abrir a revista de LP de um parceiro com Alfa e Outras e conferir os 4 cliques, as 2 tabelas e os 4 "+" com imagem e análise; editar um campo na ficha e ver o selo "desta revista".
