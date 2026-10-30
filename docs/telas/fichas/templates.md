# Ficha: Templates (lista, editor, impacto)

Telas T12 (lista), T13 (editor) e T14 (impacto). Endereços: `/ui/templates/<ano>/`, `/ui/templates/editar/<id>/`.

## Objetivo

Manter os textos-modelo das revistas (fascículos F1 e F2) de cada ano. Quem edita escreve em Markdown restrito, vê na hora como o texto fica e, antes de gravar, sabe quais revistas ativas mudam. Gravar cria uma versão nova; a anterior fica guardada.

## Quem usa

| Perfil | O que pode |
|---|---|
| Pedagógica, Mídias Digitais, Admin | ver e editar (nome e texto) |
| Impresso | só ver (lista, texto e pré-visualização) |
| Sem permissão de templates | nada: a página responde "acesso negado" |
| Sem login | vai para o login e volta para a página |

## Jornada

- **Antes:** Abrir ano (os templates chegam copiados do ano anterior) ou a carga inicial.
- **Depois:** Escolher template F1/F2 por revista (lote), Revista (textos por seção), Preview e Painel. O link "usado por N" leva ao Painel filtrado por aquele template.

## Dados mostrados

- **Lista:** por ano e fascículo (abas Textos F1 / Textos F2, com a contagem), cada template com nome, componente, número da versão atual (ou "sem texto") e o uso nas revistas ativas: "usado por N" e, se houver, "(M com cópia de seção)". Abas Matrizes e Variáveis levam às telas do ano.
- **Editor:** nome; componente, fascículo e ano (não editáveis); versão atual com data e autor; texto em Markdown; pré-visualização com as variáveis em amarelo e o resultado da validação.
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
| Novo template | lista (com permissão de criar) | formulário do admin |
| Inserir variável | editor | põe a variável escolhida no cursor e atualiza a pré-visualização |
| Digitar | editor | pré-visualização atualiza 400 ms depois de parar |
| Salvar | editor | texto igual: grava só o nome; texto mudado e válido: tela de impacto; inválido: erros |
| Confirmar e criar versão N | impacto | grava, volta ao editor com "Versão N criada." |
| Voltar e editar | impacto | volta ao editor com o texto pendente, nada gravado |

## Estados

- **Sem ano aberto:** aviso "Nenhum ano aberto. Abra um ano no admin para ter templates."
- **Aba vazia:** "Nenhum template F2 neste ano" + como eles chegam + botão Novo template (com permissão).
- **Template sem texto:** badge "sem texto" na lista; editor diz "Ainda sem texto."; pré-visualização "Nenhuma seção ainda. Comece uma com `## id` e o título na linha seguinte."
- **Texto inválido (ao vivo):** caixa vermelha "Ainda não dá para salvar:" + lista dos problemas.
- **Texto válido (ao vivo):** "Texto válido para o fascículo."
- **Só leitura por perfil:** aviso amarelo, campos `readonly`, sem Inserir variável e sem Salvar; a pré-visualização continua.
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
- Erros de validação: os do validador do texto (seção obrigatória faltando, `#` no corpo, links, imagens, HTML, variável fora da lista).

## Permissões

- Ver: ver ou alterar template. Gravar: alterar template **e** criar versão de template (igual ao admin).
- Sem permissão de gravar, todo POST do editor responde 403.
- Um editor por template: abrir o editor trava o template enquanto a página estiver aberta; o segundo vê só leitura. O POST confere a trava na mesma transação da gravação.

## HTMX

- Só a pré-visualização: o `textarea` faz `hx-post` para `.../previa/` com `hx-trigger="input changed delay:400ms"`, `hx-target="#previa"`, `hx-sync="this:replace"` (resposta velha descartada) e um indicador girando.
- A primeira pré-visualização vem pronta do servidor (funciona sem JS e no só leitura).
- Pré-visualização sem login ou permissão: 403 (o HTMX não troca o alvo e mostra o toast "sem permissão ou a sessão expirou").
- Lista, editor e impacto são páginas inteiras (o editor precisa da trava, que só a página adquire).

## Wireframes

Lista (1440):
```
Revista Eletrônica  Painel Cortes Variáveis Matrizes [Templates] Revistas Impresso    Ana  Admin  Sair
──────────────────────────────────────────────────────────────────────────────────────────────────────
Templates                                                                            [+ Novo template]
Textos-modelo das revistas, por fascículo. Editar um texto cria uma versão nova; ...
[2026|2025]
 Textos F1 (2)   Textos F2 (2)   Matrizes   Variáveis
 ─────────────   ━━━━━━━━━━━━━
 Template   Componente              Versão   Uso nas revistas ativas
 Padrão     LP Língua Portuguesa      v1     usado por 2 (1 com cópia de seção)
 Padrão     MT Matemática             v1     usado por 2
```

Editor (1440; em 390 as colunas empilham: texto, depois pré-visualização):
```
Padrão                                                                              < Templates F2
Língua Portuguesa (LP), fascículo F2, 2026. Versão atual: 1, de 30/10/2026 13:35.
[! Só leitura: ...]                       (quando for o caso)
Nome  [Padrão                    ]
Texto        [Nome do parceiro v][{} Inserir variável] │ Pré-visualização  variáveis em [amarelo]  ◌
┌──────────────────────────────────────┐              │ ✓ Texto válido para o fascículo.
│## abertura                            │              │ ## abertura
│Abertura                               │              │ Abertura
│                                       │              │ Bem-vindo.
│Bem-vindo.  ...                        │              │ ┄┄┄┄┄┄┄┄┄
└──────────────────────────────────────┘              │ ## passo1 ... [{{adjetivo...}}]
Cada seção começa com ## id ...
──────────────────────────────────────────────────────────────────────────────────────────────────────
Alteração não salva.                                                                         [Salvar]
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
3. O editor mostra o texto atual, a pré-visualização com variáveis em amarelo e "Inserir variável"; digitar atualiza a pré-visualização em ~400 ms, com os erros de validação.
4. Texto mudado e válido abre o impacto sem gravar; "Confirmar e criar versão N" cria a versão N com o autor e libera a trava; "Voltar e editar" não grava e mantém o texto.
5. Assinatura adulterada, texto trocado depois do impacto ou versão-base mudada reabrem o impacto com aviso, sem gravar.
6. Texto inválido: 200 com "Nada foi gravado: corrija os erros marcados." e o campo marcado; nada gravado.
7. Texto igual: grava só o nome, sem versão nova.
8. Impresso vê tudo em só leitura; POST dele é 403. Sem permissão de ver: 403. Sem login: vai ao login.
9. Com outro usuário editando: só leitura com o aviso de quem edita; POST com a sessão alheia não grava e avisa "perdeu o bloqueio".
10. O admin de templates continua funcionando igual (mesmas regras, mesmos testes).

## Referências técnicas

- Rotas e views: `app/nucleo/urls/ui_templates.py`. Templates: `templates/ui/templates/{lista,editar,impacto}.html`, `templates/ui/parciais/templates_previa.html`. CSS: `static/ui/telas/templates.css`.
- Regra comum (extraída do admin): `app/nucleo/templates_texto.py` (`com_uso`, `impacto`, `assinatura`/`assinar`/`ler_assinatura`, `criar_versao`, `previa`); o form `TemplateForm` segue em `admin/templates.py` e é reaproveitado.
- Bloqueio: `nucleo/ui_bloqueio.com_bloqueio` + `ui/_componentes/bloqueio.html`. Envio único do impacto: `static/nucleo/template_editor.js` (`data-envio-unico`).
- Decisões: D-076, D-098, D-099, D-102, D-105, D-109, D-115, D-118, D-123, D-125, D-162, D-163, D-183, D-186.
- Testes: `app/nucleo/tests/test_ui_templates.py`.
