# Ficha: Revista (T21; a lista T20 virou a aba Lista de Projetos)

Endereço: `/ui/revista/<ano>/<pk>/` (rota `ui_revista_editar`). A lista do ano (`/ui/revista/<ano>/`) redireciona (302) para a aba Lista de Projetos (ficha [`projeto.md`](projeto.md)), que mostra as revistas, o preview e o zip.

## Objetivo

Reunir numa página o que a equipe precisa para deixar uma revista pronta: o template de cada fascículo, os infográficos do F2, a capa, o texto de cada seção e o "Validado". Desde o U8b, a página tem duas colunas: os passos na ordem em que se resolvem, à esquerda, e a coluna Situação, fixa ao rolar, à direita, com a única lista de pendências e o "Validar revista".

## Quem usa

| Perfil | O que faz |
|---|---|
| Pedagógica, Admin | tudo: templates, infográficos, capa, textos, "Validar revista" |
| Mídias Digitais | o mesmo da Pedagógica; baixa o zip |
| Impresso | só vê (infográficos, capa, textos, Situação); abre o preview e a tela do impresso |
| Sem ver revista | recebe 403 |

## Jornada

- **Antes:** Painel (coluna da revista, "falta" de template, infográficos, capa ou textos), a aba Revistas do projeto ou a Lista de Projetos.
- **Depois:** preview, "Validar revista", tela do impresso, zip para Mídias.

## Página

1. **Trilha:** "Projetos de <ano> › <projeto>" (volta à aba Revistas do projeto).
2. **Cabeçalho:** "<projeto> · <componente>", Parceiro e Ano; selo "Arquivada" quando for o caso; link "Editar o nome do projeto" (o nome só se edita no Projeto). À direita: status do salvamento, "Abrir preview" (nova aba; arquivada: "Abrir versão arquivada"), "Baixar zip", "Baixar planilhas" (F1/F2, `impresso_planilhas`) e o link "Tela do impresso".
3. **Coluna principal:**
   - **1 Templates:** um select por fascículo ("Template do F1", "Template do F2"), só com templates do mesmo ano, componente e fascículo. Salva ao escolher.
   - **2 Infográficos** (`#infograficos`, fase 3 do F2, D-254): um cartão por infográfico ativo (Alfa antes de Outras Etapas), com "Abrir prévia" (nova aba, `preview_f2`). No cartão: habilidade destacada, texto do clique ❶ (no modal, entra depois do Diálogo do descritor do template), os checkboxes "Passos do tour" (Habilidades, Progressão, Tarefas), o texto ❷ (habilidades), a grade "Referencial por etapa" de 12 linhas fixas (1EF a 3EM: marca, código, texto), o texto ❸ (progressão) e as 4 tarefas (imagem por área de soltar com miniatura, etapa, descritor, texto alternativo, análise). Em cada passo, "Do template" (fechado) mostra só para leitura as seções do template F2 que o passo usa (`passo-*`, `dlg-descritor`, `dlg-tarefas`, `tarefas-fechamento`; a cópia, se houver), com "Editar nesta revista" para o painel da seção (D-258). As caixas de texto abrem com 4 linhas e mostram o texto todo enquanto têm foco. Passo desligado esconde o seu bloco (CSS `:has()`); a grade some só com Habilidades e Progressão desligadas. A linha de etapa ou item nasce na 1ª gravação. Sem infográfico ativo: "Esta revista não tem infográfico: faltam cortes."
   - **3 Capa** (`#arquivos`): miniatura e área de soltar ("Enviar a capa" / "Substituir a capa"). Envia ao escolher, com barra de progresso. O F2 não tem arquivo enviado: o SVG é gerado dos infográficos (D-239; o upload saiu na fase 4).
   - **4 Textos:** só com os dois templates escolhidos; antes disso, o estado vazio "Escolha os templates acima". Lista das seções à esquerda (F1 e F2, com marca "cópia" ou "desatualizada"); à direita, uma seção por vez, com o título do template (não se edita) e o texto, que salva sozinho ao sair do campo.
4. **Coluna Situação (fixa):** "N de 6 prontos" com barra de progresso, ou "Validada por <nome> em dd/mm HH:MM". Checklist dos passos (Matriz e cortes, Template do F1, Template do F2, Infográficos, Capa, Dados do projeto; "Outras pendências" se houver): ✓ pronto ou ○ pendente, em cor neutra, cada pendência um link para onde se resolve. Aviso de seções desatualizadas (não impede). Botão "Validar revista" e o link "O que mudou para o impresso".

## Dados mostrados

- Revista: projeto, parceiro, componente, ano, capa, arquivada.
- Por infográfico ativo: habilidade, os 3 textos dos cliques, passos ligados, as 12 linhas do referencial e os 4 itens.
- Por fascículo: o template em uso.
- Por seção: rótulo, título (do template), texto efetivo (cópia ou o do template), se é cópia, se está desatualizada e o diff "seu texto | template novo".
- Situação: pendências por passo, quem e quando validou, seções desatualizadas.
- Revista arquivada: as seções da foto congelada.

## Dados gravados (um campo por vez)

- Template de cada fascículo. Trocar um fascículo que tem cópias de seção apaga as cópias: o modal pede a frase "descartar N cópia(s)".
- Infográfico (`nucleo/infografico.py`, um campo por envio, nomes `inf-<pk>-…`): habilidade, textos, passo ligado/desligado, marca/código/texto de cada etapa, etapa/descritor/texto alternativo/análise e imagem (PNG, JPG ou WebP até 5 MB) de cada item.
- Capa (arquivo, hash).
- Cópia do texto de uma seção: a primeira mudança cria a cópia só dessa seção. "Manter meu texto" regrava a versão da cópia; "Descartar cópia" apaga a cópia (pede confirmação do navegador).
- "Validado" (hash, quando, quem), pelo botão "Validar revista".
- Toda gravação que muda o texto de uma revista validada abre o modal de impacto antes.

## Ações

| Ação | Onde | Resultado |
|---|---|---|
| Escolher template | 1 Templates | grava; a parte Textos e a Situação se atualizam |
| Sair de um campo do infográfico / marcar passo / escolher etapa ou marca | 2 Infográficos | grava; a Situação se atualiza (o cartão não é trocado, para não perder o campo seguinte) |
| Soltar ou escolher a imagem de uma tarefa | 2 Infográficos | envia e grava; Infográficos (miniatura) e Situação se atualizam |
| Soltar ou escolher a capa | 3 Capa | envia e grava; Capa e Situação se atualizam. Acima do limite, o erro aparece sem enviar |
| Escolher seção | lista de seções | troca o painel da direita sem recarregar (a URL muda) |
| Sair do texto alterado | painel da seção | grava a cópia; a lista de seções, a Situação e o estado da seção se atualizam |
| Manter meu texto / Descartar cópia | painel da seção | regrava a versão da cópia / apaga a cópia |
| Validar revista | coluna Situação | desligado, com o motivo, enquanto houver pendência; primário quando pronta. Grava o "Validado" da versão exibida |
| Abrir preview / Baixar zip / Tela do impresso | cabeçalho | preview em nova aba / `.zip` (com pendências, volta com a mensagem) / tela do impresso da revista |

## Estados

- **Pendência:** só na coluna Situação, como tarefa (○ neutro). Não há faixa vermelha nem caixa rosa nesta página. O vermelho fica para erro de verdade (upload recusado, falha de gravação).
- **Sem template:** a parte Textos mostra "Escolha os templates acima" · "Os textos aparecem aqui quando os dois fascículos tiverem template." Sem capa: "Sem capa." (só leitura).
- **Erro (422):** embaixo do campo ou da área de soltar ("Imagem maior que 5 MB: …"); status "Não salvo: corrija o campo marcado". Nada grava.
- **Impacto:** o modal "Trocar o template do F1…", "Salvar o infográfico…", "Trocar a capa…" ou "Salvar o texto da seção tira o “Validado” de N revista(s)". Cancelar volta o valor (no texto, o que foi digitado fica, como "Não salvo").
- **Só leitura por perfil:** aviso "Só leitura: seu perfil vê a revista, mas não altera. Para editar, peça a permissão de revista a um administrador." Sem selects, sem áreas de soltar, texto `readonly`.
- **Só leitura por bloqueio:** aviso "Somente leitura: <pessoa> está editando…" (o mesmo do admin).
- **Bloqueio perdido no meio (409):** a página vira só leitura, como no bloqueio.js.
- **Voltar e Avançar (bfcache):** a página restaurada recarrega e adquire bloqueio novo, em vez de mostrar "Você perdeu o bloqueio" (D-222).
- **Sair com texto não salvo:** clicar num link ou botão que sai da página abre o diálogo "Alterações não salvas" (Salvar e sair, Descartar e sair, Continuar editando; D-223). Fechar, recarregar ou Voltar: aviso do navegador.
- **Arquivada:** aviso "Só leitura: revista arquivada. O texto mostrado é a foto do arquivamento." Sem bloqueio, sem formulários.
- **Sucesso:** o status "Salvo às HH:MM" (autosave); "Revista validada." no "Validar revista".

## Mensagens exatas

- Seção sem mudança (Manter/Descartar sem efeito): "Nada a salvar: o texto está igual ao que abriu."
- Validar recusado: "Não validada: <motivo>." (mudou, pendências, arquivada).
- Motivo do botão desligado: "Resolva as pendências acima para validar."
- Bloqueio perdido: "Não salvo: você perdeu o bloqueio de edição (outra pessoa ou aba abriu esta página). Recarregue e refaça a alteração."
- Zip recusado: "Zip recusado. Pendências: …"
- Seção que saiu do template: "Esta seção saiu do template. Recarregue a página."
- Envio de arquivo sem arquivo: "Escolha o arquivo da capa e envie de novo."
- Campo do infográfico desconhecido, de outra revista ou de infográfico arquivado: "Este campo não pode ser alterado aqui. Recarregue a página."
- Aviso de seções desatualizadas: "Seções desatualizadas: <lista>. Não impede o “Validado”."

## Permissões

- Login obrigatório; anônimo vai ao login das telas B (`/conta/entrar/`).
- Ver: `view_revista` ou `change_revista`; sem isso, 403.
- Capa: `change_revista`. Infográficos: `change_revistainfografico` (habilidade, textos, passos); + `add/change_revistainfograficoetapa` (grade) e `add/change_revistainfograficoitem` (tarefas). Templates: + `change_revistafasciculo`. Textos: + `add/change_revistasecao`. Validar: `validar_revista`. "Editar o nome do projeto": `change_projeto`.
- Revista ou projeto arquivado: só leitura para todos; POST é 403.
- Bloqueio: abrir a revista trava o projeto dela; quem não consegue o bloqueio vê só leitura; POST sem o bloqueio não grava.
- POST com ação desconhecida (inclusive `acao=nome`): 400.

## Interações (Alpine e HTMX)

- Templates e arquivos: um form `campoAuto` com a sessão de bloqueio; cada parte tem o seu `data-url` (`?acao=templates`, `?acao=arquivos`, `?acao=infografico`). A resposta 200 traz em `trocar` o HTML novo de `#textos`, `#arquivos`, `#infograficos` (só no upload da imagem) e `#situacao`. Arquivos pelo componente `arquivoSoltar`.
- Texto: form `campoAuto` da seção (`?acao=texto&secao=F1:<id>`); a resposta troca `#secoes`, `#situacao` e o estado da seção.
- Escolher seção: `hx-get` no item da lista, alvo `#secao`, `hx-push-url` (o link funciona sem JS e ao recarregar).
- Manter meu texto / Descartar cópia: `hx-post` (`acao=secao`), troca `#secao` e, fora do alvo, `#secoes`, `#situacao` e `#mensagens`.
- Validar revista: `hx-post` (`acao=validar`) com `HX-Redirect` de volta à página.

## Wireframe (1440 px)

```
Revista Eletrônica  [2026 ▾]  Painel [Projetos] Matrizes Templates Impresso                  Ana         Sair
──────────────────────────────────────────────────────────────────────────────────────────────────────────────
Projetos de 2026 › Projeto GO
Projeto GO · Língua Portuguesa            ✓ Salvo às 10:15  [Abrir preview ↗]  Baixar zip  Tela do impresso
Parceiro GO   Ano 2026   Editar o nome do projeto
┌ coluna principal ──────────────────────────────────────────┐ ┌ Situação (fixa ao rolar) ──────┐
│ 1 Templates   Template do F1 [Padrão ▾]  do F2 [Padrão ▾]  │ │ 4 de 6 prontos  ▓▓▓▓░░          │
│               Salva ao escolher.                           │ │ ✓ Matriz e cortes               │
│ 2 Infográficos ┌ Outras Etapas ─────────── Abrir prévia ↗┐│ │ ✓ Template do F1                │
│               │ Habilidade [……]  ☑ Habil. ☑ Progr. ☑ Taref.││ │ ✓ Template do F2                │
│               │ Referencial: 12 linhas · Tarefas 1 a 4    ││ │ ○ Infográficos → falta a hab…   │
│ 3 Capa        [miniatura] [ Enviar a capa … ]              │ │ ○ Capa → Falta a capa           │
│ 4 Textos      ┌ Seções ─────┐ ┌ Introdução · F1 ─────────┐ │ │ ✓ Dados do projeto              │
│               │ ▸ Introdução│ │ Título: Análise de …     │ │ │ [Validar revista] (desligado)   │
│               │   Fechamento│ │ [texto, salva ao sair]   │ │ │ Resolva as pendências acima…    │
│               │   Abertura  │ │ [Descartar cópia]        │ │ │ O que mudou para o impresso     │
│               └─────────────┘ └──────────────────────────┘ │ └─────────────────────────────────┘
└────────────────────────────────────────────────────────────┘
```

Abaixo de 64rem (1024 px): uma coluna, com a Situação primeiro (o resumo antes dos passos) e sem ficar fixa. Em 390 px: a lista de seções vira uma faixa acima do painel; botões do cabeçalho quebram em linha.

## Critérios de aceite

1. A revista abre com os quatro passos e a coluna Situação; cada pendência aparece uma vez só, como link, sem faixa vermelha.
2. Impresso vê tudo sem campos de gravar e com o aviso de só leitura; qualquer POST dele é 403.
3. Escolher os dois templates libera a parte Textos; sem eles, o estado vazio neutro.
4. Trocar o template de um fascículo com cópias abre o modal com a frase; sem a frase certa, não troca.
5. Soltar uma capa ou a imagem de uma tarefa mostra a miniatura e "Salvo às"; imagem acima de 5 MB ou fora de PNG/JPG/WebP mostra o erro e não grava.
11. Preencher o infográfico (ou desligar os passos sem dado) zera a pendência `infografico`; desligar um passo esconde o bloco na ficha e o tira da prévia.
6. Sair do texto alterado cria a cópia só dessa seção; texto igual ao template não cria; texto inválido mostra o erro e não grava.
7. Seção desatualizada mostra o diff, "Manter meu texto" e "Descartar cópia".
8. "Validar revista" fica desligado com o motivo enquanto houver pendência; pronto, grava com o hash da página; com hash velho, recusa com a mensagem.
9. `acao=nome` responde 400; o texto "Editar nome" não aparece (o link é "Editar o nome do projeto").
10. Revista arquivada: só leitura com a foto; sem bloqueio; POST 403. Outra pessoa com o projeto aberto: só leitura. Anônimo: login das telas B (`/conta/entrar/`).

## Referências técnicas

- Requisitos: `docs/telas/inventario.md` T20, T21; D-074, D-089, D-104, D-108, D-115, D-116, D-117, D-140, D-170, D-171, D-174 e as do plano de UX (D-195 em diante).
- Regra: `app/nucleo/revista.py` (extraída de `admin/revista.py`), `app/nucleo/infografico.py`, `servicos/validacao.py`, `servicos/arquivos.py`, `servicos/empacotar.py`, `ui_bloqueio.com_bloqueio`, `ui_autosave.responder_campo`.
- View: `app/nucleo/urls/ui_revista.py` (`revista`, `_template`, `_arquivo`, `_infografico`, `_texto`, `_salvar_secao`, `_validar`, `zip_`, `PASSOS`).
- Templates: `templates/ui/revista/revista.html`, `templates/ui/parciais/revista_{infograficos,arquivos,textos,secoes,secao,secao_estado,situacao}.html`; CSS `static/ui/telas/revista.css`.
- Testes: `app/nucleo/tests/test_ui_revista.py`; `app/e2e/tests/revista-textos.spec.ts`, `app/e2e/tests/infografico.spec.ts`.
- Admin equivalente: `admin/revista.py`, `templates/nucleo/revista_change_form.html`.
