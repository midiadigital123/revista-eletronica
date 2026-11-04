# Ficha: Templates (lista, editor, impacto)

Telas T12 (lista), T13 (editor) e T14 (impacto). Endereços: `/ui/templates/<ano>/`, `/ui/templates/editar/<id>/`.

## Objetivo

Manter os textos-modelo das revistas (fascículos F1 e F2) de cada ano. Desde o U9b, o editor é por seção: o id de cada seção (`introducao`, `passo1`, `dlg-p2`) é estrutura do fascículo, aparece como um rótulo travado ("Introdução", "Passo 1", "Diálogo do passo 2") e nunca como texto editável. Quem edita escreve título e texto de uma seção por vez, vê na hora como fica e, antes de gravar, sabe quais revistas ativas mudam. Gravar cria uma versão nova; a anterior fica guardada. O formato gravado não mudou: o servidor monta o mesmo Markdown `## id`.

## Quem usa

| Perfil | O que pode |
|---|---|
| Pedagógica, Mídias Digitais, Admin | ver e editar (nome e texto) |
| Impresso | só ver (lista, texto e pré-visualização) |
| Sem permissão de templates | nada: a página responde "acesso negado" |
| Sem login | vai para o login e volta para a página |

## Jornada

- **Antes:** Abrir ano (os templates chegam copiados do ano anterior) ou a carga inicial.
- **Depois:** "Atribuir template…" na Lista de Projetos, Revista (templates e textos por seção), Preview e Painel. O link "usado por N" leva ao Painel filtrado por aquele template.

## Dados mostrados

- **Lista:** por ano e fascículo (abas Textos F1 / Textos F2, com a contagem), cada template com nome, componente, número da versão atual (ou "sem texto") e o uso nas revistas ativas: "usado por N" (link para o Painel filtrado) e, se houver, "(M com cópia de seção)".
- **Editor:** nome; componente, fascículo e ano (não editáveis); versão atual com data e autor. Três colunas:
  - **Índice** das seções, com o status de cada uma ("N erro(s)" ou ✓). Clicar troca a seção aberta: uma seção por vez (abre a primeira com erro, ou a primeira).
  - **Seção aberta:** o rótulo travado (chip), "Título" (uma linha) e "Texto", com a mini-barra **N** (negrito), *I* (itálico), lista e "{ } Variável" (insere a variável escolhida no campo em que o cursor estava, título ou texto). Os erros da validação aparecem na seção certa.
  - **Pré-visualização** da seção aberta: título e texto renderizados, sem `## id`, com as variáveis em amarelo e o resultado da validação.
- **Estrutura por fascículo:** no F1, Introdução e Fechamento, fixas (sem adicionar nem remover). No F2, Abertura e Passo 1 fixas; "+ Adicionar passo" cria o passo seguinte (maior + 1, nunca reaproveita um número removido) e "+ Adicionar diálogo" cria o diálogo do passo escolhido no select ao lado. Seção não fixa tem "Remover seção". A ordem segue a do fascículo; não se arrasta.
- **Impacto:** número da versão que será criada; para cada revista ativa que usa o template: seções com cópia (não mudam), se já tem foto do impresso, ids que faltariam no SVG (só F2 com SVG).

## Dados gravados

- Nome do template.
- Texto: uma versão nova (N+1), com autor e data. Nunca altera nem apaga versões antigas.
- Nada mais: ano, componente e fascículo não mudam (as revistas dependem deles).

## Ações

| Ação | Onde | Resultado |
|---|---|---|
| Trocar ano / aba | lista | recarrega a lista (a aba fica na URL) |
| Abrir template | lista | editor |
| Novo template | lista (com permissão de criar) | formulário do admin (`/admin/nucleo/template/add/`; tela B no S7) |
| Escolher seção no índice | editor | mostra só aquela seção e a prévia dela |
| N / I / lista / { } Variável | mini-barra da seção | aplica o formato ou insere a variável no campo com o cursor e atualiza a pré-visualização |
| + Adicionar passo / + Adicionar diálogo / Remover seção | editor (só F2) | muda a estrutura na tela; nada grava até o Salvar (recarregar desfaz) |
| Digitar | editor | pré-visualização atualiza 400 ms depois de parar |
| Salvar | editor | texto igual: grava só o nome; texto mudado e válido: tela de impacto; inválido: erros na seção certa |
| Confirmar e criar versão N | impacto | grava, volta ao editor com "Versão N criada." |
| Voltar e editar | impacto | volta ao editor com o texto pendente, nada gravado |

## Estados

- **Sem ano aberto:** aviso "Nenhum ano aberto. Abra um ano para ter templates." (link para `/ui/anos/` com `abrir_ano`; sem ela, "Peça a um administrador para abrir o ano.")
- **Aba vazia:** "Nenhum template F2 neste ano" + como eles chegam + botão Novo template (com permissão).
- **Template sem texto:** badge "sem texto" na lista; editor diz "Ainda sem texto." e já abre com as seções fixas do fascículo, vazias.
- **Texto inválido (ao vivo):** caixa vermelha "Ainda não dá para salvar:" + lista dos problemas.
- **Texto válido (ao vivo):** "Texto válido para o fascículo."
- **Só leitura por perfil:** aviso amarelo, campos `readonly`, sem mini-barra, sem adicionar ou remover seção e sem Salvar; o índice e a pré-visualização continuam.
- **Alteração não salva:** a barra troca o texto por "Alterações não salvas." e o navegador avisa ao sair só quando há alteração de verdade.
- **Só leitura por bloqueio:** aviso "Somente leitura: Ana está editando (bloqueio até 14:32:10…). Recarregue para tentar editar."
- **Impacto sem revistas:** "Nenhuma revista ativa usa este template" + "Confirmar cria a versão sem mudar nenhuma revista agora."
- **Sucesso:** mensagem verde no editor.

## Mensagens exatas

- "Nada foi gravado: corrija os erros marcados."
- "Nome salvo. O texto é igual ao da versão atual, então nenhuma versão nova foi criada."
- "Versão N criada."
- "Voltou da tela de impacto: nada foi gravado. Revise o texto e salve de novo."
- "Não salvo: o texto ou a versão atual mudou desde a tela de impacto. Confira o impacto de novo e confirme."
- "Não salvo: você perdeu o bloqueio de edição (outra pessoa ou aba abriu esta página). Recarregue e refaça a alteração."
- "Só leitura: seu perfil vê os templates, mas não altera. Para editar, peça a permissão de templates a um administrador."
- "Texto grande demais: o limite é 100.000 caracteres. Encurte o texto para ver a pré-visualização."
- Erros de validação: os do validador do texto (seção obrigatória faltando, título vazio, `#` no corpo, links, imagens, HTML, variável fora da lista), cada um na sua seção.
- Seção fora do fascículo no envio (id adulterado): 422 "Seção não prevista neste fascículo: <id>. Recarregue o editor."

## Permissões

- Ver: ver ou alterar template. Gravar: alterar template **e** criar versão de template (igual ao admin).
- Sem permissão de gravar, todo POST do editor responde 403.
- Um editor por template: abrir o editor trava o template enquanto a página estiver aberta; o segundo vê só leitura. O POST confere a trava na mesma transação da gravação.

## HTMX

- Só a pré-visualização: o form do editor faz `hx-post` para `.../previa/` com `hx-trigger="input delay:400ms"`, `hx-target="#previa"`, `hx-sync="this:replace"` (resposta velha descartada) e um indicador girando. A resposta troca também o índice e os erros de cada seção (`hx-swap-oob`).
- O estado local (seção aberta, mini-barra, adicionar e remover seção, aviso de saída) é do componente Alpine `editorSecoes` (`static/ui/componentes/editor-secoes.js`). O POST manda `secao-N-id` (oculto, conferido no servidor), `secao-N-titulo` e `secao-N-corpo`.
- A primeira pré-visualização vem pronta do servidor (funciona sem JS e no só leitura).
- Pré-visualização sem login ou permissão: 403 (o HTMX não troca o alvo e mostra o toast "sem permissão ou a sessão expirou").
- Lista, editor e impacto são páginas inteiras (o editor precisa da trava, que só a página adquire).

## Wireframes

Lista (1440):
```
Revista Eletrônica  [2026 ▾]  Painel Projetos Matrizes [Templates] Impresso                 Ana  Admin  Sair
──────────────────────────────────────────────────────────────────────────────────────────────────────
Templates                                                                            [+ Novo template]
Textos-modelo das revistas, por fascículo. Editar um texto cria uma versão nova; ...
 Textos F1 (2)   Textos F2 (2)
 ─────────────   ━━━━━━━━━━━━━
 Template   Componente              Versão   Uso nas revistas ativas
 Padrão     LP Língua Portuguesa      v1     usado por 2 (1 com cópia de seção)
 Padrão     MT Matemática             v1     usado por 2
```

Editor (1440; em 390 as colunas empilham: índice, seção, pré-visualização):
```
‹ Templates F2
Padrão
Língua Portuguesa (LP), fascículo F2, 2026. Versão atual: 1, de 30/10/2026 13:35.
[! Só leitura: ...]                       (quando for o caso)
Nome  [Padrão                    ]
┌ Seções ─────────┐ ┌ [Passo 1]                    Remover seção ┐ ┌ Pré-visualização  ◌ ──────┐
│ Abertura      ✓ │ │ Título [Leia o texto            ]          │ │ ✓ Texto válido para o      │
│▸Passo 1       ✓ │ │ Texto  N  I  ≡  [Variável ▾] [{ } Variável] │ │   fascículo.               │
│ Diálogo do      │ │ ┌───────────────────────────────────────┐ │ │ Leia o texto               │
│ passo 2  1 erro │ │ │ Observe {{adjetivo_patrio_ms}} …      │ │ │ Observe [goiano] …         │
└─────────────────┘ │ └───────────────────────────────────────┘ │ └────────────────────────────┘
                    │ [+ Adicionar passo] [Passo 2 ▾][+ Adicionar diálogo]
                    └──────────────────────────────────────────────┘
──────────────────────────────────────────────────────────────────────────────────────────────────────
Alterações não salvas.                                                                       [Salvar]
```

Impacto:
```
Confira o impacto antes de criar a versão 2
Padrão: Língua Portuguesa (LP), fascículo F2, 2026. Nada foi gravado ainda.
(i) O texto passou na validação. Confirmar cria a versão 2; a versão 1 fica guardada. ...
2 revistas ativas usam este template
 Revista        Seções com cópia   Impresso                   Ids que faltariam no SVG
▌Projeto GO LP  nenhuma            não                        [SVG incompleto: passo2]
▌Projeto PE LP  passo1             [Já tem foto do impresso]  nenhum
──────────────────────────────────────────────────────────────────────────────────────────────────────
Voltar e editar não grava nada e mantém o seu texto.          [Voltar e editar] [Confirmar e criar versão 2]
```

## Critérios de aceite

1. Com permissão, a lista mostra as abas F1/F2 com contagem, versão e "usado por N (M com cópia de seção)" com link para o Painel filtrado.
2. Ano sem templates no fascículo mostra o estado vazio.
3. O editor mostra uma seção por vez, com o rótulo travado, Título e Texto; nenhum campo editável tem `## `. A pré-visualização (variáveis em amarelo) atualiza em ~400 ms, e o erro vai para a seção certa no índice. "{ } Variável" insere `{{nome_parceiro}}` no campo com o cursor. No F2, "+ Adicionar passo" numera em sequência; id fora do fascículo no POST dá 422. A ida e a volta (seções → Markdown) preservam os seeds byte a byte.
4. Texto mudado e válido abre o impacto sem gravar; "Confirmar e criar versão N" cria a versão N com o autor e libera a trava; "Voltar e editar" não grava e mantém o texto.
5. Assinatura adulterada, texto trocado depois do impacto ou versão-base mudada reabrem o impacto com aviso, sem gravar.
6. Texto inválido: 200 com "Nada foi gravado: corrija os erros marcados." e o campo marcado; nada gravado.
7. Texto igual: grava só o nome, sem versão nova.
8. Impresso vê tudo em só leitura; POST dele é 403. Sem permissão de ver: 403. Sem login: vai ao login.
9. Com outro usuário editando: só leitura com o aviso de quem edita; POST com a sessão alheia não grava e avisa "perdeu o bloqueio".
10. O admin de templates continua funcionando igual (mesmas regras, mesmos testes).

## Referências técnicas

- Rotas e views: `app/nucleo/urls/ui_templates.py` (`secoes_do_post`, `_contexto_secoes`). Templates: `templates/ui/templates/{lista,editar,impacto}.html`, `templates/ui/parciais/templates_{previa,secao,indice,secao_erros}.html`. JS: `static/ui/componentes/editor-secoes.js` (`editorSecoes`). CSS: `static/ui/telas/templates.css`.
- Regra comum (extraída do admin): `app/nucleo/templates_texto.py` (`com_uso`, `impacto`, `assinatura`/`assinar`/`ler_assinatura`, `criar_versao`, `previa`, e do U9b `secoes_para_form`, `form_para_corpo`, `secoes_permitidas`, `id_permitido`, `rotulo`, `proximo_passo`, `previa_secoes`); o form `TemplateForm` segue em `admin/templates.py` e é reaproveitado.
- Bloqueio: `nucleo/ui_bloqueio.com_bloqueio` + `ui/_componentes/bloqueio.html`. Envio único do impacto: `static/nucleo/template_editor.js` (`data-envio-unico`).
- Decisões: D-076, D-098, D-099, D-102, D-105, D-109, D-115, D-118, D-123, D-125, D-162, D-163, D-183, D-186.
- Testes: `app/nucleo/tests/test_ui_templates.py`; `app/e2e/tests/templates-editor.spec.ts`.
