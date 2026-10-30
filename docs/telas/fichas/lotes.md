# Ficha: Lotes (Escolher matriz · Escolher template F1/F2)

## Objetivo

Atribuir, de uma vez, a mesma matriz a vários parceiros do ano, ou o mesmo template F1/F2 a várias revistas de um componente. Nada é atribuído sozinho: alguém escolhe e aplica. Quem está com o projeto aberto não perde trabalho: o projeto dele é pulado e listado.

## Quem usa

| Perfil | O que faz |
|---|---|
| Pedagógica, Mídias Digitais, Admin | Escolhem e aplicam (permissão de alterar parceiro do ano / fascículo da revista) |
| Impresso | Só vê qual matriz e quais templates cada um tem; não aplica |
| Sem nenhuma das permissões | Não entra (acesso negado) |

## Na jornada

- **Antes:** a grade de cortes cria os projetos e as revistas do ano; as matrizes e os templates do ano já existem (cadastro de matrizes e de templates).
- **Escolher matriz → Escolher template:** primeiro a matriz de cada parceiro, depois o template de cada revista.
- **Depois:** a revista (textos por seção, Validado) e o painel da temporada, onde a falta de matriz ou template aparece.

## Uma tela, duas abas

`/ui/lotes/<ano>/matriz/` e `/ui/lotes/<ano>/template/?componente=<id>`. As abas "Escolher matriz" e "Escolher template F1/F2" são links (a aba é a URL). O seletor de ano troca o ano mantendo a aba. Na aba de template, o seletor de componente vem logo abaixo; sem `?componente`, abre o primeiro componente do ano (por código).

## Dados mostrados

**Escolher matriz** (um parceiro por linha, ordem alfabética):
- Parceiro.
- Matriz atual (ou "sem matriz").
- Situação: "Em edição por Ana: será pulado" quando alguém está com o projeto aberto; "Sem projeto ativo" quando o parceiro não tem projeto ativo (grava assim mesmo).
- Ao escolher uma matriz no rodapé, as linhas marcadas mostram "→ Nova" ao lado da atual (prévia do que vai mudar).

**Escolher template F1/F2** (uma revista ativa do componente por linha, ordem do projeto):
- Revista (projeto).
- Template F1 atual e Template F2 atual (ou "sem template").
- Selo "texto próprio" no fascículo que já tem seção editada pelo projeto: trocar esse fascículo no lote é pulado.
- Situação: "Em edição por Ana: será pulado".
- Revistas e projetos arquivados não aparecem.

## Dados gravados

- Matriz: a matriz do parceiro no ano.
- Template: o template F1 e/ou F2 de cada revista marcada. Fascículo deixado em "Não mudar" fica como está.
- Cada parceiro/revista é gravado sozinho, com o bloqueio do projeto; um erro num não desfaz os outros.

## Ações

| Ação | Quem | Resultado |
|---|---|---|
| Marcar / desmarcar linha; "Marcar todos" no cabeçalho | quem aplica | contador "N selecionado(s)" no rodapé |
| Escolher a matriz (ou F1/F2) no rodapé | quem aplica | prévia "→ Nova" nas linhas marcadas (só matriz) |
| Aplicar aos selecionados | quem aplica | grava, mostra mensagens, atualiza a tabela e limpa a seleção |
| Trocar ano / aba / componente | todos | outra página (GET) |

## Estados

- **Vazio:** ano sem parceiros → "Nenhum parceiro em <ano>. Os parceiros entram no ano pela grade de cortes." + botão "Abrir cortes". Componente sem revistas ativas → "Nenhuma revista ativa de <CC> em <ano>. As revistas nascem dos cortes." + "Abrir cortes". Ano sem matriz → o seletor mostra só "Escolha a matriz" e a ajuda "Nenhuma matriz em <ano>: cadastre em Matrizes." Ano sem componentes → "Nenhum componente em <ano>. Cadastre os componentes no admin."
- **Erro de formulário:** nada gravado; a seleção e as escolhas ficam; mensagem "Nada foi gravado: corrija os erros marcados." e, no campo:
  - nenhuma linha marcada: "Marque ao menos um parceiro." / "Marque ao menos uma revista."
  - sem matriz: "Escolha a matriz."
  - sem template: "Escolha o template do F1, do F2 ou dos dois."
  - opção fora da lista (outra aba, outro ano): "Escolha uma opção da lista; a lista mudou desde que a página abriu."
- **Só leitura (Impresso):** aviso "Só leitura: seu perfil vê as atribuições, mas não altera. Para alterar, peça a permissão a um administrador."; sem caixas de marcar, sem rodapé de aplicar.
- **Bloqueio:** a tela não trava nada ao abrir. Ao aplicar, projeto aberto por outra sessão (outra pessoa ou outra aba sua) ou arquivado entre a abertura e o clique é pulado: "Pulados: GO (projeto em edição por Ana); PE (projeto arquivado)."
- **Sucesso:** "Matriz M2026 escolhida para 3 parceiro(s)." / "Template escolhido em 4 revista(s)." A tabela volta com os valores novos.

## Permissões

- Login obrigatório; anônimo vai ao login do admin.
- Escolher matriz: ver com `view_parceiroano` ou `change_parceiroano`; aplicar com `change_parceiroano`.
- Escolher template: ver com `view_revistafasciculo` ou `change_revistafasciculo`; aplicar com `change_revistafasciculo`.
- Aplicar sem a permissão → acesso negado (403), nada gravado.

## HTMX

- O formulário envia por `hx-post` e troca a si mesmo (`outerHTML`); as mensagens vêm fora do alvo (`oob`). Sem JS, o mesmo formulário envia normal e volta pela página (PRG).
- Erro de rede/servidor: toast da base. Erro de validação: 200 com o formulário e os erros.
- Marcar todos, contador e prévia "→ Nova" são JS pequeno por delegação (valem depois da troca).

## Wireframe (1440 px)

```
Revista Eletrônica   Painel Cortes Variáveis Matrizes Templates Revistas Impresso      Ana [Admin] [Sair]
─────────────────────────────────────────────────────────────────────────────────────────────────────────
Lotes                                                                         [Ver painel de 2026]
Atribua a mesma matriz ou o mesmo template a vários de uma vez.
[ 2026 | 2025 ]
 Escolher matriz   Escolher template F1/F2
 ───────────────   ────────────────────────
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│ [■] Parceiro            Matriz                         Situação                              │
│ [✓] GO                  M2025  → M2026                 (Em edição por Ana: será pulado)       │
│ [✓] PE                  sem matriz → M2026                                                    │
│ [ ] SP                  M2026                          (Sem projeto ativo)                    │
└──────────────────────────────────────────────────────────────────────────────────────────────┘
 Projetos em edição por outra sessão são pulados e listados.
─────────────────────────────────────────────────────────────────────────── (rodapé fixo) ───────
 2 selecionado(s)                         Matriz [ M2026          ▾]   [Aplicar aos selecionados]
```

Aba de template: abaixo das abas, `[ LP | MT ]`; colunas Revista · Template F1 · Template F2 · Situação; rodapé com `F1 [Não mudar ▾]  F2 [Não mudar ▾]`.

390 px: a tabela rola na horizontal dentro da caixa; o rodapé quebra em linhas (contador, campos, botão inteiro).

## Critérios de aceite

1. Pedagógica abre `/ui/lotes/2026/matriz/`: vê os parceiros com a matriz atual, as caixas de marcar e "Aplicar aos selecionados".
2. Marca GO e PE, escolhe a matriz Nova e aplica: os dois ficam com Nova e aparece "Matriz Nova escolhida para 2 parceiro(s)."
3. Com o projeto de GO aberto por outra pessoa: GO é pulado ("Pulados: GO (projeto em edição por …).") e a linha já mostrava "Em edição por …".
4. Aplicar sem marcar nada: 200, "Nada foi gravado…" e "Marque ao menos um parceiro."; nada muda.
5. Matriz de outro ano não aparece e, se enviada, é recusada.
6. Template: só templates do mesmo ano, componente e fascículo; revista com texto próprio no F1 é pulada no F1; F2 em "Não mudar" não muda; sem F1 nem F2 → "Escolha o template do F1, do F2 ou dos dois."
7. Impresso vê as duas abas em só leitura; POST → 403. Sem permissão de ver → 403. Anônimo → login do admin.
8. Via HTMX, a resposta é o formulário com os valores novos e as mensagens fora do alvo.
9. O lote do admin segue funcionando (mesma regra).

## Referências técnicas

- Regra: `app/nucleo/lotes.py` (forms, `gravar_matriz`, `gravar_template`, `escrever_travado`, `aplicar`, `em_edicao`), usada pelo admin (`admin/lote.py`) e pela página B (`urls/ui_lotes.py`).
- Decisões: D-102 (atribuição em lote), D-104 (troca de template com cópias), D-121 (pular travados), D-164/D-167 (lotes no admin, arquivados), D-183/D-186 (telas B, HTMX).
- Inventário: T18, T19.
