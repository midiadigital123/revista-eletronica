# Ficha: Variáveis (planilha projetos × variáveis)

Endereço: `/ui/projeto/ano/<ano>/variaveis/` (rota `ui_variaveis`), a aba Variáveis do hub Projetos. O endereço antigo `/ui/variaveis/<ano>/` (e `/ui/variaveis/`) redireciona para cá (302); o POST antigo continua gravando.

## Objetivo

Preencher, numa só tela, os valores que os textos dos templates usam por projeto (ISSN, adjetivo pátrio, preposições, nomes do programa, da regional e da secretaria, nomes dos padrões). Uma linha por projeto ativo do ano, uma coluna por variável. Quem preenche vê, ao lado, o que cada variável significa e em quais templates ela aparece, para saber o que vale a pena preencher primeiro.

## Quem usa

| Perfil | O que faz |
|---|---|
| Pedagógica, Mídia, Administração (editam projetos) | Veem e editam todas as células; copiam valores do ano anterior por projeto. |
| Impresso (só vê projetos) | Vê a planilha inteira, com as células travadas e sem botões de gravar. |
| Sem acesso a projetos | Recebe "sem permissão" (403). |
| Sem login | Vai para o login e volta para a planilha depois de entrar. |

## Na jornada

- **Antes:** os cortes do ano criam os projetos; a escolha de matriz e de templates define quais textos usam quais variáveis.
- **Depois:** com as variáveis preenchidas, a revista sai sem faixa vermelha de "variável vazia"; a pessoa segue para o Painel do ano e para a revisão das revistas.
- Quem prefere editar um projeto por vez usa a aba Dados do projeto; as duas gravam pela mesma rota (`ui_projeto_campo`), então o valor é um só.

## Dados mostrados

- Cabeçalho do hub Projetos com as abas Lista · Cortes · Variáveis; o ano troca pelo seletor do cabeçalho, mantendo a aba.
- Linha de ações: "Valores que os textos dos templates usam em cada projeto do ano." e o status do salvamento (só para quem edita).
- Planilha: 1ª coluna fixa com o parceiro, o nome do projeto e o botão "Copiar de <ano anterior>"; demais colunas são as 24 variáveis preenchidas à mão, agrupadas como no formulário do projeto (Coleção, Adjetivo pátrio, Parceiro, Programa, Regional e secretaria, Padrões de desempenho). O cabeçalho do grupo e o da variável ficam fixos ao rolar.
- Cada cabeçalho de variável mostra a descrição ao passar o mouse. Sob o grupo, o rótulo vem sem o nome do grupo ("masc. sing." sob "Adjetivo pátrio"); o rótulo completo fica no título e no nome acessível.
- Padrão 1 a 5 vazios mostram, em cinza dentro da célula, o nome que vale no ano ("padrão do ano: Abaixo do básico").
- Legenda recolhível "O que é cada variável": nome entre chaves duplas, descrição e onde aparece (templates do ano, pela última versão de cada um; nos padrões, também a escala do F1). As três automáticas (parceiro, projeto, ano) aparecem marcadas como "do cadastro".
- Projetos arquivados não aparecem (são só leitura no projeto).

## Dados gravados

- Uma célula por vez: sair de uma célula alterada grava só ela, pela rota da ficha do projeto (`ui_projeto_campo`). Não há "Salvar variáveis".
- A célula grava com o bloqueio do projeto só durante a escrita. Projeto aberto por outra pessoa (ou arquivado no meio do caminho): a célula não grava e responde 409 com o motivo.
- A célula não confere o valor original: se duas pessoas mudam a mesma célula, vale a última gravação.
- Se a célula muda o texto de uma revista validada, o modal de impacto lista as revistas antes de gravar.
- "Copiar de <ano anterior>": preenche só as variáveis vazias do projeto com as do projeto do mesmo parceiro no ano anterior (mesmo arquivado). Grava na hora.

## Ações

| Ação | Quem | Resultado |
|---|---|---|
| Trocar o ano (seletor do cabeçalho) | todos | abre a planilha do ano |
| Sair de uma célula alterada | quem edita | grava só aquela célula; o status mostra "Salvo às HH:MM" |
| "Copiar de <ano anterior>" na linha | quem edita | grava e troca só aquela linha, sem recarregar; as outras linhas não mudam |
| Abrir o nome do parceiro | todos | vai à página do projeto |
| Abrir "O que é cada variável" | todos | mostra a legenda |

## Estados

- **Ano sem projeto ativo:** estado vazio "Nenhum projeto ativo neste ano" + "Os projetos nascem quando os cortes do parceiro são lançados." + botão "Abrir cortes".
- **Erro de preenchimento (mais de 200 caracteres, 422):** a célula não grava; o erro aparece embaixo dela e o status diz "Não salvo: corrija o campo marcado". O que foi digitado continua na célula.
- **Impacto:** o modal "Salvar “<variável>” tira o “Validado” de N revista(s)"; Cancelar ou Esc volta o valor gravado e o foco.
- **Projeto em edição por outra pessoa ou arquivado (409):** a célula não grava e a mensagem diz quem está editando. Hoje a planilha inteira passa a só leitura até recarregar (o mesmo tratamento do bloqueio perdido).
- **Só leitura (sem permissão):** aviso de só leitura no topo; células travadas; sem "Copiar" e sem status.
- **Arquivado:** fora da planilha.
- **Sem conexão:** "Não salvo: sem conexão · Tentar de novo"; só aí (ou com envio pendente) o navegador avisa ao sair.
- **Erro de rede/servidor ao copiar:** aviso flutuante (toast) com causa e correção; a linha não muda.

## Mensagens exatas

- Célula travada: "Não salvo: projeto em edição por <nome>. Tente de novo quando a outra pessoa fechar o projeto." (ou "…: projeto arquivado. …")
- Erro de validação (célula): "<rótulo>: Certifique-se de que o valor tenha no máximo 200 caracteres (ele possui 201)."
- POST antigo da planilha inteira (sem JS): "Variáveis salvas em N projeto(s)." · "Pulados: …" · "Nada foi gravado: corrija os erros marcados."
- Só leitura: "Só leitura: seu perfil vê as variáveis, mas não altera. Para editar, peça a permissão de projetos a um administrador."
- Copiar, sucesso: "Projeto GO: copiado de 2025: issn, nome_programa."
- Copiar, nada a copiar: "Projeto GO: nada a copiar (as variáveis vazias também estão vazias em 2025)."
- Copiar, sem ano anterior: "Projeto PE: não há projeto do parceiro em 2025; nada mudou."
- Copiar, projeto travado: "Projeto GO: não copiado (projeto em edição por Ana Souza)."
- Copiar, projeto sumiu/arquivado ou de outro ano: "Projeto não encontrado ou arquivado." (a página recarrega; nada é gravado).

## Permissões

- Login obrigatório; sem login vai ao login do admin.
- Ver: permissão de ver ou de alterar projetos; sem ela, 403.
- Gravar e copiar: permissão de alterar projetos; sem ela, só leitura e qualquer envio dá 403.
- Mesmas regras da aba Variáveis do admin (a regra é a mesma, compartilhada).

## Interações (Alpine e HTMX)

- A planilha é um `<form x-data="campoAuto">`; cada `<tbody>` de projeto leva `data-url` (rota `ui_projeto_campo`) e `data-prefixo` (`form-<i>-`), que o autosave tira do nome do campo. Protocolo em [`design-system.md`](../design-system.md) §5.
- "Copiar de <ano anterior>": `hx-post` sem enviar a planilha, troca só a linha (`outerHTML` no `<tbody>` do projeto; `id` fixo no botão para o foco voltar a ele) e as mensagens (fora do alvo). Sem JS, o mesmo botão envia um formulário comum e a página recarrega.
- Projeto que sumiu ou foi arquivado no meio da cópia: a resposta pede recarga da página inteira (`HX-Refresh`).

## Wireframe

```
┌─ Revista Eletrônica  [2026 ▾]  Painel  [Projetos]  Matrizes  Templates  Impresso                 Ana         Sair ┐
│                                                                                                              │
│ Projetos                                                                                                     │
│  Lista   Cortes   Variáveis                                                                                  │
│                   ━━━━━━━━━                                                                                  │
│ Valores que os textos dos templates usam em cada projeto do ano.                       ✓ Salvo às 10:15      │
│ (só leitura: aviso amarelo aqui)                                                                             │
│ Cada célula salva sozinha ao sair dela; só ela é gravada. Padrões vazios usam o nome do ano, em cinza.        │
│ ┌──────────────────────┬────────────┬──────────────────────────────────────┬──────────────── … ─────────────┐ │
│ │ Projeto              │ Coleção    │ Adjetivo pátrio                      │ Parceiro                       │ │
│ │                      │ ISSN       │ masc. sing. │ fem. sing. │ …          │ do/da/de │ no/na/em │ Redes   │ │
│ ├──────────────────────┼────────────┼─────────────┼────────────┼───────────┼──────────┼──────────┼─────────┤ │
│ │ GO                   │ [1234-5678]│ [goiano   ] │ [goiana  ] │ …          │ [de    ] │ [em    ] │ [     ] │ │
│ │ Avalia GO 2026       │            │             │            │            │          │          │         │ │
│ │ (⟲ Copiar de 2025)   │            │             │            │            │          │          │         │ │
│ ├──────────────────────┼────────────┼─────────────┼────────────┼───────────┼──────────┼──────────┼─────────┤ │
│ │ PE …                 │            │ [xxxxxxxx…]!│            │                                           │ │
│ │  • Adjetivo pátrio masc. sing.: no máximo 200 caracteres …  (linha de erro, vermelha)                   │ │
│ └──────────────────────┴────────────┴─────────────┴────────────┴─────────────────────────────────────────┘ │
│ ▸ O que é cada variável  (legenda recolhível: {{nome}} · descrição · onde aparece)                             │
└──────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

No celular (390 px): mesma planilha com rolagem lateral dentro da caixa, 1ª coluna estreita e fixa.

## Critérios de aceite

1. Com permissão de alterar projetos, a aba abre com uma linha por projeto ativo, as 24 colunas e o status do salvamento; não há botão "Salvar variáveis". `/ui/variaveis/2026/` redireciona para cá.
2. Padrão 1 a 5 vazios mostram "padrão do ano: <nome>"; a legenda mostra onde cada variável aparece e "escala do F1" nos padrões.
3. Digitar numa célula e sair dela grava só ela e mostra "Salvo às"; recarregar não abre diálogo. Com a rede caída, "Não salvo · Tentar de novo" e o aviso ao sair.
4. Mais de 200 caracteres: 422, a célula fica marcada e nada grava.
5. Projeto aberto por outra pessoa: a célula não grava (409) e a mensagem diz quem está editando.
6. Sem permissão de alterar: aviso de só leitura, células travadas, sem botões; envio dá 403. Sem permissão de ver: 403. Sem login: vai ao login.
7. "Copiar de <ano anterior>" pelo HTMX devolve só a linha com os valores novos e a mensagem; sem JS, recarrega a página com a mesma mensagem. Só preenche as vazias.
8. Ano sem projetos mostra o estado vazio com o caminho para os cortes.

## Referências técnicas

- Regra: `app/nucleo/planilha_variaveis.py` (extraída de `admin/variaveis.py`, que passa a importá-la).
- Tela: `app/nucleo/urls/ui_variaveis.py` (`variaveis`, `antiga`, `copiar_linha`), `templates/ui/variaveis/pagina.html`, `templates/ui/parciais/variaveis_linha.html`, `static/ui/telas/variaveis.css`. Autosave: `app/nucleo/urls/ui_projeto.py` (`campo`, sem a sessão de bloqueio).
- Testes: `app/nucleo/tests/test_ui_variaveis.py`, `test_ui_autosave.py`; `app/e2e/tests/autosave.spec.ts`.
- Decisões: D-093, D-100, D-107, D-119, D-121, D-164, D-167, D-172, D-173, D-175, D-183, D-186. Inventário: T17.
