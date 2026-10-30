# Ficha: Variáveis (planilha projetos × variáveis)

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
- Quem prefere editar um projeto por vez continua usando o formulário do projeto; os valores são os mesmos.

## Dados mostrados

- Seletor de ano (os anos cadastrados, o mais recente primeiro).
- Planilha: 1ª coluna fixa com o parceiro, o nome do projeto e o botão "Copiar de <ano anterior>"; demais colunas são as 24 variáveis preenchidas à mão, agrupadas como no formulário do projeto (Coleção, Adjetivo pátrio, Parceiro, Programa, Regional e secretaria, Padrões de desempenho). O cabeçalho do grupo e o da variável ficam fixos ao rolar.
- Cada cabeçalho de variável mostra a descrição ao passar o mouse. Sob o grupo, o rótulo vem sem o nome do grupo ("masc. sing." sob "Adjetivo pátrio"); o rótulo completo fica no título e no nome acessível.
- Padrão 1 a 5 vazios mostram, em cinza dentro da célula, o nome que vale no ano ("padrão do ano: Abaixo do básico").
- Legenda recolhível "O que é cada variável": nome entre chaves duplas, descrição e onde aparece (templates do ano, pela última versão de cada um; nos padrões, também a escala do F1). As três automáticas (parceiro, projeto, ano) aparecem marcadas como "do cadastro".
- Projetos arquivados não aparecem (são só leitura no projeto).

## Dados gravados

- Só as células que a pessoa mudou, projeto a projeto. Coluna que outra pessoa mudou depois que a página abriu não é sobrescrita.
- Cada projeto é gravado com o bloqueio de edição dele. Projeto aberto por outra pessoa (ou arquivado no meio do caminho) é pulado e listado; os outros gravam.
- "Copiar de <ano anterior>": preenche só as variáveis vazias do projeto com as do projeto do mesmo parceiro no ano anterior (mesmo arquivado). Grava na hora.

## Ações

| Ação | Quem | Resultado |
|---|---|---|
| Trocar o ano | todos | Abre a planilha do ano (link; funciona sem JS). |
| Editar células e "Salvar variáveis" | quem edita | Grava as alteradas e volta à planilha com a mensagem. |
| "Copiar de <ano anterior>" na linha | quem edita | Troca só aquela linha, sem recarregar; as edições não salvas nas outras linhas continuam. Se a própria linha tem edição não salva, pede confirmação antes ("Esta linha tem alteração não salva; copiar descarta o que você digitou nela. Continuar?"). |
| Abrir o nome do projeto | todos | Vai ao formulário do projeto. |
| Abrir "O que é cada variável" | todos | Mostra a legenda. |

## Estados

- **Sem ano cadastrado:** aviso "Nenhum ano aberto. Abra um ano no admin para preencher as variáveis."
- **Ano sem projeto ativo:** estado vazio "Nenhum projeto ativo neste ano" + "Os projetos nascem quando os cortes do parceiro são lançados." + botão "Abrir cortes".
- **Erro de preenchimento (mais de 200 caracteres):** nada grava; a célula fica marcada, a linha mostra o erro abaixo dela e o topo mostra a mensagem geral. O que foi digitado continua nas células.
- **Só leitura (sem permissão):** aviso de só leitura no topo; células travadas; sem botão de salvar nem de copiar.
- **Projeto em edição por outra pessoa:** a planilha abre normalmente; ao salvar, aquele projeto é pulado e listado no aviso amarelo.
- **Arquivado:** fora da planilha; se for arquivado entre abrir e salvar, é pulado e listado.
- **Sucesso:** mensagem verde no topo; contador da barra volta a "Nenhuma alteração."
- **Alterações não salvas:** a barra conta "N projeto(s) com alteração não salva."; células alteradas ficam destacadas; sair da página pede confirmação do navegador.
- **Erro de rede/servidor ao copiar:** aviso flutuante (toast) com causa e correção; a linha não muda.

## Mensagens exatas

- Sucesso: "Variáveis salvas em 3 projeto(s)."
- Pulados: "Pulados: Projeto PE (projeto em edição por Ana Souza); Projeto GO (projeto arquivado)."
- Erro de validação (topo): "Nada foi gravado: corrija os erros marcados."
- Erro de validação (linha): "Adjetivo pátrio masc. sing.: Certifique-se de que o valor tenha no máximo 200 caracteres (ele possui 201)."
- Só leitura: "Só leitura: seu perfil vê as variáveis, mas não altera. Para editar, peça a permissão de projetos a um administrador."
- Copiar, sucesso: "Projeto GO: copiado de 2025: issn, nome_programa."
- Copiar, nada a copiar: "Projeto GO: nada a copiar (as variáveis vazias também estão vazias em 2025)."
- Copiar, sem ano anterior: "Projeto PE: não há projeto do parceiro em 2025; nada mudou."
- Copiar, projeto travado: "Projeto GO: não copiado (projeto em edição por Ana Souza)."
- Copiar, projeto sumiu/arquivado ou de outro ano: "Projeto não encontrado ou arquivado." (a página recarrega; nada é gravado).
- Sem ano: "Nenhum ano aberto. Abra um ano no admin para preencher as variáveis."

## Permissões

- Login obrigatório; sem login vai ao login do admin.
- Ver: permissão de ver ou de alterar projetos; sem ela, 403.
- Gravar e copiar: permissão de alterar projetos; sem ela, só leitura e qualquer envio dá 403.
- Mesmas regras da aba Variáveis do admin (a regra é a mesma, compartilhada).

## HTMX

- Página inteira por GET normal; salvar é um envio comum do formulário (grava e volta à página).
- "Copiar de <ano anterior>": `hx-post` sem enviar a planilha, troca só a linha (`outerHTML` no `<tbody>` do projeto; `id` fixo no botão para o foco voltar a ele) e as mensagens (fora do alvo). A linha volta com os valores gravados como novo "original", então o contador continua certo. Sem JS, o mesmo botão envia um formulário comum e a página recarrega.
- Projeto que sumiu ou foi arquivado no meio: a resposta pede recarga da página inteira.

## Wireframe

```
┌─ Revista Eletrônica   Painel  Cortes  [Variáveis]  Matrizes  Templates  Revistas  Impresso   Ana  Admin  Sair ┐
│                                                                                                              │
│ Variáveis                                                         [Ver painel de 2026]                       │
│ Valores que os textos dos templates usam em cada projeto do ano.                                              │
│ [2026] 2025 2024                                                                                             │
│ (só leitura: aviso amarelo aqui)                                                                             │
│ Preencha as células e salve. Padrões vazios usam o nome do ano (em cinza na célula).                          │
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
│ ─────────────────────────────────────────────────────────────────────────────────────────────────────────── │
│ 2 projeto(s) com alteração não salva.                                              [Salvar variáveis]  (fixa) │
└──────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

No celular (390 px): mesma planilha com rolagem lateral dentro da caixa, 1ª coluna estreita e fixa; a barra de salvar ocupa a largura toda.

## Critérios de aceite

1. Com permissão de alterar projetos, a planilha do ano abre com uma linha por projeto ativo, as 24 colunas e o botão "Salvar variáveis".
2. Padrão 1 a 5 vazios mostram "padrão do ano: <nome>"; a legenda mostra onde cada variável aparece e "escala do F1" nos padrões.
3. Salvar grava só as células alteradas, mostra "Variáveis salvas em N projeto(s)." e não sobrescreve coluna mudada por outra pessoa depois da carga.
4. Projeto aberto por outra pessoa é pulado e listado em "Pulados: …"; os outros gravam.
5. Mais de 200 caracteres: nada grava, a célula fica marcada e aparece "Nada foi gravado: corrija os erros marcados."
6. Sem permissão de alterar: aviso de só leitura, células travadas, sem botões; envio dá 403. Sem permissão de ver: 403. Sem login: vai ao login.
7. "Copiar de <ano anterior>" pelo HTMX devolve só a linha com os valores novos e a mensagem; sem JS, recarrega a página com a mesma mensagem. Só preenche as vazias.
8. Ano sem projetos mostra o estado vazio com o caminho para os cortes.

## Referências técnicas

- Regra: `app/nucleo/planilha_variaveis.py` (extraída de `admin/variaveis.py`, que passa a importá-la).
- Tela: `app/nucleo/urls/ui_variaveis.py`, `templates/ui/variaveis/pagina.html`, `templates/ui/parciais/variaveis_linha.html`, `static/ui/telas/variaveis.css`.
- Decisões: D-093, D-100, D-107, D-119, D-121, D-164, D-167, D-172, D-173, D-175, D-183, D-186. Inventário: T17.
